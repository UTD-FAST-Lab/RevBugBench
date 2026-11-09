"""Checks the condition features of bug_features.py on small C functions with known answers.

Run: python3.10 test_bug_features.py   (needs clang-18 on PATH; also works under pytest)
Each /*X*/ marks the `if` statement whose features are checked.
"""

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bug_features as bf  # noqa: E402

NESTED = r"""
#include <string.h>
#define MAGIC 0x7F
unsigned long long XXH64_digest(const void *s);
int g(int d);
int f(const char *s, int n, int depth) {
  unsigned c = (unsigned)XXH64_digest(s);
  for (int i = 0; i < n; i++) {
    if (s[i] == MAGIC) {
      /*A*/ if (i == 5) return 1;
    }
  }
  if (!strcmp(s, "<!ATT")) { /*B*/ if (n) g(1); } else { /*C*/ if (n) g(2); }
  switch (s[0]) { case 'a': /*D*/ if (n) g(3); break; default: /*E*/ if (n) g(4); }
  /*F*/ if (c != (unsigned)n) return 0;
  /*G*/ if (depth > 10) return 0;
  return f(s, n, depth + 1);
}
"""

GUARD_CLAUSES = r"""
unsigned long long XXH64_digest(const void *s);
unsigned rd(const char *s);
int g(int d);
int f(const char *s, int n) {
  if (s[0] == 'a') return 0;
  /*H*/ if (n) g(1);
  if (s[1] != 'Q') { g(9); return 0; }
  /*I*/ if (n) g(2);
  { unsigned const h = (unsigned)XXH64_digest(s);
    unsigned const r = rd(s);
    if (r != h) return -1; }
  /*J*/ if (n) g(3);
  for (int i = 0; i < n; i++) {
    unsigned const h = (unsigned)XXH64_digest(s + i);
    if (h != rd(s)) break;
    /*K*/ if (n) g(4);
  }
  return 0;
}
"""

COLUMNS = ("nest_depth", "loop_depth", "hard_checks", "checksum_checks", "guard_loop_counter",
           "guard_recursion_counter", "guard_checksum")
EXPECTED = {
    "A": (2, 1, 1, 0, True, False, False),    # inside the loop and the then-branch of s[i] == MAGIC; reads i
    "B": (1, 0, 1, 0, False, False, False),   # then-branch of !strcmp(s, "<!ATT"): needs the magic string
    "C": (1, 0, 0, 0, False, False, False),   # else-branch: any other string gets here
    "D": (1, 0, 1, 0, False, False, False),   # case 'a'
    "E": (1, 0, 0, 0, False, False, False),   # default label: not a hard check
    "F": (0, 0, 0, 0, False, False, True),    # the guard compares a checksum (c comes from XXH64_digest)
    "G": (0, 0, 1, 1, False, True, False),    # after F's checksum guard clause; reads the recursion depth
    "H": (0, 0, 0, 0, False, False, False),   # after if (s[0] == 'a') return: easy to pass
    "I": (0, 0, 1, 0, False, False, False),   # after if (s[1] != 'Q') return: needs 'Q'
    "J": (0, 0, 2, 1, False, False, False),   # also after the checksum guard clause inside the { } block
    "K": (1, 1, 3, 2, False, False, False),   # plus the in-loop checksum guard clause (break)
}


def features(source, tags):
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "t.c"
        path.write_text(source)
        src = path.read_bytes()
        offsets = {re.search(rb"/\*" + t.encode() + rb"\*/ (if)", src).start(1): t for t in tags}
        result = bf.analyze_function(path, "f", set(offsets), Path(d), [], [], [])
    return {t: tuple(result["stmts"][off][c] for c in COLUMNS) for off, t in offsets.items()}


def test_condition_features():
    got = {**features(NESTED, "ABCDEFG"), **features(GUARD_CLAUSES, "HIJK")}
    wrong = {t: (got[t], EXPECTED[t]) for t in EXPECTED if got[t] != EXPECTED[t]}
    assert not wrong, f"got vs expected: {wrong}"


if __name__ == "__main__":
    test_condition_features()
    print(f"all {len(EXPECTED)} cases pass")
