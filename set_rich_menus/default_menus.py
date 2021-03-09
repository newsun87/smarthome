#!/usr/bin/env python3
# -*- coding: utf-8

import requests
access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
rich_menus_id = 'richmenu-28169650f8dbd8ea85c406074ccd10b8'

headers = {"Authorization":"Bearer {my_access_token}".format(my_access_token=access_token),"Content-Type":"application/json"}

req = requests.request('POST', 'https://api.line.me/v2/bot/user/all/richmenu/{my_rich_menus_id}'.format(my_rich_menus_id=rich_menus_id), headers=headers)

print(req.text)
