FROM ubuntu:14.04
MAINTAINER Robert Avram robert@ravdev.com

RUN \
    apt-get -qqy update && \
    apt-get -qqy install python-flask python-sqlalchemy && \
    apt-get -qqy install postgresql python-psycopg2 &&\
    apt-get -qqy install python-pip && \
    apt-get -qqy install python2.7-dev && \
    apt-get -qqy install libjpeg-dev && \
    apt-get -qqy install zlib1g-dev && \
    pip install pillow && \
    pip install oauth2client && \
    pip install dicttoxml
    


ADD . /src

WORKDIR /src

EXPOSE 5000

CMD ["python", "application.py"]