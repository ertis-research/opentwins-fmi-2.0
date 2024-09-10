from fastapi import APIRouter, Response, Request, Depends
from fastapi.responses import JSONResponse
from service import MinioControllerService
from errors import FMUError
fmu_name = APIRouter(prefix='/{fmuName}', tags=['fmuName'])


@fmu_name.get('')
async def get_fmu(request: Request, context: str, fmuName: str, storageService: MinioControllerService = Depends(MinioControllerService)):
    response = storageService.get_fmu_description(context=context, fmu=fmuName)
    return Response(content=response, media_type="application/xml", status_code=200)


@fmu_name.delete('')
async def delete_fmu(request: Request, context: str, fmuName: str, storageService: MinioControllerService = Depends(MinioControllerService)):
    storageService.delete_fmu_files(context=context, fmu=fmuName)
    
    return JSONResponse("FMU delete succesfully", 200)