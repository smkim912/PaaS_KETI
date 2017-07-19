#!/usr/bin/python
#-*-coding:utf8-*-
# Author : Seongmin Kim, github.com/smkim912

import os
import sys
PATH = '/home/pi/picamera'
if not os.path.exists(PATH): os.makedirs(PATH)
from time import strftime, localtime, sleep
import picamera
import datetime
import socket
import threading


HOST = '125.140.110.217'
PORT = 7000

pic = '/home/pi/picamera/%s_sss.jpg'
pic_path = '/home/pi/picamera/%s'

camera =  picamera.PiCamera() 
camera.resolution = (512, 512)
#camera.rotation = -180

FIVEMINCNT = 12
saved_pics_list = []

def sendingImg(filename):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.send(filename)
    sleep(0.5)

    buf = 1024
    f = open(pic_path %filename, 'rb')
    img = f.read(buf)
    #if img:
        #sys.stdout.write('Sending.')
    while True:
        if img:
            #sys.stdout.write('.')
            #sys.stdout.flush()
            s.send(img)
            img = f.read(buf)
        else:
            print '\nDone sending: %s' %filename
            break
    f.close()
    s.close()
    os.remove(pic_path %filename)

while True:
    for i in range(FIVEMINCNT):
        time = strftime("%Y-%m-%d_%H:%M:%S", localtime())
        camera.capture(pic %time)
        print '\n A picture was saved at ' + pic %time
        saved_pics_list.append("%s_sss.jpg" %time)
        sleep(5)

    savedlen = len(saved_pics_list)
    print '\n' + str(savedlen) + ' -pics sending..........'
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((HOST, PORT))
            print 'Connected'
            s.send("alive check")
            s.close()
            break
        except socket.error:
            print "Connection failed, Re-trying.."
            sleep(1)

    for j in range(savedlen):
        filename = saved_pics_list.pop()
        threading._start_new_thread(sendingImg, (filename,))
