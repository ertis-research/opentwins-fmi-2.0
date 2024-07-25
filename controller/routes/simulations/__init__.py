from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from routes.simulations.simulation_id import simulation_id
from errors import DatabaseError, SimulationError
from service.kubernetes_controller import KubernetesControllerService
from service.sql_controller import SQLControllerService


simulations = APIRouter(prefix='/simulations/{context}', tags=['simulations'])
simulations.include_router(simulation_id)

@simulations.post('')
async def create_simulation_schema(request: Request, context: str, sqlController: SQLControllerService = Depends(SQLControllerService)):    
    try:
        payload = await request.json()
        data = await sqlController.create_simulation_schema(payload, context)
        return JSONResponse(data, 200)
    except DatabaseError as e:
        return JSONResponse("A simulation scheme with same id or name already exists", 412)


@simulations.get('')
async def get_simulation_schema_list(request: Request, context: str, sqlController: SQLControllerService = Depends(SQLControllerService)):    
    try:
        data = await sqlController.get_simulation_schema_list(context)
        return JSONResponse(data, 200)
    except SimulationError as e:
        return JSONResponse([], 404)