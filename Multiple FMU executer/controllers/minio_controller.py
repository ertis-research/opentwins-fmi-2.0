import re
import os
import boto3
# Import the logging library and the custom formatter
from loguru import logger
import tempfile
import shutil
import zipfile
from errors.errors import FMUError


class MinioControllerService:
    
    def __init__(self):
        
        MINIO_URL = os.getenv('MINIO_URL')
        MINIO_A_KEY = os.getenv('MINIO_A_KEY')
        MINIO_S_KEY = os.getenv('MINIO_S_KEY')
    
        self.s3 = boto3.resource('s3', 
                            aws_access_key_id=MINIO_A_KEY, 
                            aws_secret_access_key=MINIO_S_KEY, 
                            endpoint_url=MINIO_URL,
                            config = boto3.session.Config(signature_version='s3v4'),
                            )

    def bucket_exists(self, context):
        # Create a CLIENT with the MinIO server playground, its access key
        # and secret key.
        
        if self.s3.Bucket(context).creation_date:
            logger.info("Bucket %s exists", context)
            return True
        else:
            logger.info("Bucket %s does not exists", context)
            return False

    def download_fmu(self, context, fmu_list):
        # Download FMU from MinIO
        
        for fmu in fmu_list:
            logger.info(f"Downloading FMU {fmu}")
            download_path = 'ssp_creation/resources/{}.fmu'.format(fmu)
            my_bucket = self.s3.Bucket(context)                
            my_bucket.download_file(fmu+".fmu", download_path)
            #response = self.s3.meta.client.get_object(Bucket=context, Key=fmu)
            #response = self.s3.download_file(context, fmu, 'FMUs/{}'.format(fmu))
        return True
    
    def download_simulation_ssd(self, context, ssdID):
        # Download FMU from MinIO
        download_path = 'ssp_creation/SystemStructure.ssd'
        my_bucket = self.s3.Bucket(context)                
        response = my_bucket.download_file(ssdID+".ssd", download_path)
        return 'ssp_creation/SystemStructure.ssd'
