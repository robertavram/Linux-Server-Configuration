sed -i "s/db_container[[:space:]].*/db_container = '${DB_PORT_5432_TCP_ADDR}:5432'/" /var/www/FlaskApp/FlaskApp/other_info.py
sed -i "s|app_files.*|app_files = '${PWD}/'|" /var/www/FlaskApp/FlaskApp/other_info.py

/usr/sbin/apache2ctl -D FOREGROUND