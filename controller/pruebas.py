import sqlalchemy
from sqlalchemy import text
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from loguru import logger

context = "opentwins"
POSTGRE_HOST="postgrest.ertis.uma.es"
#POSTGRE_PORT=35432
POSTGRE_PORT=443
POSTGRE_DB="fmi-simulations-test"
POSTGRE_USER="postgres"
POSTGRE_PASSWORD="postgres"

connectionString = "postgresql+psycopg2://{}:{}@{}/{}".format( POSTGRE_USER, POSTGRE_PASSWORD, POSTGRE_HOST, POSTGRE_DB)
logger.info(connectionString)
engine = create_engine(connectionString)

query = "SELECT id, name FROM fmi_sim_schemmas"
variables = {}

if context is not None:
    query += " WHERE context = :context"
    variables = {"context":context}

schema_list = []

with engine.connect() as connection:
    result = connection.execute(text(query), variables)

for row in result:
    schema_list.append({"id":row[0], "name":row[1]})