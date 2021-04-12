#!/bin/sh

# - Ensure no relevent processes are still running:

echo "(re)starting gbsfm. This must be run in the root pydj directory!"

echo "Starting venv"
source bin/activate 

killall sc_serv
echo "sc_serv killed"
killall ices
echo "ices killed"

echo "Setting up static files directory..."
python manage.py collectstatic
echo "Starting the main web interface"
uwsgi --ini server_config/pydj_uwsgi.ini
cd ./sc_serv
nohup ./sc_serv sc_serv.conf &
echo "sc_serv started"















##sleep 1
##killall manage.py
##sleep 1
##killall python
#echo "All python-related processes killed"
##sleep 1
##sleep 1


##python manage.py runfcgi method=prefork socket=/tmp/fcgi.sock maxrequests=500 maxchildren=7

#echo "Starting the main web interface"

#echo "Main web interface started"
##sleep 1  

##nohup python manage.py ftp &
#echo "FTP-server started"
##sleep 1

#echo "Now start the stream using the webpage"
##deactivate
