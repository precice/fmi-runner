# Regression test

## Setup

This test couples the participants SolverOne and SolverTwo. Both participants are run by the preCICE-FMI Runner which calls the FMU model `Dummy.fmu`. The FMU adds an increment of 1 to the read data during every time step.

## Usage

Open two terminals and run

```bash
cd SolverOne
bash ./run.sh
```

and

```bash
cd SolverTwo
bash ./run.sh
```

Each participant creates an output directory with a `.csv` file that stores the results.

## Testing

Run the test file

```bash
python3 test.py
```

## License

The FMU model `Dummy.fmu` used for this test is based on the [Reference-FMUs](https://github.com/modelica/Reference-FMUs) from the Modelica Association Project "FMI", which are released under the [2-Clause BSD License](https://github.com/precice/fmi-runner/blob/main/thirdparty/LICENSE.txt).
