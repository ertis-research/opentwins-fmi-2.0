import re
import boto3
from fastapi import Depends
# Import the logging library and the custom formatter
from loguru import logger
from dependencies import get_minio_resource

class MinioControllerService:
    
    def __init__(self, s3 : boto3.resource = Depends(get_minio_resource)) -> None:
        self.s3 = s3
        self.REGEX = re.compile(r'^[a-zA-Z0-9]+\.fmu$')


    def bucket_exists(self, namespace):
        # Create a CLIENT with the MinIO server playground, its access key
        # and secret key.
        
        if self.s3.Bucket(namespace).creation_date:
            logger.info("Bucket %s exists", namespace)
            return True
        else:
            logger.info("Bucket %s does not exists", namespace)
            return False


    def file_uploader(self, fmu, xml, name, namespace):
        # The file to upload, change this path if needed
        # source_file = "/tmp/test-file.txt"

        # Make the bucket if it doesn't exist.
        current_bucket = self.s3.Bucket(namespace)
        
        if current_bucket.creation_date:
            logger.info("Bucket %s already exists", namespace)
        else:
            current_bucket.create()
            logger.info("Created bucket %s", namespace)


        # Upload the file, renaming it in the process
        tries = 0
        while(tries < 3):
            try:
                self.s3.meta.client.upload_file(fmu, namespace, name+".fmu")
                self.s3.meta.client.upload_file(xml, namespace, name+".xml")
                logger.info("successfully uploaded %s to bucket %s", name, namespace)
                return True
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to upload the file")
                tries +=1
        logger.error("Failed to upload the file")
        return False
        
    def fmu_list(self, namespace):
        # List all object paths in bucket that begin with my-prefixname.
        tries = 0
        while(tries < 3):
            try:
                objects = list(self.s3.Bucket(namespace).objects.all())
                return [i.key[:-4] for i in objects if not self.REGEX.match(i.key)]
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to get the file")
                tries +=1
        return []

    def get_fmu_description(self, namespace, fmu):
        # List all object paths in bucket that begin with my-prefixname.
        tries = 0
        while(tries < 3):
            try:
                response = self.s3.meta.client.get_object(Bucket=namespace, Key=fmu+".xml")
                return response["Body"].read().decode("utf-8")
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to get the file")
                tries +=1
        return False

    def delete_fmu_files(self, namespace, fmu):
        # List all object paths in bucket that begin with my-prefixname.
        tries = 0
        while(tries < 3):
            try:
                self.s3.meta.client.delete_object(Bucket=namespace, Key=fmu+".fmu")
                self.s3.meta.client.delete_object(Bucket=namespace, Key=fmu+".xml")
                logger.info("successfully deleted %s from bucket %s", fmu, namespace)
                return True
            except Exception as e:
                logger.error(e)
                logger.warning("Retrying to delete the file")
                tries +=1
        return False

    