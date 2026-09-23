#!/bin/bash
# Share internet from laptop to B2 robot via LAN
# Run with: sudo ./share_internet.sh

set -e

WIFI_INTERFACE="wlp3s0"
LAN_INTERFACE="enx00e04c6804d9"

echo "Enabling IP forwarding..."
sysctl -w net.ipv4.ip_forward=1

echo "Setting up NAT (routing traffic from $LAN_INTERFACE through $WIFI_INTERFACE)..."
iptables -t nat -A POSTROUTING -o "$WIFI_INTERFACE" -j MASQUERADE
iptables -A FORWARD -i "$LAN_INTERFACE" -o "$WIFI_INTERFACE" -j ACCEPT
iptables -A FORWARD -i "$WIFI_INTERFACE" -o "$LAN_INTERFACE" -m state --state RELATED,ESTABLISHED -j ACCEPT

echo "Done! Internet sharing enabled."
echo ""
echo "Now run on the robot (ssh b2):"
echo "  sudo ip route add default via 192.168.123.51"
echo "  echo 'nameserver 8.8.8.8' | sudo tee /etc/resolv.conf"
echo "  ping -c 3 google.com"
