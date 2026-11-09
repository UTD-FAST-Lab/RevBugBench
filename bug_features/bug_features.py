"""Per-bug features for RevBugBench injected bugs, in the spirit of FeatureBench.

Input: the RevBugBench dda.json files (../ddas) and the program sources at
RevBugBench's pinned commits, unpatched and unbuilt (--sources; fetch them with
the commits in each benchmark's Dockerfile). Output: data/bug_features.csv, one
row per injected bug. bug_features_methodology.md documents every column.

Guard features, from dda.json (FixReverter's own analysis):
- pattern (COND_ABORT / COND_ASSIGN / COND_EXEC), statement type
- guard kind: null check, numeric comparison, pointer range
- uses_field: the guard reads a struct field
- n_conditions: 1 + number of && / || in the guard
- magic_const: the guard compares against a literal other than 0, 1, -1,
  NULL or '\\0' (FeatureBench's "magic bytes"); const_bytes: bytes needed
  for the largest such literal

Static features, from clang-18 on the unpatched source (FeatureBench's
control-flow features):
- call_depth: shortest call-graph distance from LLVMFuzzerTestOneInput to
  the bug's function (direct calls only; NaN if only reachable through
  function pointers or not reachable)
- fan_in: number of distinct direct callers of the function
- recursive: the function is in a call-graph cycle
- nest_depth: enclosing if / loop / switch statements inside the function
- loop_depth, in_loop: enclosing for / while / do statements
- func_branches: if, loop, case, ?: and && / || nodes in the function
  (a cyclomatic-complexity proxy); func_lines
- path_conditions, path_loop_depth, path_hard_checks: the same counts summed
  over the whole call path from LLVMFuzzerTestOneInput (fewest over known
  direct-call paths)
- hard_checks, checksum_checks: enclosing hard checks (equality with a
  non-trivial constant, string compare with a literal, switch on non-trivial
  case labels, or checksum comparison) on the branch that leads to the bug
- guard_loop_counter, guard_recursion_counter, guard_checksum: the bug's
  condition reads an enclosing loop's counter, a recursion-depth parameter, or
  compares a checksum
Generated headers are replaced by stubs (config.h with common Linux HAVE_*
defines; a minimal Linux curl_config.h; libxml2's xmlversion.h from its .in
template with optional modules on; per-program stubs in stubs/<program>/), so
some #if branches may differ from the real build. Static functions are matched
by name, so same-named static functions in different files are merged in the
call graph.
"""

import argparse
import heapq
import json
import os
import re
import subprocess
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

HERE = Path(__file__).parent
DDAS = HERE.parent / "ddas"
OUTPUT = HERE / "data" / "bug_features.csv"
STUBS = HERE / "bug_feature_stubs"
ENTRY = "LLVMFuzzerTestOneInput"

# program: (path prefix in dda.json, source dir, call-graph sources, include dirs,
#           harness files, extra call edges for calls clang can't see; the libxml2
#           harness is C++ that clang-18 can't parse with the installed libstdc++, so
#           its library calls are listed by hand)
# Call-graph source patterns starting with "!" remove matching files (for example
# command-line tools that sit next to the library but aren't in the fuzz target).
PROGRAMS = {
    "binutils-fuzz_cxxfilt": ("/src/binutils-gdb", "binutils-gdb",
                              ["libiberty/*.c", "binutils/cxxfilt.c"], ["include", "binutils", "bfd"],
                              ["fuzz_cxxfilt.c"], [(ENTRY, "demangle_it"), ("demangle_it", "cplus_demangle")]),
    "curl": ("/src/curl", "curl", ["lib/**/*.c", "src/*.c"], ["include", "lib", "../curl_fuzzer"],
             ["../curl_fuzzer/curl_fuzzer.cc", "../curl_fuzzer/curl_fuzzer_callback.cc",
              "../curl_fuzzer/curl_fuzzer_tlv.cc"], []),
    "lcms": ("/src/Little-CMS", "lcms", ["src/*.c"], ["include", "src"],
             ["cms_transform_fuzzer.cc"], []),
    "libpcap": ("/src/libpcap", "libpcap", ["*.c"], ["."],
                ["testprogs/fuzz/fuzz_both.c"], []),
    "libxml2_reader": ("/src/libxml2", "libxml2", ["*.c"], ["include", "."],
                       [], [(ENTRY, f) for f in ("xmlReaderForFile", "xmlTextReaderRead", "xmlTextReaderNodeType",
                                                 "xmlTextReaderConstValue", "xmlFreeTextReader")]),
    # libxml2 v2.9.2, a different version from libxml2_reader's checkout; harness calls from target.cc
    "libxml2_xml": ("/src/libxml2", "libxml2_v2.9.2", ["*.c"], ["include", "."],
                    [], [(ENTRY, f) for f in ("xmlSetGenericErrorFunc", "xmlReadMemory", "xmlFreeDoc")]),
    # libproj_la_SOURCES in src/Makefile.am: src/*.c minus the tools and files it leaves out
    "proj4": ("/src/PROJ", "PROJ",
              ["src/*.c"] + [f"!src/{f}" for f in (
                  "PJ_minimal.c", "cs2cs.c", "gen_cheb.c", "geod.c", "geod_interface.c", "geod_set.c", "geodtest.c",
                  "hypot.c", "multistresstest.c", "nad2bin.c", "p_series.c", "proj.c", "test228.c")],
              ["src"], ["test/fuzzers/standard_fuzzer.cpp"], []),
    # FUZZ_SRC in tests/fuzz/Makefile, target stream_decompress
    "zstd": ("/src/zstd", "zstd",
             ["lib/common/*.c", "lib/compress/*.c", "lib/decompress/*.c", "lib/dictBuilder/*.c", "lib/legacy/*.c",
              "programs/util.c", "tests/fuzz/zstd_helpers.c"],
             ["lib", "lib/common", "lib/compress", "lib/dictBuilder", "lib/deprecated", "lib/legacy", "programs",
              "tests/fuzz"],
             ["tests/fuzz/stream_decompress.c"], []),
}
CONTROL = {"IfStmt", "ForStmt", "WhileStmt", "DoStmt", "SwitchStmt"}
LOOPS = {"ForStmt", "WhileStmt", "DoStmt"}
BRANCHES = {"IfStmt", "ForStmt", "WhileStmt", "DoStmt", "CaseStmt", "ConditionalOperator"}
WARNINGS = ["-Wno-error=implicit-function-declaration", "-Wno-error=implicit-int", "-Wno-error=int-conversion",
            "-Wno-error=incompatible-function-pointer-types", "-Wno-register"]
DEFINES = {"curl": ["-DHAVE_CONFIG_H"], "binutils-fuzz_cxxfilt": ["-DHAVE_CONFIG_H"], "libpcap": ["-DHAVE_CONFIG_H"],
           "lcms": ["-DHAVE_CONFIG_H"],
           # src/Makefile.am AM_CPPFLAGS and configure.ac on Linux
           "proj4": ["-DMUTEX_pthread", "-DHAVE_C99_MATH=1", '-DPROJ_LIB="/usr/local/share/proj"'],
           # tests/fuzz/Makefile FUZZ_CPPFLAGS plus fuzz.py's defaults
           "zstd": ["-DZSTD_MULTITHREAD", "-DZSTD_LEGACY_SUPPORT=1", "-DDEBUGLEVEL=1", "-DMEM_FORCE_MEMORY_ACCESS=0",
                    "-DFUZZ_RNG_SEED_SIZE=4"]}
TRIVIAL = {"0", "1", "-1", "NULL", "'\\0'", "0L", "0U", "0UL", "1U"}

# Hard checks (features 4 and 5). Functions whose return value is a checksum, from a survey of the 8 programs'
# sources: zstd's XXH32/XXH64 (also under ZSTD_ namespacing), libiberty's crc32/xcrc32, libxml2's crc32. The
# MD5 routines in curl, lcms and libiberty fill digest buffers instead, so they don't appear in comparisons.
CHECKSUM_FUNC = re.compile(r"(^|_)(XXH(32|64)(_digest)?|x?crc32|adler32|checksum|cksum)$", re.I)
# String/memory compares: zero means equal (STR_CMP_ZERO) or nonzero means equal (STR_CMP_TRUE).
STR_CMP_ZERO = {"strcmp", "strncmp", "memcmp", "bcmp", "strcasecmp", "strncasecmp", "xmlStrcmp", "xmlStrncmp",
                "xmlStrcasecmp", "xmlStrncasecmp", "cmsstrcasecmp"}
STR_CMP_TRUE = {"xmlStrEqual", "xmlStrQEqual", "Curl_strcasecompare", "Curl_strncasecompare",
                "Curl_safe_strcasecompare"}
WRAPPERS = {"ImplicitCastExpr", "ParenExpr", "CStyleCastExpr", "ConstantExpr", "FullExpr", "ExprWithCleanups"}


def guard_features(e):
    tags = [i.get("tag", "").split("[")[0] for i in e["ids"]]
    by_order = {i["order"]: i.get("tag", "").split("[")[0] for i in e["ids"]}
    literals = []
    for tok in e["tokenOrder"][1:]:
        tag = by_order.get(tok["order"], "")
        if tag == "endSpot" or tag.startswith("traceVarAssign"):
            break
        if not tag and re.fullmatch(r"-?(0x[0-9a-fA-F]+|\d+)[uUlL]*|'.*'|NULL", tok["val"]):
            literals.append(tok["val"])
    magic = [v for v in literals if v not in TRIVIAL]

    def nbytes(v):
        if v.startswith("'"):
            return 1
        n = abs(int(re.sub(r"[uUlL]+$", "", v), 0))
        return max(1, (n.bit_length() + 7) // 8)

    return {
        "pattern": e["pattern"],
        "stmt_type": e["stmt"]["type"],
        "guard_null": any("NullCheck" in t for t in tags),
        "guard_num": any("NumCmp" in t for t in tags),
        "guard_ptr_range": any("PtrRange" in t for t in tags),
        "uses_field": any(t.endswith("Field") for t in tags),
        "n_conditions": 1 + tags.count("logic"),
        "magic_const": bool(magic),
        "const_bytes": max((nbytes(v) for v in magic), default=0),
    }


def clang(args, cwd):
    return subprocess.run(["clang-18", "-w", "-ferror-limit=0", *args], cwd=cwd,
                          capture_output=True, text=True, errors="replace").stdout


def flags(root, includes, stubs, path, defines=()):
    cxx = ["-x", "c++", "-std=c++17"] if path.endswith((".cc", ".cpp")) else []
    return (cxx + WARNINGS + list(defines) + [f"-I{s}" for s in stubs] + [f"-I{Path(path).parent}"]
            + [f"-I{root / i}" for i in includes])


def call_graph(root, sources, includes, harness, extra, stubs, jobs, defines):
    """Direct-call edges, and the files that define each function."""
    keep = {str(p) for pat in sources if not pat.startswith("!") for p in root.glob(pat)}
    drop = {str(p) for pat in sources if pat.startswith("!") for p in root.glob(pat[1:])}
    files = sorted(keep - drop) + [str(h) for h in harness]

    def one(path):
        out = subprocess.run(["clang-18", "--analyze", "-Xanalyzer", "-analyzer-checker=debug.DumpCallGraph",
                              "-w", "-ferror-limit=0", *flags(root, includes, stubs, path, defines), path, "-o", "/dev/null"],
                             cwd=root, capture_output=True, text=True, errors="replace").stderr
        return path, re.findall(r"Function: (\S+) calls: ([^\n]*)", out)

    edges, defined_in = defaultdict(set), defaultdict(set)
    with ThreadPoolExecutor(jobs) as pool:
        for path, found in pool.map(one, files):
            for caller, callees in found:
                if caller != "<":
                    edges[caller].update(callees.split())
                    defined_in[caller].add(path)
    for a, b in extra:
        edges[a].add(b)
    return edges, defined_in


def depths(edges):
    dist, queue = {ENTRY: 0}, deque([ENTRY])
    while queue:
        f = queue.popleft()
        for g in edges.get(f, ()):
            if g not in dist:
                dist[g] = dist[f] + 1
                queue.append(g)
    return dist


def path_minimum(edges, weight):
    """Fewest weighted steps from ENTRY to each function (Dijkstra); weight(caller, callee) >= 0."""
    dist, heap = {ENTRY: 0}, [(0, ENTRY)]
    while heap:
        d, f = heapq.heappop(heap)
        if d > dist[f]:
            continue
        for g in edges.get(f, ()):
            nd = d + weight(f, g)
            if nd < dist.get(g, float("inf")):
                dist[g] = nd
                heapq.heappush(heap, (nd, g))
    return dist


def recursive_functions(edges):
    index, low, stack, on, out, counter = {}, {}, [], set(), set(), [0]

    def visit(v):
        work = [(v, iter(edges.get(v, ())))]
        index[v] = low[v] = counter[0]; counter[0] += 1; stack.append(v); on.add(v)
        while work:
            node, it = work[-1]
            for w in it:
                if w not in index:
                    index[w] = low[w] = counter[0]; counter[0] += 1; stack.append(w); on.add(w)
                    work.append((w, iter(edges.get(w, ()))))
                    break
                if w in on:
                    low[node] = min(low[node], index[w])
            else:
                work.pop()
                if work:
                    low[work[-1][0]] = min(low[work[-1][0]], low[node])
                if low[node] == index[node]:
                    comp = []
                    while True:
                        w = stack.pop(); on.discard(w); comp.append(w)
                        if w == node:
                            break
                    if len(comp) > 1 or node in edges.get(node, ()):
                        out.update(comp)

    for v in list(edges):
        if v not in index:
            visit(v)
    return out


def begin_offset(node):
    b = node.get("range", {}).get("begin", {})
    return b.get("expansionLoc", b).get("offset")


def json_objects(text):
    decoder, i = json.JSONDecoder(), 0
    while (i := text.find("{", i)) != -1:
        try:
            obj, end = decoder.raw_decode(text, i)
        except json.JSONDecodeError:
            i += 1
            continue
        yield obj
        i = end


# ---- AST helpers for the condition features ---------------------------------------------------------------

def nodes(n):
    """All dict nodes in a subtree."""
    stack = [n]
    while stack:
        x = stack.pop()
        if isinstance(x, dict) and x:
            yield x
            stack.extend(x.get("inner", []))


def strip(n):
    while isinstance(n, dict) and n.get("kind") in WRAPPERS and n.get("inner"):
        n = n["inner"][0]
    return n


def const_value(n):
    """Integer value of a literal (macros are already expanded in the AST), else None."""
    n = strip(n)
    kind = n.get("kind") if isinstance(n, dict) else None
    if kind in ("IntegerLiteral", "CharacterLiteral"):
        return int(n["value"])
    if kind == "UnaryOperator" and n.get("opcode") == "-":
        v = const_value(n["inner"][0])
        return -v if v is not None else None
    return None


def callee(n):
    if n.get("kind") != "CallExpr" or not n.get("inner"):
        return None
    c = strip(n["inner"][0])
    ref = c.get("referencedDecl", {}) if c.get("kind") == "DeclRefExpr" else {}
    return ref.get("name") if ref.get("kind") == "FunctionDecl" else None


def refs(n):
    return {x["referencedDecl"]["id"] for x in nodes(n) if x.get("kind") == "DeclRefExpr" and "referencedDecl" in x}


def is_checksum(n, ck_vars):
    return any(CHECKSUM_FUNC.search(callee(x) or "-") for x in nodes(n)) or bool(refs(n) & ck_vars)


def hard_kinds(cond, ck_vars):
    """Which hard checks must pass to enter each branch: (then-branch kinds, else-branch kinds), each a subset
    of {"magic", "checksum"}. && needs every conjunct for the then-branch; || needs every disjunct to fail."""
    n = strip(cond)
    kind, op = n.get("kind"), n.get("opcode")
    inner = n.get("inner", [])
    if kind == "UnaryOperator" and op == "!":
        t, e = hard_kinds(inner[0], ck_vars)
        return e, t
    if kind == "BinaryOperator" and op in ("&&", "||"):
        (lt, le), (rt, re_) = hard_kinds(inner[0], ck_vars), hard_kinds(inner[1], ck_vars)
        return (lt | rt, le & re_) if op == "&&" else (lt & rt, le | re_)
    if kind == "BinaryOperator" and op in ("==", "!="):
        left, right = inner[0], inner[1]
        if const_value(right) == 0 or const_value(left) == 0:      # x == 0 is !x, x != 0 is x
            t, e = hard_kinds(left if const_value(right) == 0 else right, ck_vars)
            return (e, t) if op == "==" else (t, e)
        found = set()
        if any(v is not None and v not in (0, 1, -1) for v in (const_value(left), const_value(right))):
            found.add("magic")
        if is_checksum(left, ck_vars) or is_checksum(right, ck_vars):
            found.add("checksum")
        return (found, set()) if op == "==" else (set(), found)
    if kind == "CallExpr":
        name = callee(n)
        literal = any(strip(a).get("kind") == "StringLiteral" for a in inner[1:] if isinstance(a, dict))
        if literal and name in STR_CMP_ZERO:      # strcmp(s, "x") is true when they differ
            return set(), {"magic"}
        if literal and name in STR_CMP_TRUE:
            return {"magic"}, set()
    return set(), set()


def condition(node):
    """The condition expression of a control statement."""
    kind, inner = node.get("kind"), node.get("inner", [])
    i = {"IfStmt": int(bool(node.get("hasInit"))) + int(bool(node.get("hasVar"))),
         "SwitchStmt": int(bool(node.get("hasInit"))) + int(bool(node.get("hasVar"))),
         "WhileStmt": int(bool(node.get("hasVar"))), "ForStmt": 2, "DoStmt": 1}[kind]
    return inner[i] if i < len(inner) and isinstance(inner[i], dict) and inner[i] else {}


def modified(n):
    """Variables changed by ++, --, = or op= in a subtree."""
    out = set()
    for x in nodes(n):
        kind, op = x.get("kind"), x.get("opcode")
        target = None
        if kind == "UnaryOperator" and op in ("++", "--"):
            target = x["inner"][0]
        elif kind == "CompoundAssignOperator" or (kind == "BinaryOperator" and op == "="):
            target = x["inner"][0]
        target = strip(target) if target else None
        if target and target.get("kind") == "DeclRefExpr" and "referencedDecl" in target:
            out.add(target["referencedDecl"]["id"])
    return out


def loop_counters(node):
    """Variables a loop counts with: changed in a for's increment, or read in the condition and changed in the body."""
    inner = node.get("inner", [])
    cond = condition(node)
    body = inner[0] if node["kind"] == "DoStmt" else inner[-1] if inner else {}
    counters = refs(cond) & modified(body) if cond else set()
    if node["kind"] == "ForStmt" and len(inner) > 3 and inner[3]:
        counters |= modified(inner[3])
    return counters


EXITS = {"ReturnStmt", "GotoStmt", "BreakStmt", "ContinueStmt"}
NORETURN = {"abort", "exit", "_exit", "longjmp", "siglongjmp", "__assert_fail"}


def always_exits(stmt):
    """The statement always leaves the enclosing block: return/goto/break/continue, a noreturn call, or a
    block that ends in one."""
    stmt = strip(stmt) if isinstance(stmt, dict) else {}
    kind = stmt.get("kind")
    if kind in EXITS or (kind == "CallExpr" and callee(stmt) in NORETURN):
        return True
    if kind == "CompoundStmt":
        inner = [c for c in stmt.get("inner", []) if isinstance(c, dict) and c]
        return bool(inner) and always_exits(inner[-1])
    return False


def guard_clause(stmt):
    """The IfStmt of a guard clause `if (cond) <exit>;` with no else, else None."""
    if not isinstance(stmt, dict) or stmt.get("kind") != "IfStmt" or stmt.get("hasElse"):
        return None
    cond = condition(stmt)
    raw = stmt.get("inner", [])
    ci = next((j for j, c in enumerate(raw) if c is cond), None)
    return stmt if ci is not None and ci + 1 < len(raw) and always_exits(raw[ci + 1]) else None


def analyze_function(path, func, offsets, root, includes, stubs, defines):
    """Features of a function's bug statements (by start offset) and of its call sites."""
    out = clang(["-fsyntax-only", *flags(root, includes, stubs, str(path), defines), "-Xclang", "-ast-dump=json",
                 "-Xclang", f"-ast-dump-filter={func}", str(path)], cwd=path.parent)
    decl = None
    for node in json_objects(out):
        if node.get("kind") == "FunctionDecl" and node.get("name") == func and \
                any(c.get("kind") == "CompoundStmt" for c in node.get("inner", [])):
            decl = node
    if decl is None:
        return None

    # checksum values held in variables, and parameters that count recursion depth (self-calls only)
    ck_vars, params = set(), [c["id"] for c in decl.get("inner", []) if c.get("kind") == "ParmVarDecl"]
    rec_params = set()
    for x in nodes(decl):
        kind = x.get("kind")
        if kind == "VarDecl" and x.get("inner") and is_checksum(x["inner"][0], set()):
            ck_vars.add(x["id"])
        elif kind == "BinaryOperator" and x.get("opcode") == "=":
            lhs = strip(x["inner"][0])
            if lhs.get("kind") == "DeclRefExpr" and is_checksum(x["inner"][1], set()):
                ck_vars.add(lhs["referencedDecl"]["id"])
        elif kind == "CallExpr" and callee(x) == func:
            for k, arg in enumerate(x.get("inner", [])[1:]):
                a = strip(arg)
                if k < len(params) and (a.get("kind") == "BinaryOperator" and a.get("opcode") in ("+", "-") or
                                        a.get("kind") == "UnaryOperator" and a.get("opcode") in ("++", "--")) \
                        and params[k] in refs(a):
                    rec_params.add(params[k])

    found, calls, branches = {}, [], [0]

    def entry(node, kinds=frozenset()):
        return {"nest": True, "loop": node["kind"] in LOOPS, "hard": bool(kinds), "checksum": "checksum" in kinds,
                "counters": loop_counters(node) if node["kind"] in LOOPS else set(), "kind": node["kind"]}

    def walk(node, stack):
        kind = node.get("kind")
        if kind in BRANCHES or (kind == "BinaryOperator" and node.get("opcode") in ("&&", "||")):
            branches[0] += 1
        if kind == "CallExpr" and (name := callee(node)):
            calls.append((name, sum(s["nest"] for s in stack), sum(s["loop"] for s in stack),
                          sum(s["hard"] for s in stack)))
        off = begin_offset(node)
        if kind in CONTROL and off in offsets and off not in found:
            cond = condition(node)
            t, e = hard_kinds(cond, ck_vars) if cond else (set(), set())
            grefs = refs(cond) if cond else set()
            counters = set().union(*(s["counters"] for s in stack if s["loop"]))
            found[off] = {"nest_depth": sum(s["nest"] for s in stack), "loop_depth": sum(s["loop"] for s in stack),
                          "hard_checks": sum(s["hard"] for s in stack),
                          "checksum_checks": sum(s["checksum"] for s in stack),
                          "guard_loop_counter": bool(grefs & counters),
                          "guard_recursion_counter": bool(grefs & rec_params),
                          "guard_checksum": "checksum" in (t | e)}
        inner = [c for c in node.get("inner", []) if isinstance(c, dict) and c]
        if kind not in CONTROL:
            if kind == "DefaultStmt":      # the default label of the nearest switch isn't a hard check
                i = max((j for j, s in enumerate(stack) if s["kind"] == "SwitchStmt"), default=None)
                if i is not None:
                    stack = stack[:i] + [{**stack[i], "hard": False}] + stack[i + 1:]
            added = []
            for c in inner:
                sub = walk(c, stack)
                if kind != "CompoundStmt":
                    continue
                # a guard clause (if (cond) return/goto/break/continue;) protects every later statement in the
                # block: they need its else-branch, so its hard checks count for them (but not as nesting).
                # A nested plain { } block passes its guard clauses on to the statements after it.
                new = list(sub) if c.get("kind") == "CompoundStmt" else []
                if (g := guard_clause(c)) is not None:
                    _, e = hard_kinds(condition(g), ck_vars)
                    if e:
                        new.append({"nest": False, "loop": False, "hard": True, "checksum": "checksum" in e,
                                    "counters": set(), "kind": "GuardClause"})
                stack, added = stack + new, added + new
            return added
        # control statement: its condition (and a for's init) run outside it, its branches/body inside it
        raw = node.get("inner", [])
        cond = condition(node)
        if kind == "IfStmt":
            t, e = hard_kinds(cond, ck_vars) if cond else (set(), set())
            ci = next((j for j, c in enumerate(raw) if c is cond), len(raw))
            for j, c in enumerate(raw):
                if isinstance(c, dict) and c:
                    walk(c, stack if j <= ci else stack + [entry(node, t if j == ci + 1 else e)])
        elif kind == "SwitchStmt":
            ci = next((j for j, c in enumerate(raw) if c is cond), len(raw))
            body = raw[-1] if raw else {}
            magic = any(x.get("kind") == "CaseStmt" and x.get("inner") and
                        (v := const_value(x["inner"][0])) is not None and v not in (0, 1, -1) for x in nodes(body))
            for j, c in enumerate(raw):
                if isinstance(c, dict) and c:
                    walk(c, stack if j <= ci else stack + [entry(node, {"magic"} if magic else set())])
        else:      # loops: condition and for-init outside, body (and increment) inside
            body = raw[0] if kind == "DoStmt" else raw[-1] if raw else {}
            for c in raw:
                if isinstance(c, dict) and c:
                    walk(c, stack + [entry(node)] if c is body else stack)

    walk(decl, [])
    rng = decl["range"]
    text = path.read_bytes()
    lines = text[begin_offset(decl):rng["end"].get("offset", begin_offset(decl))].count(b"\n") + 1
    return {"stmts": {off: {**v, "func_branches": branches[0], "func_lines": lines} for off, v in found.items()},
            "calls": calls}


def base_name(func):
    """libxml2's real build (-DPIC) renames exported functions to X__internal_alias via elfgcchack.h,
    and dda.json records that name. Our parse doesn't define PIC, so look functions up by X."""
    return func.removesuffix("__internal_alias")


def line_col_to_offset(path_lines, line, col):
    return sum(len(l) for l in path_lines[:line - 1]) + col - 1


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sources", required=True, help="folder with the program checkouts")
    parser.add_argument("--harnesses", required=True, help="RevBugBench benchmarks/ folder (harness files)")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--stubs", default=str(STUBS), help="folder with the stub headers")
    parser.add_argument("--output", default=str(OUTPUT))
    args = parser.parse_args()
    sources, harness_dir = Path(args.sources).resolve(), Path(args.harnesses).resolve()
    stubs = Path(args.stubs).resolve()
    for h in ("config.h", "curl_config.h", "libxml/xmlversion.h", "libxml2_xml/libxml/xmlversion.h",
              "proj4/proj_config.h"):
        if not (stubs / h).exists():
            raise SystemExit(f"missing stub header {stubs / h}; see the module docstring")

    rows = []
    for program, (prefix, srcdir, cg_sources, includes, harness, extra) in PROGRAMS.items():
        root = sources / srcdir
        harness_paths = [(root / h).resolve() if (root / h).exists() else harness_dir / program / h for h in harness]
        defines = DEFINES.get(program, [])
        # a per-program stub folder (stubs/<program>/) goes before the shared stubs
        prog_stubs = [d for d in (stubs / program, stubs) if d.is_dir()]
        edges, defined_in = call_graph(root, cg_sources, includes, harness_paths, extra, prog_stubs, args.jobs,
                                       defines)
        dist, rec = depths(edges), recursive_functions(edges)
        callers = defaultdict(set)
        for a, bs in edges.items():
            for b in bs:
                callers[b].add(a)

        bugs = json.load(open(DDAS / program / "dda.json"))
        groups = defaultdict(list)
        for e in bugs:
            f = e["fileName"] if e["fileName"].startswith("/") else os.path.normpath(os.path.join(e["commandDir"], e["fileName"]))
            path = root / f[len(prefix) + 1:] if f.startswith(prefix + "/") else None
            groups[(path, e["func"]["name"])].append(e)

        # functions to analyze: each bug's function (with its statement offsets) and every function reachable
        # from the entry point (for the call sites on the path)
        tasks, bug_offsets = defaultdict(set), {}
        for (path, func), es in groups.items():
            if path is None or not path.exists():
                continue
            lines = [l + b"\n" for l in path.read_bytes().split(b"\n")]
            offs = {e["index"]: line_col_to_offset(lines, int(e["stmt"]["start"]["line"]), int(e["stmt"]["start"]["col"]))
                    for e in es}
            bug_offsets[(path, func)] = offs
            tasks[(path, base_name(func))] |= set(offs.values())
        for f in dist:
            for p in defined_in.get(f, ()):
                tasks[(Path(p), f)] |= set()

        with ThreadPoolExecutor(args.jobs) as pool:
            results = dict(zip(tasks, pool.map(
                lambda k: analyze_function(k[0], k[1], tasks[k], root, includes, prog_stubs, defines), list(tasks))))

        # call-site weights (fewest conditions / loops / hard checks around any call from caller to callee);
        # an edge with no call site in the AST (hand-listed harness calls, macros) gets weight 0
        site = {}
        for (_, f), res in results.items():
            for name, *w in (res or {}).get("calls", []):
                key = (f, name)
                site[key] = tuple(map(min, site[key], w)) if key in site else tuple(w)
        path_min = [path_minimum(edges, lambda a, b, i=i: site.get((a, b), (0, 0, 0))[i]) for i in range(3)]

        for (path, func), es in groups.items():
            base = base_name(func)
            res = results.get((path, base)) if (path, func) in bug_offsets else None
            for e in es:
                s = (res or {}).get("stmts", {}).get(bug_offsets.get((path, func), {}).get(e["index"]), {})
                reach = bool(s) and base in path_min[0]
                rows.append({"program": program, "bug": e["index"],
                             "file": str(path.relative_to(root)) if path and path.exists() else None,
                             "function": func, **guard_features(e),
                             "static_found": bool(s),
                             **{k: s.get(k) for k in ("nest_depth", "loop_depth", "func_branches", "func_lines")},
                             "in_loop": s["loop_depth"] > 0 if s else None,
                             "call_depth": dist.get(base), "fan_in": len(callers.get(base, ())),
                             "recursive": base in rec,
                             "path_conditions": path_min[0][base] + s["nest_depth"] if reach else None,
                             "path_loop_depth": path_min[1][base] + s["loop_depth"] if reach else None,
                             "path_hard_checks": path_min[2][base] + s["hard_checks"] if reach else None,
                             **{k: s.get(k) for k in ("hard_checks", "checksum_checks", "guard_loop_counter",
                                                      "guard_recursion_counter", "guard_checksum")}})
        found = [r for r in rows if r["program"] == program]
        print(f"{program}: {len(found)} bugs, static features for {sum(r['static_found'] for r in found)}, "
              f"call depth for {sum(r['call_depth'] is not None for r in found)}, "
              f"path features for {sum(r['path_conditions'] is not None for r in found)}; "
              f"{len(edges)} functions in call graph, {len(dist)} reachable from {ENTRY}")

    pd.DataFrame(rows).to_csv(args.output, index=False)
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
