from numpy import genfromtxt

# Expected final results
expected_solver_one = 9
expected_solver_two = 10

# Calculated results
data_solver_one = genfromtxt('./SolverOne/output/test-SolverOne.csv', delimiter=',', skip_header=1)
data_solver_two = genfromtxt('./SolverTwo/output/test-SolverTwo.csv', delimiter=',', skip_header=1)

calc_solver_one = data_solver_one[6,1]
calc_solver_two = data_solver_two[6,1]

assert expected_solver_one == calc_solver_one, "Results of SolverOne are wrong"
assert expected_solver_two == calc_solver_two, "Results of SolverTwo are wrong"

print("Test finished successfully")
