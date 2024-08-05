from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from routes.simulations.simulation_id import simulation_id
from errors import DatabaseError, SimulationError
from service.kubernetes_controller import KubernetesControllerService
from service.sql_controller import SQLControllerService

simulations = APIRouter(prefix='/simulations/{context}', tags=['simulations'])
simulations.include_router(simulation_id)

#TODO: Implement the following route
@simulations.post('')
async def deploy_simulation(request: Request, context: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService), sqlController: SQLControllerService = Depends(SQLControllerService)):    
    # try:
    payload = await request.json()
    data = await kubernetesService.deploy_simulation(payload, context, sqlController)
    return JSONResponse(data, 200)
    # except Exception as e:
    #     return JSONResponse("Some error occurred", 412)



@simulations.get('')
async def get_running_simulations_list(request: Request, context: str, kubernetesService : KubernetesControllerService = Depends(KubernetesControllerService)):    
    try:
        simulations_list = await kubernetesService.get_running_simulations(context)
        return JSONResponse(simulations_list, 200)
    except SimulationError as e:
        return JSONResponse([], 404)