"""Make tea's Python libraries importable without an installed bin/ tree.

The tests here cover pure logic only -- URL derivation, staging atomicity, merge planning
and input validation -- so they deliberately import the modules directly from the source
tree and never need ROOT, gfal, xrootd or condor.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for relative_path in ("pylibs/logger", "pylibs/helpers", "apps/examples"):
  path = os.path.join(REPO_ROOT, relative_path)
  if path not in sys.path:
    sys.path.insert(0, path)
