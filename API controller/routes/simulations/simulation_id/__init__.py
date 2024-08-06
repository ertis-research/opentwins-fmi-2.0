
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.kubernetes_controller import KubernetesControllerService
from errors import SimulationError, DatabaseError

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])


@simulation_id.get('')
async def get_simulation_info(request: Request, context: str, simulation_id: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService)):
    data = await kubernetesService.get_simulation_info(context, simulation_id)
    return JSONResponse(data, 200)
    
    
@simulation_id.delete('')
async def delete_simulation(request: Request, context: str, simulation_id: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService)):
    data = await kubernetesService.delete_simulation(context, simulation_id)
    return JSONResponse("Schema deleted succesfully", 200)



@simulation_id.post('/pause')
async def stop_agent(request: Request, context :str, simulation_id: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    kubernetesController.stop_resume_simulation(context, simulation_id, nreplicas = 0)
    return JSONResponse(200)

    
@simulation_id.post('/resume')
async def resume_agent(request: Request, context :str, simulation_id: str, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    kubernetesController.stop_resume_simulation(context, simulation_id, nreplicas = 1)
    return JSONResponse(200)