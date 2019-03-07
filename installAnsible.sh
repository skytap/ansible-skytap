#!/bin/sh

# awk -F= '/^NAME/{print $2}' /etc/os-release

if [ -f /etc/redhat-release ]; then
  sudo yum update
  sudo yum -y install epel-release
  sudo yum -y install ansible
  sudo yum -y install sshpass
  #sudo yum -y install git
fi

if [ -f /etc/lsb-release ]; then
  sudo apt-get update -y
  sudo apt-get install software-properties-common
  sudo apt-add-repository ppa:ansible/ansible
  sudo apt-get update -y
  sudo apt-get install ansible -y
  sudo apt-get install sshpass -y
  #sudo apt-get install git -y
fi

sudo groupadd -g 5001 ansible
sudo usermod -a -G ansible skytap

ssh-keygen -t rsa -b 4096

read -p "Please insert the PSTools asset in the CD Drive and then press Enter" CD
sudo mount /dev/cdrom /media/cdrom
mkdir ansiblebase
cp -R /media/cdrom/* ansiblebase






