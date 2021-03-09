#!/usr/bin/env python3
# -*- coding: utf-8

from linebot import (
    LineBotApi, WebhookHandler
)
access_token = 'dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU='
line_bot_api = LineBotApi('{my_access_token}'.format(my_access_token=access_token))
rich_menus_id = 'richmenu-18c77570d5310069d934313683a2b688'

line_bot_api.delete_rich_menu('{my_rich_menus_id}'.format(my_rich_menus_id=rich_menus_id))
