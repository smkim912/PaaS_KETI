import paho.mqtt.client as mqtt

mqttc = mqtt.Client("python_pub")  
#mqttc.connect("test.mosquitto.org", 1883) 
mqttc.connect("1.214.215.226", 1883)
mqttc.publish("GW01", "Hello World!")
mqttc.loop(2)      
