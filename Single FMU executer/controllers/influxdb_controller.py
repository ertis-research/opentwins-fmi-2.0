import os
import json
import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS


class InfluxDBController:
    def __init__(self):
        self.INFLUXDB_HOST  = os.getenv('INFLUXDB_HOST')
        self.INFLUXDB_TOKEN = os.getenv('INFLUXDB_TOKEN')
        self.INFLUXDB_DB    = os.getenv('INFLUXDB_DB')

        self.client = influxdb_client.InfluxDBClient(url=self.INFLUXDB_HOST, token=self.INFLUXDB_TOKEN, org=self.INFLUXDB_DB)
        
    def get_variable(self, query):
        query_api = self.client.query_api()
        tables = query_api.query(query)
        
        result = json.loads(tables.to_json())
        
        print(result[0])
        
        if not (len(result) > 1 or len(result)) < 1:
            return result[0]["_value"]
        else:
            raise Exception("Query returned multiple values")
        