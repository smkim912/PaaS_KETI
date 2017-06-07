#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author : Seongmin Kim, https://github.com/smkim912

#server program
import socket
import threading
import signal
import sys
from cmpInfluxDB import InfluxDBManager

HOST = ''
PORT = 4000
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(3)
conn, addr = s.accept()
print(' '*10, 'Connected by', addr)

g_influxdbconn = InfluxDBManager()

# def sendingMsg():
# 	while True:
# 		data = input()
# 		data = data.encode("utf-8")
# 		conn.send(data)
# 	conn.close()

def signal_handler(signal, frame):
	print 'You pressed Ctrl+C. Application update is started!'
	comm = '\x04\x00\x00\x00\x02'	# 0x02 command
	print comm
	print "join  > " + "".join("%02x" % ord(c) for c in comm)
#	conn.send(comm)
	sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def gettingMsg():
	while True:
		data = conn.recv(1024)
		if not data:
			break
		elif data == 'A':
			print(data + ' -> signal received.')
			conn.send(data)
			print(data + ' -> signal sended.(return)')
		else:
			print "data  > " + data
			print "join  > " + "".join("%02x" % ord(c) for c in data)
			
			# split of data frame
			fullen = data[:4]
			ID = data[4:8]
			equip = data[8:16]
			factory = data[16:24]
			datalen = data[24:28]
			n = int("0x" + str(''.join(reversed(datalen)).encode("hex")), 16)
			data_idx = 28 + n
			data = data[28:data_idx]
			
			print 'Split test' 
			print '[ALL_LEN] : ' + fullen + " " + fullen.encode("hex") 
			print '[ID]      : ' + ID + " " + ID.encode("hex")
			print '[EQUIP.]  : ' + equip + " " + equip.encode("hex")
			print '[FACTORY] : ' + factory + " "  + factory.encode("hex")
			print '[DATA_LEN]: ' + datalen + " "  + datalen.encode("hex") + " int:" + str(n)
			print '[DATA]    : ' + data + " "  + data.encode("hex")
#			g_influxdbconn.insert(ID.encode("hex"), equip.encode("hex"), factory.encode("hex"), datalen.encode("hex"), data.encode("hex"))
	
	conn.close()

threading._start_new_thread(gettingMsg,())

while True:
	pass
