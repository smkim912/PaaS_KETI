#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author : Seongmin Kim, https://github.com/smkim912

#server program
import socket
from cmpInfluxDB import InfluxDBManager

HOST = ''
PORT = 4000

# COMMANDS for falinux
UPDATECOMM = '\x05\x00\x00\x00\x02'

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(3)
conn, addr = s.accept()
print 'Connected by ', addr

print "The update command is being sending > " + "".join("%02x" % ord(c) for c in UPDATECOMM)
conn.send(UPDATECOMM)
conn.close()
