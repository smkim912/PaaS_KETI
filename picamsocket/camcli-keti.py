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

pic = '/home/pi/picamera/%s_sss_press.jpg'

camera =  picamera.PiCamera() 
#camera.resolution = (1024, 768)
camera.resolution = (512, 512)
#camera.rotation = -180


def sendingImg():
    time = strftime("%Y-%m-%d_%H:%M:%S", localtime())
    camera.capture(pic %time)
    print '\n A picture was saved at ' + pic %time
    sleep(0.5)

    buf = 1024
    f = open(pic %time, 'rb')
    img = f.read(buf)
    if img:
        sys.stdout.write('Sending.')
    while(1):
        if img:
            sys.stdout.write('.')
            sys.stdout.flush()
            s.send(img)
            img = f.read(buf)
        else:
            print '\nDone sending'
            break
    f.close()
    s.close()
    sleep(15)
    os.remove(pic %time)


while True:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        print 'Connected'
#        threading._start_new_thread(sendingImg,())
        th = threading.Thread(target=sendingImg, args=())
        th.start()
        th.join()
    except socket.error:
        print "Connection Failed, Retrying.."
        sleep(1)
