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
                await connection.commit()
        except sqlalchemy.exc.IntegrityError as e:
            raise DatabaseError("Simulation schema already exists")
        print(result)
         
    async def get_simulation_schema(self, context, schema_id):
        query = "SELECT sim_schemme FROM fmi_sim_schemmas WHERE id = :id and context = :context".format(schema_id, context)
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), {"context":context, "id":schema_id})
        except Exception as e:
            raise DatabaseError("No controlo aun en get simulation schema")
        
        schema_list = []            
        for row in result:
            schema_list.append(row[0])
            
        return schema_list
    
    async def delete_simulation_schema(self, context, schema_id):
        query = "DELETE FROM fmi_sim_schemmas WHERE id = :id and context = :context".format(schema_id, context)
        try:
            async with self.engine.connect() as connection:
                result = await connection.execute(text(query), {"context":context, "id":schema_id})
                await connection.commit()
        except Exception as e:
            raise DatabaseError("Error que no controlo aun")
        
        print(result)