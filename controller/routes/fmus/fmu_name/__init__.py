from fastapi import APIRouter, Response, Request, Depends
from fastapi.responses import JSONResponse
from service import MinioControllerService
from errors import FMUError
fmu_name = APIRouter(prefix='/{fmuName}', tags=['fmuName'])


@fmu_name.get('')
async def get_fmu(request: Request, fmuName: str, storageService: MinioControllerService = Depends(MinioControllerService)):
    try:
        namespace = request.headers.get('namespace')
        response = storageService.get_fmu_description(namespace=namespace, fmu=fmuName)
        return Response(content=response, media_type="application/xml", status_code=200)
    except FMUError as e:
        return JSONResponse(str(e), 404)

@fmu_name.delete('')
async def delete_fmu(request: Request, fmuName: str, storageService: MinioControllerService = Depends(MinioControllerService)):
    try:
        namespace = request.headers.get('namespace')
        storageService.delete_fmu_files(namespace=namespace, fmu=fmuName)
        
        return JSONResponse("FMU delete succesfully", 200)
    except FMUError as e:
        return JSONResponse(str(e), 500)