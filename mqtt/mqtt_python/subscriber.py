import paho.mqtt.client as mqtt


def on_connect(client, userdata, rc):
  print ("Connected with result coe " + str(rc))
  client.subscribe("GW01")


def on_message(client, userdata, msg):
  print "Topic: ", msg.topic + '\nMessage: ' + str(msg.payload)

client = mqtt.Client()       
client.on_connect = on_connect 
client.on_message = on_message  

client.connect("test.mosquitto.org", 1883, 60)  

client.loop_forever()
