import os
import sys

sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/utils')
sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/service')

from loguru import logger
from errors import FMUError

import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, Response, Request, Depends, APIRouter
from fastapi.responses import JSONResponse
from urllib3 import HTTPResponse
from service import MinioControllerService

import zipfile
from routes.fmus.fmu_name import fmu_name

fmus = APIRouter(prefix='/fmus/{context}', tags=['fmus'])
fmus.include_router(fmu_name)


@fmus.post('')
async def upload_fmu(request: Request, context: str, file: UploadFile = File(...), storageService: MinioControllerService = Depends(MinioControllerService)):   
    logger.info("Uploading FMU")
    # Request data reading    
    if not file.filename:
        logger.error("File not found")
        return JSONResponse("File not recieved", 415)
    
    storageService.file_uploader(context, file)
    return JSONResponse("File uploaded", 200)


@fmus.get('')
async def get_fmu_list(request: Request, context: str, storageService: MinioControllerService = Depends(MinioControllerService)):
    data = storageService.fmu_list(context)
    return data
