
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.kubernetes_controller import KubernetesControllerService
from errors import SimulationError

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])

@simulation_id.get('')
async def get_simulation_info(simulation_id: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        data = kubernetesController.get_simulation_info(simulation_id)
        return JSONResponse(data, 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)

@simulation_id.delete('')
async def delete_simulation(simulation_id: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        kubernetesController.delete_simulation_pod(simulation_id)
        return JSONResponse("DELETED", 200)
    except SimulationError:
        return JSONResponse("Failed to delete simulation", 400)
    
@simulation_id.patch('/pause')
async def pause_simulation():
    return ["PAUSE PLACEHOLDER"]

@simulation_id.patch('/resume')
async def resume_simulation():
    return ["RESUME PLACEHOLDER"] 
