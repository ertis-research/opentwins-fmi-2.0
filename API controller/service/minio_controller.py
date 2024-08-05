import re
import os
import boto3
from fastapi import Depends, File
# Import the logging library and the custom formatter
from loguru import logger
from dependencies import get_minio_resource
from errors import FMUError
import dotenv
import tempfile
import shutil
import zipfile
import xml.etree.ElementTree as ET


class MinioControllerService:
    
    def __init__(self, s3 : boto3.resource = Depends(get_minio_resource)) -> None:
        self.s3 = s3
        #self.REGEX = re.compile(r'^[a-zA-Z0-9]+\.fmu$')


    def bucket_exists(self, context):
        # Create a CLIENT with the MinIO server playground, its access key
        # and secret key.
        
        if self.s3.Bucket(context).creation_date:
            logger.info(f"Bucket {context} exists")
            return True
        else:
            logger.info(f"Bucket {context} does not exists")
            return False

    def extract_file(self, zip_path, target_file, output_dir):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            if target_file in zip_ref.namelist():
                extracted_path = zip_ref.extract(target_file, output_dir)
                os.rename(extracted_path, zip_path[:-3]+"xml")
                return True
            else:
                return False
    
    def file_uploader(self, context, file):
        # The file to upload, change this path if needed
        # source_file = "/tmp/test-file.txt"
        tempDir = tempfile.mkdtemp()
        zipPath = os.path.join(tempDir, file.filename)
        print(zipPath)
        
        with open(zipPath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        if not self.extract_file(zipPath, "modelDescription.xml", tempDir):
            raise FMUError("modelDescription.xml not found in the zip file")
            
        logger.info("File saved successfully")
        
        fmu = zipPath
        xml = zipPath[:-3]+"xml"
        name = file.filename[:-4]
        #Antiguo de aqui para arriba.
        
        # Make the bucket if it doesn't exist.
        current_bucket = self.s3.Bucket(context)
        
        if current_bucket.creation_date:
            logger.info("Bucket %s already exists", context)
        else:
            current_bucket.create()
            logger.info("Created bucket %s", context)


        # Upload the file, renaming it in the process
        tries = 0
        while(tries < 3):
            try:
                self.s3.meta.client.upload_file(fmu, context, name+".fmu")
                self.s3.meta.client.upload_file(xml, context, name+".xml")
                logger.info("successfully uploaded %s to bucket %s", name, context)
                return True
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to upload the file")
                tries +=1
        logger.error("Failed to upload the file")
        raise FMUError("Failed to upload the file")
        
    def fmu_list(self, context):
        # List all object paths in bucket that begin with my-prefixname.
        tries = 0
        #while(tries < 3):
            # try:
            # if not self.bucket_exists(context):
            #     break

        bucket_result = self.s3.Bucket(context).objects.all()
        objects = list(bucket_result)
        print(len(objects))
        
        #fmu_names = [i.key[:-4] for i in objects if self.REGEX.match(i.key[:4])] #No se porque falla, pero repite algun que otro nombre
        fmu_names = [i.key[:-4] for i in objects if "xml" in i.key[-3:]]
        
        fmu_list = []
        
        for fmu in fmu_names:
            print(fmu)
            response = self.s3.meta.client.get_object(Bucket=context, Key=fmu+".xml")
            xml_description = response["Body"].read().decode("utf-8")
            
            root = ET.fromstring(xml_description)
            modelVariables = root.findall('ModelVariables')[0]
            
            fmu_variables = []
            for variable in modelVariables:
                if "initial" in variable.attrib and variable.attrib["initial"] == "exact" or "causality" in variable.attrib and variable.attrib["causality"] == "input":
                    fmu_variables.append({
                        "name": variable.attrib["name"],
                        "type": variable[0].tag,
                        "default": variable[0].attrib,
                        "description": variable.attrib["description"] if "description" in variable.attrib else ""
                    })
                # elif "causality" in variable.attrib and variable.attrib["causality"] == "input":
                #     fmu_variables.append({
                #         "name": variable.attrib["name"],
                #         "type": variable[0].tag,
                #         "default": variable[0].attrib,
                #         "description": variable.attrib["description"] if "description" in variable.attrib else ""
                #     })
            #fmu_variables = [{"name": variable.attrib["name"], "type": variable[0].tag, "default": variable[0].attrib, "description": variable.attrib["description"]} for variable in modelVariables if variable.attrib["initial"] == "exact" or variable.attrib["causality"] == "input"]

            fmu_list.append({
                "id": fmu,
                "inputs": fmu_variables
            })
            
        return fmu_list
            # except Exception as e:
            #     logger.error(e)
            #     logger.warning("Retrying to get the file")
            #     tries +=1
        raise FMUError("Failed to retrieve FMU list")

    def get_fmu_description(self, context, fmu):
        # List all object paths in bucket that begin with my-prefixname.
        
        tries = 0
        while(tries < 3):
            try:
                response = self.s3.meta.client.get_object(Bucket=context, Key=fmu+".xml")
                return response["Body"].read().decode("utf-8")
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to get the file")
                tries +=1
        raise FMUError("Failed to retrieve FMU description")

    def delete_fmu_files(self, context, fmu):
        # List all object paths in bucket that begin with my-prefixname.
        tries = 0
        while(tries < 3):
            try:
                self.s3.meta.client.delete_object(Bucket=context, Key=fmu+".fmu")
                self.s3.meta.client.delete_object(Bucket=context, Key=fmu+".xml")
                logger.info("successfully deleted %s from bucket %s", fmu, context)
                return True
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to delete the file")
                tries +=1
                
        raise FMUError("Failed to delete the file")