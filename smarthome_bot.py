# -*- coding: UTF-8 -*-

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
from flask import render_template 
import paho.mqtt.client as mqtt
from datetime import datetime
import os
import json
import random
import time
import firebase_admin
import requests
from firebase_admin import credentials
from firebase_admin import db
import subprocess
import configparser

config = configparser.ConfigParser()
config.read('smart_home.conf')

#取得通行憑證
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : 'https://line-bot-test-77a80.firebaseio.com/'
})

weather_url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore'
#apikey = 'CWB-A247B989-2950-4B3B-8665-1D92E72BC2AB'
apikey = config.get('weather_url', 'apikey')

#access_token = "dWhp1zz+Irv8ktCX06FWQFpF0BwSrzs5VSBUK/Fp7NLG0kBAVZe2VTwko8d0KO3ajTOw/jlwJPtpPYe+dVhN6G0eWwbdoLbECjMEbQQriKKk/imWqL8mA19YOiF9JaGwD9gmmpnEhLjwQvXek8FkDwdB04t89/1O/w1cDnyilFU="
#channel_secret = "b396a51f336580d711303f8adf09816f"
access_token = config.get('linebot', 'access_token')
channel_secret = config.get('linebot', 'channel_secret')

camera_url = 'unknown'  

app = Flask(__name__)

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret) 

@app.route('/')
def showIndexPage():
 return render_template('index.html')
 
@app.route('/translate')
def showTranslateHelpPage():
 return render_template('translator_help.html') 
 
@app.route('/music')
def showMusicHelpPage():
 return render_template('music_help.html')  
 
@app.route('/appliances')
def showAppliancesHelpPage():
 return render_template('appliances_help.html')   

@app.route('/airbox')
def showAirboxHelpPage():
 return render_template('airbox_help.html')   

@app.route('/getdata', methods=['GET', 'POST']) 
def getData():
  with open('record.txt','r', encoding = "utf-8") as fileobj:
    word = fileobj.read().strip('\n')
    print(word)  
  return word

# 監聽所有來自 /callback 的 Post Request
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    return 'OK'

# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
  ref = db.reference('/') # 參考路徑 	
  userId = 'ypl'
  users_userId_ref = ref.child('youtube_music/'+ userId)  
  global nlu_text  
  if event.message.text.startswith('【youtube url】'):
      new_message = event.message.text.lstrip('【youtube url】')
      line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text="馬上播放 " + new_message))
      client.publish("youtube_url", new_message, 0, True) #發佈訊息
      
  elif event.message.text.startswith('https://youtube.com/watch?'):      
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="馬上播放 " + event.message.text))      
      client.publish("youtube_url", event.message.text, 0, True) #發佈訊息
      
  elif event.message.text.startswith('https://www.youtube.com/watch?'):      
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="馬上播放 " + event.message.text))      
      client.publish("youtube_url", event.message.text, 0, True) #發佈訊息
      
  elif event.message.text.startswith('weather'): 
      split_array = event.message.text.split("~")
      cityname = split_array [1]
      weather_info = get_weather(cityname)
      message = get_weather_state(weather_info, cityname)      
      line_bot_api.reply_message(event.reply_token, message)
      
  elif event.message.text.startswith('infrared'):
      split_array = event.message.text.split("~")
      device = split_array [1]      
      if device == 'sound':     
        message = switch_infrared_device(0)
      elif device == 'tv':     
        message = switch_infrared_device(1) 
      elif device == 'ovo':     
        message = switch_infrared_device(2)
      elif device == 'fan':     
        message = switch_infrared_device(5)                     
      line_bot_api.reply_message(event.reply_token, message)          
	          
  elif event.message.text.startswith('pm25'): 
      split_array = event.message.text.split("~")
      cityname = split_array [1]
      pm25_info = get_pm25(cityname)
      message = TextSendMessage(text="["+cityname + "] 空氣品質： " +  pm25_info)
      message = [
	      TextSendMessage(text="["+cityname + "] 空氣品質： " +  pm25_info),
	      TextSendMessage(text="空氣品質監測網： " +  "https://liff.line.me/1654118646-8q4qo3vy")
	  ]      
      line_bot_api.reply_message(event.reply_token, message)  
      
  elif event.message.text.startswith('volume'): 
      split_array = event.message.text.split("~")
      volume = int(split_array [1])
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child('smarthome/config')      
      users_userId_ref.update({'volume':volume})       
      message = TextSendMessage(text = '音量設定為： ' + split_array [1] + '%')
      line_bot_api.reply_message(event.reply_token, message)  
 
  elif event.message.text == 'music_menu':
	  buttons_template_message = music_menu()
	  line_bot_api.reply_message(event.reply_token, buttons_template_message)
	  
  elif event.message.text == 'appliances_menu':
	  buttons_template_message = appliances_menu()	  
	  line_bot_api.reply_message(event.reply_token, buttons_template_message)
	  
  elif event.message.text.startswith('plug'):
     split_array = event.message.text.split("~")
     device = split_array [1]
     if device == 'livingroom':
       deviceSN = '10792465'
     elif device == 'bedroom':
       deviceSN = '10796572'  
     message = switch_plug(deviceSN)           
     line_bot_api.reply_message(event.reply_token, message)
       
  elif event.message.text == 'airbox_menu':
	  buttons_template_message = airbox_menu()
	  line_bot_api.reply_message(event.reply_token, buttons_template_message)  
	  
  elif event.message.text == 'live_menu':
	  buttons_template_message = live_menu()
	  line_bot_api.reply_message(event.reply_token, buttons_template_message)	  
	  
  elif event.message.text == 'music_play':
      ref = db.reference('/') # 參考路徑      
      videourl = users_userId_ref.get()['videourl'] 
      line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="馬上播放 " + videourl))
      client.publish("youtube_url", videourl, 0, True)
      
  elif event.message.text == '取消動作':
	  message = TextSendMessage(text="沒有問題!")	  
	  line_bot_api.reply_message(event.reply_token, message)    
      
  elif event.message.text == 'player_restart':
      confirm_template_message = TemplateSendMessage(
        alt_text = "這是一個確認樣板",
        template = ConfirmTemplate(
        text = "你確定要重新開機?",
     actions =  [
        PostbackAction (
          label = '確認',
          display_text = '準備重新開機.....',
          data = 'restart'),
        MessageAction(
          label = '否',
          text = '取消動作') 
       ]
     ))
 
      line_bot_api.reply_message(
        event.reply_token, confirm_template_message)     
      
  elif event.message.text == '歌曲資訊':      
      users_userId_ref = ref.child('youtube_music/'+ userId)
      videourl = users_userId_ref.get()['videourl']   	        
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="歌曲資訊 " + videourl)) 
      
  elif event.message.text == 'menu':
      QuickReply_text_message = getQuickReply_music_work()      
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 
      
  elif event.message.text == 'favor':
      QuickReply_text_message = getQuickReply_music()      
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 
          
  elif event.message.text == 'help':
      with open('help.txt', mode='r', encoding = "utf-8") as f:
        content = f.read()
        print(content)
        message = TextSendMessage(text=content)      
        line_bot_api.reply_message(event.reply_token, message)
        
  elif event.message.text == 'setup':
      buttons_template_message = setup_menu()
      line_bot_api.reply_message(event.reply_token, buttons_template_message)
      
  elif event.message.text.startswith('翻譯'): 
      split_array = event.message.text.split("~")
      text = split_array [1]      
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child('smarthome/config/lang')      
      language = users_userId_ref.get()
      print('language...', language)
      message = translation(text, language)      
      line_bot_api.reply_message(event.reply_token, message)  
      
  elif event.message.text.startswith('lang'): 
      split_array = event.message.text.split("~")
      language = split_array [1]
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child('smarthome/config')
      if language == '英文':
        lang_text = 'en'        
      elif language == '日文':
        lang_text = 'ja'        
      elif language == '韓文':
        lang_text = 'ko'
      elif language == '泰文':
        lang_text = 'th'
      elif language == '越南文':
        lang_text = 'vi'
      elif language == '法文':
        lang_text = 'fr'
      users_userId_ref.update({'lang':lang_text})       
      message = TextSendMessage(text = '語言設定為： ' + language)
      line_bot_api.reply_message(event.reply_token, message)          
                   
  else:	               
      message = nlu(event.message.text)      
      line_bot_api.reply_message(event.reply_token, message)   

from translate import Translator   
baseurl = 'https://smarthome-123.herokuapp.com/static/'
def translation(text, language):       
    translator = Translator(from_lang = 'zh-Hant', to_lang = language)
    translation = translator.translate(text)
    #將中文text翻成英文，並去掉亂碼
    #translation = translator.translate(text).replace("&#39;","")        
    print('translation result: ',translation)
    translation_modify = translation.replace(" ", "")
    #將英文文字 translation_modify 轉成語音(STT)
    stream_url ='https://google-translate-proxy.herokuapp.com/api/tts?query=' \
           + translation + '&language=' + language 
    r = requests.get(stream_url, stream=True)
    with open('./static/stream.m4a', 'wb') as f:
       try:
          for block in r.iter_content(1024):
              f.write(block)
       except KeyboardInterrupt:
          pass          
    message = [
          TextSendMessage(text = '翻譯文字： ' + translation),
          AudioSendMessage(
		    original_content_url = baseurl + 'stream.m4a',
		    duration = 10000
		  )
	]    		
    return message

# 處理 postback 事件
@handler.add(PostbackEvent)
def handle_postback_message(event):
    postBack = event.postback.data
    print('poskback......', postBack)
    if postBack == 'volume':
       QuickReply_text_message = getQuickReply_volume()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)   
                   
    elif postBack == 'weather':
       QuickReply_text_message = getQuickReply_weather()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 
       
    elif postBack == 'pm25':
       QuickReply_text_message = getQuickReply_pm25() # 取得 pm25 快速選單      
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)
       
    elif postBack == 'plugs':
       imagecarousel_template_message = TemplateSendMessage(
          alt_text = '我是插座選單模板',  # 通知訊息的名稱
          template = ImageCarouselTemplate(           
          columns = [               
                ImageCarouselColumn(
                    image_url = 'https://i.imgur.com/MMblDTQ.png',  # 呈現圖片                    
                    action = MessageAction(
                            label = '客廳',  # 顯示的文字
                            text = 'plug~livingroom'
                    )
                 ),
                ImageCarouselColumn( 
                    image_url = 'https://i.imgur.com/MMblDTQ.png',   
                    action = MessageAction(
                        label = '寢室',
                        text =  'plug~bedroom'
                    )
                )
              ]
           )
        )
       line_bot_api.reply_message(event.reply_token, imagecarousel_template_message)       
       
    elif postBack == 'infrared':
       imagecarousel_template_message = TemplateSendMessage(
          alt_text = '我是遙控器選單模板',  # 通知訊息的名稱
          template = ImageCarouselTemplate(           
          columns = [ 
                ImageCarouselColumn(
                    image_url = 'https://i.imgur.com/wX5PzH5.jpg', # 呈現圖片                             
                    action = MessageAction(
                            label = '風扇電源',  # 顯示的文字
                            text = 'infrared~fan'
                    )
                 ),              
                ImageCarouselColumn(
                    image_url = 'https://i.imgur.com/wtcS4dh.png', # 呈現圖片                             
                    action = MessageAction(
                            label = '音響電源',  # 顯示的文字
                            text = 'infrared~sound'
                    )
                 ),
                ImageCarouselColumn( 
                    image_url = 'https://i.imgur.com/Y756BCk.png',   
                    action = MessageAction(
                        label = '電視電源',
                        text =  'infrared~tv'
                    )
                ),
                ImageCarouselColumn( 
                    image_url = 'https://i.imgur.com/LnaTWFZ.png',   
                    action = MessageAction(
                        label = '機上盒電源',
                        text =  'infrared~ovo'
                    )
                )
              ]
           )
        )
       line_bot_api.reply_message(event.reply_token, imagecarousel_template_message) 
            
    elif postBack == 'stock':
        result = subprocess.getoutput("sh ./twstockGet.sh")
        print(result)
        bubble = getFlex_stock(result)
        message = FlexSendMessage(alt_text = "彈性配置範例", contents = bubble)        
        line_bot_api.reply_message(event.reply_token, message) 
        
    elif postBack == 'camera':
      QuickReply_text_message = getQuickReply_camera_work() # 取得 pm25 快速選單      
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message)
                    
        #message = TextSendMessage(text = camera_url)        
        #line_bot_api.reply_message(event.reply_token, message)           
    
    elif postBack == 'airbox':
        URL_API = '{host_url}/{SN}/CONFIG/{KEY}'.format( 
		   host_url = 'https://service.wf8266.com/api/mqtt', 
		   SN = '5440973', 
		   KEY = 'ADu2FL4V7LdfprFNL9xpKkbVw873')
        try: 
            response = requests.get(URL_API,timeout = 5)            
            resObj = json.loads(response.text)
            print('Temperature： ',  resObj['data']['Message'][0]['C'] ) # 取出溫度
            print('Humidity： ',  resObj['data']['Message'][0]['H'] ) # 取出濕度
            print('PM2.5： ',  resObj['data']['Message'][0]['PMAT25'] ) 
            airbox_data = str(resObj['data']['Message'][0]['C']) + '~' \
                      + str(resObj['data']['Message'][0]['H']) + '~' \
                      + str(resObj['data']['Message'][0]['PMAT25'])
            bubble = getFlex_airbox(airbox_data) 
            message = FlexSendMessage(alt_text = "彈性配置範例", contents = bubble)                        
        except requests.exceptions.Timeout as e:
            airbox_data = 'error'
            message = TextSendMessage(text = "空氣盒子未連線.....")           
                  
        line_bot_api.reply_message(event.reply_token, message)     
         
    elif postBack == 'translator':
       QuickReply_text_message = getQuickReply_lang()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)
       
    elif postBack == 'restart':
       client.publish("music", 'restart', 0, True) #發佈訊息
       time.sleep(1)
       client.publish("music", ' ', 0, True) #發佈訊息          

def getQuickReply_plugs():
	QuickReply_text_message = TextSendMessage(
       text="點選你想要開關的插座",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "客廳", text = "livingroom_plug"),
            image_url = 'https://i.imgur.com/EhBR2Vu.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "房間", text = "bedroom_plug"),
            image_url = 'https://i.imgur.com/EhBR2Vu.png'
          )
        ]
       )
      )
	return QuickReply_text_message  	
	
def getQuickReply_volume():
	QuickReply_text_message = TextSendMessage(
       text="點選你想要調整的音量",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "80", text = "volume~80"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "70", text = "volume~60"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "60", text = "volume~60"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "50", text = "volume~50"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          )         
        ]
       )
      )
	return QuickReply_text_message  
        
def getQuickReply_music_work():
	QuickReply_text_message = TextSendMessage(
       text="點選你想要的操作功能",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "重新開機", text = "player_restart"),
            image_url = 'https://i.imgur.com/mtQhzCP.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "停止播放", text = "停止播放"),
            image_url = 'https://i.imgur.com/PEHPvG8.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "音樂播放", text = "music_play"),
            image_url = 'https://i.imgur.com/W1jVNlS.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "喜愛音樂", text = "favor"),
            image_url = 'https://i.imgur.com/kPxgRM7.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "音量大聲", text = "音量大聲一點"),
            image_url = 'https://i.imgur.com/jPHUkGZ.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "音量小聲", text = "音量小聲一點"),
            image_url = 'https://i.imgur.com/fmArX5z.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "音量最小聲", text = "音量最小聲"),
            image_url = 'https://i.imgur.com/sC1Xf98.png'
          )
          
        ]
       )
      )
	return QuickReply_text_message
	
def getQuickReply_camera_work():
	QuickReply_text_message = TextSendMessage(
       text="點選你想要的操作功能",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "開啟攝影機", text = "open_camera"),
            image_url = 'https://i.imgur.com/gNTGLC7.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "重新開機", text = "camera_restart"),
            image_url = 'https://i.imgur.com/PEHPvG8.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "開啟移動偵測", text = "move_enable"),
            image_url = 'https://i.imgur.com/bWvqGuM.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "關閉移動偵測", text = "move_disable"),
            image_url = 'https://i.imgur.com/SykzuZc.png'
          )
          
        ]
       )
      )
	return QuickReply_text_message	
	
def getQuickReply_music():
	QuickReply_text_message = TextSendMessage(
       text="點選你喜歡的音樂",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "張惠妹", text = "我要聽歌手張惠妹的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "張信哲", text = "我要聽歌手張信哲的歌"),
            image_url = 'https://i.imgur.com/Q3lUQJa.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "田馥甄", text = "我要聽歌手田馥甄的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "鄧紫棋", text = "我要聽歌手鄧紫棋的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "藍又時", text = "我要聽歌手藍又時的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "李玖哲", text = "我要聽歌手李玖哲的歌"),
            image_url = 'https://i.imgur.com/Q3lUQJa.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "蔡藍欽", text = "我要聽歌手蔡藍欽的歌"),
            image_url = 'https://i.imgur.com/Q3lUQJa.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "伍佰", text = "我要聽歌手伍佰的歌"),
            image_url = 'https://i.imgur.com/Q3lUQJa.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "陳奕迅", text = "我要聽歌手陳奕迅的歌"),
            image_url = 'https://i.imgur.com/sC1Xf98.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "郁可唯", text = "我要聽歌手郁可唯的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "浪漫", text = "我要聽浪漫的歌"),
            image_url = 'https://i.imgur.com/bwOyWxe.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "抒情", text = "我要聽抒情的歌"),
            image_url = 'https://i.imgur.com/bwOyWxe.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "鋼琴", text = "我要聽鋼琴音樂的歌"),
            image_url = 'https://i.imgur.com/bwOyWxe.png'
          )                        
        ]
       )
      )
	return QuickReply_text_message
	
def getQuickReply_weather():
	QuickReply_text_message = TextSendMessage(
       text="點選你要查詢的城市",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "臺北市", text = "weather~臺北市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "基隆市", text = "weather~基隆市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "桃園市", text = "weather~桃園市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "臺中市", text = "weather~臺中市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "臺南市", text = "weather~臺南市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "高雄市", text = "weather~高雄市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          )
          
        ]
       )
      )
	return QuickReply_text_message
	
def getQuickReply_lang():
   QuickReply_text_message = TextSendMessage(
       text="點選你要查詢的城市",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "英文", text = "lang~英文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "日文", text = "lang~日文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "韓文", text = "lang~韓文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "泰文", text = "lang~泰文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "越南文", text = "lang~越南文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "法文", text = "lang~法文"),
            image_url = 'https://i.imgur.com/JmnOtyi.png'
          )                   
        ]
       )
      )
   return QuickReply_text_message			        
	 
def getQuickReply_pm25():
    QuickReply_text_message = TextSendMessage(
       text="點選你要查詢的城市",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "新北市", text = "pm25~新北市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "基隆市", text = "pm25~基隆市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "臺北市", text = "pm25~臺北市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "桃園市", text = "pm25~桃園市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ), 
          
          QuickReplyButton(
            action = MessageAction(label = "桃園市", text = "pm25~桃園市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),           
          QuickReplyButton(
            action = MessageAction(label = "新竹市", text = "pm25~新竹市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "苗栗縣", text = "pm25~苗栗縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),  
           QuickReplyButton(
            action = MessageAction(label = "台中市", text = "pm25~台中市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ), 
           QuickReplyButton(
            action = MessageAction(label = "雲林縣", text = "pm25~雲林縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ), 
          QuickReplyButton(
            action = MessageAction(label = "嘉義縣", text = "pm25~嘉義縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ), 
          QuickReplyButton(
            action = MessageAction(label = "臺南市", text = "pm25~臺南市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ), 
          QuickReplyButton(
            action = MessageAction(label = "高雄市", text = "pm25~高雄市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ) 
                   
        ]
       )
      )
    return QuickReply_text_message			              

def getFlex_airbox(airbox_result):
       split_array = airbox_result.split("~")   
       bubble = BubbleContainer(
            direction='ltr', #項目由左向右排列
            header=BoxComponent(  #標題
                layout='vertical',
                contents=[
                    TextComponent(text='環境感測', weight='bold', size='xxl'),
                ]
            ),
            hero=ImageComponent(  #主圖片
                url='https://i.imgur.com/YLrIWLz.png',
                size='xxl',
                aspect_ratio='792:555',  #長寬比例
                aspect_mode='cover',
            ),
            body=BoxComponent(  #主要內容
                layout='vertical',
                contents=[
                    TextComponent(text='即時感測資訊', size='md',color='#FF0000'),                    
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    IconComponent(size='4xl', url='https://i.imgur.com/toxS2Qq.png'),
                                    TextComponent(text= '溫度 ' + split_array[0] + ' C', color='#666666', size='lg', flex=5)
                                ],
                            ),
                            SeparatorComponent(color='#0000FF'),
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    IconComponent(size='4xl', url='https://i.imgur.com/Dcd1Ifx.png'),
                                    TextComponent(text= '濕度 ' +split_array[1] +  ' %', color='#666666', size='lg', flex=5),
                                ],
                            ),
                             BoxComponent(
                                layout='baseline',
                                contents=[
                                    IconComponent(size='4xl', url='https://i.imgur.com/TA1a6AL.png'),
                                    TextComponent(text= 'PM2.5 ' + split_array[2] +  ' ug/m3', color='#666666', size='lg', flex=5),
                                ],
                            ),
                        ],
                    )
                    
                ],
            ),
            footer=BoxComponent(  #底部版權宣告
                layout='vertical',
                contents=[
                    TextComponent(text='Copyright@xxxx  2020', color='#888888', size='sm', align='center')
                ]
            )
        )
       return bubble 
	
def getFlex_stock(stock_result):  #取得彈性配置樣板
        split_array = stock_result.split("~")   
        bubble = BubbleContainer(
            direction='ltr', #項目由左向右排列
            header=BoxComponent(  #標題
                layout='vertical',
                contents=[
                    TextComponent(text='臺灣股票', weight='bold', size='xxl'),
                ]
            ),
            hero=ImageComponent(  #主圖片
                url='https://i.imgur.com/6gF3FIp.png',
                size='full',
                aspect_ratio='792:555',  #長寬比例
                aspect_mode='cover',
            ),
            body=BoxComponent(  #主要內容
                layout='vertical',
                contents=[
                    TextComponent(text='即時交易資訊', size='md',color='#FF0000'),                    
                    BoxComponent(
                        layout='vertical',
                        margin='lg',
                        contents=[
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(text=split_array[0], color='#666666', size='sm', flex=5)
                                ],
                            ),
                            SeparatorComponent(color='#0000FF'),
                            BoxComponent(
                                layout='baseline',
                                contents=[
                                    TextComponent(text=split_array[1], color='#666666', size='sm', flex=5),
                                ],
                            ),
                        ],
                    )
                    
                ],
            ),
            footer=BoxComponent(  #底部版權宣告
                layout='vertical',
                contents=[
                    TextComponent(text='Copyright@xxxx  2020', color='#888888', size='sm', align='center')
                ]
            )
        )
        return bubble 
        
def switch_plug(deviceSN):
        URL_API_RequestState = '{host_url}/{SN}/RequestState/{KEY}'.format( 
		   host_url = 'https://service.wf8266.com/api/mqtt', 
		   SN = deviceSN, 
		   KEY = 'ADu2FL4V7LdfprFNL9xpKkbVw873'
		)
        URL_API_GPIO_ON = '{host_url}/{SN}/GPIO/{KEY}/12,1'.format( 
		   host_url = 'https://service.wf8266.com/api/mqtt', 
		   SN = deviceSN, 
		   KEY = 'ADu2FL4V7LdfprFNL9xpKkbVw873'		   		   
		)
        URL_API_GPIO_OFF = '{host_url}/{SN}/GPIO/{KEY}/12,0'.format( 
		   host_url = 'https://service.wf8266.com/api/mqtt', 
		   SN = deviceSN, 
		   KEY = 'ADu2FL4V7LdfprFNL9xpKkbVw873'		   		   
		)
        try: 
            response = requests.get(URL_API_RequestState,timeout = 5)            
            resObj = json.loads(response.text)
            print('PlugState： ', resObj['data']['Data'][2])
            plug_state = resObj['data']['Data'][2]
            if plug_state == '0':                           
              response = requests.get(URL_API_GPIO_ON,timeout = 5)								
              message = TextSendMessage(text = "開關已打開")
            elif plug_state == '1':                           
              response = requests.get(URL_API_GPIO_OFF,timeout = 5)								
              message = TextSendMessage(text = "開關已關閉")                           
        except requests.exceptions.Timeout as e:
            airbox_data = 'error'
            message = TextSendMessage(text = "插座未連線.....") 
        return message

#https://service.wf8266.com/api/mqtt/08630817/IRSend/ADu2FL4V7LdfprFNL9xpKkbVw873/15, 5
def switch_infrared_device(IR_num):
        URL_API_IRSend = '{host_url}/{SN}/IRSend/{KEY}/15,{value}'.format( 
		   host_url = 'https://service.wf8266.com/api/mqtt', 
		   SN = '8630813', 
		   KEY = 'ADu2FL4V7LdfprFNL9xpKkbVw873',	
		   value = IR_num	   		   
		)       
        try: 
            response = requests.get(URL_API_IRSend,timeout = 5)            
            resObj = json.loads(response.text)            
            code_state = resObj['code']            
            message = TextSendMessage(text = "遙控器設備已切換")                                     
        except requests.exceptions.Timeout as e:
            code_state = 'error'
            message = TextSendMessage(text = "紅外線控制器未連線.....") 
        return message           
	
def get_weather(cityname):
    r = requests.get('%s/F-C0032-001?Authorization=%s&locationName=%s'\
        % (weather_url, apikey, cityname)).text
    weather_data = json.loads(r)
    print('今天的天氣')
    weather_wx = weather_data["records"]['location'][0]['weatherElement'][0]\
       ['time'][0]['parameter']['parameterName']
    weather_CI = weather_data["records"]['location'][0]['weatherElement'][3]\
       ['time'][0]['parameter']['parameterName'] 
    weather_MinT = weather_data["records"]['location'][0]['weatherElement'][2]\
       ['time'][0]['parameter']['parameterName']
    weather_MaxT =  weather_data["records"]['location'][0]['weatherElement'][4]\
       ['time'][0]['parameter']['parameterName']    
    return weather_wx + '，' + weather_CI + '，' + "最低溫 " \
     + weather_MinT +'度，' + "最高溫 " +weather_MaxT + '度'

def get_weather_state(weather_info,cityname):
    if "陰時多雲短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/F7c7WnN.png'
    elif "多雲短暫陣雨" in weather_info:	
          imageurl = 'https://i.imgur.com/i3AF7dg.png'
    elif "陰時短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/F7c7WnN.png' 
    elif "陰短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/F7c7WnN.png'     
    elif "多雲短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/F7c7WnN.png'	     
    elif "陰天有雨" in weather_info:	
          imageurl = 'https://i.imgur.com/DptJzac.png'
    elif "多雲時晴" in weather_info :
          imageurl = 'https://i.imgur.com/AJbKWzL.png'
    elif "晴時多雲" in weather_info:
          imageurl = 'https://i.imgur.com/ycSrwVV.png'	    	               
    elif "多雲" in weather_info:	
          imageurl = 'https://i.imgur.com/5HpJaF7.png'         	
    else:
          imageurl = 'https://i.imgur.com/P5EiNgQ.png' 	    	  
    message = [
	  TextSendMessage(text="["+cityname + "] 今天天氣狀態： " +  weather_info),
	  ImageSendMessage(original_content_url= imageurl, \
	        preview_image_url= imageurl)
	]
    return message      

import urllib.request  
def get_pm25(cityname):
    src = "http://opendata2.epa.gov.tw/AQI.json" #PM2.5 open data
    with urllib.request.urlopen(src) as response:
      data_list=json.load(response) # 取得json資料轉物件
      count = 0; PM25 = 0
      for item in data_list:
       if cityname == item["County"]:
        PM25 = PM25 + int(item["PM2.5"])
        count = count+1
       
        message = "全台灣共有%d個測站，在%s共有%d個測站, PM2.5平均值為%f"\
           % (len(data_list), cityname, count, round(PM25/count))
        print(message)
        return message 
         
ref = db.reference('/') # 參考路徑  	
userId = 'volume'
users_userId_ref = ref.child('smarthome/config/'+ userId)
volume_num = users_userId_ref.get() 
print('volume....', volume_num)
mqttmsg = str(volume_num )+ '%' 
            
def random_int_list(num):
  list = range(1, num)
  random_list = [*list]
  random.shuffle(random_list)
  return random_list
  
def nlu(text):
  global nlu_text, songnum, songkind, client, genUrl_state, volume_num	
  cmd = './olami-nlu-api-test.sh https://tw.olami.ai/cloudservice/api 8bd057135ec8432bb7bd2b2caa510aca 3fd33f86b57642c08fbea22f8eb9132d %s'     
  output = os.popen(cmd % text) #點歌語意      
  fp = open("output.txt", "w")  
  fp.write(output.read()) # 文字語意理解過程結果寫入檔案      
  fp.close()  
  os.system('cat output.txt | grep nli | grep status > nlu_output.txt') # 文字語意理解結果輸出
  f = open('nlu_output.txt', 'r')
  temp = json.load(f) # json格式讀取文字語意理解結果
  print(temp)    
  f.close()
  type =  temp['data']['nli'][0]['type']        
  status = temp['data']['nli'][0]['desc_obj']['status']      
  print('status', status)
  print('type', type)         
        
  if status == 0 and type == 'smarthome':     
    action = temp['data']['nli'][0] ['semantic'][0]['modifier'][0]
    if action == 'playsong': #播放指定歌曲
       nlu_text = temp['data']['nli'][0]['desc_obj']['result']
       print('nlu', nlu_text) 
       songname = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value'] 
       randomList = random_int_list(15)[0:1]       
       mqttmsg = songname + '~' + str(randomList[0])           
       print('songname ', songname)       
       songnum = randomList[0]
       songkind = songname
       with open('record.txt','w', encoding = "utf-8") as fileobj:
         word = fileobj.write(songname)                    
       client.publish("playsong", mqttmsg, 0, retain=False) #發佈訊息
       print("message published")
       message = TextSendMessage(text = nlu_text)
       return message                                
               
    if action == 'playsinger': #播放指定歌手
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text) 
        singername = temp['data']['nli'][0]['semantic'][0]['slots'][0]['value']       
        randomList = random_int_list(15)[0:1]
        mqttmsg = singername + '~' + str(randomList[0])                                
        print('singername ', singername)                  
        songnum = randomList[0]
        songkind = singername
        with open('record.txt','w', encoding = "utf-8") as fileobj:
         word = fileobj.write(singername)                                 
        client.publish("playsong", mqttmsg, 0, retain=False) #發佈訊息
        print("message published")
        message = TextSendMessage(text = nlu_text)
        return message                        

    if action == 'playpause': #播放暫停/繼續
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text)
        mqttmsg ='playpause'
        client.publish("pause_play", mqttmsg, 0, retain=False) #發佈訊息
        print("message published")
        message = TextSendMessage(text = nlu_text)
        return message         

    if action == 'adjust': #調整音量
         volume = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value']         
         nlu_text = temp['data']['nli'][0]['desc_obj']['result']
         print('nlu', nlu_text)
         if volume == '大聲':
             volume_num = volume_num + 10            
             print("volume_num ", volume_num )
             volume_str = str(volume_num )+'%'
             mqttmsg = volume_str            
             client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息                             
         elif volume == '小聲':
              volume_num = volume_num - 10
              volume_str = str(volume_num)+'%'
              mqttmsg = volume_str             
              client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息              
         elif volume == '最小聲':
              volume_num = 50
              volume_str = str(volume_num)+'%'             
              mqttmsg = volume_str             
              client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息   
         elif volume == '最大聲':
              volume_num = 100
              volume_str = str(volume_num)+'%'
              mqttmsg = volume_str               
              client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息           
         elif volume == '適中' or volume == '剛好':
              volume_num = 70
              volume_str = str(volume_num)+'%'
              mqttmsg = volume_str               
              client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息
         ref.child('smarthome/config').update({
               'volume':volume_num}                
         )
         
         message = TextSendMessage(text = nlu_text)
         return message                 
   
    if action == 'query':
        solt_item1 = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value']
        print(solt_item1)
        if solt_item1 == '天氣':
            cityname = temp['data']['nli'][0] ['semantic'][0]['slots'][1]['value']
            print(cityname)
            weather_info = get_weather(cityname)
            message = get_weather_state(weather_info, cityname)
            return message
            
    if action == 'translate':
        language = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value']
        text = temp['data']['nli'][0] ['semantic'][0]['slots'][1]['value']
        print(text)
        if language == '英文':
          language ='en'        
          message = translation(text, language)
          return message
        elif language == '日文':
          language ='ja'        
          message = translation(text, language)
          return message      
        elif language == '韓文':
          language ='ko'        
          message = translation(text, language)
          return message
        elif language == '泰文':
          language = 'th'
          message = translation(text, language)
          return message  
        else:
          message = translation(text, 'en')
          return message			                          		  
		 
  else:
      nlu_text = temp['data']['nli'][0]['desc_obj']['result']
      message = TextSendMessage(text = nlu_text)
      return message 

  print("播放NLU結果的語音......"+ nlu_text)
  
def airbox_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是空氣盒子按鈕選單模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/YOKF4hz.png', 
            title = '空氣盒子功能選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                URIAction(
                    label = '使用說明', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-LAoV1RPG'  
                ),                 
                PostbackAction(
                    label = '即時感測', # 在按鈕模板上顯示的名稱
                    data = 'airbox'  
                ), 
                URIAction(
                    label = '家中監測儀錶', # 在按鈕模板上顯示的名稱
                    uri = 'line://app/1635604759-k6eoNlbA'                     
                ), 
                URIAction(
                    label = '空氣盒子觀測站', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-g2ojnZ23'                     
                ),                    
            ]
         )
        )
    return buttons_template_message
    
def setup_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是系統設定按鈕選單模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/he05XcJ.png', 
            title = '系統設定選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！                
                PostbackAction(
                    label = '音量設定', # 在按鈕模板上顯示的名稱
                    data = 'volume'  
                ), 
                 PostbackAction(
                    label = '翻譯設定', # 在按鈕模板上顯示的名稱
                    data = 'translator'  
                )              
            ]
         )
        )
    return buttons_template_message
    
def music_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是音樂選單按鈕模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/fOSegKL.png', 
            title = '雲端音樂功能選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                URIAction(
                    label = '使用說明', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-nPa4OL57'  # 跳轉到的url，看你要改什麼都行，只要是url                    
                ),
                URIAction(
                    label = '網頁點歌', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-4ANQr5B3'  # 跳轉到的url，看你要改什麼都行，只要是url                    
                ),
                # 跟上面差不多
                MessageAction(
                    label = '歌曲資訊',   # 在按鈕模板上顯示的名稱
                    text = '歌曲資訊'  
                ),
                # 跳轉到URL
                MessageAction(
                    label = '歌曲播放選項',  # 在按鈕模板上顯示的名稱
                    text = 'menu'
                )
            ]
         )
        )
    return buttons_template_message 
       
def appliances_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是智慧家電選單按鈕模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/y6imeRO.png', 
            title = '智慧家電控制選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                URIAction(
                    label = '使用說明', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-BEX5p8QD'  # 跳轉到的url，看你要改什麼都行，只要是url                    
                ),
                PostbackAction(
                    label = '智慧插座', # 在按鈕模板上顯示的名稱
                    data = 'plugs'  # 跳轉到的url，看你要改什麼都行，只要是url                    
                ),
                PostbackAction(
                    label = '遠端遙控器',   # 在按鈕模板上顯示的名稱
                    data = 'infrared'  
                ),
                PostbackAction(
                    label = '遠端攝影機',   # 在按鈕模板上顯示的名稱
                    data = 'camera'  
                )
            ]
         )
        )
    return buttons_template_message      
def live_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是生活資訊選單按鈕模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/QgqPHUu.png', 
            title = '生活資訊功能選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                PostbackAction(
                    label = '天氣資訊', # 在按鈕模板上顯示的名稱
                    data = 'weather'                    
                ),
                PostbackAction(
                    label = '空氣品質', # 在按鈕模板上顯示的名稱
                    data = 'pm25'                    
                ),
                PostbackAction(
                    label = '台灣股市行情', # 在按鈕模板上顯示的名稱
                    data = 'stock'                    
                )
                
            ]
         )
        )
    return buttons_template_message 
    
def on_connect(client, userdata, flags, rc):  
    print("Connected with result code "+str(rc))
    client.subscribe("genurl", 0) 
    client.subscribe("homesecurity/ngrokurl", 2)       

def on_message(client, userdata, msg): 
    global camera_url     
    print(msg.topic + " " + str(msg.payload))
    #if msg.topic == 'homesecurity/ngrokurl':
     #camera_url = str(msg.payload)
     
             

client = mqtt.Client()    
client.on_connect = on_connect  
client.on_message = on_message  
client.connect("broker.mqttdashboard.com", 1883) 
client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息 
client.loop_start()

if __name__ == "__main__":           
    app.run(debug=True, host='0.0.0.0', port=5000)    

    
    
