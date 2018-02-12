#!/bin/sh
ssh-keygen -t rsa1 -f /etc/ssh/ssh_host_rsa_key
ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key
