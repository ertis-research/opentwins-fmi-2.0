import os
import json
from kubernetes import client
# Import the logging library and the custom formatter
from loguru import logger
from fastapi import APIRouter, Request, Depends
from dependencies import get_kubernetes_api_client, get_kube_namespace
from errors import *
from fastapi.encoders import jsonable_encoder
from service.sql_controller import SQLControllerService

import urllib3

urllib3.disable_warnings() # HABRIA QUE QUITARLO EN PRODUCCION

class KubernetesControllerService:
    def __init__(self, api_client : client.ApiClient=Depends(get_kubernetes_api_client), namespace : str=Depends(get_kube_namespace)) -> None:
        self.api_client = api_client
        self.api_instance = client.CoreV1Api(api_client)
        self.k8s_apps_v1 = client.AppsV1Api(api_client)
        self.batch_api = client.BatchV1Api(api_client)
        self.namespace = namespace
        
         
    def check_if_exists(self, context: str, simulationId: str):
        logger.info("Searching in job list")
        label_selector = "opentwins.fmi/kind=ot-fmi, opentwins.fmi/context={}, opentwins.fmi/id={}, opentwins.fmi/schedule=one-time".format(context, simulationId)
        list_of_jobs = self.batch_api.list_namespaced_job(self.namespace, label_selector=label_selector)
        if list_of_jobs.items:
            return "Job"
        
        logger.info("Searching in cronjob list")
        label_selector = "opentwins.fmi/kind=ot-fmi, opentwins.fmi/context={}, opentwins.fmi/id={}, opentwins.fmi/schedule=scheduled".format(context, simulationId)
        list_of_cronjobs = self.batch_api.list_namespaced_cron_job(self.namespace, label_selector=label_selector)
        if list_of_cronjobs.items:
            return "CronJob"
        
        
        return False

    async def get_running_simulations(self, context: str = None):
        logger.info("Listing pods with their IPs:")
        
        label_selector = "opentwins.fmi/kind=ot-fmi"
        if context != None:
            label_selector += ", opentwins.fmi/context={}".format(context)
        
        ############################################################
        # SPECIFIC FOR CRONJOBS
        
        cronjob_list = self.batch_api.list_namespaced_cron_job(self.namespace, label_selector=label_selector)              
        
        list_of_cronjobs = []
        for cronjob in cronjob_list.items:
            pod_list = self.api_instance.list_namespaced_pod(self.namespace, label_selector="opentwins.fmi/kind=ot-fmi, opentwins.fmi/schedule=scheduled, opentwins.fmi/context={}, opentwins.fmi/id={}".format(cronjob.metadata.labels["opentwins.fmi/context"], cronjob.metadata.labels["opentwins.fmi/id"]),watch=False)
            
            list_of_pods = [
                {
                    "simulation-id": pod.metadata.labels["opentwins.fmi/id"],
                    "phase": pod.status.phase,
                    "status": pod.status.container_statuses[0].ready,
                    "creation_timestamp": pod.metadata.creation_timestamp.strftime("%Y/%m/%d, %H:%M:%S%z"),
                } for pod in pod_list.items
            ]
            
            cronjob_info = {
                "schema-id": cronjob.metadata.labels["opentwins.fmi/schema"],
                "simulation-id": cronjob.metadata.labels["opentwins.fmi/id"],
                "namespace":cronjob.metadata.labels["opentwins.fmi/context"],
                "type": "cronjob",
                "schedule": cronjob.spec.schedule,
                "status": "Active" if not cronjob.spec.suspend else "Paused",
                "last_scheduled" : cronjob.status.last_schedule_time.strftime("%Y/%m/%d, %H:%M:%S+%z") if cronjob.status.last_schedule_time is not None else None,
                "last_scheduled_successful" : cronjob.status.last_successful_time.strftime("%Y/%m/%d, %H:%M:%S%z") if cronjob.status.last_successful_time is not None else None,
                "pods" : list_of_pods
                } 
            list_of_cronjobs.append(cronjob_info)
        
        # SPECIFIC FOR CRONJOBS    
        ############################################################
        
        ############################################################
        # SPECIFIC FOR JOBS
        
        job_list = self.batch_api.list_namespaced_job(self.namespace, label_selector=label_selector)

        list_of_jobs = []
        for job in job_list.items:
            pod_list = self.api_instance.list_namespaced_pod(self.namespace, label_selector="opentwins.fmi/kind=ot-fmi, opentwins.fmi/schedule=one-time, opentwins.fmi/context={}, opentwins.fmi/id={}".format(job.metadata.labels["opentwins.fmi/context"], job.metadata.labels["opentwins.fmi/id"]),watch=False)
            
            list_of_pods = [
                {
                    "simulation-id": pod.metadata.labels["opentwins.fmi/id"],
                    "phase": pod.status.phase,
                    "status": pod.status.container_statuses[0].ready,
                    "creation_timestamp": pod.metadata.creation_timestamp.strftime("%Y/%m/%d, %H:%M:%S%z"),
                } for pod in pod_list.items
            ]
            
            job_info = {
                "schema-id": job.metadata.labels["opentwins.fmi/schema"],
                "simulation-id": job.metadata.labels["opentwins.fmi/id"],
                "namespace":job.metadata.labels["opentwins.fmi/context"],
                "type": "one-time",
                "status": "Active" if not job.spec.suspend else "Paused",
                "pods" : list_of_pods
                } 
            list_of_cronjobs.append(job_info)
            
        # SPECIFIC FOR JOBS
        ############################################################
        
        list_of_simulations = list_of_cronjobs + list_of_jobs
        return list_of_simulations
    
    async def delete_simulation(self, context: str, simulationId: str):
        logger.info("Deleting simulation %s", simulationId)    
        kind = self.check_if_exists(context, simulationId)
        if not kind:
            raise DeleteSimulationError("There is not any simulation with that characteristics")
        elif kind == "Job":
            logger.info("Found fmi job, deleting...")
            self.batch_api.delete_namespaced_job('fmu-job-'+simulationId, self.namespace)
        else:
            logger.info("Found fmi cronjob, deleting...")
            self.batch_api.delete_namespaced_cron_job('fmu-cronjob-'+simulationId, self.namespace)
            
        return True

    async def stop_resume_simulation(self, context: str, simulationId: str, nreplicas = 0):
        kind = self.check_if_exists(context, simulationId)
        if not kind:
            raise SimulationError("There is not any simulation with that characteristics")
        elif kind == "Job":
            raise SimulationError("Cannot pause a one-time simulation")
        else:
            logger.info("Found, patching the process...")
            nreplicas = False if nreplicas else True
            self.batch_api.patch_namespaced_cron_job("fmu-cronjob-"+simulationId, self.namespace, {'spec': {'suspend' : nreplicas}})
 
        return True
    
    async def get_simulation_info(self, context: str, simulationId: str):
        logger.info("Getting deployment %s info", simulationId)
        
        
        kind = self.check_if_exists(context, simulationId)
        if not kind:
            raise SimulationError("There is not any simulation with that characteristics")
        elif kind == "Job":
            logger.info("Found, retrieving info...")
            data = self.batch_api.read_namespaced_job('fmu-job-'+simulationId, self.namespace)
        else:
            logger.info("Found, retrieving info...")
            data = self.batch_api.read_namespaced_cron_job('fmu-cronjob-'+simulationId, self.namespace)
            
        data_dict = data.to_dict()                
        
        data_dict = json.dumps(data_dict, default=str)
        return data_dict
    
    async def deploy_simulation(self, executionInfo: str, context: str, sqlController: SQLControllerService):
       
        SIMULATION_ID = executionInfo["id"]
        SIMULATION_NAME = executionInfo["name"]
        SIMULATION_SCHEMA = executionInfo["schemaId"]
        SIMULATION_SCHEDULE = executionInfo["configuration"]["SIMULATION_TYPESCHEDULE"]
        
        logger.info(f"Deploying simulation {SIMULATION_ID}")

        kind = self.check_if_exists(context, SIMULATION_ID)
        if kind:
            raise SimulationAlreadyExistsError("There is a simulation with that characteristics")
        
        logger.info("There is not any simulation with that characteristics")
        
        schema = await sqlController.get_simulation_schema(context, SIMULATION_SCHEMA)
        if not schema:
            raise SimulationError("Schema not found")
        schema = schema[0]
        
        logger.info("Found schema, creating simulation %s", SIMULATION_ID)
        
        
        SIMULATION_ENV_VAR = []
        
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_ID", "value": SIMULATION_ID})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_NAME", "value": SIMULATION_NAME})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_SCHEMA", "value": SIMULATION_SCHEMA})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_CONTEXT", "value": context})
        
        # TARGER CONNECTION THINGS
        if "targetConnection" in executionInfo.keys():
            for variable in executionInfo["targetConnection"]:
                SIMULATION_ENV_VAR.append({"name": variable, "value": executionInfo["targetConnection"][variable]})
        else:
            SIMULATION_ENV_VAR.append({"name": "BROKER_TYPE", "value": os.getenv('BROKER_TYPE')})
            SIMULATION_ENV_VAR.append({"name": "BROKER_IP", "value": os.getenv('BROKER_IP')})
            SIMULATION_ENV_VAR.append({"name": "BROKER_PORT", "value": os.getenv('BROKER_PORT')})
            SIMULATION_ENV_VAR.append({"name": "BROKER_TOPIC", "value": os.getenv('BROKER_TOPIC')})
            SIMULATION_ENV_VAR.append({"name": "BROKER_USERNAME", "value": os.getenv('BROKER_USERNAME')})
            SIMULATION_ENV_VAR.append({"name": "BROKER_PASSWORD", "value": os.getenv('BROKER_PASSWORD')})
            
        # INFLUXDB THINGS
        SIMULATION_ENV_VAR.append({"name": "INFLUXDB_HOST", "value": os.getenv('INFLUXDB_HOST')})
        SIMULATION_ENV_VAR.append({"name": "INFLUXDB_TOKEN", "value": os.getenv('INFLUXDB_TOKEN')})
        SIMULATION_ENV_VAR.append({"name": "INFLUXDB_DB", "value": os.getenv('INFLUXDB_DB')})
        
        # POSTGRE THINGS
        SIMULATION_ENV_VAR.append({"name": "POSTGRE_HOST", "value": os.getenv('POSTGRE_HOST')})
        SIMULATION_ENV_VAR.append({"name": "POSTGRE_PORT", "value": os.getenv('POSTGRE_PORT')})
        SIMULATION_ENV_VAR.append({"name": "POSTGRE_DB", "value": os.getenv('POSTGRE_DB')})
        SIMULATION_ENV_VAR.append({"name": "POSTGRE_USER", "value": os.getenv('POSTGRE_USER')})
        SIMULATION_ENV_VAR.append({"name": "POSTGRE_PASSWORD", "value": os.getenv('POSTGRE_PASSWORD')})
            
        # MINIO THINGS
        SIMULATION_ENV_VAR.append({"name": "MINIO_TOKEN", "value": os.getenv('MINIO_TOKEN')})
        SIMULATION_ENV_VAR.append({"name": "MINIO_URL", "value": os.getenv('MINIO_URL')})
        SIMULATION_ENV_VAR.append({"name": "MINIO_A_KEY", "value": os.getenv('MINIO_A_KEY')})
        SIMULATION_ENV_VAR.append({"name": "MINIO_S_KEY", "value": os.getenv('MINIO_S_KEY')})
        
            
        # SIMULATION CONFIGURATION THINGS         
        if float(executionInfo["configuration"]["SIMULATION_END_TIME"]) < float(executionInfo["configuration"]["SIMULATION_START_TIME"]):
            raise SimulationError("End time is lower than start time")
        elif float(executionInfo["configuration"]["SIMULATION_END_TIME"]) - float(executionInfo["configuration"]["SIMULATION_START_TIME"]) < float(executionInfo["configuration"]["SIMULATION_STEP_SIZE"]):
            raise SimulationError("Step size bigger than simulation time")
        
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_START_TIME", "value": str(executionInfo["configuration"]["SIMULATION_START_TIME"])})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_END_TIME", "value": str(executionInfo["configuration"]["SIMULATION_END_TIME"])})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_STEP_SIZE", "value": str(executionInfo["configuration"]["SIMULATION_STEP_SIZE"])})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_DELAY_WARNING", "value": str(executionInfo["configuration"]["SIMULATION_DELAY_WARNING"])})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_LAST_VALUE", "value": str(executionInfo["configuration"]["SIMULATION_LAST_VALUE"])})
                    
        # FMUs VARIABLE THINGS
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_INPUTS", "value": json.dumps(executionInfo["inputs"])})
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_OUTPUTS", "value": json.dumps(executionInfo["outputs"])})
        
        # SIMULATION SCHEMA CONNECTION THINGS
        SIMULATION_ENV_VAR.append({"name": "SIMULATION_FMUS", "value": json.dumps(schema["fmus"])})
        #SIMULATION_ENV_VAR.append({"name": "SIMULATION_FMUS_SCHEMA", "value": json.dumps(schema["schema"]) if "schema" in schema.keys() else None})
        
        
        if SIMULATION_SCHEDULE == "one-time":
            manifest = {
                'apiVersion': "batch/v1",
                'kind': "Job",
                'metadata': {
                    'name': 'fmu-job-'+SIMULATION_ID,
                    'labels': {}
                },
                "spec": {
                    "template": {
                        "metadata":{
                            'labels': {}
                        },
                        "spec": {
                            "containers": [{
                                'image': "registry.ertis.uma.es/opentwins-fmu-runner-single-v2:latest" if len(schema["fmus"]) == 1 else "registry.ertis.uma.es/opentwins-fmu-runner-multiple-v2:latest", 
                                'name': 'fmu-executer-'+SIMULATION_ID,
                                'env': SIMULATION_ENV_VAR,
                                'imagePullPolicy': 'Always'
                            }],
                            "restartPolicy": "OnFailure"
                        }
                    },
                    "backoffLimit": 4
                }  
            }
            
            manifest["metadata"]["labels"]["opentwins.fmi/id"] = SIMULATION_ID
            manifest["metadata"]["labels"]["opentwins.fmi/context"] = context
            manifest["metadata"]["labels"]["opentwins.fmi/kind"] = "ot-fmi"
            manifest["metadata"]["labels"]["opentwins.fmi/schema"] = SIMULATION_SCHEMA
            manifest["metadata"]["labels"]["opentwins.fmi/schedule"] = "one-time"
            
            
            manifest["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/id"] = SIMULATION_ID
            manifest["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/context"] = context
            manifest["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/kind"] = "ot-fmi"
            manifest["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/schema"] = SIMULATION_SCHEMA
            manifest["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/schedule"] = "one-time"
            
            
            logger.info('Creating job')
            resp = self.batch_api.create_namespaced_job(body=manifest, namespace=self.namespace)
            logger.info('Job created')
            
        else:
            # Template cronjob manifest
            manifest = {
                'apiVersion': 'batch/v1',
                'kind': 'CronJob', # Esto hay que parametrizarlo
                'metadata': {
                    'name': 'fmu-cronjob-'+SIMULATION_ID,
                    'labels': {}
                },
                'spec': {
                    "schedule": SIMULATION_SCHEDULE,
                    'jobTemplate' : {
                        'spec': {
                            "template": {
                                "metadata":{
                                    'labels': {}
                                },
                                "spec": {
                                    'containers': [{
                                            'image': "registry.ertis.uma.es/opentwins-fmu-runner-single-v2:latest" if len(schema["fmus"]) == 1 else "registry.ertis.uma.es/opentwins-fmu-runner-multiple-v2:latest", 
                                            'name': 'fmu-executer-'+SIMULATION_ID,
                                            'env': SIMULATION_ENV_VAR,
                                            'imagePullPolicy': 'Always'
                                        }],
                                    'restartPolicy': 'OnFailure'
                                } 
                            }
                        }
                    }
                }
            }
            
            manifest["metadata"]["labels"]["opentwins.fmi/id"] = SIMULATION_ID
            manifest["metadata"]["labels"]["opentwins.fmi/context"] = context
            manifest["metadata"]["labels"]["opentwins.fmi/kind"] = "ot-fmi"
            manifest["metadata"]["labels"]["opentwins.fmi/schema"] = SIMULATION_SCHEMA
            manifest["metadata"]["labels"]["opentwins.fmi/schedule"] = "scheduled"
            
            
            manifest["spec"]["jobTemplate"]["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/id"] = SIMULATION_ID
            manifest["spec"]["jobTemplate"]["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/context"] = context
            manifest["spec"]["jobTemplate"]["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/kind"] = "ot-fmi"
            manifest["spec"]["jobTemplate"]["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/schema"] = SIMULATION_SCHEMA
            manifest["spec"]["jobTemplate"]["spec"]["template"]["metadata"]["labels"]["opentwins.fmi/schedule"] = "scheduled"
            
            
            logger.info('Creating Cronjob')
            resp = self.batch_api.create_namespaced_cron_job(body=manifest, namespace=self.namespace)
            logger.info('Cronjob Created')
        
        return True