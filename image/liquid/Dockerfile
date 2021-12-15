FROM ubuntu:latest
MAINTAINER Gustav Almstrom <gustav@almstrom.org>

RUN apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get -y install bash icecast2 nano libfdkaac-ocaml-dynlink python3 python3-pip python3-dev default-libmysqlclient-dev build-essential wget && \
    pip3 install -U mysqlclient && \
    useradd liq && \
    mkdir /home/liq && \
    chsh liq -s /bin/bash && \
    chown -R liq:liq /home/liq && \
    wget -O /root/liq.deb https://github.com/savonet/liquidsoap/releases/download/v1.4.3/liquidsoap-v1.4.3_1.4.3-ubuntu-focal-amd64-1_amd64.deb && \
    apt-get install -y /root/liq.deb
COPY --chown=liq:liq bees.mp3 /home/liq/bees.mp3
COPY icecast.xml /etc/icecast2/icecast.xml
COPY entrypoint.sh /root/entrypoint.sh
COPY --chown=liq:liq ices.liq /home/liq/ices.liq
COPY --chown=liq:liq getsong.py /home/liq/getsong.py
COPY --chown=liq:liq streampw.py /home/liq/streampw.py

#CMD tail -f /dev/null

ENTRYPOINT ["/bin/bash", "/root/entrypoint.sh"]