#!/usr/bin/python
#-*- coding: utf-8 -*-
# Author : Seongmin Kim, https://github.com/smkim912

#server program
import socket
import threading
import signal
import sys
import time
#from cmpInfluxDB import InfluxDBManager
from datetime import datetime

HOST = ''
PORT = 7000

conn_list = []
conn_cnt = 0
exit_flag_list = []

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)

#g_influxdbconn = InfluxDBManager()

date = datetime.today().strftime("%Y%m%d")
date = date + "-paas-log"
#log = open(date, 'w')

pic = '/home/smkim/camera/%s'

def signal_handler(signal, frame):
	global exit_flag_list, conn_list, conn_cnt, log

	while conn_cnt > 0:
		exit_flag_list[conn_cnt-1] = -1
		conn = conn_list.pop()
		conn_cnt -= 1
		conn.close()
	time.sleep(1)
	conn_list[:] = []
	exit_flag_list[:] = []
#	log.close()
	sys.exit()

signal.signal(signal.SIGINT, signal_handler)

def gettingMsg(conn, thNum):
	if exit_flag_list[thNum] == -1:
		time.sleep(0.1)
		sys.exit()

	filename = ''
	data = conn.recv(1024)
	if data == 'alive check':
		print 'alive checking.'
		conn.close()
		return
	if data:
		filename = pic %data
		f = open(filename, 'wb')
		print filename + " receiving........"
		time.sleep(0.1)
	else:
		print "what the...????"
		conn.close()
		return		

	data = conn.recv(1024)
	time.sleep(0.1)
	#if data:
		#sys.stdout.write("Receiving.")
	while True:
		if data:
			f.write(data)
			data = conn.recv(1024)
			#sys.stdout.write(".")
			#sys.stdout.flush()
			time.sleep(0.1)
		else:
			print "\nDone receiving.: %s" %filename
			break	
	f.close()
	conn.close()


while True:
	conn, addr = s.accept()
	print '\nConnected by ', addr
#	log.write('Connected by ' + str(addr) + '\n')
	threading._start_new_thread(gettingMsg,(conn,conn_cnt,))	

	try:
		idx = conn_list.index(-1)
	except ValueError:
		idx = -1

	if idx == -1:
		conn_list.append(conn)
		exit_flag_list.append(0)
	else:
		conn_list[idx] = conn
		exit_flag_list[idx] = 0
	conn_cnt += 1
