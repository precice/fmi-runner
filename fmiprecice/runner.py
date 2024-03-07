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


def main():
    """
    Executes the Runner

    - Load settings from json files
    - Load FMU model and prepare the simulation
    - Create an object of the preCICE participant
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
        signals = np.array([tuple(i) for i in signal_data], dtype=dtype)
    except BaseException:
        signals = None

    input = Input(fmu, model_description, signals)

    # preCICE setup

    # Current limitations of the Runner
    solver_process_index = 0
    solver_process_size = 1
    num_vertices = 1

    if precice.get_version_information().decode()[0] != "3":
        raise Exception("This version of the FMI Runner is only compatible with preCICE v3.")

    # Create the participant
    participant = precice.Participant(
        precice_data["coupling_params"]["participant_name"],
        precice_data["coupling_params"]["config_file_name"],
        solver_process_index,
        solver_process_size
    )

    mesh_name = precice_data["coupling_params"]["mesh_name"]
    read_data_name = precice_data["coupling_params"]["read_data_name"]
    write_data_name = precice_data["coupling_params"]["write_data_name"]

    mesh_dimensions = participant.get_mesh_dimensions(mesh_name)
    vertices = np.zeros((num_vertices, mesh_dimensions))

    read_data_dimensions = participant.get_data_dimensions(mesh_name, read_data_name)
    read_data = np.zeros((num_vertices, read_data_dimensions))

    write_data_dimensions = participant.get_data_dimensions(mesh_name, write_data_name)
    write_data = np.zeros((num_vertices, write_data_dimensions))

    vertex_id = participant.set_mesh_vertices(mesh_name, vertices)

    # write initial data
    if participant.requires_initial_data():
        write_data[0] = np.array(fmu_write_data_init)  # only one vertex
        participant.write_data(mesh_name, write_data_name, vertex_id, write_data)

    participant.initialize()

    recorder = Recorder(fmu=fmu, modelDescription=model_description, variableNames=output_names)

    t = 0

    recorder.sample(t, force=False)

    while participant.is_coupling_ongoing():

        if participant.requires_writing_checkpoint():

            # Check if model has the appropriate functionalities
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

        # Compute current time step size
        precice_dt = participant.get_max_time_step_size()
        dt = precice_dt  # FMU always does the max possible dt

        read_data = participant.read_data(mesh_name, read_data_name, vertex_id, precice_dt)

        # Convert data to list for FMU
        if participant.get_data_dimensions(mesh_name, read_data_name) > 1:
            # TODO: The program should abort if data_type = vector and the number of entries
            # in vr_read / vr_write do not match the number of elements in read_data / write_data
            # preCICE aborts for write_data() with the wrong dimensions, that is ok for now
            read_data = read_data[0]

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

        # Convert result for preCICE
        # Convert to array
        if participant.get_data_dimensions(mesh_name, write_data_name) == 1:
            write_data = np.array(result)
        else:
            write_data = np.array([result])

        participant.write_data(mesh_name, write_data_name, vertex_id, write_data)

        t = t + dt

        participant.advance(dt)

        if participant.requires_reading_checkpoint():
            fmu.setFMUState(state_cp)
            t = t_cp

        else:
            # Save output data for completed timestep
            recorder.sample(t, force=False)

    participant.finalize()

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
