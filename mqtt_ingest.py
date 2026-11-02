import paho.mqtt.client as mqtt
import json
from farmtelementary_database import Session, FieldTelemetry

MQTT_BROKER = "broker.emqx.io"
MQTT_TOPIC = "farm/field_1/sensors"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker. Listening on topic: {MQTT_TOPIC}")
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        print(f"Received live data: {payload}")
        
        session = Session()
        telemetry = FieldTelemetry(
            soil_moisture=payload['moisture'],
            temperature=payload['temp'],
            humidity=payload['humidity']
        )
        
        session.add(telemetry)
        session.commit()
        session.close()
        print("Data successfully written to farm_telemetry.db")
        
    except Exception as e:
        print(f"Error saving to database: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker...")
client.connect(MQTT_BROKER, 1883, 60)
client.loop_forever()