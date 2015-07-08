
# since the rsa key was coppied, make sure not to allow password ssh
word='#PasswordAuthentication[[:space:]]*yes'
rep='PasswordAuthentication no'
sed -i "s/${word}/${rep}/g" /etc/ssh/sshd_config


# restart ssh
service ssh restart

# configure ufw to only allow
# 123 udp for ntp
ufw allow 123/udp
# 2200 tcp for ssh
ufw allow 2200/tcp
# 80 tcp for http
ufw allow 80/tcp
# enable ufw
ufw enable

# install ntp
apt-get install -y ntp

# install fail2ban - defense against brute force attacks
apt-get install -y fail2ban

# make a conf backup
cp /etc/fail2ban/jail.conf /etc/fail2ban/jailconf.local

# set bantime to 1800 sec
word="bantime[[:space:]]*=[[:space:]][[:digit:]]*"
rep="bantime = 1800"
sed -i "s/${word}/${rep}/" /etc/fail2ban/jail.local

# set the email to my email
word="destemail[[:space:]]*=[[:space:]]root@localhost"
rep="destemail = robert@ravdev.com"
sed -i "s/${word}/${rep}/" /etc/fail2ban/jail.local

# set the sender to some recongnizable name
word="sendername[[:space:]]*=[[:space:]]Fail2Ban"
rep="sendername = FlutterHub_Server_Fail2Ban"
sed -i "s/${word}/${rep}/" /etc/fail2ban/jail.local

# change the ssh port in jail.local
sed -i "/\[ssh\]/{N
                       N
                       N
                       s/\(\[ssh\]\n.*\n.*\)\n.*/\1\nport     = 2200/ }" /etc/fail2ban/jail.local

# change the default action to also send an email in case of failed login attempts
sed -i "s/\(action_)/(action_mwl)/" /etc/fail2ban/jail.local

# install sendmail
apt-get install -y sendmail


# system monitoring tools
apt-get install -y python-pip build-essential python-dev
pip install Glances

# install docker
# make sure wget is installed
apt-get install -y wget

# make sure the key is added to apt
wget -qO- https://get.docker.com/gpg | apt-key add

# Get the latest Docker package
wget -qO- https://get.docker.com/ | sh

# build docker images
# build application image
docker build -t flutterhub:v1 /src/.
# build database image
docker build -t flutterhubdb:v1 /src/db/.

# create data volume
docker create -v /etc/postgresql -v /var/log/postgresql -v /var/lib/postgresql --name dbdata flutterhubdb:v1 /bin/true
# start database container with the volumes from dbdata
docker run --restart=always -d --volumes-from dbdata --name db flutterhubdb:v1
# start application container linked to the database container
# add the apache log directory as a volume in the container in order to be able to monitor the logs from the host machine
docker run --restart=always -d -v /var/log/apache2:/var/log/apache2 -p 80:80 --name web --link db:db flutterhub:v1
