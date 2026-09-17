import os
import json
import threading
from paho.mqtt import client as mqtt_client
import random

from common.errors import MQTTInputError


class MessageBrokerController:
    def __init__(self):
        # Target broker information
        self.BROKER_IP       = os.getenv('BROKER_IP')
        self.BROKER_PORT     = int(os.getenv('BROKER_PORT')) if os.getenv('BROKER_PORT') != None else None
        self.BROKER_TOPIC    = os.getenv('BROKER_TOPIC')
        self.BROKER_USERNAME = os.getenv('BROKER_USERNAME')
        self.BROKER_PASSWORD = os.getenv('BROKER_PASSWORD')

        # Create a client instance
        self.client = mqtt_client.Client(mqtt_client.CallbackAPIVersion.VERSION1, "fmi-simulator-"+os.getenv('SIMULATION_ID'))
        if self.BROKER_USERNAME != None and self.BROKER_PASSWORD != None:
            self.client.username_pw_set(username=self.BROKER_USERNAME, password=self.BROKER_PASSWORD)
        if self.BROKER_PORT != None:
            self.client.connect(self.BROKER_IP, self.BROKER_PORT)
        else:
            self.client.connect(self.BROKER_IP)

    def send_message(self, messages):
        self.client.publish(self.BROKER_TOPIC, messages)

    def get_variable(self, topic, mapper, timeout=10):
        """ Subscribe to `topic` and return the value of the first message received, read from
            the field pointed to by `mapper` (a dot-separated path into the JSON payload, e.g.
            "value" or "data.temperature"). Waits up to `timeout` seconds for a message to arrive. """
        received = threading.Event()
        outcome = {}

        def on_message(client, userdata, msg):
            try:
                payload = json.loads(msg.payload.decode())
                value = payload
                for key in mapper.split('.'):
                    value = value[key]
                outcome["value"] = value
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as e:
                outcome["error"] = e
            finally:
                received.set()

        self.client.on_message = on_message
        self.client.subscribe(topic)
        self.client.loop_start()

        try:
            if not received.wait(timeout):
                raise MQTTInputError(f"No message received on topic '{topic}' within {timeout}s")
            if "error" in outcome:
                raise MQTTInputError(f"Failed to read '{mapper}' from the message received on topic '{topic}': {outcome['error']}")
            return outcome["value"]
        finally:
            self.client.unsubscribe(topic)
            self.client.loop_stop()
            self.client.on_message = None
