#!/bin/bash
# Enable internet access on the B2 robot via laptop gateway
# Run with: sudo ./robot_enable_internet.sh

set -e

LAPTOP_IP="192.168.123.51"

echo "Adding default route through laptop ($LAPTOP_IP)..."
ip route add default via "$LAPTOP_IP"

echo "Setting DNS server (Google's public DNS)..."
echo "nameserver 8.8.8.8" > /etc/resolv.conf

echo "Verifying internet access..."
ping -c 3 google.com

echo "Done! Internet access enabled."
