import os
import sys

sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/utils')
sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/service')

from loguru import logger

# from minio_utils import *
# from kubernetes_controller import KubernetesControllerService

import dotenv
import tempfile
import shutil

from fastapi import FastAPI, UploadFile, File, Response, Request, Depends, APIRouter
from urllib3 import HTTPResponse
from service import MinioControllerService

import zipfile
from routes.fmus.fmu_name import fmu_name

fmus = APIRouter(prefix='/fmus', tags=['fmus'])
fmus.include_router(fmu_name)


def extract_file(zip_path, target_file, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        if target_file in zip_ref.namelist():
            extracted_path = zip_ref.extract(target_file, output_dir)
            os.rename(extracted_path, zip_path[:-3]+"xml")
            return True
        else:
            return False

@fmus.post('')
async def upload_fmu(file: UploadFile = File(...)):
    return "FMU upload"    
    # logger.info("Uploading FMU")
    # tempDir = tempfile.mkdtemp()
    
    # # Request data reading
    
    # if not file.filename:
    #     logger.error("File not found")
    #     return Response("File not recieved", 500)
    
    # zipPath = os.path.join(tempDir, file.filename)
    # print(zipPath)
    
    # with open(zipPath, "wb") as buffer:
    #     shutil.copyfileobj(file.file, buffer)
        
    # if not extract_file(zipPath, "modelDescription.xml", tempDir):
    #     return Response("modelDescription.xml not found in the zip file", 500)
        
    # logger.info("File saved successfully")
        
    # # Upload to minio        
    # if file_uploader(zipPath, zipPath[:-3]+"xml", file.filename[:-4], context):
    #     return Response("File uploaded successfully", 200)
    # # TODO: The bucket name should be a parameter
    # else:
    #     return Response("Failed to upload the file", 500)

@fmus.get('')
async def get_fmu_list():
    
    data = MinioControllerService.fmu_list(context)
    return data
