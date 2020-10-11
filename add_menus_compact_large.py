#!/usr/bin/env python3
# -*- coding: utf-8

import requests
import json

access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
headers = {"Authorization":"Bearer {my_access_token}".format(my_access_token=access_token),"Content-Type":"application/json"}

body = {
    "size": {"width": 2500, "height": 843},
    "selected": "true",
    "name": "main_menu",
    "chatBarText": "主選單",
    "areas":[
        {
          "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
          "action": {"type": "message", "text": "music"}
        },
        {
          "bounds": {"x": 834, "y": 0, "width": 834, "height": 843},
          "action": {"type": "message", "text": "information"}
        },
        {
          "bounds": {"x": 1669, "y": 0, "width": 833, "height": 843},
          "action": {"type": "message", "text": "IOT"}
        }
    ]
  }

req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu', 
                       headers=headers,data=json.dumps(body).encode('utf-8'))

print(req.text)
