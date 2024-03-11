from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from routes.simulations.simulation_id import simulation_id
from errors import SimulationError
from service.kubernetes_controller import KubernetesControllerService


simulations = APIRouter(prefix='/simulations', tags=['simulations'])
simulations.include_router(simulation_id)

@simulations.get('')
async def get_simulation_list(request: Request, kubernetesController: KubernetesControllerService = Depends(KubernetesControllerService)):
    namespace = request.headers.get('namespace')
    
    try:
        data = kubernetesController.get_running_simulations(namespace)
        return JSONResponse(data, 200)
    except SimulationError as e:
        return JSONResponse([], 404)

@simulations.post('')
async def deploy_simulation():
    return "Creada simulacion"
    # try:
    #     data = fmu_list(context)
    #     return data
    # except FileNotFoundError:
    #     abort(400)
