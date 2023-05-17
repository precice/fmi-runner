from __future__ import division

import argparse
import numpy as np
import precice
import csv
import os
from fmpy import read_model_description, extract
from fmpy.simulation import Input, Recorder, instantiate_fmu, apply_start_values
from fmpy.util import write_csv
import shutil
import sys
import json


# Define functions

def precice_read_data(interface, data_type, read_data_id, vertex_id):
    """
    Reads data from preCICE. The preCICE API call depends on the data type, scalar or vector.
    """

    if data_type == "scalar":
        read_data = interface.read_scalar_data(read_data_id, vertex_id)
    elif data_type == "vector":
        read_data = interface.read_vector_data(read_data_id, vertex_id)
    else:
        raise Exception("Please choose data type from: scalar, vector.")

    return read_data


def precice_write_data(interface, data_type, write_data_id, vertex_id, write_data):
    """
    Writes data to preCICE. The preCICE API call depends on the data type, scalar or vector.
    """

    if data_type == "scalar":
        write_data = interface.write_scalar_data(write_data_id, vertex_id, write_data)
    elif data_type == "vector":
        write_data = interface.write_vector_data(write_data_id, vertex_id, write_data)
    else:
        raise Exception("Please choose data type from: scalar, vector.")


def main():
    """
    Executes the Runner

    - Load settings from json files
    - Load FMU model and prepare the simulation
    - Initialize the preCICE interface
    - Run the coupled simulation
    - Store the results
    - Terminate FMU model and preCICE
    """

    # Load settings from json files

    parser = argparse.ArgumentParser()
    parser.add_argument("fmi_setting_file", help="Path to the fmi setting file (*.json).", type=str)
    parser.add_argument("precice_setting_file", help="Path to the precice setting file (*.json).", type=str)
    args = parser.parse_args()

    fmi_setting_file = args.fmi_setting_file
    precice_setting_file = args.precice_setting_file

    folder = os.path.dirname(os.path.join(os.getcwd(), fmi_setting_file))
    path = os.path.join(folder, os.path.basename(fmi_setting_file))
    read_file = open(path, "r")
    fmi_data = json.load(read_file)

    folder = os.path.dirname(os.path.join(os.getcwd(), precice_setting_file))
    path = os.path.join(folder, os.path.basename(precice_setting_file))
    read_file = open(path, "r")
    precice_data = json.load(read_file)

    # FMU setup

    fmu_file_name = fmi_data["simulation_params"]["fmu_file_name"]
    fmu_instance = fmi_data["simulation_params"]["fmu_instance_name"]
    folder = os.path.join(os.getcwd(), os.path.dirname(fmu_file_name))
    path = os.path.join(folder, os.path.basename(fmu_file_name))
    model_description = read_model_description(path)

    vrs = {}
    for variable in model_description.modelVariables:
        vrs[variable.name] = variable.valueReference

    output_names = fmi_data["simulation_params"]["output"]

    fmu_read_data_names = fmi_data["simulation_params"]["fmu_read_data_names"]
    fmu_write_data_names = fmi_data["simulation_params"]["fmu_write_data_names"]

    vr_read = list()
    for read_name in fmu_read_data_names:
        vr = vrs[read_name]
        vr_read.append(vr)

    vr_write = list()
    for write_name in fmu_write_data_names:
        vr = vrs[write_name]
        vr_write.append(vr)

    can_get_and_set_fmu_state = model_description.coSimulation.canGetAndSetFMUstate

    is_fmi1 = (model_description.fmiVersion == '1.0')
    is_fmi2 = (model_description.fmiVersion == '2.0')
    is_fmi3 = (model_description.fmiVersion == '3.0')

    unzipdir = extract(fmu_file_name)

    # Instantiate FMU

    fmu = instantiate_fmu(unzipdir=unzipdir, model_description=model_description, fmi_type="CoSimulation")

    if is_fmi1:
        # Set initial parameters
        if "initial_conditions" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["initial_conditions"])
        if "model_params" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["model_params"])
        # Get initial write data
        fmu_write_data_init = fmu.getReal(vr_write)

    elif is_fmi2:
        # Set initial parameters
        fmu.enterInitializationMode()
        if "initial_conditions" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["initial_conditions"])
        if "model_params" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["model_params"])
        fmu.exitInitializationMode()
        # Get initial write data
        fmu_write_data_init = fmu.getReal(vr_write)

    elif is_fmi3:
        # Set initial parameters
        fmu.enterInitializationMode()
        if "initial_conditions" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["initial_conditions"])
        if "model_params" in fmi_data:
            apply_start_values(fmu, model_description, fmi_data["model_params"])
        fmu.exitInitializationMode()
        # Get initial write data
        fmu_write_data_init = fmu.getFloat64(vr_write)

    # Create input object

    try:
        signal_names = fmi_data["input_signals"]["names"]
        signal_data = fmi_data["input_signals"]["data"]
        dtype = []
        for i in range(len(signal_names)):
            tpl = tuple([signal_names[i], type(signal_data[0][i])])
            dtype.append(tpl)
        signals = np.array([tuple(i) for i in signal_data],dtype=dtype)
    except BaseException:
        signals = None

    input = Input(fmu, model_description, signals)

    # preCICE setup

    # Current limitations of the Runner
    solver_process_index = 0
    solver_process_size = 1
    num_vertices = 1

    # Initialize interface
    interface = precice.Interface(
        precice_data["coupling_params"]["participant_name"],
        precice_data["coupling_params"]["config_file_name"],
        solver_process_index,
        solver_process_size
    )

    mesh_id = interface.get_mesh_id(precice_data["coupling_params"]["mesh_name"])
    dimensions = interface.get_dimensions()

    vertices = np.zeros((num_vertices, dimensions))
    read_data = np.zeros((num_vertices, dimensions))
    write_data = np.zeros((num_vertices, dimensions))

    vertex_id = interface.set_mesh_vertices(mesh_id, vertices)
    read_data_id = interface.get_data_id(precice_data["coupling_params"]["read_data"]["name"], mesh_id)
    write_data_id = interface.get_data_id(precice_data["coupling_params"]["write_data"]["name"], mesh_id)
    read_data_type = precice_data["coupling_params"]["read_data"]["type"]
    write_data_type = precice_data["coupling_params"]["write_data"]["type"]

    # check entries for data types
    if read_data_type not in ["scalar", "vector"]:
        raise Exception("Wrong data type for read data in the precice settings file. Please choose from: scalar, vector")
    if write_data_type not in ["scalar", "vector"]:
        raise Exception("Wrong data type for write data in the precice settings file. Please choose from: scalar, vector")

    # initial value for write data
    if write_data_type == "scalar":
        write_data = fmu_write_data_init[0]
    elif write_data_type == "vector":
        write_data = np.array(fmu_write_data_init)

    precice_dt = interface.initialize()
    my_dt = precice_dt  # use my_dt < precice_dt for subcycling

    # write initial data
    if interface.is_action_required(precice.action_write_initial_data()):
        precice_write_data(interface, write_data_type, write_data_id, vertex_id, write_data)
        interface.mark_action_fulfilled(precice.action_write_initial_data())

    interface.initialize_data()

    recorder = Recorder(fmu=fmu, modelDescription=model_description, variableNames=output_names)

    t = 0

    recorder.sample(t, force=False)

    while interface.is_coupling_ongoing():
        if interface.is_action_required(precice.action_write_iteration_checkpoint()):

            # Check if model has the appropiate functionalities
            if is_fmi1:
                raise Exception("Implicit coupling not possible because FMU model with FMI1 can't reset state. "
                                "Please update model to FMI2 or FMI3. "
                                "Alternatively, choose an explicit coupling scheme.")
            if not can_get_and_set_fmu_state:
                raise Exception("Implicit coupling not possible because FMU model can't reset state. "
                                "Please implement getFMUstate() and setFMUstate() in FMU "
                                "and set the according flag in ModelDescription.xml. "
                                "Alternatively, choose an explicit coupling scheme.")
            
            # Save checkpoint
            state_cp = fmu.getFMUState()
            t_cp = t
            
            interface.mark_action_fulfilled(precice.action_write_iteration_checkpoint())

        # Compute current time step size
        dt = np.min([precice_dt, my_dt])

        # Read data from other participant
        read_data = precice_read_data(interface, read_data_type, read_data_id, vertex_id)

        # Convert data to list for FMU
        if read_data_type == "scalar":
            read_data = [read_data]
        elif read_data_type == "vector":
            read_data = list(read_data)

        # Set signals in FMU
        input.apply(t)

        # Compute next time step
        if is_fmi1 or is_fmi2: 
            fmu.setReal(vr_read, read_data)
            fmu.doStep(t, dt)
            result = fmu.getReal(vr_write)
        if is_fmi3:
            fmu.setFloat64(vr_read, read_data)
            fmu.doStep(t, dt)
            result = fmu.getFloat64(vr_write)

        # Convert result to double or array for preCICE
        if write_data_type == "scalar":
            write_data = result[0]
        elif write_data_type == "vector":
            write_data = np.array(result)

        # Write data to other participant
        precice_write_data(interface, write_data_type, write_data_id, vertex_id, write_data)

        t = t + dt

        precice_dt = interface.advance(dt)

        if interface.is_action_required(precice.action_read_iteration_checkpoint()):
            
            fmu.setFMUState(state_cp)
            t = t_cp
            
            interface.mark_action_fulfilled(precice.action_read_iteration_checkpoint())

        else:
            # Save output data for completed timestep
            recorder.sample(t, force=False)

    interface.finalize()

    # store final results
    try:
        # create output directory
        output_dir = os.path.dirname(fmi_data["simulation_params"]["output_file_name"])
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # store data
        recorder.sample(t, force=False)
        results = recorder.result()
        write_csv(fmi_data["simulation_params"]["output_file_name"], results)

    except BaseException:

        pass

    # terminate FMU
    fmu.terminate()
    fmu.freeInstance()
    shutil.rmtree(unzipdir, ignore_errors=True)


if __name__ == "__main__":
    main()
