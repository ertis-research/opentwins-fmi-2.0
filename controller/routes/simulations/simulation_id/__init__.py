
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.postgre_controller import PostgreSQLControllerService
from errors import SimulationError

simulation_id = APIRouter(prefix='/{simulation_id}', tags=['simulation_id'])

@simulation_id.get('')
async def get_simulation_info(simulation_id: str, postgreSQLController: PostgreSQLControllerService = Depends(PostgreSQLControllerService)):
    try:
        data = postgreSQLController.get_simulation_schemma(simulation_id)
        return JSONResponse(data, 200)
    except SimulationError:
        return JSONResponse("Failed retrieving info", 404)
