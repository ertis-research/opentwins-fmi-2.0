
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.sql_controller import SQLControllerService
from errors import SimulationError, DatabaseError

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])

@simulation_id.get('')
async def get_simulation_schema(request: Request, context: str, simulation_id: str, sqlController: SQLControllerService = Depends(SQLControllerService)):
    try:
        data = await sqlController.get_simulation_schema(context, simulation_id)
        return JSONResponse(data, 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)
    
    
@simulation_id.delete('')
async def delete_simulation_schema(request: Request, context: str, simulation_id: str, sqlController: SQLControllerService = Depends(SQLControllerService)):
    try:
        data = await sqlController.delete_simulation_schema(context, simulation_id)
        return JSONResponse(data, 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)
