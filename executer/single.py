import time
import numpy as np
import sys
import os
from fmpy import simulate_fmu
from fmpy.util import download_test_file, download_file
from fmpy.simulation import _get_output_variables
from fmpy import *
import matplotlib.pyplot as plt
from controllers.minio_controller import MinioControllerService



def retrieve_data():
    # FMU has default values for the parameters. By default the simulation will run with those parameters unless the user specifies them either in the
    # message broker or in the simulation request.
    
    variable_graph = os.getenv('VARIABLE_GRAPH')
    input_output_source = os.getenv('INPUT_OUTPUT_SOURCE')
    
    
    pass

def run_simulation(data, fmu_path):
    pass

def send_results_to_broker(results):
    pass




if __name__ == "__main__":
    ##################################
    # Retrieving environment variables
    ##################################

    # General information
    SIMULATION_NAME = os.getenv('SIMULATION_NAME')
    SIMULATION_ID = os.getenv('SIMULATION_ID')

    # Target broker informationWW
    BROKER_IP = os.getenv('BROKER_IP')
    BROKER_PORT = os.getenv('BROKER_PORT')
    BROKER_TOPIC = os.getenv('BROKER_TOPIC')

    # Simulation information
    SIMULATION_START_TIME = os.getenv('SIMULATION_START_TIME')
    SIMULATION_END_TIME = os.getenv('SIMULATION_END_TIME')
    SIMULATION_STEP_SIZE = os.getenv('SIMULATION_STEP_SIZE')

    SIMULATION_DELAY_WARNING = os.getenv('SIMULATION_DELAY_WARNING')

    SIMULATION_SCHEDULE_TYPE = os.getenv('SIMULATION_SCHEDULE_TYPE')

    # FMU information
    FMU_NAME = os.getenv('FMU_NAME')


    controlador = MinioControllerService()
    fmu_path = controlador.download_fmu("opentwins", "FirstOrder.fmu")
    
    # Retrieve the data
    retrieved_data = retrieve_data()
    
    # Run the simulation
    simulation_results = run_simulation(retrieved_data, fmu_path)

    # Send the results to the broker
    send_results_to_broker(simulation_results)

    print("Simulation finished")

