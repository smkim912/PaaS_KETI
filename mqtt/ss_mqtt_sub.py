import paho.mqtt.client as mqtt
import json
import ast #sample test
from influxdb import InfluxDBClient

class InfluxDB :
	m_conn = None
	
	def __init__(self) :
		pass

	def open(self) :
		bConti = True
		while bConti :
			try :
				self.m_dConn = InfluxDBClient('127.0.0.1', 8086, 'keti', 'itek', 'mqttdb')
				bConti = False
			except Exception, e :
#time.sleep(CmpGlobal.g_nConnectionRetryInterval)
				time.sleep(5)
				print "-------------------------- influxdb connect fail -----------------------------"

	def insertData(self, jsondata) :
		print("Write points: {0}".format(jsondata))
		self.m_dConn.write_points(jsondata)



class InfluxDBManager :
	m_oDBConn = None
	
	def __init__(self) :
		self.m_oDBConn = InfluxDB() 
		self.m_oDBConn.open()

	def insert(self, deviceid, json_dict) :
		json_body = [
			{ 
				"measurement": deviceid, 
				"fields": json.loads(json_dict)
			}
		]
#		print json_body
		self.m_oDBConn.insertData(json_body)
		return 0



g_influxdbconn = InfluxDBManager()




#msgfd = open("msg", 'r')
#sample = msgfd.readline()
#payload_dict = ast.literal_eval(sample)

def payloadParser(payload_dict):
#	eventid = payload_dict['EventId']
	devicelist = payload_dict['DeviceList']
	device_list = []
	for i in range(len(devicelist)):
		device_list.append(dict(devicelist[i]))
	for j in range(len(device_list)):
		deviceid = device_list[i]['DeviceId']
		datalist = device_list[i]['DataList']
		data_list = []
		for k in range(len(datalist)):
			data_list.append(dict(datalist[k]))
		json_dict = {}
		for l in range(len(data_list)):
			name = data_list[l]['DataId']
			val = data_list[l]['Value']
			json_dict[name] = float(val)
		if len(json_dict) != 0:
			json_val = json.dumps(json_dict)
			g_influxdbconn.insert(deviceid, json_val)

def on_connect(client, userdata, rc):
	print ("Connected with result code " + str(rc))
	client.subscribe('GW01')

def on_message(client, userdata, msg):
	print "Topic: ", msg.topic + '\nMessage: ' + str(msg.payload)
	payload_dict = json.loads(msg.payload)
	payloadParser(payload_dict)

client = mqtt.Client()       
client.on_connect = on_connect 
client.on_message = on_message  

client.connect("1.214.215.226", 1883, 60)  

client.loop_forever()

