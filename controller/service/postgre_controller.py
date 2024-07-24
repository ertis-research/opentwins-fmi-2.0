# Import the logging library and the custom formatter
from loguru import logger
from fastapi import Depends
from dependencies import get_postgre_client
from errors import SimulationError
from fastapi.encoders import jsonable_encoder
import psycopg2


class PostgreSQLControllerService:

    def __init__(self, client : psycopg2.extensions.connection = Depends(get_postgre_client)):
        self.connection = client
        self.cursor = self.connection.cursor()


    def get_simulation_list(self, context = None):
        query = "SELECT name FROM fmi_sim_schemmas"
        
        if context is not None:
            query += " WHERE context = '{}'".format(context)
        
        self.cursor.execute(query)
        
        result = self.cursor.fetchall()
        result = [x[0] for x in result]
        print(result)
        
        self.connection.close()
        return result
    
    def get_simulation_schemma(self, simulation_id):
        query = "SELECT sim_schemme FROM fmi_sim_schemmas WHERE id = {}".format(simulation_id)
        
        self.cursor.execute(query)
        
        result = self.cursor.fetchall()
        result = [x[0] for x in result]
        
        self.connection.close()
        return result