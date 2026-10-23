import subprocess
import sys


def main() -> None:
  executable, config, output = sys.argv[1:]
  for mode, expected in (
    ("collision", "Ambiguous histogram name: volume"),
    ("irregular_collision", "Ambiguous histogram name: variable"),
    ("unknown", "Couldn't find key: unknown in 3D histograms or 2D profiles maps"),
  ):
    result = subprocess.run([executable, config, output, mode], capture_output=True, text=True, check=False)
    if result.returncode != 1 or expected not in result.stdout + result.stderr:
      raise AssertionError(f"{mode} did not fail with the expected diagnostic: {result.stdout}{result.stderr}")


if __name__ == "__main__":
  main()
