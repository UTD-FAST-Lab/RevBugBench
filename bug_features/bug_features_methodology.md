# Bug feature extraction for RevBugBench (FeatureBench-style)

How `bug_features.py` turns FixReverter's injected bugs into one feature row per bug. Follow it to reproduce `data/bug_features.csv` or to extend it to more programs. The features follow FeatureBench (Miao et al., "Program Feature-Based Benchmarking for Fuzz Testing", ISSTA 2025; `data/3728899.pdf`); §8 maps them to the paper.

Last regenerated on 2026-11-04 (5,889 rows, 30 columns), on Ubuntu 20.04 with clang 18.1.8, glibc 2.31 and OpenSSL 1.1.1f. A rerun on another system can differ slightly: `func_branches` counts branches after macro expansion, so system-header macros (for example glibc's `FD_SET`) and `#if OPENSSL_VERSION_NUMBER` blocks change it. Moving from an earlier, newer system to this one changed 4 of the 3,353 then-existing rows (curl bug 540; libxml2_reader bugs 208–210).

## 1. What it produces

`data/bug_features.csv` has one row per injected bug in 8 of RevBugBench's 10 programs. binutils-fuzz_disassemble and usrsctp are left out because those benchmarks currently have problems.

| Program | Bugs | Static features found | Call depth / path features found | Bugs with a hard check (`hard_checks` > 0) |
|---|---:|---:|---:|---:|
| binutils-fuzz_cxxfilt | 96 | 96 | 96 / 96 | 26 |
| curl | 181 | 154 | 0 / 0 | 47 |
| lcms | 382 | 382 | 132 / 132 | 21 |
| libpcap | 100 | 92 | 8 / 8 | 26 |
| libxml2_reader | 2,594 | 2,587 | 1,211 / 1,210 | 142 |
| libxml2_xml | 2,000 | 1,994 | 803 / 802 | 133 |
| proj4 | 233 | 233 | 55 / 55 | 11 |
| zstd | 303 | 303 | 267 / 267 | 28 |
| **Total** | **5,889** | **5,841** | **2,572 / 2,570** | **434** |

The path features need both a call path and the bug's statement in the AST. That's why they're missing for the 2 bugs in the libxml2 programs whose statement wasn't found.

Features come in two groups:
- **Guard features** come from FixReverter's own record of each bug (`dda.json`), with no compilation.
- **Static features** come from clang-18 run on the program's source, unpatched and unbuilt.

Several static features are approximations, because they're measured on real programs rather than generated ones (§7).

## 2. Inputs

| Input | Where | Notes |
|---|---|---|
| `dda.json` per program | `../ddas/<program>/dda.json` (the repo's `ddas/` folder) | One JSON list per program, one entry per injected bug. The script reads them from this fixed path. |
| Program sources at RevBugBench's pinned commits | Any folder, passed as `--sources` | Unpatched, not built. Folder names must match `PROGRAMS` in the script (table below). |
| RevBugBench `benchmarks/` folder | The repo's `benchmarks/`, passed as `--harnesses` | Supplies the fuzz harness files that are not part of the program source. |
| Stub headers | `bug_feature_stubs/` (default `--stubs`) | See §4.2. |
| clang-18 | `clang-18` on `PATH` | Tested with Ubuntu clang 18.1.8. |
| Python 3.10 with pandas | | |

Source checkouts. Each commit is the one in that benchmark's `Dockerfile` in RevBugBench:

| `--sources` subfolder | Used by | Repository | Commit |
|---|---|---|---|
| `binutils-gdb` | binutils-fuzz_cxxfilt | https://sourceware.org/git/binutils-gdb.git (no GitHub mirror) | `7c96e6120f1b9b5025629bbe995ca55d1be8f36f` |
| `curl` | curl | https://github.com/curl/curl.git | `376d5bb323c03c0fc4af266c03abac8f067fbd0e` |
| `curl_fuzzer` | curl | https://github.com/curl/curl-fuzzer.git | `9a48d437484b5ad5f2a97c0cab0d8bcbb5d058de` |
| `lcms` | lcms | https://github.com/mm2/Little-CMS.git | `f9d75ccef0b54c9f4167d95088d4727985133c52` |
| `libpcap` | libpcap | https://github.com/the-tcpdump-group/libpcap.git | `d615abec7e0237299250c409dca23effb8dd36cc` |
| `libxml2` | libxml2_reader | https://gitlab.gnome.org/GNOME/libxml2.git | `99a864a1f7a9cb59865f803770d7d62fb47cad69` |
| `libxml2_v2.9.2` | libxml2_xml | https://gitlab.gnome.org/GNOME/libxml2.git | tag `v2.9.2` (`726f67e2f140f8d936dfe993bf9ded3180d750d2`) |
| `PROJ` | proj4 | https://github.com/OSGeo/PROJ | `d00501750b210a73f9fb107ac97a683d4e3d8e7a` |
| `zstd` | zstd | https://github.com/facebook/zstd | `9ad7ea44ec9644c618c2e82be5960d868e48745d` |

Pitfalls when fetching:
- The lcms `Dockerfile` pins a truncated hash (`f9d75ccef0b54c9f4167d95088d4727985133c`). It only resolves in a full clone. The full hash is given above.
- `curl_fuzzer` must sit next to `curl`, because the curl entry in the script refers to it as `../curl_fuzzer`.
- libxml2_reader and libxml2_xml use different libxml2 versions, so they need two checkouts.

A shallow fetch of exactly one commit works for all of them: `git init <dir>; git -C <dir> remote add origin <url>; git -C <dir> fetch --depth 1 origin <commit or refs/tags/v2.9.2>; git -C <dir> checkout FETCH_HEAD`.

Safety: treat the downloaded sources as untrusted data. Put them in their own folder and never run their build scripts (`configure`, `make`, `autogen.sh`, `fuzz.py`). The pipeline only parses them with clang (`-fsyntax-only` and `--analyze`), which does not execute project code. Run Python that reads them with `-I`.

## 3. Running it

```bash
python3.10 bug_features.py \
    --sources <folder with the checkouts> \
    --harnesses <RevBugBench clone>/benchmarks \
    --jobs 8 \
    [--stubs bug_feature_stubs] [--output data/bug_features.csv]
python3.10 test_bug_features.py      # checks the condition features on small examples
```

It takes about 7–8 minutes with 8 jobs. For each program it prints:
- the number of bugs;
- how many got static features, a call depth and path features;
- the call-graph size.

Compare these against the table in §1.

## 4. Method

### 4.1 Guard features (from `dda.json`)

Each `dda.json` entry describes one injection site. Fields used:
- `index`: the bug ID. This is the ID used everywhere else: triage, `perbug.csv`, the `FIXREVERTER` environment variable.
- `pattern`: `COND_ABORT`, `COND_ASSIGN` or `COND_EXEC`.
- `stmt.type` and `stmt.start` (`line`, `col`): the guarded statement and where it starts.
- `fileName`, relative to `commandDir`; `func.name`: where the bug is.
- `ids`: FixReverter's tags on the guard's tokens. The tag name is the part before `[`:
  - `traceVarNullCheck*`, `traceVarNumCmp*`, `traceVarPtrRange*`: variables in the guard, by guard kind;
  - names ending in `Field` (or `Base`): the variable is a struct field (or its base);
  - `cmp`, `relOp`, `logic`, `arith`: operators;
  - `traceVarAssign*`: the assignment in an ASSIGN pattern;
  - `endSpot`: end of the guard.
- `tokenOrder`: the guard's tokens in source order. Each token has an `order` that links it to its `ids` tag, if any.

| Column | Definition |
|---|---|
| `pattern`, `stmt_type` | Copied from the entry. |
| `guard_null`, `guard_num`, `guard_ptr_range` | Some tag contains `NullCheck` / `NumCmp` / `PtrRange`. More than one can be true. |
| `uses_field` | Some tag ends in `Field`. |
| `n_conditions` | 1 + number of `logic` tags (`&&` / `||`). |
| `magic_const` | The guard compares against a literal other than the trivial ones (`0`, `1`, `-1`, `NULL`, `'\0'`, `0L`, `0U`, `0UL`, `1U`). Any comparison counts, including `<` and `>`. |
| `const_bytes` | Bytes needed for the largest such literal (1 for a char literal; otherwise ceil(bit length / 8), at least 1). |

To find literals, scan `tokenOrder` after the first token (`if`) and stop at the first `endSpot` or `traceVarAssign*` token. A literal is an untagged token matching a decimal or hex integer (with optional `u`/`l` suffixes), a char literal, or `NULL`. No guard in these 8 programs contains a string literal or a string-compare call, so multi-byte magic strings never appear in guards.

### 4.2 Parsing the unbuilt source

Real builds generate headers (via `configure`/CMake) that a checkout doesn't have, so clang is given stubs. The include path starts with `--stubs/<program>/` (if it exists), then `--stubs`.
- **`config.h`:** common Linux `HAVE_*` defines (standard headers, `snprintf`, `strdup` and so on) plus `VA_LIST_IS_ARRAY`.
- **`curl_config.h`:** bool, socket and `send`/`recv` type defines, `SIZEOF_*` for 64-bit Linux, `CURL_DISABLE_LDAP`, `USE_OPENSSL 0`, plus the `config.h` block.
- **`libxml/xmlversion.h`** (libxml2_reader, version 2.9.10) and **`libxml2_xml/libxml/xmlversion.h`** (version 2.9.2): generated from that checkout's `include/libxml/xmlversion.h.in`:
  - each `@WITH_*@` becomes 1, except ICU, LZMA, ZLIB, ICONV, THREADS, THREAD_ALLOC, MEM_DEBUG, RUN_DEBUG, TRIO and DOCB, which become 0;
  - `@VERSION@` and `@LIBXML_VERSION_NUMBER@` get the release's version;
  - `@LIBXML_VERSION_EXTRA@` becomes empty and `@MODULE_EXTENSION@` becomes `.so`.

  libxml2_xml's real build also turns off threads, zlib and lzma (`build.sh`), which matches.
- **`proj4/proj_config.h`:** what PROJ's `configure.ac` finds on 64-bit Linux: `HAVE_LOCALECONV`, `HAVE_PTHREAD_MUTEX_RECURSIVE`, `HAVE_LIBM`, `HAVE_LIBPTHREAD` and the standard header checks. JNI is off.
- zstd needs no stub.

Compiler flags, per file:
- `-w -ferror-limit=0` (keep going after errors);
- `-Wno-error=implicit-function-declaration`, `-Wno-error=implicit-int`, `-Wno-error=int-conversion`, `-Wno-error=incompatible-function-pointer-types`, `-Wno-register` (old C code and C++17 `register`);
- per-program defines (`DEFINES` in the script):
  - curl, cxxfilt, libpcap, lcms: `-DHAVE_CONFIG_H`;
  - proj4: `-DMUTEX_pthread -DHAVE_C99_MATH=1 -DPROJ_LIB=...` (from `src/Makefile.am`);
  - zstd: `-DZSTD_MULTITHREAD -DZSTD_LEGACY_SUPPORT=1 -DDEBUGLEVEL=1 -DMEM_FORCE_MEMORY_ACCESS=0 -DFUZZ_RNG_SEED_SIZE=4` (from `tests/fuzz/Makefile` and `fuzz.py`'s defaults). `ZSTD_LEGACY_SUPPORT` matters most: most zstd bugs are in the legacy decoders, which are compiled only with it.
- `-x c++ -std=c++17` for `.cc` / `.cpp` harnesses;
- includes: the stubs, the file's own folder, and the program's include folders from `PROGRAMS`.

### 4.3 Locating each bug in the source

1. Resolve the file. If `fileName` is relative, join it with `commandDir`. Strip the container prefix from `PROGRAMS` (for example `/src/curl`) to get the path inside the checkout. Paths outside the prefix are left unresolved.
2. Convert `stmt.start` (line, 1-based column) to a byte offset in the file.
3. Look up the function by its base name. libxml2's real build compiles with `-DPIC`, which makes `elfgcchack.h` rename exported functions to `X__internal_alias`, and `dda.json` records that name. Our parse doesn't define `PIC`, so the suffix is removed for every lookup (AST and call graph). The `function` column keeps the `dda.json` name. This affects 471 libxml2_reader bugs and 390 libxml2_xml bugs. Before this step existed, all of them were missing static features.
4. Dump the clang AST of that function only:
   `clang-18 -fsyntax-only <flags> -Xclang -ast-dump=json -Xclang -ast-dump-filter=<func> <file>`.
   The output is several JSON objects back to back, so read them in a `raw_decode` loop. Keep the `FunctionDecl` with that name that has a body (`CompoundStmt`).
5. Walk the function's AST. The bug's statement is the first `if`/`for`/`while`/`do`/`switch` node whose start offset (`range.begin.offset`, or `expansionLoc.offset` inside macros) equals the offset from step 2.

Check: of the 5,889 `dda.json` statement locations, 5,881 match the unpatched source text, meaning the text at `stmt.start` begins with `stmt.type`. The other 8 are libpcap bugs in parser and scanner files that only exist after a build (`build/grammar.c`, 7 bugs; `build/scanner.c`, 1 bug). All 2,536 locations in libxml2_xml, proj4 and zstd match. Repeat this check for any new program before trusting its features.

### 4.4 Static features within the function

| Column | Definition |
|---|---|
| `static_found` | The statement was found in the AST (§4.3). If false, all the static columns are empty. |
| `nest_depth` | Number of enclosing `if` / `for` / `while` / `do` / `switch` statements within the function, not counting the bug's own statement. |
| `loop_depth`, `in_loop` | The same, counting loops only; `in_loop` = `loop_depth > 0`. |
| `func_branches` | In the whole function: `if`, loop, `case`, `?:` and `&&` / `||` nodes. A cyclomatic-complexity proxy. |
| `func_lines` | Lines from the start to the end of the function definition. |

A statement is "enclosed" by a control statement only if it's in that statement's branches or body. The condition (and a `for`'s init) run before the statement, so a call in `if (foo())` is not inside that `if`.

### 4.5 Call-graph features (FeatureBench feature C1, number of conditional branches, extended across functions)

Building the call graph:
- Run `clang-18 --analyze -Xanalyzer -analyzer-checker=debug.DumpCallGraph` on every source file listed for the program in `PROGRAMS`, plus the harness files. Read the `Function: X calls: Y Z` lines. They also record which file defines each function.
- `PROGRAMS` patterns starting with `!` remove files. proj4 uses this to keep only `libproj_la_SOURCES` from `src/Makefile.am` and drop PROJ's command-line tools.
- Harness files are looked up in the source checkout first, then in `<harnesses>/<program>/`.
- `PROGRAMS` adds a few call edges by hand where clang can't see them:
  - cxxfilt: `LLVMFuzzerTestOneInput → demangle_it → cplus_demangle`;
  - libxml2_reader: `LLVMFuzzerTestOneInput →` `xmlReaderForFile`, `xmlTextReaderRead`, `xmlTextReaderNodeType`, `xmlTextReaderConstValue`, `xmlFreeTextReader`;
  - libxml2_xml: `LLVMFuzzerTestOneInput →` `xmlSetGenericErrorFunc`, `xmlReadMemory`, `xmlFreeDoc` (from `benchmarks/libxml2_xml/target.cc`).

  The libxml2 harnesses are C++ that clang-18 couldn't parse against the libstdc++ on the machine where this was set up, so their calls are listed by hand from the harness source.

Every function reachable from `LLVMFuzzerTestOneInput` is then analyzed like the bug's function (§4.3 step 4). Each of its direct call sites gets three weights: the number of enclosing control statements, enclosing loops, and hard checks (§4.6) around it. A call-graph edge with no call site in the AST gets weight 0. These are hand-listed harness calls, or calls clang's call graph sees but the filtered AST doesn't.

| Column | Definition |
|---|---|
| `call_depth` | Shortest number of calls from `LLVMFuzzerTestOneInput` to the bug's function (breadth-first search over direct calls). Empty if not reachable that way. |
| `fan_in` | Number of distinct direct callers of the function. |
| `recursive` | The function is in a call-graph cycle (Tarjan strongly connected components; size > 1 or a self-call). |
| `path_conditions` | Fewest enclosing control statements over all known call paths from `LLVMFuzzerTestOneInput` to the bug (Dijkstra over the call-site weights), plus `nest_depth`. The closest match to FeatureBench's Depth. |
| `path_loop_depth` | The same for loops (fewest over all paths), plus `loop_depth`. |
| `path_hard_checks` | The same for hard checks (fewest over all paths), plus `hard_checks`. |

Each `path_*` column is minimized on its own, so the three can come from different paths. Each is a lower bound for reaching the bug through direct calls. They are empty when `call_depth` is empty or the statement wasn't found.

### 4.6 Hard checks, loop counters and checksums (FeatureBench features C3, D1–D3)

A **hard check** is a condition that only a specific input value passes:
- an equality comparison (`==` / `!=`) with an integer or character literal other than 0, 1 and −1. Macros are expanded in the AST, so `#define MAGIC 0x7F` counts;
- a string or memory compare with a string literal argument: `strcmp`-style functions where 0 means equal (`strcmp`, `strncmp`, `memcmp`, `strcasecmp`, `xmlStrcmp`, `xmlStrncmp`, `cmsstrcasecmp`, …), and ones where nonzero means equal (`xmlStrEqual`, `xmlStrQEqual`, `Curl_strcasecompare`, …);
- a `switch` with a non-trivial case label (everything in its body except the `default:` label's statement);
- a **checksum comparison**: `==` / `!=` where one side calls a checksum function, or reads a variable assigned from one. Checksum functions match `XXH32`, `XXH64`, `XXH*_digest`, `crc32`, `xcrc32`, `adler32`, `checksum` and `cksum`, with optional prefixes such as `ZSTD_`. The list comes from a survey of the 8 programs' sources. Their MD5 routines fill digest buffers instead of returning a value, so they aren't included.

Which branch needs the check matters:
- The then-branch of `x == 'a'` needs the magic value; its else-branch doesn't.
- For `&&`, the then-branch needs every conjunct.
- For `||`, the else-branch needs every disjunct to fail.
- `!` swaps the branches, and `x == 0` is treated as `!x`.

A check counts for a statement in two cases:
1. The statement is in the branch that needs the check (nesting).
2. The statement comes after a **guard clause** `if (cond) <exit>;` in the same block, and getting past the guard clause needs the check. `<exit>` is `return`, `goto`, `break`, `continue`, a call to `abort`/`exit`/`longjmp`, or a block ending in one of them. A guard clause inside a nested plain `{ }` block also counts for the statements after that block. Guard clauses are how real parsers do most magic-byte and checksum checks, for example `if (CUR != '<') return;` and zstd's `RETURN_ERROR_IF(check32 != h32, checksum_wrong)`.

Guard clauses count only toward hard checks. They don't count toward `nest_depth` or `path_conditions`, which stay nesting counts like FeatureBench's Depth. Most guard clauses are null or error checks, which would only add noise there.

| Column | Definition |
|---|---|
| `hard_checks` | Hard checks that must pass to reach the bug's statement within its function (nesting plus guard clauses). |
| `checksum_checks` | How many of those are checksum comparisons. |
| `guard_checksum` | The bug's own condition contains a checksum comparison. |
| `guard_loop_counter` | The bug's own condition reads a counter of an enclosing loop. A counter is a variable changed in a `for` loop's increment, or read in a loop's condition and changed (`++`, `--`, `=`, `op=`) in its body. This is FeatureBench's loop-iteration feature, `if (i == $Iteration)`. |
| `guard_recursion_counter` | The bug's own condition reads a parameter that the function passes to itself as `p + k`, `p - k`, `++p` or `--p`. This is FeatureBench's recursion-iteration feature. Direct self-calls only. |

`test_bug_features.py` checks these definitions on 11 small cases with known answers.

What the 8 programs show:
- No bug is guarded by a checksum, so `checksum_checks` and `guard_checksum` are 0 everywhere. zstd, the only program that compares checksums on the decoding path, verifies the frame checksum as the last step of `ZSTD_decompressFrame`, after all block decoding. So no bug depends on it.
- `guard_recursion_counter` is 0 everywhere. The only recursion-depth parameters on the bugs' paths (for example `xmlRelaxNGCheckCycles(..., depth + 1)`) don't have injected bugs.
- `guard_loop_counter` is true for 132 bugs.

## 5. Output columns

`program, bug, file, function, pattern, stmt_type, guard_null, guard_num, guard_ptr_range, uses_field, n_conditions, magic_const, const_bytes, static_found, nest_depth, loop_depth, func_branches, func_lines, in_loop, call_depth, fan_in, recursive, path_conditions, path_loop_depth, path_hard_checks, hard_checks, checksum_checks, guard_loop_counter, guard_recursion_counter, guard_checksum`

`bug` is the `dda.json` `index`. To join with triage results, use (`program` = `benchmark`, `bug`) in `perbug.csv`. The first 22 columns are the original feature set; the last 8 were added for the FeatureBench gaps (§8). Adding them didn't change any of the first 22 columns.

## 6. Adding a program

1. Check that `../ddas/<program>/dda.json` exists. The repo has it for all 10 programs.
2. Check out its source at the commit in its RevBugBench `Dockerfile`.
3. Add an entry to `PROGRAMS` in `bug_features.py`:
   - the container path prefix (the `/src/...` folder in `commandDir`);
   - the checkout folder name;
   - glob patterns for the files that make up the fuzz target (`!pattern` to exclude). Take them from the benchmark's `build.sh` and the project's makefiles;
   - include folders;
   - harness files;
   - any call edges clang can't see.

   Add the build's defines to `DEFINES`.
4. If parsing fails on a missing generated header, add a stub to `bug_feature_stubs/` (or `bug_feature_stubs/<program>/` if it would clash with another program's) rather than building the program.
5. Rerun and check before using the features:
   - how many statement locations match the source (§4.3);
   - the share of bugs with `static_found`;
   - for the missing ones, whether `dda.json` uses names the parse doesn't see (as with `__internal_alias`);
   - the share with `call_depth`;
   - that the call graph reaches a plausible number of functions from `LLVMFuzzerTestOneInput`.
6. Update this document: the tables in §1 and §2, and §4.2.

## 7. Known limitations

- **Function pointers aren't followed.** `call_depth` and the `path_*` columns exist for:
  - none of curl's bugs;
  - 8% of libpcap's (8 of 100);
  - 24% of proj4's (55 of 233);
  - 35% of lcms's (132 of 382).

  These programs dispatch through function pointers: curl's protocol handlers, libpcap's per-platform operations, PROJ's table of projection constructors (165 of the 178 missing proj4 bugs are in `PJ_*.c` projection files), and lcms's plugin tables. The columns are most complete for cxxfilt (all), zstd (88%), libxml2_reader (47%) and libxml2_xml (40%). Treat an empty value as "unknown", not "unreachable".
- **Hard checks are candidates, not confirmed input checks.** There's no data-flow analysis from the fuzz input yet. So a comparison of internal state with a `#define` constant (for example `iattr->state == XML_SCHEMAS_ATTR_DEFAULT` in libxml2) counts the same as a magic byte read from the input. `hard_checks` and `path_hard_checks` are therefore upper bounds on input-dependent hard checks. Enum constants are not counted, because their values aren't in the filtered AST dump, while `#define` constants are. Both limits would go away with an input-dependence (taint) analysis (§8).
- **Path features ignore guard clauses for conditions and use weight 0 for edges without a call site.** `path_conditions` counts nesting only, and hand-listed harness edges add nothing. So it's a lower bound on the conditions the input must pass.
- **The `analyzer` step skips files with any hard error.** Functions only defined in such files are missing from the call graph. There is no per-file report; check the printed call-graph sizes.
- **Stubbed headers can pick the wrong `#if` branches,** so a few bugs may sit in code the real build compiles differently. This is the main reason the remaining bugs aren't found in the AST, together with generated files (libpcap) and macros.
- **System headers change macro-based counts** (`func_branches`, and in principle the condition columns) across machines; see the top of this document.
- **Static functions are matched by name,** so same-named static functions in different files are merged in the call graph (this affects `fan_in`, `recursive`, `call_depth` and the `path_*` columns).
- **Recursion counters are found for direct self-calls only;** mutual recursion through other functions isn't checked.
- **`switch` hard checks are approximate:** every statement in the body except the `default:` label's own statement counts as needing a case value.
- **Some features are not independent.** `func_branches` and `func_lines` are per function, so all bugs in a function share them, and guard kinds can overlap. Each bug has its own statement: no two bugs share a start location.

## 8. Mapping to FeatureBench

FeatureBench defines 7 features through 10 parameters, set by construction in generated programs. Here is what we measure for each:

| FeatureBench feature (parameter) | Our columns | Status |
|---|---|---|
| C1 Number of conditional branches (Depth) | `path_conditions`; `nest_depth` within the function | Measured; lower bound, direct calls only |
| C1 (Width) | `func_branches` (per function, not per path) | Rough proxy |
| C2 Execution probability (Weight, BBranch) | none | Not yet: needs coverage counts from a reference corpus per program |
| C3 Loops and recursion (Iteration) | `in_loop`, `loop_depth`, `path_loop_depth`, `recursive`, `guard_loop_counter`, `guard_recursion_counter` | Structure and loop-counter guards measured; the iteration count needed isn't |
| C4 Loops/recursion with data constraints (Has_Data_Constraint) | `guard_loop_counter` together with `hard_checks` | Partial: input dependence not yet known |
| D1 Magic bytes (Length) | `magic_const`, `const_bytes` (guard); `hard_checks` (string compares count) | Partial; no per-check byte length on the path |
| D1 (Start) | none | Not yet: needs a mapping from the check to an input offset (runtime taint) |
| D2 Checksum tests (Count) | `checksum_checks`, `guard_checksum`; `n_conditions` counts any `&&`/`||` | Measured; 0 in these programs |
| D3 Nested magic bytes / checksums (Depth) | `hard_checks`, `path_hard_checks` | Measured as candidates (see §7) |

### Features still to do

1. **Input dependence** (feature 2): whether each condition is computed from the fuzz input. This would turn the candidate hard checks into confirmed ones and give FeatureBench's C4. Options:
   - a runtime analysis (DataFlowSanitizer or AFL++ comparison logging), which also gives magic-byte Start (D1);
   - a static taint analysis (CodeQL or PhASAR).

   Both need a build of each program, inside RevBugBench's Docker images.
2. **Execution probability** (feature 3, FeatureBench C2): the share of inputs reaching each bug, and per-branch probabilities along its path. Inputs: the FixReverter artifact's 24-hour corpora (`/home/tahmeed/FixReverter/artifact/experiment-data/exp`; 5 fuzzers × 3 trials × all programs, with coverage builds). Its `triage/<program>/<fuzzer>/queue_seeds.pickle` already records, for each corpus input, which bugs it reaches and triggers. Caveats:
   - the binutils-fuzz_cxxfilt and libxml2_reader records are empty;
   - libxml2_reader and libxml2_xml use a different bug numbering from `dda.json`, so they must be matched by source location.
3. **Iteration counts** (C3): how many loop or recursion iterations a bug needs. This would need runtime data or symbolic reasoning.
4. **Indirect calls:** resolving function pointers would fill `call_depth` and the `path_*` columns for curl, libpcap, proj4 and lcms. A points-to analysis on a build would do it, for example PhASAR's call graph.
