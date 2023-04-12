# Regression test

## Setup

This test solves a simple mass-spring oscillator with two masses and three springs. The system is cut at the middle spring and solved in a partitioned fashion. The setup and equations are the same as in the [preCICE Oscillator tutorial](https://github.com/precice/tutorials/tree/master/oscillator).

## Solvers

One participant is computed with the FMI Runner, the other side is calculated with a Python script. Both sides implement the same formulas and integration methods but use different initial conditions.

For the test, we will **always** compute the left side with the FMI Runner and the right side with the Python solver.

You can run the Python solver manually by typing

```bash
python3 python_solver.py Mass-Right
```

## Results

Each simulation run creates two files containing position and velocity of the two masses over time. These files are called `test-result-fmi.csv` and `test-result-python.csv`.

## Testing

The result files are compared to the expected results `expected-result-Mass-Left.csv` and `expected-result-Mass-Right.csv`.

## License

The FMU model `Oscillator.fmu` used for this test is based on the [Reference-FMUs](https://github.com/modelica/Reference-FMUs) from the Modelica Association Project "FMI", which are released under the [2-Clause BSD License](https://github.com/precice/fmi-runner/thirdparty/LICENSE.txt). 
