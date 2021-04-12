#!/bin/bash

PID=`ps -ef|grep "python manage.py ftp"|grep -v grep|awk '{print $2}'`
echo $PID
kill -9 $PID
