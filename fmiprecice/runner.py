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

def precice2_read_data(participant, data_type, read_data_id, vertex_id):
    """
    Reads data from preCICE. The preCICE API call depends on the data type, scalar or vector.
    """

    if is_precice2:
        if data_type == "scalar":
            read_data = participant.read_scalar_data(read_data_id, vertex_id)
        elif data_type == "vector":
            read_data = participant.read_vector_data(read_data_id, vertex_id)

    return read_data


def precice2_write_data(participant, data_type, write_data_id, vertex_id, write_data):
    """
    Writes data to preCICE. The preCICE API call depends on the data type, scalar or vector.
    """

    if data_type == "scalar":
        write_data = participant.write_scalar_data(write_data_id, vertex_id, write_data)
    elif data_type == "vector":
        write_data = participant.write_vector_data(write_data_id, vertex_id, write_data)
    else:
        raise Exception("Please choose data type from: scalar, vector.")


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
    
    # Determine version of preCICE (currently still returns v2 for pyprecice-develop-3.0.0)
    #is_precice2 = (precice.get_version_information().decode()[0] == "2")
    #is_precice3 = (precice.get_version_information().decode()[0] == "3")
    is_precice2 = False
    is_precice3 = True

    
    if is_precice2:
        # Create the participant
        participant = precice.Interface(
            precice_data["coupling_params"]["participant_name"],
            precice_data["coupling_params"]["config_file_name"],
            solver_process_index,
            solver_process_size
        )
        
        mesh_id = participant.get_mesh_id(precice_data["coupling_params"]["mesh_name"])
        dimensions = participant.get_dimensions()

        vertices = np.zeros((num_vertices, dimensions))
        read_data = np.zeros((num_vertices, dimensions))
        write_data = np.zeros((num_vertices, dimensions))

        vertex_id = participant.set_mesh_vertices(mesh_id, vertices)
        read_data_id = participant.get_data_id(precice_data["coupling_params"]["read_data"]["name"], mesh_id)
        write_data_id = participant.get_data_id(precice_data["coupling_params"]["write_data"]["name"], mesh_id)
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

        precice_dt = participant.initialize()
        my_dt = precice_dt  # use my_dt < precice_dt for subcycling, necessary here?

        # write initial data
        if participant.is_action_required(precice.action_write_initial_data()):
            precice2_write_data(participant, write_data_type, write_data_id, vertex_id, write_data)
            participant.mark_action_fulfilled(precice.action_write_initial_data())

        participant.initialize_data()
        
    elif is_precice3:
        # Create the participant
        participant = precice.Participant(
            precice_data["coupling_params"]["participant_name"],
            precice_data["coupling_params"]["config_file_name"],
            solver_process_index,
            solver_process_size
        )

        mesh_name = precice_data["coupling_params"]["mesh_name"]
        read_data_name = precice_data["coupling_params"]["read_data"]["name"]
        write_data_name = precice_data["coupling_params"]["write_data"]["name"]
        
        dimensions = participant.get_mesh_dimensions(mesh_name)

        vertices = np.zeros((num_vertices, dimensions))
        read_data = np.zeros((num_vertices, dimensions))
        write_data = np.zeros((num_vertices, dimensions))
        
        # you can use this to read from precice-config if you exchange scalar data (dim=1) or vector data (dim=2 or 3)
        # With this information, you can remove the entry "data type" from the JSON config files
        # Until now, the information had to be passed by the user but be equal to the config entry
        # Dont forget to change data type in config during testing
        print("Use participant.get_data_dimensions() and remove data_type from JSON files.")
        print(participant.get_data_dimensions(mesh_name, read_data_name))

        vertex_id = participant.set_mesh_vertices(mesh_name, vertices)       

        # check entries for data types
        read_data_type = precice_data["coupling_params"]["read_data"]["type"]
        write_data_type = precice_data["coupling_params"]["write_data"]["type"]
        if read_data_type not in ["scalar", "vector"]:
            raise Exception("Wrong data type for read data in the precice settings file. Please choose from: scalar, vector")
        if write_data_type not in ["scalar", "vector"]:
            raise Exception("Wrong data type for write data in the precice settings file. Please choose from: scalar, vector")

        # initial value for write data
        if write_data_type == "scalar":
            write_data = fmu_write_data_init[0]
        elif write_data_type == "vector":
            write_data = np.array(fmu_write_data_init)

        # write initial data
        if participant.requires_initial_data():
            participant.write_data(mesh_name, write_data_name, vertex_id, write_data)
        
        participant.initialize()


    recorder = Recorder(fmu=fmu, modelDescription=model_description, variableNames=output_names)

    t = 0

    recorder.sample(t, force=False)
    

    while participant.is_coupling_ongoing():
        
        # Wrapper function instead of if / else?
        if is_precice2:    
            if participant.is_action_required(precice.action_write_iteration_checkpoint()): # v3: Wrapper function?

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

                participant.mark_action_fulfilled(precice.action_write_iteration_checkpoint())

        elif is_precice3:
            if participant.requires_writing_checkpoint():

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
        
        # Is this necessary for v2 or can it go?
        #dt = np.min([precice_dt, my_dt])
        
        # Compute current time step size
        precice_dt = participant.get_max_time_step_size() # v3 only
        dt = precice_dt

        # Read data from other participant
        if is_precice2:
            read_data = precice2_read_data(participant, read_data_type, read_data_id, vertex_id) 
        elif is_precice3:
            read_data = participant.read_data(mesh_name, read_data_name, vertex_id, precice_dt)     
        
        # Convert data to list for FMU
        if is_precice2:
            if read_data_type == "scalar":
                read_data = [read_data]
            elif read_data_type == "vector":
                read_data = list(read_data)
        if is_precice3:
            if read_data_type == "scalar":
                # preCICE 3 returns the scalar data as a list
                pass
            elif read_data_type == "vector":
                # why does this work with one-entry vectors? A (1,2) vector is written on a single scalar FMU variable. This is not correct
                # The program should abort if data_type = vector and the number of entries in vr_read / vr_write do not match the number of elements in read_data / write_data
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
        if is_precice2:
            # Convert to double or array
            if write_data_type == "scalar":
                write_data = result[0]
            elif write_data_type == "vector":
                write_data = np.array(result)
        elif is_precice3:
            # Convert to array
            if write_data_type == "scalar":
                write_data = np.array(result)
                #write_data = result # this also works, result is a list and therefore array-like
            elif write_data_type == "vector":
                write_data = np.array([result])

        # Write data to other participant
        if is_precice2:
            precice2_write_data(participant, write_data_type, write_data_id, vertex_id, write_data)
        elif is_precice3:
            participant.write_data(mesh_name, write_data_name, vertex_id, write_data)

        t = t + dt

        # Wrapper function instead of if / else?
        if is_precice2:
            precice_dt = participant.advance(dt)

            if participant.is_action_required(precice.action_read_iteration_checkpoint()): #v3: Wrapper function?

                fmu.setFMUState(state_cp)
                t = t_cp

                participant.mark_action_fulfilled(precice.action_read_iteration_checkpoint())

            else:
                # Save output data for completed timestep
                recorder.sample(t, force=False)
                
        elif is_precice3:
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
