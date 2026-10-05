import os

histogramsOutputFilePath = os.environ["TEA_TH3D_TEST_OUTPUT"]

histParams3D = [
  ("wrong_arity", 2, 0, 2),
  ("wrong_name", 2, 0, 2, 2, 0, 2, 2, 0, 2, 42),
  None,
]
for axis in range(3):
  for bin_count, lower, upper in (
    (0, 0, 2),
    (-1, 0, 2),
    (2**100, 0, 2),
    (2.5, 0, 2),
    (2, 1, 1),
    (2, 2, 1),
    (2, 0, float("inf")),
    (2, float("nan"), 2),
    (2, "bad", 2),
    (2, 0, 10**1000),
  ):
    axes = [2, 0, 2] * 3
    axes[3 * axis : 3 * axis + 3] = [bin_count, lower, upper]
    histParams3D.append((f"invalid_axis_{axis}", *axes))
histParams3D.extend(
  (
    ("volume", 2, 0, 2, 3, -1, 2, 4, 10, 14, "volumes"),
    ("unselected", 2, 0, 2, 3, -1, 2, 4, 10, 14),
    ("empty", 1, 0, 1, 1, 0, 1, 1, 0, 1, "volumes"),
  )
)

irregularHistParams3D = [("wrong_edges_arity", (0, 1)), ("wrong_directory", (0, 1), (0, 1), (0, 1), 42)]
for axis in range(3):
  for edges in ((), (0,), (0, 1, 1), (0, 2, 1), (0, float("inf")), (0, float("nan")), (0, "bad"), 2):
    axes = [(0, 1, 3), (-2, 0, 4), (10, 11, 15)]
    axes[axis] = edges
    irregularHistParams3D.append((f"invalid_edges_{axis}", *axes))
irregularHistParams3D.extend(
  (
    ("variable", (0, 1, 3), [-2, 0, 4], (10, 11, 15), "variable_volumes"),
    ("variable_top", [0, 1, 3], (-2, 0, 4), [10, 11, 15]),
  )
)

histParams = (("regression", "one", 2, 0, 2),)
irregularHistParams = (("regression", "variable", (0, 1, 3)),)
histParams2D = (("two", 2, 0, 2, 2, 0, 2),)
irregularHistParams2D = (("two_variable", (0, 1, 3), (0, 1, 3), ""),)
profile2DParams = (("profile", 2, 0, 2, 2, 0, 2),)
irregularProfile2DParams = (("profile_variable", (0, 1, 3), (0, 1, 3)),)

SFvariationVariables = (
  "volume",
  "variable",
  "variable_top",
  "regression_one",
  "regression_variable",
  "two",
  "two_variable",
  "profile",
  "profile_variable",
)

mode = os.environ.get("TEA_TH3D_TEST_MODE", "")
if mode == "collision":
  profile2DParams += (("volume", 2, 0, 2, 2, 0, 2),)
elif mode == "irregular_collision":
  irregularProfile2DParams += (("variable", (0, 1, 3), (0, 1, 3)),)
