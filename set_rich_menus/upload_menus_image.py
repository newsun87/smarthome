#!/usr/bin/env python3
# -*- coding: utf-8

from linebot import (
    LineBotApi, WebhookHandler
)
access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi('{my_access_token}'.format(my_access_token=access_token))
rich_menus_id = 'richmenu-0fd87fec32dfc540ed39df882c4afc32'

with open("../rich_menus/iot.jpg", 'rb') as f:
  line_bot_api.set_rich_menu_image("{my_richmenu_id}".format(my_richmenu_id=rich_menus_id ), "image/jpeg", f)
