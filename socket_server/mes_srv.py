#!/usr/bin/python
#-*- coding: utf-8 -*-
# Author : Seongmin Kim, https://github.com/smkim912

#server program
import socket
import threading
import signal
import sys
import time
from cmpInfluxDB import InfluxDBManager
from datetime import datetime
import paho.mqtt.client as mqtt
import json

VERSION = '170926'
HOST = ''
PORT = 6000

# COMMANDS for falinux
UPDATECOMM = '\x05\x00\x00\x00\x02'
ALIVECOMM = '\x04\x00\x00\x00' 
ALIVEPERIOD = 2100	# 35mins

# equiptments data length
METERLEN = 101
MESLEN = 117

conn_list = []
conn_cnt = 0
exptimer_list = []
exit_flag_list = []
reset_flag_list = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(3)

print 'Run a Server program for MES. ver_' + VERSION

def on_disconnect(client, userdata, rc):
	print "Disconnected from MQTT server with code: %s\n" % rc
	log.write('Disconnected from MQTT server with code: ' + str(rc))
	while rc != 0:
		time.sleep(1)
		print "Reconnecting..."
		log.write("Reconnecting...")
		rc = mqttc.reconnect()

mqttc = mqtt.Client("keti_mes_pub")
mqttc.on_disconnect = on_disconnect
mqttc.username_pw_set("admin", "AQSWdefr1234")
#mqttc.connect("52.79.176.120", 61613)

#secondary exem mqtt
def cp_on_disconnect(client, userdata, rc):
	print "Disconnected from MQTT server with code: %s\n" % rc
	log.write('Disconnected from MQTT server with code: ' + str(rc))
	while rc != 0:
		time.sleep(1)
		print "Reconnecting..."
		log.write("Reconnecting...")
		rc = cp_mqttc.reconnect()

cp_mqttc = mqtt.Client("keti_mes_pub2")
cp_mqttc.on_disconnect = cp_on_disconnect
#cp_mqttc.connect("13.124.194.253", 61613)

g_influxdbconn = InfluxDBManager('mesdb')

date = datetime.today().strftime("%Y%m%d_%H%M%S")
date = date + "-paas-log"
log = open(date, 'w')

def signal_handler(signal, frame):
	global exptimer_list, exit_flag_list, reset_flag_list, conn_list, conn_cnt, log
	print 'You pressed Ctrl+C. The application update has started!'
	print "The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM)
	log.write('You pressed Ctrl+C. The application update has started!\n')
	log.write("The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM) + "\n")

	for n in conn_list:
		print "conn_list:" + str(conn_list.index(n)) + ":" + str(n)
	print 'conn_cnt: ' + str(conn_cnt)
	while conn_cnt > 0:
		exit_flag_list[conn_cnt-1] = -1
		conn_list[conn_cnt-1].send(UPDATECOMM)	#update comm error 170530 smkim
		conn = conn_list.pop()
		conn_cnt -= 1
		try:
			conn.close()
		except AttributeError:
			conn = 0
	time.sleep(1)
	conn_list[:] = []
	exptimer_list[:] = []
	exit_flag_list[:] = []
	reset_flag_list[:] = []
	log.close()
	sys.exit()

signal.signal(signal.SIGINT, signal_handler)


def aliveExpired(count, thNum):
	global conn_list, exptimer_list, exit_flag_list, reset_flag_list, conn_cnt
	for i in range(count):
		if exit_flag_list[thNum] == -1:
			sys.exit()
		if reset_flag_list[thNum] == 1:
			i = 0
			reset_flag_list[thNum] = 0
		time.sleep(1)
	print 'Alive Timer Expired!'
	log.write('Alive Timer Expired!\n')
	conn_list[thNum] = -1
	exptimer_list[thNum] = -1
	exit_flag_list[thNum] = -1
	reset_flag_list[thNum] = -1
	conn_cnt -= 1
	time.sleep(1)
	sys.exit()


def classifyBuff(buff):
	break_flag = 0

	while break_flag == 0:		
		fullen = buff[:4]
		h_len = int("0x" + str(''.join(reversed(fullen)).encode("hex")), 16)
		if len(buff) < h_len:
#			print 'classifyBuff(): Packet loss.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
			buff = ''
			break
		elif len(buff) == h_len:
#			print 'classifyBuff(): Suitable one-packet.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
			chunk = buff
			buff = ''
			break_flag = 1
		else:
#			print 'classifyBuff(): Multiple packet.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
			chunk = buff[:h_len] 
			rem = buff[h_len:]
			buff = ''
			buff = rem
			
		ID = chunk[4:8]
		equip = chunk[8:16]
		factory = chunk[16:24]

		if equip[:5] == 'meter':
			meterMsgParser(chunk)
		elif equip[:6] == '1600Vx':		#with device number(e.g., 1600Vx01, 1600Vx02, ...)
			mesMsgParser(chunk) 
		else:
			print 'classifyBuff(): Unknown equipment: ' + equip
			log.write('classifyBuff(): Unknown equipment: ' + equip + '\n')
			break

def mesMsgParser(chunk):
	ID = chunk[4:8]
	if ID[1] == '3':
		print 'mesMsgParser(): <MES:' + ID + '> data packet are received.'
		print 'mesMsgParser(): data> ' + chunk.encode("hex")
	log.write('mesMsgParser(): <MES:' + ID + '> data packet are received.\n')
	log.write('mesMsgParser(): data> ' + chunk.encode("hex") + '\n')

	# split of data frame
	fullen = chunk[:4]
	h_len = int("0x" + str(''.join(reversed(fullen)).encode("hex")), 16)
	equip = chunk[8:16]
	factory = chunk[16:24]
	txtype = chunk[24:25]
	datalen = chunk[25:29]
	d_len = int("0x" + str(''.join(reversed(datalen)).encode("hex")), 16)
	data_idx = 29 + d_len
	devdata = chunk[29:data_idx]

	if txtype == 'T':
		return
	if d_len != MESLEN and d_len != MESLEN-1:	# unknown 'ff' after (EOT)
		#print 'mesMsgParser(): <MES> data packet loss.'
		log.write('mesMsgParser(): <MES> data packet loss.\n')
		return -1
	# we may need CRC(?) check.
	# split for the data frame of the power meter
	try:
		mes_num = devdata[1:3].decode("utf8")
		comm = devdata[3:5].decode("utf8")
		h_event = devdata[6:16].decode("utf8")
		order_num = devdata[17:37].decode("utf8")
		sys_status = devdata[38:40].decode("utf8")
		work_status = devdata[41].decode("utf8")
		work_prio = devdata[43].decode("utf8")
		worker_code = devdata[45:49].decode("utf8")
		production = devdata[50:54].decode("utf8")
		faulty_1 = devdata[55:59].decode("utf8")
		faulty_2 = devdata[60:64].decode("utf8")
		faulty_3 = devdata[65:69].decode("utf8")
		faulty_4 = devdata[70:74].decode("utf8")
		faulty_5 = devdata[75:79].decode("utf8")
		faulty_6 = devdata[80:84].decode("utf8")
		faulty_7 = devdata[85:89].decode("utf8")
		faulty_8 = devdata[90:94].decode("utf8")
		faulty_9 = devdata[95:99].decode("utf8")
		argdate = devdata[100:106]
		tdate = str("%02d"% int(argdate[:2],16))+str("%02d"% int(argdate[2:4],16))+str("%02d"% int(argdate[4:6],16))
		tdate = tdate.decode("utf8")
		argtime = devdata[106:112]
		ttime = str("%02d"% int(argtime[:2],16))+str("%02d"% int(argtime[2:4],16))+str("%02d"% int(argtime[4:6],16))
		ttime = ttime.decode("utf8")
	except ValueError,UnicodeDecodeError:	#unknown error (e.g., MES num = 0x8a)
		return

	json_list = []
	json_list.append(mes_num)
	json_list.append(comm)
	json_list.append(h_event)
	json_list.append(order_num)
	json_list.append(sys_status)
	json_list.append(work_status)
	json_list.append(work_prio)
	json_list.append(worker_code)
	json_list.append(production)
	json_list.append(faulty_1)
	json_list.append(faulty_2)
	json_list.append(faulty_3)
	json_list.append(faulty_4)
	json_list.append(faulty_5)
	json_list.append(faulty_6)
	json_list.append(faulty_7)
	json_list.append(faulty_8)
	json_list.append(faulty_9)
	json_list.append(tdate)
	json_list.append(ttime)

	json_val = json.dumps(json_list)
	#mqttc.publish("mesd", json_val)
	#cp_mqttc.publish("SS_Q", json_val)

	ts = time.mktime(time.strptime("20"+tdate+ttime, '%Y%m%d%H%M%S'))
	influx_ts = int(ts) * 1000000000
	try:
		g_influxdbconn.insertMES("mes", ID,
			equip, 
			factory, 
			mes_num, 
			comm, 
			h_event, 
			order_num,
			sys_status,
			work_status,
			worker_code,
			int(production, 16),
			int(faulty_1, 16),
			int(faulty_2, 16),
			int(faulty_3, 16),
			int(faulty_4, 16),
			int(faulty_5, 16),
			int(faulty_6, 16),
			int(faulty_7, 16),
			int(faulty_8, 16),
			int(faulty_9, 16),
			influx_ts)
	except ValueError,UnicodeDecodeError:	#unknown error (e.g., MES num = 0x8a)
		return

'''
	print '[mes_num]     : ' + mes_num
	print '[comm]        : ' + comm
	print '[h_event]     : ' + h_event
	print '[order_num]   : ' + order_num
	print '[sys_status]  : ' + sys_status
	print '[work_status] : ' + work_status
	print '[work_prio]   : ' + work_prio
	print '[worker_code] : ' + worker_code
	print '[production]  : ' + production
	print '[faulty_1]    : ' + faulty_1
	print '[faulty_9]    : ' + faulty_9
	print '[date]        : ' + date
	print '[time]        : ' + time'''

'''	print '<<Received data>>' 
	print '[ALL_LEN] : ' + fullen + " / " + fullen.encode("hex") + " int:" + str(h_len)
	print '[ID]      : ' + ID + " / " + ID.encode("hex")
	print '[EQUIP.]  : ' + equip + " / " + equip.encode("hex")
	print '[FACTORY] : ' + factory + " / "  + factory.encode("hex")
	print '[TxTYPE]  : ' + txtype + " / " + txtype.encode("hex")
	print '[DATA_LEN]: ' + datalen + " / "  + datalen.encode("hex") + " int:" + str(d_len)
	print '[DATA]    : ' + devdata + " / "  + devdata.encode("hex")'''



def meterMsgParser(chunk):
	ID = chunk[4:8]
	print 'meterMsgParser(): <PowerMeter:' + ID + '> data packet are received.'
	print 'meterMsgParser(): data> ' + chunk.encode("hex")
	log.write('meterMsgParser(): <PowerMeter:' + ID + '> data packet are received.\n')
	log.write('meterMsgParser(): data> ' + chunk.encode("hex") + '\n')

	# split of data frame
	fullen = chunk[:4]
	h_len = int("0x" + str(''.join(reversed(fullen)).encode("hex")), 16)
	equip = chunk[8:16]
	factory = chunk[16:24]
	datalen = chunk[24:28]
	d_len = int("0x" + str(''.join(reversed(datalen)).encode("hex")), 16)
	data_idx = 28 + d_len
	devdata = chunk[28:data_idx]
	
	if d_len != METERLEN:
		print 'meterMsgParser(): <PowerMeter> data packet loss.'
		log.write('meterMsgParser(): <PowerMeter> data packet loss.\n')
		return -1

	# we may need CRC(?) check.
	# split for the data frame of the power meter
	active_pow = devdata[11:15]
	reactive_pow = devdata[15:19]
	A_volt = devdata[19:23]
	B_volt = devdata[23:27]
	C_volt = devdata[27:31]
	A_current = devdata[31:35]
	B_current = devdata[35:39]
	C_current = devdata[39:43]
	A_angle = devdata[43:47]
	B_angle = devdata[47:51]
	C_angle = devdata[51:55]
	A_pow_factor = devdata[55:59]
	B_pow_factor = devdata[59:63]
	C_pow_factor = devdata[63:67]
	total_active_pow = devdata[67:71]
	total_reactive_pow = devdata[71:75]
	A_active_pow = devdata[75:79]
	B_active_pow = devdata[79:83]
	C_active_pow = devdata[83:87]
	A_reactive_pow = devdata[87:91]
	B_reactive_pow = devdata[91:95]
	C_reactive_pow = devdata[95:99]

	json_list = []
	json_list.append(h_len)
	json_list.append(ID)
	json_list.append(equip)
	json_list.append(factory)
	json_list.append(d_len)
	json_list.append(long("0x"+active_pow.encode("hex"),16))
	json_list.append(long("0x"+reactive_pow.encode("hex"),16))
	json_list.append(float.fromhex("0x"+A_volt.encode("hex")))
	json_list.append(float.fromhex("0x"+B_volt.encode("hex")))
	json_list.append(float.fromhex("0x"+C_volt.encode("hex")))
	json_list.append(float.fromhex("0x"+A_current.encode("hex")))
	json_list.append(float.fromhex("0x"+B_current.encode("hex")))
	json_list.append(float.fromhex("0x"+C_current.encode("hex")))
	json_list.append(float.fromhex("0x"+A_angle.encode("hex")))
	json_list.append(float.fromhex("0x"+B_angle.encode("hex")))
	json_list.append(float.fromhex("0x"+C_angle.encode("hex")))
	json_list.append(float.fromhex("0x"+A_pow_factor.encode("hex")))
	json_list.append(float.fromhex("0x"+B_pow_factor.encode("hex")))
	json_list.append(float.fromhex("0x"+C_pow_factor.encode("hex")))
	json_list.append(float.fromhex("0x"+total_active_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+total_reactive_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+A_active_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+B_active_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+C_active_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+A_reactive_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+B_reactive_pow.encode("hex")))
	json_list.append(float.fromhex("0x"+C_reactive_pow.encode("hex")))

	json_val = json.dumps(json_list)
	#mqttc.publish("meterd", json_val)

	g_influxdbconn.insert("meter", ID, 
			equip, 
			factory, 
			long("0x"+active_pow.encode("hex"),16), 
			long("0x"+reactive_pow.encode("hex"),16), 
			float.fromhex("0x"+A_volt.encode("hex")), 
			float.fromhex("0x"+B_volt.encode("hex")), 
			float.fromhex("0x"+C_volt.encode("hex")), 
			float.fromhex("0x"+A_current.encode("hex")), 
			float.fromhex("0x"+B_current.encode("hex")), 
			float.fromhex("0x"+C_current.encode("hex")), 
			float.fromhex("0x"+A_angle.encode("hex")), 
			float.fromhex("0x"+B_angle.encode("hex")), 
			float.fromhex("0x"+C_angle.encode("hex")), 
			float.fromhex("0x"+A_pow_factor.encode("hex")), 
			float.fromhex("0x"+B_pow_factor.encode("hex")), 
			float.fromhex("0x"+C_pow_factor.encode("hex")), 
			float.fromhex("0x"+total_active_pow.encode("hex")), 
			float.fromhex("0x"+total_reactive_pow.encode("hex")), 
#			long("0x"+total_active_pow.encode("hex"),16), 
#			long("0x"+total_reactive_pow.encode("hex"),16), 
			float.fromhex("0x"+A_active_pow.encode("hex")), 
			float.fromhex("0x"+B_active_pow.encode("hex")), 
			float.fromhex("0x"+C_active_pow.encode("hex")), 
			float.fromhex("0x"+A_reactive_pow.encode("hex")), 
			float.fromhex("0x"+B_reactive_pow.encode("hex")), 
			float.fromhex("0x"+C_reactive_pow.encode("hex")))

'''	print '<<Received data>>' 
	print '[ALL_LEN] : ' + fullen + " / " + fullen.encode("hex") + " int:" + str(h_len)
	print '[ID]      : ' + ID + " / " + ID.encode("hex")
	print '[EQUIP.]  : ' + equip + " / " + equip.encode("hex")
	print '[FACTORY] : ' + factory + " / "  + factory.encode("hex")
	print '[DATA_LEN]: ' + datalen + " / "  + datalen.encode("hex") + " int:" + str(d_len)
#	print '[DATA]    : ' + devdata + " / "  + devdata.encode("hex")'''


def gettingMsg(conn, thNum):
	global reset_flag_list
	while True:
		if exit_flag_list[thNum] == -1:
			time.sleep(0.1)
			sys.exit()
		data = ''
		time.sleep(0.1)
		data = conn.recv(1024)
		time.sleep(0.1)
		if not data:
			time.sleep(0.1)
			continue
		elif data == ALIVECOMM:
			print(data + ' -> alive check signal has arrived.')
			print 'Alive Timer Re-setting!'
			log.write(data + ' -> alive check signal has arrived.\n')
			log.write('Alive Timer Re-setting!\n')
			reset_flag_list[thNum] = 1
#			conn.send(ALIVECOMM)
			conn.send(data)
			time.sleep(0.1)
			print(data + ' -> alive check signal is being sent.')
			log.write(data + ' -> alive check signal is being sent.\n')
		else:
			#print "data  > " + data
			print "\nrecv  > " + "".join("%02x" % ord(c) for c in data)
			reset_flag_list[thNum] = 1 # no alive-check signal from falinux_v2 (170810 smkim)
			classifyBuff(data)
			time.sleep(0.1)
	conn.close()


while True:
	conn, addr = s.accept()
	print 'Connected by ', addr
	log.write('Connected by ' + str(addr) + '\n')

	try:
		idx = conn_list.index(-1)
	except ValueError:
		idx = -1

	if idx == -1:
		conn_list.append(conn)
		thNum = conn_list.index(conn)
		print 'thread num: ', thNum
		log.write('thread num: ' + str(thNum) + '\n')
		timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD, thNum])
		exptimer_list.append(timer)
		exit_flag_list.append(0)
		reset_flag_list.append(0)
	else:
		conn_list[idx] = conn
		exptimer_list[idx] = conn
		exit_flag_list[idx] = 0
		reset_flag_list[idx] = 0
		thNum = idx
		print 'thread Num: ', thNum
		timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD, thNum])
	conn_cnt += 1

	threading._start_new_thread(gettingMsg,(conn,thNum,))	
	timer.start()
