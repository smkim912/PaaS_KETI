#!/bin/bash
cd /home/smkim/runner/socket_server
tmux new -s mes -d 'python mes_srv.py'
tmux new -s meter -d 'python meter_srv.py'
cd /home/smkim/runner/mqtt
tmux new -s mqtt -d 'python ss_mqtt_sub.py'
tmux new -s mqttcn -d 'python sscn_mqtt_sub.py'
