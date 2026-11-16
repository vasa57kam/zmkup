#!/bin/bash
DIR="${1:-$(cd "$(dirname "$0")" && pwd)}"
echo "=== Полное удаление панели в $DIR ==="
pkill -f "python3 $DIR/swh.py" 2>/dev/null
pkill -f "python3 swh.py" 2>/dev/null
sleep 2
( crontab -l 2>/dev/null | grep -v 'swh.py' ) | crontab - 2>/dev/null
if [ "$FULL" == "1" ]; then
  echo '=== Сносим поставленные пакеты ==='
  apt-get remove -y snmp sshpass traceroute 2>/dev/null
  pip3 uninstall -y flask flask-cors 2>/dev/null
fi
cd /tmp
rm -rf "$DIR"
rm -f /tmp/swh_uninstall.sh
echo '=== Панель удалена полностью. Сервер как до установки. ==='
