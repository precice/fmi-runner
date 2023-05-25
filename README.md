# preCICE-FMI Runner

The [Functional Mock-Up Interface](https://fmi-standard.org/) (FMI) is a standard for the exchange of dynamic simulation models. Currently, it is the de-facto industry standard for co-simulation. The models implementing the FMI standard are called Functional Mock-Up Units (FMU).

This project contains the runner script `fmiprecice` to couple FMU models with other simulation tools via the coupling library [preCICE](https://precice.org/). The runner serves as an importer for the FMU to steer the simulation. Additionally, it calls the preCICE library to communicate and coordinate with other solvers. 

![img](docs/images/precice-fmi-runner-setup.png)

## Dependencies

* Python 3 or higher
* [preCICE](https://precice.org/installation-overview.html), v2
* [pyprecice: Python language bindings for preCICE](https://github.com/precice/python-bindings)
* [NumPy](https://numpy.org/install/)
* [FMPy](https://fmpy.readthedocs.io/en/latest/install/) (tested for v0.3.13)

## Installation 

Clone this repository and open a terminal in the root directory.

To use **pip** for the installation, run the command:

```bash
pip3 install --user -e .
```

The editable flag `-e` allows you to update the preCICE-FMI Runner by pulling the repository.

To use **Python** for the installation, run the command:

```bash
python setup.py install --user
```

## Usage

The Runner is called from the terminal with the command `fmiprecice`. It takes two input files, one with settings for the FMU simulation and one with settings for preCICE. Start the runner by pointing to the input files:

```bash
fmiprecice ./fmi-settings.json ./precice-settings.json
```

You can find more information about the runner, its abilities, and its limitations in [1]. This adaption of the [oscillator tutorial](https://github.com/LeonardWilleke/precice-tutorials/tree/create-fmu-oscillator-v2/oscillator) features a first complete setup with FMU model and setting files. 

## References

[1] L. Willeke, A preCICE-FMI Runner to couple controller models to PDEs, Master Thesis, University of Stuttgart, 2023 (Publication pending)

