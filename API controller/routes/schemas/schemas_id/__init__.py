
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from service.sql_controller import SQLControllerService
from errors import SimulationError, DatabaseError
from service.minio_controller import MinioControllerService

schema_id = APIRouter(prefix='/{schema_id}', tags=['schema_id'])

@schema_id.get('')
async def get_simulation_schema(request: Request, context: str, schema_id: str, sqlController: SQLControllerService = Depends(SQLControllerService)):
    data = await sqlController.get_simulation_schema(context, schema_id)
    return JSONResponse(data, 200)
    
    
@schema_id.delete('')
async def delete_simulation_schema(request: Request, context: str, schema_id: str, sqlController: SQLControllerService = Depends(SQLControllerService), storageService: MinioControllerService = Depends(MinioControllerService)):
    await sqlController.delete_simulation_schema(context, schema_id)
    await storageService.delete_fmu_graph(context, schema_id)
    return JSONResponse("Schema deleted succesfully", 200)
