#!/bin/bash
sudo kill $(pidof ngrok)
ngrok http 5000 > /dev/null& 
sleep 3
#���o���浲�G(��})���ܼ�
URL4040=$(curl -s localhost:4040/api/tunnels | awk -F"https" '{print $2}' | awk -F"//" '{print $2}' | awk -F'"' '{print $1}')
ACCESS_TOKEN="HgPlOKPR695mnmzWg9R7rOXsNx7gwl0ddTIqkUDHCLs" #Line Notify �����ҽX
message="https://"$URL4040  #�ǤJ�v���ɪ����|
curl https://notify-api.line.me/api/notify -X POST \
   -H "Authorization: Bearer $ACCESS_TOKEN" \
   -F "message=$message"  
