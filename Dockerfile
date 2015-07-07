FROM ubuntu:14.04
MAINTAINER Robert Avram robert@ravdev.com

RUN \
    apt-get -y update && \
    apt-get -y upgrade && \
    apt-get -y install python-flask python-sqlalchemy && \
    apt-get -y install python-psycopg2 &&\
    apt-get -y install python-pip && \
    apt-get -y install python2.7-dev && \
    apt-get -y install libjpeg-dev && \
    apt-get -y install zlib1g-dev && \
    apt-get -y install apache2 && \
    apt-get -y install python-setuptools &&\
    apt-get -y install libapache2-mod-wsgi && \
    pip install pillow && \
    pip install oauth2client && \
    pip install dicttoxml
    

RUN sed "s/exit[[:space:]]101/exit 0/" /usr/sbin/policy-rc.d
    
RUN service apache2 restart
    
ADD flaskapp.wsgi /var/www/FlaskApp/
ADD FlaskApp /var/www/FlaskApp/FlaskApp/
ADD FlaskApp.conf /etc/apache2/sites-available/

RUN a2ensite FlaskApp
RUN a2dissite 000-default




VOLUME /var/log/apache2/


WORKDIR /var/www/FlaskApp/FlaskApp


EXPOSE 80

COPY ./app-entrypoint.sh /
RUN chmod +x /app-entrypoint.sh
ENTRYPOINT /app-entrypoint.sh


