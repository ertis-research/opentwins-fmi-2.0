import os
from paho.mqtt import client as mqtt_client
import random

class MessageBrokerController:
    def __init__(self):
        # Target broker information
        self.BROKER_IP       = os.getenv('BROKER_IP')
        self.BROKER_PORT     = int(os.getenv('BROKER_PORT'))
        self.BROKER_TOPIC    = os.getenv('BROKER_TOPIC')
        self.BROKER_USERNAME = os.getenv('BROKER_USERNAME')
        self.BROKER_PASSWORD = os.getenv('BROKER_PASSWORD')
        
        # Create a client instance 
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, "fmi-simulator-"+os.getenv('SIMULATION_ID'))
        if self.BROKER_USERNAME != None and self.BROKER_PASSWORD != None:
            self.client.username_pw_set(username=self.BROKER_USERNAME, password=self.BROKER_PASSWORD)
        self.client.connect(self.BROKER_IP, self.BROKER_PORT)

    def send_message(self, messages):
        self.client.publish(self.BROKER_TOPIC, messages)