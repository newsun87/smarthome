#!/bin/bash
ngrok http 5000& 
sleep 2
#���o���浲�G(��})���ܼ�
URL4040=$(curl -s localhost:4040/api/tunnels | awk -F"https" '{print $2}' | awk -F"//" '{print $2}' | awk -F'"' '{print $1}')
ACCESS_TOKEN="MMkiyW15qX19JAYquvr1pvET8As9lMEslY40P0C6QZ3" #Line Notify �����ҽX
message="https://"$URL4040  #�ǤJ�v���ɪ����|
curl https://notify-api.line.me/api/notify -X POST \
   -H "Authorization: Bearer $ACCESS_TOKEN" \
   -F "message=$message"  
