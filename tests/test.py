import pandas as pd


# Expected final results
expected_solver_one = 9
expected_solver_two = 10

# Calculated results
df_solver_one = pd.read_csv("./SolverOne/output/test-SolverOne.csv")
df_solver_two = pd.read_csv("./SolverTwo/output/test-SolverTwo.csv")

calc_solver_one = df_solver_one["write_data"][6]
calc_solver_two = df_solver_two["write_data"][6]

assert expected_solver_one == calc_solver_one, "Results of SolverOne are wrong"
assert expected_solver_two == calc_solver_two, "Results of SolverTwo are wrong"

print("Test finished succesfully")
