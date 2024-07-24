from kubernetes import client
# Import the logging library and the custom formatter
from loguru import logger
from fastapi import Depends
from dependencies import get_kubernetes_api_client, get_kube_namespace
from errors import SimulationError
from fastapi.encoders import jsonable_encoder

class KubernetesControllerService:
    def __init__(self, api_client : client.ApiClient=Depends(get_kubernetes_api_client), namespace : str=Depends(get_kube_namespace)) -> None:
        self.api_client = api_client
        self.api_instance = client.CoreV1Api(api_client)
        self.namespace = namespace

    def get_running_simulations(self, context = None):
        logger.info("Listing pods with their IPs:")
        
        print(context)
        print(self.namespace)
        
        tries = 0
        while(tries < 3):
            try:
                if context:
                    pod_list = self.api_instance.list_namespaced_pod(self.namespace, label_selector="opentwins/kind=fmu-simulation, opentwins/context={}".format(context),watch=False)
                else:
                    pod_list = self.api_instance.list_namespaced_pod(self.namespace, label_selector="opentwins/kind=fmu-simulation".format(context),watch=False)
                    
                list_of_pods = [
                    {
                        "name": pod.metadata.name,
                        "phase": pod.status.phase,
                    } for pod in pod_list.items
                ]
                
                return list_of_pods
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to get the pods")
                tries +=1
        raise SimulationError("Failed to get the pods")
        
    def delete_simulation_pod(self, pod_name):
        logger.info("Deleting pod %s", pod_name)

        try:
            self.api_instance.delete_namespaced_pod(pod_name, self.namespace, body=client.V1DeleteOptions())
        except Exception as e:
            logger.error(e)
            logger.error("Failed to delete pod %s", pod_name)

    def get_simulation_info(self, pod_name):
        logger.info("Getting pod %s info", pod_name)
        try: 
            data = self.api_instance.read_namespaced_pod(pod_name, self.namespace)
            data_dict = data.to_dict()
            
            sendBackData = {
                'name' : data_dict['metadata']['name'],
                'start_time' : data.status.start_time.isoformat(),
                'status' : jsonable_encoder(data_dict['status']['container_statuses'][0]['state']),
                'env_variables' : data_dict['spec']['containers'][0]['env']
            }
            
            return sendBackData
        except Exception as e:
            logger.error(e)
            logger.error("Failed to get pod %s info", pod_name)
            raise SimulationError("Failed to get pod info")