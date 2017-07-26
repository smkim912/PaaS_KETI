import paho.mqtt.client as mqtt
import json


def on_connect(client, userdata, rc):
  print ("Connected with result coe " + str(rc))
  client.subscribe("keti/meterd")


def on_message(client, userdata, msg):
  print "Topic: ", msg.topic + '\nMessage: ' + str(msg.payload)
  payload_list = json.loads(msg.payload)

  fullen = payload_list[0] 
  ID = payload_list[1]
  equip = payload_list[2]
  factory = payload_list[3]
  active_pow = payload_list[5]
  reactive_pow = payload_list[6]
  print fullen, ID, equip, factory, active_pow, reactive_pow



client = mqtt.Client()       
client.on_connect = on_connect 
client.on_message = on_message  

client.connect("test.mosquitto.org", 1883, 60)  

client.loop_forever()
