# cmpInfluxDB.py
# coding=utf-8
import time
from influxdb import InfluxDBClient

class InfluxDB :
	m_conn = None
	
	def __init__(self) :
		pass

	def open(self, dbname) :
		bConti = True
		while bConti :
			try :
				self.m_dConn = InfluxDBClient('127.0.0.1', 8086, 'keti', 'itek', dbname)
				bConti = False
			except Exception, e :
#time.sleep(CmpGlobal.g_nConnectionRetryInterval)
				time.sleep(5)
				print "--------------------------------- influxdb connect fail -------------------------------------"

	def insertData(self, jsondata) :
		#print("Write points: {0}".format(jsondata))
		self.m_dConn.write_points(jsondata)



class InfluxDBManager :
	m_oDBConn = None
	
	def __init__(self, dbname) :
		self.m_oDBConn = InfluxDB() 
		self.m_oDBConn.open(dbname)


	def insertMES(self, nDev, nId, nEqp, nFact, nMesNum, nComm, nHardEvent, nOrderNum, nSysStatus, nWorkStatus, nWorkerCode, nProduct, nF1, nF2, nF3, nF4, nF5, nF6, nF7, nF8, nF9, timestamp) :
		json_falinux_body = [
			{
				"measurement": nDev,
				"tags": {
			        "id":				nId,
					"equip":			nEqp,
					"factory":			nFact,
					"Mes num.":			nMesNum
				},
				"fields": {
					"Command":			nComm,
					"Hardware event":	nHardEvent,
					"Order num.":		nOrderNum,
					"System status":	nSysStatus,
					"Work status":		nWorkStatus,
					"Workder code":		nWorkerCode,
					"Production":		nProduct,
					"Faulty(1)":		nF1,
					"Faulty(2)":		nF2,
					"Faulty(3)":		nF3,
					"Faulty(4)":		nF4,
					"Faulty(5)":		nF5,
					"Faulty(6)":		nF6,
					"Faulty(7)":		nF7,
					"Faulty(8)":		nF8,
					"Faulty(9)":		nF9					
				},
				"time": timestamp
			}
		]
		self.m_oDBConn.insertData(json_falinux_body)
		return 0


	def insert(self, nDev, nId, nEqp, nFact, nActPow, nReactPow, nAvolt, nBvolt, nCvolt, nAcurr, nBcurr, nCcurr, nAangl, nBangl, nCangl, nApowFact, nBpowFact, nCpowFact, nTotActPow, nTotReactPow, nAactPow, nBactPow, nCactPow, nAreactPow, nBreactPow, nCreactPow) :
		json_falinux_body = [
			{
			    "measurement": nDev,
			    "tags": {
			        "id":  nId,
					"equip": nEqp,
					"factory": nFact
			    },
			    "fields": {
			        "Active Power":		nActPow,
					"Reactive Power":	nReactPow,
					"A Voltage":		nAvolt,
					"B Voltage":		nBvolt,
					"C Voltage":		nCvolt,
					"A Current":		nAcurr,
					"B Current":		nBcurr,
					"C Current":		nCcurr,
					"A Phase Angle":	nAangl,
					"B Phase Angle":	nBangl,
					"C Phase Angle":	nCangl,
					"A Power Factor":	nApowFact,
					"B Power Factor":	nBpowFact,
					"C Power Factor":	nCpowFact,
					"Total Active Power":	nTotActPow,
					"Total Reactive Power":	nTotReactPow,
					"A Active Power":	nAactPow,
					"B Active Power":	nBactPow,
					"C Active Power":	nCactPow,
					"A Reactive Power":	nAreactPow,
					"B Reactive Power":	nBreactPow,
					"C Reactive Power":	nCreactPow
			    }
			}
		]
		self.m_oDBConn.insertData(json_falinux_body)
		return 0
