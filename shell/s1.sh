# assumes openssh already installed
# assume git installed and these scripts are source is cloned in /src/
# run sudo su before executing this script

# update all the packages
apt-get update

# upgrade all
apt-get upgrade

# let packages auto-update
apt-get install unattended-upgrades

# enable auto-update
dpkg-reconfigure -plow unattended-upgrades

# configure time-zone data
dpkg-reconfigure tzdata


# add a new user grader
adduser --gecos "" grader

# make a copy of the sudoers file to the temp /etc/sudoers.tmp
cp /etc/sudoers /etc/sudoers.tmp

# change sudoers file
# erase the root   ALL=(ALL) ALL
word='root[[:space:]]*ALL=(ALL:ALL)[[:space:]]ALL'
# Replace it with grader
rep="grader     ALL=(ALL:ALL) NOPASSWD: ALL"

sed -i "s/${word}/${rep}/" /etc/sudoers.tmp

# remove the necessity for password for sudo
word='%sudo[[:space:]]*ALL=(ALL:ALL)[[:space:]]ALL'
rep='%sudo ALL=(ALL:ALL) NOPASSWD: ALL'

sed -i "s/${word}/${rep}/g" /etc/sudoers.tmp

mv /etc/sudoers.tmp /etc/sudoers

# make the sudoers readonly
chmod 0444 /etc/sudoers

# make a backup of sshd_config
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

#change port from 22 to 2200
word='Port[[:space:]]22'
rep='Port 2200'
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
service ssh restart


# here we break and wait for the user to upload the rsa public key to the server
echo 'Please Upload the RSA private key to the server before running the next script'
echo 'run ssh-keygen on your machine'
echo 'ssh-copy-id -p 2200 -i /users/username/.ssh/udacity.rsa grader@ip'
echo 'ssh -p 2200 -i /users/username/.ssh/udacity.rsa grader@ip'


