FROM ubuntu:14.04
MAINTAINER Robert Avram robert@ravdev.com


RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8

RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ precise-pgdg main" > /etc/apt/sources.list.d/pgdg.list

RUN apt-get update && apt-get install -y python-software-properties software-properties-common postgresql-9.3 postgresql-client-9.3 postgresql-contrib-9.3

USER postgres

RUN    /etc/init.d/postgresql start &&\
    psql --command "CREATE USER catalog WITH CREATEDB LOGIN PASSWORD 'funnymonkeys';" &&\
    createdb -O catalog catalog &&\
    psql -U postgres -d catalog -c "REVOKE ALL ON SCHEMA public FROM public;" &&\
    psql -U postgres -d catalog -c "GRANT ALL ON SCHEMA public TO catalog;"
    

# Adjust PostgreSQL configuration so that remote connections to the
# database are possible. These connections are only possible from within other docker containers. 
# The ports are not exposed to the host machine unless specified so whe running the container. 
# Technically remote connections are imposible to the db
RUN echo "host all  all    0.0.0.0/0  md5" >> /etc/postgresql/9.3/main/pg_hba.conf

# And add ``listen_addresses`` to ``/etc/postgresql/9.3/main/postgresql.conf``
RUN echo "listen_addresses='*'" >> /etc/postgresql/9.3/main/postgresql.conf

# RUN sed -i "s|data_directory[[:space:]]=.*|data_directory = '/dbdata'|" /etc/postgresql/9.3/main/postgresql.conf
# Expose the PostgreSQL port
EXPOSE 5432

# Add VOLUMEs to allow backup of config, logs and databases
VOLUME  ["/etc/postgresql", "/var/log/postgresql", "/var/lib/postgresql"]


CMD ["/usr/lib/postgresql/9.3/bin/postgres", "-D", "/var/lib/postgresql/9.3/main", "-c", "config_file=/etc/postgresql/9.3/main/postgresql.conf"]
#CMD ["/usr/lib/postgresql/9.3/bin/postgres", "-D", "/dbdata", "-c", "config_file=/etc/postgresql/9.3/main/postgresql.conf"]
# to start db manually inside the container
# /usr/lib/postgresql/9.3/bin/postgres -D /var/lib/postgresql/9.3/main -c config_file=/etc/postgresql/9.3/main/postgresql.conf >/var/log/postgresql/logfile 2>&1 &