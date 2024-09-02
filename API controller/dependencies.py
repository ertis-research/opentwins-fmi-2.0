from kubernetes import client, config
import os
from loguru import logger
import boto3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# from dotenv import load_dotenv

# load_dotenv()

def get_sql_client():
    """ Get the SQL client from the environment variables
        Return:
            str: connection_string
    """
    if os.getenv('POSTGRE_PORT') is not None:
        connectionString = "postgresql+asyncpg://{}:{}@{}:{}/{}".format( os.getenv('POSTGRE_USER'), os.getenv('POSTGRE_PASSWORD'), os.getenv('POSTGRE_HOST'), os.getenv('POSTGRE_PORT'), os.getenv('POSTGRE_DB'))
    else:
        connectionString = "postgresql+asyncpg://{}:{}@{}/{}".format( os.getenv('POSTGRE_USER'), os.getenv('POSTGRE_PASSWORD'), os.getenv('POSTGRE_HOST'), os.getenv('POSTGRE_DB'))
    logger.info(connectionString)
    engine = create_async_engine(connectionString)

    return engine
    
# def get_postgre_client():
#     """ Get the PostgreSQL client from the environment variables
#         Return:
#             str: connection_string
#     """
#     connectionString = "host={} dbname={} user={} password={} port={} async=1".format( os.getenv('POSTGRE_HOST'), os.getenv('POSTGRE_DB'), os.getenv('POSTGRE_USER'), os.getenv('POSTGRE_PASSWORD'), os.getenv('POSTGRE_PORT'))
#     #connectionString = "host='{}' dbname = '{}' user = '{}' password = '{}' port = '{}'".format( os.getenv('POSTGRE_HOST'), os.getenv('POSTGRE_DB'), os.getenv('POSTGRE_USER'), os.getenv('POSTGRE_PASSWORD'), os.getenv('POSTGRE_PORT'))
#     logger.info(connectionString)
#     #conn = psycopg2.connect(connectionString)
#     conn = psycopg2.connect(host=os.getenv('POSTGRE_HOST'), dbname=os.getenv('POSTGRE_DB'), user=os.getenv('POSTGRE_USER'), password=os.getenv('POSTGRE_PASSWORD'), port=os.getenv('POSTGRE_PORT'), async_=1)
    
#     return conn

def get_minio_resource():
    MINIO_URL = os.getenv('MINIO_URL')
    MINIO_A_KEY = os.getenv('MINIO_A_KEY')
    MINIO_S_KEY = os.getenv('MINIO_S_KEY')
    
    print(MINIO_URL)
    print(MINIO_A_KEY)
    print(MINIO_S_KEY)

    s3 = boto3.resource('s3', 
                        aws_access_key_id=MINIO_A_KEY, 
                        aws_secret_access_key=MINIO_S_KEY, 
                        endpoint_url=MINIO_URL,
                        config = boto3.session.Config(signature_version='s3v4'),
                        )
    return s3

def get_kubernetes_api_client():
    """ Get Kubernetes configuration.
        You can provide a token and the external host IP 
        to access a external Kubernetes cluster. If one
        of them is not provided the configuration returned
        will be for your local machine.
        Parameters:
            str: token 
            str: external_host
        Return:
            Kubernetes API client
    """
    # KUBERNETES code goes here
    aConfiguration = client.Configuration()
    inside_cluster = os.getenv("INSIDE_CLUSTER", 'False').lower() in ('true', '1', 't')
    
    
    if inside_cluster:
        logger.info("RUNNING INSIDE CLUSTER")
        config.load_incluster_config(aConfiguration) # To run inside the container
    else:
        logger.info("RUNNING OUTSIDE CLUSTER")
        external_host = os.getenv('KUBE_HOST')
        token = os.getenv('TOKEN_KUBERNETES')

        config.load_kube_config() # To run externally
        
        aConfiguration.host = external_host 
        aConfiguration.verify_ssl = False
        aConfiguration.api_key = { "authorization": "Bearer " + token }
        
    api_client = client.ApiClient(aConfiguration)
    
    return api_client

def get_kube_namespace():
    """ Get the namespace from the environment variables
        Return:
            str: namespace
    """
    return os.getenv('KUBE_NAMESPACE')