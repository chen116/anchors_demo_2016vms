#1/bin/sh
set -x
sudo ip addr flush dev br-ex 
sudo ip addr add 172.16.91.138/24 dev br-ex brd 172.16.91.255
sudo ip link set br-ex up
sudo ip link set eth0 up
sudo ip addr flush dev eth0
ip r add default via 172.16.91.2

# This allows access directly to the VM without using floating IPs
sudo ip route add 192.168.100.0/24 via 172.16.91.245

