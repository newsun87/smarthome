#!/usr/bin/env python3
# -*- coding: utf-8

from linebot import (
    LineBotApi, WebhookHandler
)
access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi('{my_access_token}'.format(my_access_token=access_token))
rich_menus_id = 'richmenu-45024f77d44b3e3d128c3e41429314fa'

with open("../rich_menus/main_menu1.jpg", 'rb') as f:
  line_bot_api.set_rich_menu_image("{my_richmenu_id}".format(my_richmenu_id=rich_menus_id ), "image/jpeg", f)
