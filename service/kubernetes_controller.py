from kubernetes import client
# Import the logging library and the custom formatter
from loguru import logger
from fastapi import Depends
from dependencies import get_kubernetes_api_client

class KubernetesControllerService:
    def __init__(self, api_client : client.ApiClient=Depends(get_kubernetes_api_client)) -> None:
        self.api_client = api_client
        self.api_instance = client.CoreV1Api(api_client)

    def get_running_simulations(self, context):
        logger.info("Listing pods with their IPs:")
        
        tries = 0
        while(tries < 3):
            try:
                pod_list = self.api_instance.list_namespaced_pod("digitaltwins", label_selector="kind=fmu-simulation, context={}".format(context),watch=False)
                    
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
        logger.error("Failed to get the pods")
        return []  
        
    def delete_simulation_pod(self, pod_name):
        logger.info("Deleting pod %s", pod_name)

        try:
            self.api_instance.delete_namespaced_pod(pod_name, "digitaltwins", body=client.V1DeleteOptions())
        except Exception as e:
            logger.error(e)
            logger.error("Failed to delete pod %s", pod_name)
