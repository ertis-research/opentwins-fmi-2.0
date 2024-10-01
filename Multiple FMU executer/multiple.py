import sys
import os
import time
import json
import shutil
import os.path
from fmpy import *
import numpy as np
import pandas as pd
from loguru import logger
from pathlib import Path
from fmpy import simulate_fmu
from utils.simulation import simulate_ssp
from fmpy.simulation import _get_output_variables
from utils.ssd import read_ssd, read_ssd_from_ssp
from fmpy.util import download_test_file, download_file
from controllers.minio_controller import MinioControllerService
from controllers.message_broker_controller import MessageBrokerController
from controllers.influxdb_controller import InfluxDBController


def get_variable_from_influxdb(influxController, query):
    return influxController.get_variable(query)

def get_variable_from_mqtt(topic, mapper):
    raise Exception("Not implemented yet")


def retrieve_data():
    # FMU has default values for the parameters. By default the simulation will run with those parameters unless the user specifies them either in the
    # message broker or in the simulation request.
    
    #ANOTATIONS: FMU NAME IS THE NAME WITHOUT THE .FMU EXTENSION
    start_values = {}
    
    inputs = json.loads(os.getenv('SIMULATION_INPUTS'))
    outputs = json.loads(os.getenv('SIMULATION_OUTPUTS'))
 
    influxController = InfluxDBController()
    
    for input in inputs:
        
        if input["type"] == "influxdb":
            start_value = get_variable_from_influxdb(influxController, input["query"])
        elif input["type"] == "mqtt":
            start_value = get_variable_from_mqtt(input["topic"], input["mapper"]) # Not implemented yet
        elif input["type"] == "fixed":
            start_value = input["value"]
        elif input["type"] == "default":
            continue
        else:
            raise Exception("Input type not recognized")
        
        start_values[input["id"]] = start_value
        
    outputs = [variable["id"] for variable in outputs]

      
    # start_values = None # TODO: Remove this line when the schema is ready
    # outputs = None # TODO: Remove this line when the schema is ready
    
    retrieved_data = {
            # General information
            "SIMULATION_NAME" : os.getenv('SIMULATION_NAME'),
            "SIMULATION_ID"   : os.getenv('SIMULATION_ID'),
            "SIMULATION_SCHEMA": os.getenv('SIMULATION_SCHEMA'),
            "SIMULATION_CONTEXT": os.getenv('SIMULATION_CONTEXT'),

            # Simulation information
            "SIMULATION_START_TIME"   : float(os.getenv('SIMULATION_START_TIME')),
            "SIMULATION_END_TIME"     : float(os.getenv('SIMULATION_END_TIME')),
            "SIMULATION_STEP_SIZE"    : float(os.getenv('SIMULATION_STEP_SIZE')),

            "SIMULATION_DELAY_WARNING"    : float(os.getenv('SIMULATION_DELAY_WARNING')),
            "SIMULATION_LAST_VALUE"       : bool(os.getenv('SIMULATION_LAST_VALUE')),
            
            "INPUTS"     : start_values,
            "OUTPUTS"    : outputs,
            "FMU_LIST"   : [fmu["id"] for fmu in json.loads(os.getenv('SIMULATION_FMUS'))]
    }
    
    
    return retrieved_data

def run_simulation(data, ssp_path):
    result = simulate_ssp(ssp_path, 
                          stop_time=data["SIMULATION_END_TIME"],
                          start_time=data["SIMULATION_START_TIME"],
                          step_size=data["SIMULATION_STEP_SIZE"],
                          input=data["INPUTS"])
    # TODO: Es posible que los inputs sean concretamente las entradas, por lo que otras variables sean simplemente parámetros. Eso hay que controlarlo.
    
    ssd = read_ssd(ssp_path)
        
    names = []

    for connector in ssd.system.connectors:
        names.append(connector.name)

    # Create a DataFrame with the results using the names sof the connectors
    results_df = pd.DataFrame(result, columns=names)
    
    if data["SIMULATION_LAST_VALUE"]:
        logger.info("Last value requested")
        results_df = pd.DataFrame(results_df.iloc[-1])
    return results_df

    
    
def send_results_to_broker(results):
    broker_controller = MessageBrokerController()
    #results = results.transpose()
    
    for index, row in results.iterrows():
        result = row.to_dict()
        result["SIMULATION_ID"] = os.getenv('SIMULATION_ID')
        result["SIMULATION_NAME"] = os.getenv('SIMULATION_NAME') 
        
        result = json.dumps(result)
        broker_controller.send_message(result)

def create_ssp(simulation_id):
    archived = shutil.make_archive(simulation_id, 'zip', 'ssp_creation')
    
    if os.path.exists(f"{simulation_id}.zip"):
        print(archived)
    else: 
        print("ZIP file not created")
        
    
    p = Path(f'{simulation_id}.zip')
    p.rename(p.with_suffix('.ssp'))
    
    return f"{simulation_id}.ssp"


if __name__ == "__main__":
    os.mkdir("ssp_creation") 
    os.mkdir("ssp_creation/resources")
    ##################################
    # Retrieving environment variables
    ##################################
    logger.info("Starting simulation")
    
    # Retrieve the data
    logger.info("Retrieving data")
    retrieved_data = retrieve_data()
    logger.info("Retrieved data from environment variables successfully")
    fmu_list = retrieved_data['FMU_LIST']
    context = retrieved_data['SIMULATION_CONTEXT']
    schema_id = retrieved_data['SIMULATION_SCHEMA']
    simulation_id = retrieved_data['SIMULATION_ID']
    

    # Download the FMU and ssd
    logger.info("Downloading FMUs")
    controladorMINIO = MinioControllerService()
    controladorMINIO.download_fmu(context, fmu_list)
    logger.info("FMUs downloaded successfully")
    schema_path = controladorMINIO.download_simulation_ssd(context, schema_id)
    ssp_path = create_ssp(simulation_id)
    
    # Run the simulation
    logger.info("Running simulation")
    simulation_results = run_simulation(retrieved_data, ssp_path)
    logger.info("Simulation finished")

    # Send the results to the broker
    logger.info("Sending results to broker")
    send_results_to_broker(simulation_results)
    logger.info("Results sent to broker")

    logger.info("Simulation finished successfully")

