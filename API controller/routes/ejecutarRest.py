import os
import sys

sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/utils')
sys.path.insert(1, 'c:/Users/SergioI/Proyectos/FMI/opentwins-fmi-2.0/service')

from loguru import logger

from minio_utils import *
from kubernetes_controller import KubernetesControllerService

import dotenv
import tempfile
import shutil
from fastapi import FastAPI, UploadFile, File, Response, Request, Depends, APIRouter
from urllib3 import HTTPResponse

import zipfile

app = FastAPI()

BaseRouter = APIRouter()

def extract_file(zip_path, target_file, output_dir):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        if target_file in zip_ref.namelist():
            extracted_path = zip_ref.extract(target_file, output_dir)
            os.rename(extracted_path, zip_path[:-3]+"xml")
            return True
        else:
            return False

@app.post('/fmus/{context}')
def upload_fmu(context, file: UploadFile = File(...)):
    
    logger.info("Uploading FMU")
    tempDir = tempfile.mkdtemp()
    
    # Request data reading
    
    if not file.filename:
        logger.error("File not found")
        return Response("File not recieved", 500)
    
    zipPath = os.path.join(tempDir, file.filename)
    print(zipPath)
    
    with open(zipPath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if not extract_file(zipPath, "modelDescription.xml", tempDir):
        return Response("modelDescription.xml not found in the zip file", 500)
        
    logger.info("File saved successfully")
        
    # Upload to minio        
    if file_uploader(zipPath, zipPath[:-3]+"xml", file.filename[:-4], bucketName):
        return Response("File uploaded successfully", 200)
    # TODO: The bucket name should be a parameter
    else:
        return Response("Failed to upload the file", 500)

@app.get('/fmus/{context}')
def get_fmu_list(context):
    try:
        data = fmu_list(bucketName)
        return data
    except FileNotFoundError:
        abort(400)

@app.get('/fmus/{context}/{fmuName}')
def get_fmu(context, fmuName):
    return get_fmu_description(bucketName, fmuName)

@app.delete('/fmus/{context}/{fmuName}')
def delete_fmu(context, fmuName):
    if delete_fmu_files(bucketName, fmuName):
        return Response("FMU delete succesfully", 200)
    else:
        return Response("Failed to delete the FMU", 500)

@app.get('/simulation/{context}')
def get_simulations(context, controller_service: KubernetesControllerService = Depends(KubernetesControllerService)):
    return get_running_simulations(context)