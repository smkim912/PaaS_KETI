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

HOST = ''
PORT = 4000

# COMMANDS for falinux
UPDATECOMM = '\x05\x00\x00\x00\x02'
ALIVECOMM = '\x04\x00\x00\x00' 
ALIVEPERIOD = 2100	# 35mins
#ALIVEPERIOD = 10	# test

# equiptments data length
METERLEN = 101

expired_flag = 0
exit_flag = 0
canceltimer_flag = 0
buff = ''

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(3)
conn, addr = s.accept()
print 'Connected by ', addr

g_influxdbconn = InfluxDBManager()


def signal_handler(signal, frame):
	global expired_flag, exit_flag, conn
	print 'You pressed Ctrl+C. The application update has started!'
	print "The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM)
	conn.send(UPDATECOMM)
	expired_flag = 1
	exit_flag = 1
	conn.close()
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)


def aliveExpired(count):
	global conn, addr, expired_flag, timer, canceltimer_flag
	for i in range(count):
		if exit_flag == 1:
			sys.exit(0)
		elif canceltimer_flag == 1:
			canceltimer_flag = 0
			sys.exit(0)
		time.sleep(1)
	print 'Alive Timer Expired!'
	expired_flag = 1
	time.sleep(2)
	conn.close()
	conn, addr = s.accept()
	print 'Connected by', addr
	expired_flag = 0
	if exit_flag == 0:
		timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD])
		timer.start()

timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD])
timer.start()


def classifyBuff():
	global buff
	break_flag = 0

	while break_flag == 0:
		fullen = buff[:4]
		h_len = int("0x" + str(''.join(reversed(fullen)).encode("hex")), 16)
		if len(buff) < h_len:
			print 'classifyBuff(): Packet loss.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
			buff = ''
			break
		elif len(buff) == h_len:
			print 'classifyBuff(): Suitable one-packet.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
			chunk = buff
			buff = ''
			break_flag = 1
		else:
			print 'classifyBuff(): Multiple packet.'+' (real)'+str(len(buff))+' (header)'+str(h_len)
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
#				meterMsgParser(devdata)
				meterMsgParser(chunk)
			else:
				print 'classifyBuff(): <PowerMeter> data packet loss.'
		else:
			print 'classifyBuff(): Unknown equipment'
			break
'''		elif equip == 'oil':
			if d_len == OILLEN:
				oilMsgParser(chunk)
		elif equip == 'mes':
			if d_len == MESLEN:				
				mesMsgParser(chunk)'''


def meterMsgParser(chunk):
	print 'meterMsgParser(): <PowerMeter> data packet are received.'
	print 'meterMsgParser(): data> ' + chunk.encode("hex")

	# split of data frame
	fullen = chunk[:4]
	h_len = int("0x" + str(''.join(reversed(fullen)).encode("hex")), 16)
	ID = chunk[4:8]
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

'''
	print 'Split test' 
	print '[ALL_LEN] : ' + fullen + " / " + fullen.encode("hex") + " int:" + str(h_len)
	print '[ID]      : ' + ID + " / " + ID.encode("hex")
	print '[EQUIP.]  : ' + equip + " / " + equip.encode("hex")
	print '[FACTORY] : ' + factory + " / "  + factory.encode("hex")
	print '[DATA_LEN]: ' + datalen + " / "  + datalen.encode("hex") + " int:" + str(d_len)
	print '[DATA]    : ' + devdata + " / "  + devdata.encode("hex")
#	g_influxdbconn.insert(ID.encode("hex"), equip.encode("hex"), factory.encode("hex"), datalen.encode("hex"), devdata.encode("hex"))'''


def gettingMsg():
	global timer, buff, canceltimer_flag
	while True:
		if expired_flag == 1:
			continue
		data = ''
		data = conn.recv(1024)
		if not data:
			continue
		elif data == ALIVECOMM:
			print(data + ' -> alive check signal has arrived.')
			print 'Alive Timer Re-setting!'			
			timer.cancel()
			canceltimer_flag = 1
			timer.join()
			timer = threading.Timer(0, aliveExpired, args=[ALIVEPERIOD])
			timer.start()
#			conn.send(ALIVECOMM)
			conn.send(data)
			print(data + ' -> alive check signal is being sent.')
		else:
#			print "data  > " + data
			print "\nrecv  > " + "".join("%02x" % ord(c) for c in data)
			buff += data
			classifyBuff()
	conn.close()

threading._start_new_thread(gettingMsg,())

while True:
	pass
