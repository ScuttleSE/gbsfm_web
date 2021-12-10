#FROM python:3.8-bullseye
FROM tiangolo/uwsgi-nginx:python3.8

WORKDIR /srv/pydj
RUN ls -la
ENV UWSGI_INI /srv/pydj/pydj_uwsgi.ini

#RUN pip install --upgrade pip
#RUN pip install pipenv
#RUN ls
#RUN pipenv install --system
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY nginx.conf /app
#COPY run.sh /
#CMD /run.sh