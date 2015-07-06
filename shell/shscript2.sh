# make a backup of sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

#change port from 22 to 2200
word='/<Port[[:space:]]22/>'
rep='Port 2200'
sed -i "s/${word}/${rep}/g" /etc/ssh/sshd_config

#make sure not to allow password auth
word='#PasswordAuthentication[[:space:]]*yes'
rep='PasswordAuthentication no'
sed -i "s/${word}/${rep}/g" /etc/ssh/sshd_config

# add grader to the list of AllowedUsers for ssh
if grep -q "AllowUsers" /etc/ssh/sshd_config; then
    word='AllowUsers'
    rep='AllowUsers grader'
    sed -i "s/${word}/${rep}/" /etc/ssh/sshd_config
else 
    echo "AllowUsers grader" >> /etc/ssh/sshd_config
fi

# restart ssh
service sshd restart

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
apt-get install ntp

# install fail2ban
apt-get install fail2ban

# make a conf backup
cp /etc/fail2ban/jail.conf /etc/fail2ban/jailconf.local

word="bantime[[:space:]]*=[[:space:]][[:digit:]]*"
rep="bantime = 1800"
sed -i "s/${word}/${rep}/" /etc/fail2ban/jail.local

word="destemail[[:space:]]*=[[:space:]]root@localhost"
rep="destemail = robert@ravdev.com"
sed -i "s/${word}/${rep}/" /etc/fail2ban/jail.local

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
apt-get install sendmail



# install docker
# make sure wget is installed
apt-get install wget

# make sure the key is added to apt
wget -qO- https://get.docker.com/gpg | sudo apt-key add

# Get the latest Docker package
wget -qO- https://get.docker.com/ | sh

# might have to do this:
#word='DEFAULT_FORWARD_POLICY="DROP"'
#rep='DEFAULT_FORWARD_POLICY="ACCEPT"'
#sed -i "s/${word}/${rep}/" /etc/default/ufw
#sudo ufw reload

#Postgresql container


# Application
# build docker image
docker build -t flutterhub:v1 /src/.
docker build -t flutterhubDB:v1 /src/db/.


docker create -v /dbdata --name dbdata flutterhubDB:v1 /bin/true
docker run -d --volumes-from dbdata --name db flutterhubDB:v1
docker run -d -v /var/log/apache2:/var/log/apache2 -p 80:80 --name web --link db:db flutterhub:v1

# start the application
#sudo docker run -d -v /var/log/apache2:/var/log/apache2 -p 80:80 flutterhub:v1

# when it doesnt autorun
# sudo docker run -d -it -v /var/log/apache2:/var/log/apache2 -p 80:80 --name web flutterhub:v1
# sudo docker exec -d web service apache2 restart

# run the db container
#sudo docker run  -d myps:v2

# start the application and connect it to the db
# sudo docker run -d -v /var/log/apache2:/var/log/apache2 -p 80:80 --name web --link db:db flutterhub:v1


#
#
# create auto update script
# create docker for auto-backup of data to tar
# auto system check for app if it's still working
# 












#cat <<EOT >> greetings.txt
#AllowUser 
#line 2
#EOT