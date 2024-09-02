import re
import os
import boto3
from fastapi import Depends, File
# Import the logging library and the custom formatter
from loguru import logger
from dependencies import get_minio_resource
from errors import FMUError
import tempfile
import shutil
import zipfile
import xml.etree.ElementTree as ET


class MinioControllerService:
    
    def __init__(self, s3 : boto3.resource = Depends(get_minio_resource)) -> None:
        self.s3 = s3
        #self.REGEX = re.compile(r'^[a-zA-Z0-9]+\.fmu$')
        
        
    def create_xml(self, system_name, inputs, outputs, fmus, graph, final_time):
        # Root element
        root = ET.Element("ssd:SystemStructureDescription", 
                        version="1.0",
                        name=system_name)

        root.set("xmlns:ssd", "http://ssp-standard.org/SSP1/SystemStructureDescription")
        root.set("xmlns:ssc", "http://ssp-standard.org/SSP1/SystemStructureCommon")
        
        # System element
        system = ET.SubElement(root, "ssd:System", 
                                name=system_name)

        # Input and output of the system
        system_connector = ET.SubElement(system, "ssd:Connectors")
        
        for input in inputs:
            connector = ET.SubElement(system_connector, "ssd:Connector", 
                                    name=input, kind="input")
        for output in outputs:
            connector = ET.SubElement(system_connector, "ssd:Connector", 
                                    name=output, kind="output")
            
        # Declaration of every input and output of each FMU
        elements = ET.SubElement(system, "ssd:Elements")
        
        for fmu in fmus:
            fmu_element = ET.SubElement(elements, "ssd:Component", 
                                type = "application/x-fmu-sharedlibrary",
                                source = "resources/{}.fmu".format(fmu["id"]),
                                name=fmu["id"])
            fmu_connector = ET.SubElement(fmu_element, "ssd:Connectors")

            for input in fmu["inputs"]:
                connector = ET.SubElement(fmu_connector, "ssd:Connector", 
                                        name=input["id"], kind="input")
            for output in fmu["outputs"]:
                connector = ET.SubElement(fmu_connector, "ssd:Connector", 
                                        name=output["id"], kind="output")
        # Connections of variables of the FMU
        connections = ET.SubElement(system, "ssd:Connections")

        for connection in graph:
            var_connection = ET.SubElement(connections, "ssd:Connection",
                                        startConnector = connection["from"]["var"],
                                        endConnector = connection["to"]["var"])
            if "id" in connection["from"]:
                var_connection.set("startElement", connection["from"]["id"])
            if "id" in connection["to"]:
                var_connection.set("endElement", connection["to"]["id"])
        # Final configurations
        df_experiment = ET.SubElement(root, "ssd:DefaultExperiment", 
                                    stopTime=str(final_time))
        tree = ET.ElementTree(root)
        
        tempDir = tempfile.mkdtemp()
        file_path = os.path.join(tempDir, "{}.xml".format(system_name))
        
        tree.write(file_path, xml_declaration=True, encoding="utf-8", method="xml")
        return file_path

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
        logger.info("Uploading FMU")
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
            
            fmu_inputs = []
            fmu_outputs = []
            fmu_other_variables = []
            for variable in modelVariables:
                if "causality" in variable.attrib and variable.attrib["causality"] == "input":
                    fmu_inputs.append({
                        "name": variable.attrib["name"],
                        "type": variable[0].tag,
                        "default": variable[0].attrib,
                        "description": variable.attrib["description"] if "description" in variable.attrib else ""
                    })
                elif "causality" in variable.attrib and variable.attrib["causality"] == "output":
                    fmu_outputs.append({
                        "name": variable.attrib["name"],
                        "type": variable[0].tag,
                        "default": variable[0].attrib,
                        "description": variable.attrib["description"] if "description" in variable.attrib else ""
                    })
                elif "initial" in variable.attrib and variable.attrib["initial"] == "exact":
                    fmu_other_variables.append({
                        "name": variable.attrib["name"],
                        "type": variable[0].tag,
                        "default": variable[0].attrib,
                        "description": variable.attrib["description"] if "description" in variable.attrib else ""
                    })
               
            fmu_list.append({
                "id": fmu,
                "inputs": fmu_inputs,
                "outputs": fmu_outputs,
                "other_variables": fmu_other_variables
            })
            
        return fmu_list


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
    
    async def delete_fmu_graph(self, context, schema_id):
        # List all object paths in bucket that begin with my-prefixname.
        self.s3.meta.client.delete_object(Bucket=context, Key=schema_id+".ssd")
        logger.info(f"successfully deleted {schema_id} from bucket {context}")
    
    async def upload_fmu_graph(self, payload, context):
        system_inputs = []
        system_outputs = []
        
        for conection in payload["schema"]:
            if "id" not  in conection["from"]:
                system_inputs.append(conection["from"]["var"])
            elif "id" not in conection["to"]:
                system_outputs.append(conection["to"]["var"])
             
        file_path = self.create_xml(payload["id"], system_inputs, system_outputs, payload["fmus"], payload["schema"], 5)
        
        # Make the bucket if it doesn't exist.
        current_bucket = self.s3.Bucket(context)
        
        if current_bucket.creation_date:
            logger.info(f"Bucket {context} already exists")
        else:
            current_bucket.create()
            logger.info(f"Created bucket {context}")
        
        self.s3.meta.client.upload_file(file_path, context, payload["id"]+".ssd")
        