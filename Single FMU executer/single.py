import sys
import os
import time
import json
import numpy as np
import pandas as pd
from fmpy import simulate_fmu
from fmpy.util import download_test_file, download_file
from fmpy.simulation import _get_output_variables
from fmpy import *
from controllers.minio_controller import MinioControllerService
from controllers.message_broker_controller import MessageBrokerController
from controllers.influxdb_controller import InfluxDBController
from loguru import logger



def get_variable_from_influxdb(influxController, query):
    return influxController.get_variable(query)

def get_variable_from_mqtt(topic, mapper):
    pass


def retrieve_data():
    # FMU has default values for the parameters. By default the simulation will run with those parameters unless the user specifies them either in the
    # message broker or in the simulation request.
    
    #ANOTATIONS: FMU NAME IS THE NAME WITHOUT THE .FMU EXTENSION
    start_values = {}
    
    inputs = json.loads(os.getenv('SIMULATION_INPUTS'))
    outputs = json.loads(os.getenv('SIMULATION_OUTPUTS'))
    
    print(type(inputs))
    print(inputs)
    
    #inputs = schema["inputs"]  #TODO: QUITAR CUANDO FUNCIONE EL SCHEMA
    # outputs = schema["outputs"] #TODO: QUITAR CUANDO FUNCIONE EL SCHEMA
    
    
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
            "SIMULATION_LAST_VALUE"       : True if os.getenv('SIMULATION_LAST_VALUE') is not None and os.getenv('SIMULATION_LAST_VALUE') == "True" else False,
            
            "INPUTS"     : start_values,
            "OUTPUTS"    : outputs,
            "FMU_NAME"   : json.loads(os.getenv('SIMULATION_FMUS'))[0]["id"]
    }
    
    
    return retrieved_data

def run_simulation(data, fmu_path):
    # def __new__(subtype, shape, dtype=float, buffer=None, offset=0, strides=None, order=None, modelDescription=None):
    #     obj = super(SimulationResult, subtype).__new__(subtype, shape, dtype, buffer, offset, strides, order)
    #     obj.modelDescription = modelDescription
    #     return obj

    result = simulate_fmu(fmu_path, 
                          start_time=data["SIMULATION_START_TIME"], 
                          stop_time=data["SIMULATION_END_TIME"],
                          output_interval=data["SIMULATION_STEP_SIZE"],
                          input = data["INPUTS"] if data["INPUTS"] else None)
    
    
    header = list(result.dtype.names)
    
    results_df = pd.DataFrame(result, columns=header)
    
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




if __name__ == "__main__":
    ##################################
    # Retrieving environment variables
    ##################################
    logger.info("Starting simulation")
    
    # Retrieve the data
    logger.info("Retrieving data")
    retrieved_data = retrieve_data()
    logger.info("Retrieved data from environment variables successfully")
    fmu_name = retrieved_data['FMU_NAME']
    context = retrieved_data['SIMULATION_CONTEXT']
    
    # Download the FMU
    logger.info("Downloading FMU")
    controladorMINIO = MinioControllerService()
    fmu_path = controladorMINIO.download_fmu(context, fmu_name+".fmu")
    logger.info("FMU downloaded successfully")
    
    # Run the simulation
    logger.info("Running simulation")
    simulation_results = run_simulation(retrieved_data, fmu_path)
    logger.info("Simulation finished")

    print("########################## Simulation results ##########################")
    print(simulation_results.head())
    print("##########################################################################")

    # Send the results to the broker
    logger.info("Sending results to broker")
    send_results_to_broker(simulation_results)
    logger.info("Results sent to broker")

    logger.info("Simulation finished successfully")

