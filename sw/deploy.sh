#!/bin/bash
set -e
cd "$(dirname "$0")"
echo '=== Развёртывание панели замены коммутаторов ==='
apt-get update && apt-get install -y python3-pip snmp sshpass traceroute || true
pip3 install flask flask-cors || apt-get install -y python3-flask python3-flask-cors || true
( crontab -l 2>/dev/null | grep -v 'swh.py' ; echo "* * * * * cd $PWD && (curl -s -o /dev/null --max-time 3 http://localhost:9500/ || nohup python3 swh.py >> swh.log 2>&1 &)" ; echo "@reboot sleep 5 && cd $PWD && nohup python3 swh.py >> swh.log 2>&1 &" ) | crontab -
nohup python3 swh.py > swh.log 2>&1 &
sleep 3
echo '=== Готово: http://<IP_ЭТОГО_СЕРВЕРА>:9500/ ==='
echo 'PIN прежний. Ollama-модели при необходимости поставьте отдельно на новом сервере.'
