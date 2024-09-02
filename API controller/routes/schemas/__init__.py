from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse
from routes.schemas.schemas_id import schema_id
from errors import DatabaseError, SimulationError
from service.kubernetes_controller import KubernetesControllerService
from service.sql_controller import SQLControllerService
from service.minio_controller import MinioControllerService



schemas = APIRouter(prefix='/schemas/{context}', tags=['schemas'])
schemas.include_router(schema_id)

@schemas.post('')
async def create_simulation_schema(request: Request, context: str, sqlController: SQLControllerService = Depends(SQLControllerService), storageService: MinioControllerService = Depends(MinioControllerService)):    
    payload = await request.json()
    data = await sqlController.create_simulation_schema(payload, context)
    if "schema" in payload:
        await storageService.upload_fmu_graph(payload, context)
    
    return JSONResponse("Schema created succesfully", 200)



@schemas.get('')
async def get_simulation_schema_list(request: Request, context: str, sqlController: SQLControllerService = Depends(SQLControllerService)):    
    schema_list = await sqlController.get_simulation_schema_list(context)
    return JSONResponse(schema_list, 200)
