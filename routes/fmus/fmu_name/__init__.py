from fastapi import APIRouter, Response, Request
from service import MinioControllerService
fmu_name = APIRouter(prefix='/{fmuName}', tags=['fmuName'])


@fmu_name.get('')
async def get_fmu(request: Request, fmuName: str):
    namespace = request.headers.get('namespace')
    response = MinioControllerService.get_fmu_description(namespace, fmuName)
    if not response:
        return Response("FMU not found", 404)
    else:
        return response

@fmu_name.delete('')
async def delete_fmu(fmuName):
    if MinioControllerService. delete_fmu_files(fmuName):
        return Response("FMU delete succesfully", 200)
    else:
        return Response("Failed to delete the FMU", 500)