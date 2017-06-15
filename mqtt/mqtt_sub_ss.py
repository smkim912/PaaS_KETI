import paho.mqtt.client as mqtt
import json
import ast #sample test

msgfd = open("msg", 'r')
sample = msgfd.readline()
sample_dict = ast.literal_eval(sample)

eventid = sample_dict['EventId']
print type(eventid), eventid

devicelist = sample_dict['DeviceList']
device_list = []
for i in range(len(devicelist)):
	device_list.append(dict(devicelist[i]))
print type(device_list[0]), device_list[0]

for j in range(len(device_list)):
	deviceid = device_list[i]['DeviceId']
	print type(deviceid), deviceid
	datalist = device_list[i]['DataList']
	datalist_dict = dict(datalist)
	print type(datalist_dict), len(datalist_dict), datalist_dict


'''
def on_connect(client, userdata, rc):
	print ("Connected with result code " + str(rc))
	client.subscribe('GW01')


def on_message(client, userdata, msg):
	print "Topic: ", msg.topic + '\nMessage: ' + str(msg.payload)
	dict_msg = json.loads(msg.payload)

client = mqtt.Client()       
client.on_connect = on_connect 
client.on_message = on_message  

client.connect("1.214.215.226", 1883, 60)  

client.loop_forever()
'''
