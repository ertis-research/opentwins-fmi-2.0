
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.kubernetes_controller import KubernetesControllerService
from errors import SimulationError, DatabaseError

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])


@simulation_id.get('')
async def get_simulation_info(request: Request, context: str, simulation_id: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        data = await kubernetesService.get_simulation_info(context, simulation_id)
        return JSONResponse(data, 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)
    
    
@simulation_id.delete('')
async def delete_simulation(request: Request, context: str, simulation_id: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        data = await kubernetesService.delete_simulation(context, simulation_id)
        return JSONResponse("Schema deleted succesfully", 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)


@simulation_id.post('/pause')
async def stop_agent(request: Request, context :str, agentId: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        kubernetesController.stop_resume_simulation(context, agentId, nreplicas = 0)
        return JSONResponse(200)
    except SimulationError as e:
        return JSONResponse("Failed stopping agent {} in context {}".format(agentId, context), 404)
    
@simulation_id.post('/resume')
async def resume_agent(request: Request, context :str, agentId: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    try:
        kubernetesController.stop_resume_simulation(context, agentId, nreplicas = 1)
        return JSONResponse(200)
    except SimulationError as e:
        return JSONResponse("Failed resuming agent {} in context {}".format(agentId, context), 404)