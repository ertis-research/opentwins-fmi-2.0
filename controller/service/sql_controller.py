# Import the logging library and the custom formatter
from loguru import logger
from fastapi import Depends
from dependencies import get_sql_client
from errors import SimulationError, DatabaseError
from fastapi.encoders import jsonable_encoder
import sqlalchemy
from sqlalchemy import text
import json

class SQLControllerService:

    def __init__(self, client : sqlalchemy.engine = Depends(get_sql_client)):
        self.engine = client
        #self.cursor = self.connection.cursor()


    async def get_simulation_schema_list(self, context = None):
        query = "SELECT id, name FROM fmi_sim_schemmas"
        variables = {}
        
        if context is not None:
            query += " WHERE context = :context"
            variables = {"context":context}
        
        schema_list = []
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), variables)
                
        except Exception as e:
            raise DatabaseError("Failed to retrieve simulation list")
        
        for row in result:
            schema_list.append({"id":row[0], "name":row[1]})
        return schema_list
      
    async def create_simulation_schema(self, data, context):
        id = data['id']
        name = data['name']
        
        query = "INSERT INTO fmi_sim_schemmas (id, name, context, sim_schemme) VALUES (:id, :name, :context, :sim_schemme)"
        
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), {"context":context, "name":name, "id":id, "sim_schemme":json.dumps(data)})
                connection.commit()
        except sqlalchemy.exc.IntegrityError as e:
            raise DatabaseError("Simulation schema already exists")
        print(result)
         
    async def get_simulation_schema(self, context, simulation_id):
        query = "SELECT sim_schemme FROM fmi_sim_schemmas WHERE id = :id and context = :context".format(simulation_id, context)
        print("Entro")
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), {"context":context, "id":simulation_id})
        except sqlalchemy.exc.IntegrityError as e:
            raise DatabaseError("Simulation schema already exists")
        
        schema = result.fetchone()[0]
        return schema
    
    #TODO: Terminar el delete
    async def delete_simulation_schema(self, context, simulation_id):
        query = "DELETE FROM FROM fmi_sim_schemmas WHERE id = :id and context = :context".format(simulation_id, context)
        print("Entro")
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), {"context":context, "id":simulation_id})
        except Exception as e:
            raise DatabaseError("Error que no controlo aun")
        
        schema = result.fetchone()[0]
        return schema