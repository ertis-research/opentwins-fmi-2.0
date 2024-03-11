import os
import sys

sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/utils')
sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/service')

from loguru import logger
from errors import FMUError

import dotenv
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, Response, Request, Depends, APIRouter
from fastapi.responses import JSONResponse
from urllib3 import HTTPResponse
from service import MinioControllerService

import zipfile
from routes.fmus.fmu_name import fmu_name

fmus = APIRouter(prefix='/fmus', tags=['fmus'])
fmus.include_router(fmu_name)


@fmus.post('')
async def upload_fmu(request: Request, file: UploadFile = File(...), storageService: MinioControllerService = Depends(MinioControllerService)):   
    logger.info("Uploading FMU")
    # Request data reading
    namespace = request.headers.get('namespace')
    
    if not file.filename:
        logger.error("File not found")
        return JSONResponse("File not recieved", 415)
    
    try:
        storageService.file_uploader(namespace, file)
        return JSONResponse("File uploaded", 200)
    except FMUError as e:
        return JSONResponse(str(e), 500)

@fmus.get('')
async def get_fmu_list(request: Request, storageService: MinioControllerService = Depends(MinioControllerService)):
    try:
        namespace = request.headers.get('namespace')
        data = storageService.fmu_list(namespace)
    except FMUError as e:
        return JSONResponse(str(e), 404)
    return data
