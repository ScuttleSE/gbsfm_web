FROM python:3.8-bullseye


WORKDIR /var/www
RUN pip install --upgrade pip
RUN pip install pipenv
COPY run.sh /
CMD /run.sh