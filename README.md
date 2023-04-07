# preCICE-FMI Runner

A Runner tool to enable co-simulations with FMU models via the coupling library [preCICE](https://github.com/precice/precice).

## Installation 

### Required dependencies

Ensure that the following dependencies are installed:

* Python 3 or higher
* [preCICE](https://github.com/precice/precice/wiki)
* [pyprecice: Python language bindings for preCICE](https://github.com/precice/python-bindings)
* [numpy](https://numpy.org/install/)
* [fmpy](https://fmpy.readthedocs.io/en/latest/install/)

### Build and install the Runner using pip

After cloning this repository, go to the project directory `fmi-runner` and run `pip3 install --user .`. 
If you want to be able to update the Runner by simply pulling this repository, run `pip3 install --user -e .`.

### Build and install the Runner using Python

After cloning this repository, go to the project directory `fmi-runner` and run `python setup.py install --user`.

## Running a simulation

The Runner is called from the terminal with the command `fmiprecice`. It takes two input files, one with settings for the FMU simulation and one with settings for preCICE. Start the runner by calling

```bash
fmiprecice ./fmi-settings.json ./precice-settings.json
```

Have a look at the preCICE [Oscillator tutorial](https://github.com/precice/tutorials/tree/master/oscillator) for a first complete setup with FMU model and setting files. 
