---
title: The FMI runner
permalink: tooling-fmi-runner-overview.html
keywords: tooling, fmi, runner, fmi-settings, precice-settings
summary: A tool to couple FMUs to PDE-based solvers using preCICE.
---

## What is this?

The [Functional Mock-Up Interface](https://fmi-standard.org/) (FMI) is a standard for the exchange of dynamic simulation models. Currently, it is the de-facto industry standard for co-simulation. The models implementing the FMI standard are called Functional Mock-Up Units (FMU).

This tool contains the runner script `fmiprecice` to couple FMU models with other simulation tools via the coupling library [preCICE](https://precice.org/). The runner serves as an importer for the FMU to steer the simulation. Additionally, it calls the preCICE library to communicate and coordinate with other solvers. 

![img](docs/images/precice-fmi-runner-setup.png)

## Usage

The runner is called from the terminal with the command `fmiprecice`. It takes two input files, one with settings for the FMU simulation and one with settings for preCICE. Start the runner by pointing to the input files:

```bash
fmiprecice ./fmi-settings.json ./precice-settings.json
```

Read on to find out how to install and configure the runner. More information about the software, its abilities, and its limitations can be found in [1]. If you are ready to run your first case, have a look at the [oscillator tutorial](https://github.com/LeonardWilleke/precice-tutorials/tree/create-fmu-oscillator-v2/oscillator). 

## Get the Runner

### Dependencies

**Maybe include pip commands to install pyprecice, numpy and fmpy here**

Before you start the installation, make sure you have installed the following packages:

* Python 3 or higher
* [preCICE](https://precice.org/installation-overview.html), v2
* [pyprecice: Python language bindings for preCICE](https://github.com/precice/python-bindings)
* [NumPy](https://numpy.org/install/)
* [FMPy](https://fmpy.readthedocs.io/en/latest/install/) (tested for v0.3.13)

### Installation 

The software is [hosted on GitHub](https://github.com/precice/fmi-runner). Clone the repository and switch to the root directory:

```bash
git clone https://github.com/precice/fmi-runner.git
cd fmi-runner
```

To use **pip** for the installation, run the command:

```bash
pip3 install --user -e .
```

The editable flag `-e` allows you to update the FMI Runner by pulling the repository.

To use **Python** for the installation, run the command:

```bash
python setup.py install --user
```

## Configuration

We use two settings files to configure the software to the specific simulation case.

### Configure the FMU

The file `fmi-settings.json` holds all the necessary information to run a simulation with the FMU. Additionally, you can choose which data should be exchanged with preCICE.

```json
{
    "simulation_params": {
        "fmu_file_name": "../model.fmu",
        "fmu_read_data_names": ["input_1", "input_2"],
        "fmu_write_data_names":["output_1", "output_2"],
        "output": ["data_1", "data_2"],
        "output_file_name": "./results.csv",
        "fmu_instance_name": "model_1"
    },
    "model_params": {
        "apply_filter":         false,
        "integration_method":   "euler"
    },
    "initial_conditions": {
        "variable_1":   5.0,
        "variable_2":   10.0
    
    },
    "input_signals": {
        "names":    ["time",    "variable_3",   "variable_4"],
        "data":     [
                    [0.0,       0.0,            0.0],
                    [1.0,       2.0,            0.0],
                    [3.0,       2.0,            4.0]
                    ]
    }
}
```

The config file allows you to access and manipulate the variables within the FMU model. Therefore, the variable names have to match with the variables listed in the `ModelDescription.xml` of the FMU.

Let's have a closer look at the specific dictionaries:

**simulation_params**: The list `fmu_read_data_names` is used to specify the read data of the FMU, while the list `fmu_write_data_names` concerns the write data. If you exchange vector data via preCICE, the number of list entries has to match the dimensions of the solver interface in the `precice-config.xml`. If you exchange scalar data, use a list with one entry instead.

Optionally, you can choose variables in `output` that are tracked and stored as a timeseries in `output_file_name`.

{% disclaimer %}
The runner can currently not deal with FMU vectors. All FMU variables need to be scalars. Besides that, any data type implemented in the FMU (integer, float, boolean, string) is supported.
{% enddisclaimer %}

**model_params**: Use this to set internal parameters before the start of the simulation. In this example, the parameters `apply_filter` and `integration_method` are set. The keys of this dictionary are the names of specific FMU variables.

**initial_conditions**: Use this to set initial conditions for internal parameters. Again, the keys of this dictionary are the names of specific FMU variables.

**input_signals**: You can set time-dependent input signals. The list `names` holds the different parameters. The first entry of this list is always `time`. The list `data` sets the input values for the variables given in `time`. The first entry of each nested list in `data` is the time at which the following data is set. Here, `variable_1` is set to 2.0 at `t=2.0` while `variable_2` is set to 4.0 at `t=3.0`. Of course, you can also set the values of boolean and string parameters.

### Configure the coupling

The file `precice-settings.json` is used to configure the coupling with preCICE. It consist of one dictionary **coupling_params**

```json
{
    "coupling_params": {
        "participant_name": "Participant",
        "config_file_name": "../precice-config.xml",
        "mesh_name": "Mesh-Participant",
        "write_data": {"name": "write_data_name", "type": "vector"}, 
        "read_data": {"name": "read_data_name", "type": "vector"}
    }
}
```

The `participant_name` and `mesh_name` need to match the entries in the `precice-config`. The same is true for `write_data` and `read_data`, which control the data exchange. The `type` can be set to `scalar` or `vector`.

## Limitations

Current limitations of the FMI Runner software are:

- Can only be used with preCICE v2
- All accessed FMU variables are scalar
- Data can only be exchanged via one vertex. The exchange of multiple vertices or full meshes is not possible.

## How to cite

If you are using the Runner, pĺease consider citing the Thesis:

**Add a nice info box with link to Thesis and Bibtex download**

## References

[1] L. Willeke, A preCICE-FMI Runner to couple controller models to PDEs, Master Thesis, University of Stuttgart, 2023 (Publication pending)

