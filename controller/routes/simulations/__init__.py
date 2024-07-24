from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from routes.simulations.simulation_id import simulation_id
from errors import SimulationError
from service.kubernetes_controller import KubernetesControllerService
from service.postgre_controller import PostgreSQLControllerService


simulations = APIRouter(prefix='/simulations/{context}', tags=['simulations'])
simulations.include_router(simulation_id)


@simulations.get('')
async def get_simulation_list(request: Request, postgreSQLController: PostgreSQLControllerService = Depends(PostgreSQLControllerService)):    
    try:
        data = postgreSQLController.get_simulation_list()
        return JSONResponse(data, 200)
    except SimulationError as e:
        return JSONResponse([], 404)