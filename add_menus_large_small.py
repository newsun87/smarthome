#!/usr/bin/env python3
# -*- coding: utf-8

import requests
import json

access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
headers = {"Authorization":"Bearer {my_access_token}".format(my_access_token=access_token),"Content-Type":"application/json"}

body = {
    "size": {"width": 800, "height": 540},
    "selected": "true",
    "name": "information_menu",
    "chatBarText": "資訊選單",
    "areas":[
        {
          "bounds": {"x": 0, "y": 0, "width": 266, "height": 270},
          "action": {"type": "message", "text": "main_menu"}
        },
        {
          "bounds": {"x": 267, "y": 0, "width": 267, "height": 270},
          "action": {"type": "postback", "data": "weather"}
        },
        {
          "bounds": {"x": 535, "y": 0, "width": 267, "height": 270},
          "action": {"type": "postback", "data": "pm25"}
        },
        {
          "bounds": {"x": 0, "y": 271, "width": 266, "height": 270},
          "action": {"type": "postback", "data": "stock"}
        },
        {
          "bounds": {"x": 267, "y": 271, "width": 267, "height": 270},
          "action": {"type": "postback", "data": "AIImage"}
        },
        {
          "bounds": {"x": 535, "y": 271, "width": 267, "height": 270},
          "action": {"type": "message", "text": "other"}
        }        
    ]
  }

req = requests.request('POST', 'https://api.line.me/v2/bot/richmenu', 
                       headers=headers,data=json.dumps(body).encode('utf-8'))

print(req.text)
