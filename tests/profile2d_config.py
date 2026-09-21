import os

histogramsOutputFilePath = os.environ["TEA_PROFILE2D_TEST_OUTPUT"]

profile2DParams = (
  ("response", 2, 0.0, 2.0, 2, -1.0, 1.0, "profiles"),
  ("zero_x_bins", 0, 0.0, 2.0, 2, -1.0, 1.0),
  ("negative_y_bins", 2, 0.0, 2.0, -1, -1.0, 1.0),
  ("equal_x_bounds", 2, 1.0, 1.0, 2, -1.0, 1.0),
  ("reversed_y_bounds", 2, 0.0, 2.0, 2, 1.0, -1.0),
  ("non_finite_x_bound", 2, 0.0, float("inf"), 2, -1.0, 1.0),
  ("non_finite_y_bound", 2, 0.0, 2.0, 2, float("nan"), 1.0),
)

irregularProfile2DParams = (
  ("response_variable", (0.0, 1.0, 3.0), [-2.0, 0.0, 4.0], "variable_profiles"),
  ("duplicate_x_edge", (0.0, 1.0, 1.0), (-2.0, 0.0, 4.0)),
  ("descending_y_edge", (0.0, 1.0, 3.0), (-2.0, 4.0, 0.0)),
  ("non_finite_x_edge", (0.0, float("inf"), 3.0), (-2.0, 0.0, 4.0)),
  ("non_finite_y_edge", (0.0, 1.0, 3.0), (-2.0, float("nan"), 4.0)),
)

SFvariationVariables = ("response", "response_variable")
