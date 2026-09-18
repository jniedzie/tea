import os

histogramsOutputFilePath = os.environ["TEA_PROFILE2D_TEST_OUTPUT"]

profile2DParams = (("response", 2, 0.0, 2.0, 2, -1.0, 1.0, "profiles"),)

irregularProfile2DParams = (("response_variable", (0.0, 1.0, 3.0), (-2.0, 0.0, 4.0), "variable_profiles"),)

SFvariationVariables = ("response", "response_variable")
