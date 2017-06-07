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

HOST = ''
PORT = 4000

# COMMANDS for falinux
UPDATECOMM = '\x05\x00\x00\x00\x02'
ALIVECOMM = '\x04\x00\x00\x00' 
ALIVEPERIOD = 2100	# 35mins

# equiptments data length
METERLEN = 101

conn_list = []
conn_cnt = 0
exptimer_list = []
exit_flag_list = []
reset_flag_list = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(3)

g_influxdbconn = InfluxDBManager()

date = datetime.today().strftime("%Y%m%d")
date = date + "-paas-log"
log = open(date, 'w')

def signal_handler(signal, frame):
	global exptimer_list, exit_flag_list, reset_flag_list, conn_list, conn_cnt, log
	print 'You pressed Ctrl+C. The application update has started!'
	print "The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM)
	log.write('You pressed Ctrl+C. The application update has started!\n')
	log.write("The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM) + "\n")

	while conn_cnt > 0:
		exit_flag_list[conn_cnt-1] = -1
#		conn_list[conn_cnt-1].send(UPDATECOMM)	//update comm error 170530 smkim
		conn = conn_list.pop()
		conn_cnt -= 1
		conn.close()
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
		datalen = chunk[24:28]
		d_len = int("0x" + str(''.join(reversed(datalen)).encode("hex")), 16)

		if equip == 'meter\x00\x00\x00':
			if d_len == METERLEN:
				meterMsgParser(chunk)
			else:
				print 'classifyBuff(): <PowerMeter> data packet loss.'
				log.write('classifyBuff(): <PowerMeter> data packet loss.\n')
		else:
			print 'classifyBuff(): Unknown equipment'
			log.write('classifyBuff(): Unknown equipment\n')
			break
'''		elif equip == 'oil':
			if d_len == OILLEN:
				oilMsgParser(chunk)
		elif equip == 'mes':
			if d_len == MESLEN:				
				mesMsgParser(chunk)'''


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

	g_influxdbconn.insert(ID, 
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
#			float.fromhex("0x"+total_active_pow.encode("hex")), 
#			float.fromhex("0x"+total_reactive_pow.encode("hex")), 
			long("0x"+total_active_pow.encode("hex"),16), 
			long("0x"+total_reactive_pow.encode("hex"),16), 
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
#			print "data  > " + data
#			print "\nrecv  > " + "".join("%02x" % ord(c) for c in data)
#			buff += data
			classifyBuff(data)
			time.sleep(0.1)
	conn.close()


while True:
	conn, addr = s.accept()
	print 'Connected by ', addr
	log.write('Connected by ' + str(addr) + '\n')
	threading._start_new_thread(gettingMsg,(conn,conn_cnt,))	
	timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD, conn_cnt-1])

	try:
		idx = conn_list.index(-1)
	except ValueError:
		idx = -1

	if idx == -1:
		conn_list.append(conn)
		exptimer_list.append(timer)
		exit_flag_list.append(0)
		reset_flag_list.append(0)
	else:
		conn_list[idx] = conn
		exptimer_list[idx] = conn
		exit_flag_list[idx] = 0
		reset_flag_list[idx] = 0
	conn_cnt += 1
	timer.start()
