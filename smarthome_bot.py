# -*- coding: UTF-8 -*-

from flask import Flask, request, abort
from flask_apscheduler import APScheduler
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
import time
import firebase_admin
import requests
from firebase_admin import credentials
from firebase_admin import db
import subprocess
import configparser
from line_notify import LineNotify
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import random
import datetime

config = configparser.ConfigParser()
config.read('smart_home.conf')

#取得通行憑證
cred = credentials.Certificate("serviceAccount.json")
#cred = credentials.Certificate("newsun87app-firebase-adminsdk-9xkh0-2e34b341b9.json")
firebase_admin.initialize_app(cred, {
   'databaseURL' : 'https://line-bot-test-77a80.firebaseio.com/'	
})

weather_url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore'
#apikey = 'CWB-A247B989-2950-4B3B-8665-1D92E72BC2AB'
apikey = config.get('weather_url', 'apikey')

#取得 linebot 通行憑證
access_token = config.get('linebot', 'access_token')
#access_token = ""
channel_secret = config.get('linebot', 'channel_secret')
camera_url = 'unknown' 

def get_access_token(autho_code):
     url = 'https://notify-bot.line.me/oauth/token'	
     payload = {'grant_type': 'authorization_code',
                 'code': autho_code, 
	             'redirect_uri':host+'/register', 
	             'client_id':'RsTuQZObEzJHPBU59HKhCI',
	             'client_secret': 'My9RHffhEkSyJtZecod84GSoGsQT4gfCpFzP4ZC3KTL'}
     headers = {'content-type': 'application/x-www-form-urlencoded'} 
     try:     
       r = requests.post(url, data=payload, headers=headers) # 回應為 JSON 字串
       print('r.text...',r.text) 
     except exceptions.Timeout as e:
        print('请求超时：'+str(e.message))
     except exceptions.HTTPError as e:
        print('http请求错误:'+str(e.message))
     else:       
        if r.status_code == 200:          			
          json_obj = json.loads(r.text) # 轉成 json 物件
          access_token = json_obj['access_token']
          print('access_token:', json_obj['access_token'])          
          return access_token            
        else:
           return 'error'
           
def default_menu(rich_menus_id): # 預設圖文選單
 headers = {"Authorization":"Bearer {my_access_token}".format(my_access_token=access_token),"Content-Type":"application/json"}
 req = requests.request('POST', 'https://api.line.me/v2/bot/user/all/richmenu/{my_rich_menus_id}'.format(my_rich_menus_id=rich_menus_id), headers=headers)    
 print(req.text) 

def get_menus_id_list(): # 取得圖文選單 ID 串列
 rich_menus_id_list = []		
 rich_menu_list = line_bot_api.get_rich_menu_list()#取得圖文選單資料串列
 for rich_menu in rich_menu_list:
    #print(rich_menu.rich_menu_id)
    rich_menus_id_list.append(rich_menu.rich_menu_id)
 return rich_menus_id_list            

app = Flask(__name__)

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret) 
rich_menus_id_list = get_menus_id_list() # 取得選單 ID 串列
print('rich_menu_list...', rich_menus_id_list)
default_menu(rich_menus_id_list[2]) # 預設啟動後的選單

@app.route('/')
def showIndexPage():
 return render_template('index.html')

@app.route('/register', methods=['GET', 'POST']) 
def showRegister():    
    ref = db.reference('/') # 參考路徑    
    if request.method=='GET':
      userId = request.args.get('state')  
      if userId != None:
        #profile = line_bot_api.get_profile(userId)# 呼叫取得用戶資訊 API 
        #userId = profile.user_id # 取得用戶 userId   
        autho_code = request.args.get('code') #取得 LineNotify 驗證碼
        time.sleep(1)
        linenotify_access_token = get_access_token(autho_code) #取得存取碼
        #access_token = linenotify_access_token
        print('linenotify_access_token...', linenotify_access_token)               
        users_userId_ref = ref.child('smarthome-bot/'+ userId +'/profile')        
        users_userId_ref.update({'LineNotify':'{access_token}'.format(access_token=linenotify_access_token)})
        return '<html><h1>LineNotify 連動設定成功....</h1></html>' 
      else:
        return '<html><h1>LineNotify 連動已設定....</h1></html>' 
    
@app.route('/translate')
def showTranslateHelpPage():
 return render_template('translator_help.html') 
 
@app.route('/musichelp')
def showMusicHelpPage():
 return render_template('music_help.html')  
 
@app.route('/music')
def showMusicPage():
 return render_template('music.html')  
 
@app.route('/camera_register')
def showCameraRegPage():
 return render_template('camera_register.html')    
 
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
  

# 回應圖片的 imgurl    
image_url = {'sticker_imag1':'https://i.imgur.com/GDsd8KJ.jpg'}
host = 'https://liff.line.me/1654118646-4ANQr5B3'
base_users_userId  = 'smarthome-bot/'
ref = db.reference('/') # 參考路徑 
singerList = []

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
    
line_token = ''
# 處理文字訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event): 
  global userId, nlu_text, imagga_api_key, imagga_secret_key, singerList, line_token  
  ref = db.reference('/') # 參考路徑 
  userId = event.source.user_id  
  profile = line_bot_api.get_profile(userId)# 呼叫取得用戶資訊 API
  print('profile...',profile)
  line_token = ref.child(base_users_userId+userId+'/profile/LineNotify').get()
  print("line_token", line_token)  
  #---判斷用戶是否有註冊 LINE Notify---------------         
  if ref.child(base_users_userId+userId+'/profile/LineNotify').get()==None:   
   buttons_template_message = linenotify_menu()
   line_bot_api.reply_message(event.reply_token, buttons_template_message)
        
# -----雲端音樂功能的指令-------------- 
  # ----播放影片網址---------    
  if event.message.text.startswith('【youtube url】'):
      new_message = event.message.text.lstrip('【youtube url】')
      ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":videourl})
      print("歌曲 {videourl} 更新成功...".format(videourl=new_message))
      line_bot_api.reply_message(
        event.reply_token, TextSendMessage(text="馬上播放 " + new_message))
      client.publish("music/youtubeurl", userId+'~'+ new_message, 2, retain=True) #發佈訊息
      time.sleep(1)
      client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息           
      
  elif event.message.text.startswith('https://youtube.com/watch?'):      
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="馬上播放 " + event.message.text))
      ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":event.message.text})
      print("歌曲 {videourl} 更新成功...".format(videourl=event.message.text))      
      client.publish("music/youtubeurl", userId +'~'+ event.message.text, 2, retain=True) #發佈訊息 
      time.sleep(1)
      client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息     
      
  elif event.message.text.startswith('https://www.youtube.com/watch?'):      
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="馬上播放 " + event.message.text))
      ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":event.message.text})
      print("歌曲 {videourl} 更新成功...".format(videourl=event.message.text))          
      client.publish("music/youtubeurl", userId +'~'+ event.message.text, 2, retain=True) #發佈訊息
      time.sleep(1)
      client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息       
    # -----------------------------------------------------------------------
# -------新增或刪除喜愛歌手功能-------------------------------
  elif event.message.text.startswith('addsinger'): 
      split_array = event.message.text.split("~")
      singername = split_array [1]
      print('singername..', singername)
      favorsingerList = ref.child(base_users_userId + userId + '/youtube_music/favorsinger').get()
      if singername not in favorsingerList: 
        number = len(favorsingerList)
       # print( 'number...', number) 
        ref.child(base_users_userId + userId + '/youtube_music/favorsinger').update({number:singername})
        message = TextSendMessage(text="新增喜愛的歌手 " + singername + " 已成功" )  
      else:
        message = TextSendMessage(text="歌手已在清單中...")           
      line_bot_api.reply_message(event.reply_token, message)
  elif event.message.text.startswith('delsinger'): 
      split_array = event.message.text.split("~")
      singername = split_array [1]
      print('singername..', singername)
      favorsingerList = ref.child(base_users_userId + userId + '/youtube_music/favorsinger').get()
      if singername in favorsingerList: # 找到歌手名稱
        favorsingerList.remove(singername) # 移除歌手名稱      
        print('favorsingerList..', favorsingerList)
        #重新寫入歌手清單
        ref.child(base_users_userId + userId + '/youtube_music/favorsinger').set(favorsingerList)
        message = TextSendMessage(text="刪除喜愛的歌手 " + singername + " 已成功" )  
      else:
        message = TextSendMessage(text="歌手不在清單中...")           
      line_bot_api.reply_message(event.reply_token, message)          
# ----------------------------------------------------------------------- 
# -------地區天氣查詢功能-------------------------------
  elif event.message.text.startswith('weather'): 
      split_array = event.message.text.split("~")
      cityname = split_array [1]
      weather_info = get_weather(cityname)
      print("天氣資訊...", weather_info)
      message = get_weather_state(weather_info, cityname)      
      line_bot_api.reply_message(event.reply_token, message)     
# ----------------------------------------------------------------------- 
# ------------圖文選單動態切換----------------------------------------------
  elif event.message.text == 'main_menu':      
      line_bot_api.link_rich_menu_to_user(userId, rich_menus_id_list[2]) # 切換選單
      message = TextSendMessage(text="回到主選單...")
      line_bot_api.reply_message(event.reply_token, message)
  elif event.message.text == 'music':
      message = TextSendMessage(text="切換成音樂選單...")         
      line_bot_api.link_rich_menu_to_user(userId, rich_menus_id_list[3]) # 切換選單
      line_bot_api.reply_message(event.reply_token, message)            
  
  elif event.message.text == 'information':      
      line_bot_api.link_rich_menu_to_user(userId, rich_menus_id_list[1]) # 切換選單
      message = TextSendMessage(text="切換成資訊選單...")
      line_bot_api.reply_message(event.reply_token, message)
  elif event.message.text == 'IOT':      
      line_bot_api.link_rich_menu_to_user(userId, rich_menus_id_list[0]) # 切換選單
      message = TextSendMessage(text="切換成物聯網選單...")
      line_bot_api.reply_message(event.reply_token, message)            
        
# -----------------------------------------------------------------------          
# ------------AI 圖片辨識功能----------------------------------------------        
  elif event.message.text == 'categorization':
	#讀取 Imagga 設定檔的資訊
    imagga_api_key = config.get('imagga', 'api_key') #取得設定資訊
    imagga_api_secret = config.get('imagga', 'api_secret')
    image_path = 'temp_image.jpg'   
    response = requests.post(
            'https://api.imagga.com/v2/categories/personal_photos',
             auth=(imagga_api_key, imagga_api_secret),
             files={'image': open(image_path, 'rb')}
    )    
    #AI 辨識推論影像資料 
    AI_result = response.json()["result"]["categories"][0]["name"]["en"]    
    print('影像辨識結果....', AI_result)
    message = TextSendMessage(text="此圖片辨識結果可能是 " + AI_result)      
    line_bot_api.reply_message(event.reply_token, message)
    
  elif event.message.text == 'tags':
    imagga_api_key = config.get('imagga', 'api_key') #取得設定資訊
    imagga_api_secret = config.get('imagga', 'api_secret')
    image_path = 'temp_image.jpg'     
    response = requests.post(
            'https://api.imagga.com/v2/tags',
             auth=(imagga_api_key, imagga_api_secret),
             files={'image': open(image_path, 'rb')}
    )    
    #AI 辨識推論影像資料 
    AI_result = response.json()["result"]["tags"][0]["tag"]["en"]   
    print('影像辨識結果....', AI_result)
    message = TextSendMessage(text="此圖片辨識結果可能是 " + AI_result)      
    line_bot_api.reply_message(event.reply_token, message)  
# -----------------------------------------------------------------------       
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
      #pm25_info = get_pm25(cityname)
      message = get_pm25(cityname)
      #message = TextSendMessage(text="["+cityname + "] 空氣品質： " +  pm25_info)
      #message = [	   
	     # TextSendMessage(text="["+cityname + "] 空氣品質： " +  pm25_info),
	     # TextSendMessage(text="空氣品質監測網： " +  "https://liff.line.me/1654118646-8q4qo3vy")
	  #]      
      line_bot_api.reply_message(event.reply_token, message)  
      
  elif event.message.text.startswith('volume'): 
      split_array = event.message.text.split("~")
      volume = int(split_array [1])
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child(base_users_userId + userId + '/youtube_music')      
      users_userId_ref.update({'volume':volume})
      mqttmsg = str(volume)           
      client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息        
      message = TextSendMessage(text = '音量設定為： ' + split_array [1] + '%')
      line_bot_api.reply_message(event.reply_token, message) 
	  
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
      users_userId_ref = ref.child(base_users_userId + userId + '/youtube_music')            
      videourl = users_userId_ref.get()['videourl'] 
      line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="馬上播放 " + videourl))
      client.publish("music/youtubeurl", userId+'~'+ videourl, 2, retain=True)  
      time.sleep(1)
      client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息 
      
  elif event.message.text == '取消動作':
	  message = TextSendMessage(text="沒有問題!")	  
	  line_bot_api.reply_message(event.reply_token, message)
	  
# -----遠端攝影機 quickreply 的指令操作--------------
  elif event.message.text.startswith('cameraID'): 
      split_array = event.message.text.split("~")
      cameraid = split_array [1]
      ref.child(base_users_userId + userId + '/camera').update({"camera_ID":"cam"+cameraid})
      message = TextSendMessage(text = "用攝影機註冊成功....")
      line_bot_api.reply_message(event.reply_token, message)  
  elif event.message.text == 'register_camera':
      message = TextSendMessage(text = "註冊攝影機: " + host + '/camera_register')                 
      line_bot_api.reply_message(event.reply_token, message)  
  elif event.message.text == 'open_camera':
      if ref.child(base_users_userId+userId+'/camera/camera_ID').get()== "":
         message = TextSendMessage(text = "用戶尚未註冊攝影機....")                 
      else:
         camera_url = ref.child(base_users_userId+userId+'/camera/camera_URL').get()
         print('camera_url...', camera_url)         
         message = TextSendMessage(text = "攝影機網址: " + camera_url)        
      line_bot_api.reply_message(event.reply_token, message)      
  elif event.message.text == 'camera_restart':
      client.publish("homesecurity/restart", "0", 0, retain=True)
      time.sleep(1)
      client.publish("homesecurity/restart", '', 0, retain=True) #發佈訊息
      message = TextSendMessage(text = '攝影機已重新開機....')                       
      line_bot_api.reply_message(event.reply_token, message)
  elif event.message.text == 'move_enable':
      client.publish("homesecurity/move_detect", "1", 0, retain=True) #發佈訊息       
      message = TextSendMessage(text = '移動偵測已啟動....')        
      line_bot_api.reply_message(event.reply_token, message) 
  elif event.message.text == 'move_disable':
      client.publish("homesecurity/move_detect", "0", 0, retain=True) #發佈訊息                  
      message = TextSendMessage(text = '移動偵測已關閉....')        
      line_bot_api.reply_message(event.reply_token, message)                  
# -------------------------------- 
# ------雲端音樂功能------------------     
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
      users_userId_ref = ref.child(base_users_userId + userId + '/youtube_music/')
      videourl = users_userId_ref.get()['videourl']   	        
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="歌曲資訊 " + videourl)) 
      
  elif event.message.text == 'menu': # 音樂選單 quickreply
      QuickReply_text_message = getQuickReply_music_work()      
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 
      
  elif event.message.text == 'favor':
      QuickReply_text_message = getQuickReply_music()      
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message)
# --------------------------------------------------------------------------          
  elif event.message.text == 'help':
      with open('help.txt', mode='r', encoding = "utf-8") as f:
        content = f.read()
        print(content)
        message = TextSendMessage(text=content)      
        line_bot_api.reply_message(event.reply_token, message)            
# ------系統設定功能------------------           
  elif event.message.text == 'setup':
      buttons_template_message = setup_menu()
      line_bot_api.reply_message(event.reply_token, buttons_template_message)
  elif event.message.text.startswith('lang'): #語言翻譯設定
      split_array = event.message.text.split("~")
      language = split_array [1]
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child(base_users_userId + userId + '/translate/')
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
# ----------------------------------------------------------------      
# ------語言翻譯功能------------------        
  elif event.message.text.startswith('翻譯'): 
      split_array = event.message.text.split("~")
      text = split_array [1]      
      ref = db.reference('/') # 參考路徑  	
      users_userId_ref = ref.child(base_users_userId + userId + '/translate/lang')      
      language = users_userId_ref.get()
      print('language...', language)
      message = translation(text, language)      
      line_bot_api.reply_message(event.reply_token, message)  
# ----------------------------------------------------------------          
# ------OLAMI 語意理解功能------------------                     
  else:	               
      message = nlu(event.message.text)      
      line_bot_api.reply_message(event.reply_token, message)  
# ----------------------------------------------------------------          

from translate import Translator
from lxml import etree  
#heroku_baseurl = 'https://smarthome-123.herokuapp.com'

def translation(text, language): 
    heroku_baseurl = 'https://smarthome-123.herokuapp.com/static'      
    translator = Translator(from_lang = 'zh-Hant', to_lang = language)
    translation = translator.translate(text)          
    print('translation result: ',translation)
    translation_modify = translation.replace(" ", "")
    #將英文文字 translation_modify 轉成語音(STT)
    stream_url ='https://google-translate-proxy.herokuapp.com/api/tts?query=' \
           + translation + '&language=' + language 
    r = requests.get(stream_url, stream=True)
    with open('./stream.m4a', 'wb') as f:
       try:
          for block in r.iter_content(1024):
            f.write(block)
       except KeyboardInterrupt:
          pass          
    message = [
          TextSendMessage(text = '翻譯文字： ' + translation),
          AudioSendMessage(
		    original_content_url = heroku_baseurl + '/stream.m4a',
		    duration = 10000
		  )
	]    		
    return message
    
# 處理圖片訊息
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event): 
  if event.message.type == 'image':
    print("event: ", event) 
    message_id = event.message.id    	  
	  # 讀取圖片資料
    message_content = line_bot_api.get_message_content(message_id)    
    with open('temp_image.jpg', 'wb') as fd: # 儲存圖片
      for chunk in message_content.iter_content():
        fd.write(chunk)	  
    QuickReply_text_message = getQuickReply_aiimage()       
    line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 

# 處理 postback 事件
@handler.add(PostbackEvent)
def handle_postback_message(event):
    postBack = event.postback.data
    print('poskback......', postBack)         
# ----生和資訊功能功能操作------------------                   
    if postBack == 'weather':
       QuickReply_text_message = getQuickReply_weather()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)       
    elif postBack == 'pm25':
       QuickReply_text_message = getQuickReply_pm25() # 取得 pm25 快速選單      
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)       
    elif postBack == 'stock':
        result = subprocess.getoutput("sh ./twstockGet.sh")
        print(result)
        bubble = getFlex_stock(result)
        message = FlexSendMessage(alt_text = "彈性配置範例", contents = bubble)        
        line_bot_api.reply_message(event.reply_token, message)
    elif postBack == 'AIImage':
       QuickReply_text_message = getQuickReply_aiimage()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)           
# ---------------------------------------------------------------       
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
  #--------------------處理音樂播放-----------------------------------------------
    elif postBack == 'volume':
       QuickReply_text_message = getQuickReply_volume()       
       line_bot_api.reply_message(event.reply_token, QuickReply_text_message)    
    else:
       action= postBack.split("~")[0]
       video_url = postBack.split("~")[1]
       songname = postBack.split("~")[2]
       userId = postBack.split("~")[3]
       print(video_url, songname, userId, base_users_userId)
       if action == 'mqtt_publish':
        ref.child(base_users_userId + userId + '/youtube_music/').update({"songkind":songname})         
        ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":video_url})      
        client.publish("music/youtubeurl", userId +'~'+ video_url, 2, retain=True) #發佈訊息 
        print("message published")
        time.sleep(1)
        client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=video_url))                      

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
            action = MessageAction(label = "100", text = "volume~100"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "90", text = "volume~90"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "80", text = "volume~80"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "70", text = "volume~70"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "60", text = "volume~60"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "50", text = "volume~50"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "40", text = "volume~40"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "30", text = "volume~30"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "20", text = "volume~20"),
            image_url = 'https://i.imgur.com/cMIj4N5.png'
          )                        
        ]
       )
      )
	return QuickReply_text_message 
	
def getQuickReply_aiimage(): # 影像辨識功能 quickreply
	QuickReply_text_message = TextSendMessage(
       text="點選你想要辨識的功能",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "影像分類", text = 'categorization'),
            image_url = 'https://i.imgur.com/nWsDQqI.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "標籤", text = "tags"),
            image_url = 'https://i.imgur.com/nWsDQqI.png'
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
            action = MessageAction(label = "註冊攝影機", text = "register_camera"),            
            image_url = 'https://i.imgur.com/gNTGLC7.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "開啟攝影機", text = "open_camera"),            
            image_url = 'https://i.imgur.com/gNTGLC7.png'
          )          
        ]
       )
      )
	return QuickReply_text_message	
	
def getQuickReply_music():	 
	singerList = ref.child(base_users_userId + userId + '/youtube_music/favorsinger').get() 
	items = []
	# 動態加入歌手清單
	for key in range(len(singerList)):	
	 items.append(QuickReplyButton(
            action = MessageAction(label = singerList[key], text = "我要聽"+singerList[key]+"的歌"),
            image_url = 'https://i.imgur.com/0yjTHss.png'
     ))
            
	QuickReply_text_message = TextSendMessage(
       text="點選你喜歡的音樂",
       quick_reply = QuickReply(        
         items 
       )
    )
	return QuickReply_text_message
	
def getQuickReply_weather():
    QuickReply_text_message = TextSendMessage(
       text="點選你要查詢的城市",
       quick_reply = QuickReply(
        items = [          
          QuickReplyButton(
            action = MessageAction(label = "基隆市", text = "weather~基隆市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "臺北市", text = "weather~臺北市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "新北市", text = "weather~新北市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),         
           QuickReplyButton(
            action = MessageAction(label = "桃園市", text = "weather~桃園市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "苗栗縣", text = "weather~苗栗縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "臺中市", text = "weather~臺中市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "彰化縣", text = "weather~彰化縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "雲林縣", text = "weather~雲林縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "嘉義縣", text = "weather~嘉義縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "臺南市", text = "weather~臺南市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "高雄市", text = "weather~高雄市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),          
           QuickReplyButton(
            action = MessageAction(label = "宜蘭縣", text = "weather~宜蘭縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
           QuickReplyButton(
            action = MessageAction(label = "臺東縣", text = "weather~臺東縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          )         
        ]
       )
      )
    return QuickReply_text_message
	
def getQuickReply_lang():
   QuickReply_text_message = TextSendMessage(
       text="點選你要翻譯的語言",
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
            action = MessageAction(label = "新竹市", text = "pm25~新竹市"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),
          QuickReplyButton(
            action = MessageAction(label = "苗栗縣", text = "pm25~苗栗縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),  
           QuickReplyButton(
            action = MessageAction(label = "臺中市", text = "pm25~臺中市"),
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
          ), 
           QuickReplyButton(
            action = MessageAction(label = "屏東縣", text = "pm25~屏東縣"),
            image_url = 'https://i.imgur.com/cSx1PLC.png'
          ),          
          QuickReplyButton(
            action = MessageAction(label = "宜蘭縣", text = "pm25~宜蘭縣"),
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
    URL_API_RequestState = "curl -s 'https://service.wf8266.com/api/mqtt/{my_deviceSN}/RequestState/ADu2FL4V7LdfprFNL9xpKkbVw873' \
  -H 'Connection: keep-alive' \
  -H 'Cache-Control: max-age=0' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Sec-Fetch-Site: none' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-User: ?1' \
  -H 'Sec-Fetch-Dest: document' \
  -H 'Accept-Language: en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ja;q=0.6' \
  -H 'Cookie: connect.sid=s%3AWrA9WGu2NXFwLnBwjk1-jMDLbqjUWkBN.HiY3T5dFPfXas6cv7oDHrmQzLpKOyjQX5G6lEDtMIMY; __cfduid=df80e5c1cd8b704b596eb1703cfbe83631606599384; _ga=GA1.2.163570825.1606599384; _gid=GA1.2.1129529752.1606599384' \
  --compressed \
  --insecure".format(my_deviceSN=deviceSN)
    URL_API_GPIO_ON = "curl -s 'https://service.wf8266.com/api/mqtt/{my_deviceSN}/GPIO/ADu2FL4V7LdfprFNL9xpKkbVw873/12,1' \
  -H 'Connection: keep-alive' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Sec-Fetch-Site: none' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-User: ?1' \
  -H 'Sec-Fetch-Dest: document' \
  -H 'Accept-Language: en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ja;q=0.6' \
  -H 'Cookie: connect.sid=s%3AWrA9WGu2NXFwLnBwjk1-jMDLbqjUWkBN.HiY3T5dFPfXas6cv7oDHrmQzLpKOyjQX5G6lEDtMIMY; __cfduid=df80e5c1cd8b704b596eb1703cfbe83631606599384; _ga=GA1.2.163570825.1606599384; _gid=GA1.2.1129529752.1606599384' \
  --compressed \
  --insecure".format(my_deviceSN=deviceSN) 
    URL_API_GPIO_OFF = "curl -s 'https://service.wf8266.com/api/mqtt/{my_deviceSN}/GPIO/ADu2FL4V7LdfprFNL9xpKkbVw873/12,0' \
  -H 'Connection: keep-alive' \
  -H 'Upgrade-Insecure-Requests: 1' \
  -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36' \
  -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9' \
  -H 'Sec-Fetch-Site: none' \
  -H 'Sec-Fetch-Mode: navigate' \
  -H 'Sec-Fetch-User: ?1' \
  -H 'Sec-Fetch-Dest: document' \
  -H 'Accept-Language: en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7,ja;q=0.6' \
  -H 'Cookie: connect.sid=s%3AWrA9WGu2NXFwLnBwjk1-jMDLbqjUWkBN.HiY3T5dFPfXas6cv7oDHrmQzLpKOyjQX5G6lEDtMIMY; __cfduid=df80e5c1cd8b704b596eb1703cfbe83631606599384; _ga=GA1.2.163570825.1606599384; _gid=GA1.2.1129529752.1606599384' \
  --compressed \
  --insecure".format(my_deviceSN=deviceSN)
    try:     
     r = os.popen(URL_API_RequestState)	
     text = r.read()   
     r.close()
     print(text)
     resObj = json.loads(text)
     print('PlugState： ', resObj['data']['Data'][2])	
     plug_state = resObj['data']['Data'][2]
     if plug_state == '0':
      os.system(URL_API_GPIO_ON)    								
      print("開關已打開")
      message = TextSendMessage(text = "開關已打開")
     elif plug_state == '1':                           
      os.system(URL_API_GPIO_OFF)
      print("開關已關閉")
      message = TextSendMessage(text = "開關已關閉")    
    except requests.exceptions.Timeout as e:
       print("插座未連線.....")
       message = TextSendMessage(text = "插座未連線.....")       
    return message 

def switch_infrared_device(IR_num): # 切換紅外線裝置
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
	
def get_weather(cityname): # 取得天氣資訊
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
    # 天氣圖片網址 https://www.cwb.gov.tw/V8/C/K/Weather_Icon.html
    if "陰時多雲短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/bsGmXXO.png'
    elif "多雲短暫陣雨" in weather_info:	
          imageurl = 'https://i.imgur.com/WFiKlIk.png'
    elif "陰時短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/F7c7WnN.png'
    elif "陰短暫雨" in weather_info:	
          imageurl = 'https://i.imgur.com/6OjSN0b.png'           
    elif "陰短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/6OjSN0b.png'     
    elif "多雲短暫陣雨或雷雨" in weather_info:	
          imageurl = 'https://i.imgur.com/bsGmXXO.png'
    elif "陰時多雲" in weather_info:	
          imageurl = 'https://i.imgur.com/5dixrNV.png'
    elif "陰時多雲短暫雨" in weather_info:	
          imageurl = 'https://i.imgur.com/bsGmXXO.png'                    	     
    elif "陰天有雨" in weather_info:	
          imageurl = 'https://i.imgur.com/RLcdccF.png'
    elif "陰天" in weather_info:	
          imageurl = 'https://i.imgur.com/8Yo1ea3.png'
    elif "多雲時晴" in weather_info :
          imageurl = 'https://i.imgur.com/VMeO5Us.png'
    elif "多雲時陰" in weather_info :
          imageurl = 'https://i.imgur.com/QI5NI4P.png'
    elif "多雲時陰短暫雨" in weather_info :
          imageurl = 'https://i.imgur.com/KswxMPl.png'
    elif "多雲短暫雨" in weather_info :
          imageurl = 'https://i.imgur.com/gFwgxmA.png'          
    elif "晴時多雲" in weather_info:
          imageurl = 'https://i.imgur.com/M69byPq.png'	    	               
    elif "多雲" in weather_info:	
          imageurl = 'https://i.imgur.com/VMeO5Us.png'       	
    else:
          imageurl = 'https://i.imgur.com/P5EiNgQ.png' 	    	  
    message = [
	  TextSendMessage(text="["+cityname + "] 今天天氣狀態： " +  weather_info),
	  ImageSendMessage(original_content_url= imageurl, \
	        preview_image_url= imageurl)
	]
    return message      

import urllib.request 
def get_pm25(cityname): #取得 PM2.5資訊
    
    src = "http://opendata2.epa.gov.tw/AQI.json" #PM2.5 open data
    with urllib.request.urlopen(src) as response:
      data_list=json.load(response) # 取得json資料轉物件
      count = 0; PM25 = 0; AQI=0
      for item in data_list:
       if cityname == item["County"]:
        print(cityname, item["County"])
        PM25 = PM25 + int(item["PM2.5"])
        AQI = AQI + int(item["AQI"])
        count = count+1       
      AQI_info = "全台灣共有%d個測站，在%s共有%d個測站, PM2.5平均值為%f, 空氣品質平均指標(AQI)為%d" \
         % (len(data_list), cityname, count, round(PM25/count), round(AQI/count))
      print(AQI_info)
      if round(AQI/count) > 0 and round(AQI/count) <= 50:
        imageurl = 'https://i.imgur.com/crrkAuO.png'
      elif round(AQI/count) > 50 and round(AQI/count) <= 100:
        imageurl = 'https://i.imgur.com/4SJSYlp.png'
      elif round(AQI/count) > 100 and round(AQI/count) <= 150:
        imageurl = 'https://i.imgur.com/PEDG5xR.png' 
      elif round(AQI/count) > 150 and round(AQI/count) <= 300:
        imageurl = 'https://i.imgur.com/4MHNFFv.png' 
      elif round(AQI/count) > 300:
        imageurl = 'https://i.imgur.com/6d4R1HA.png'            
      message_all = [
         TextSendMessage(text="["+cityname + "] 空氣品質： " +  AQI_info),
         ImageSendMessage(original_content_url= imageurl, \
             preview_image_url= imageurl), 
         TextSendMessage(text="空氣品質監測網： " +  "https://liff.line.me/1654118646-8q4qo3vy")	      
     ]      
      return message_all
        
def sendCameraURL(ACCESS_TOKEN, ngrok_url):    
    notify = LineNotify(ACCESS_TOKEN) 
    notify.send('攝影機網址 ' + ngrok_url)        
           
def nlu(text): # 取得語意分析結果
  global nlu_text, songnum, songkind, client, genUrl_state	
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
    if status == 0 and type == 'smarthome':     
     action = temp['data']['nli'][0] ['semantic'][0]['modifier'][0]
     if action == 'playsong': #播放指定歌曲
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text) 
        songname = temp['data']['nli'][0]['semantic'][0]['slots'][0]['value']       
        message_list = yt_search(songname, userId)
        video_url = message_list[1]
        ref.child(base_users_userId + userId + '/youtube_music/').update({"songkind":songname})         
        ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":video_url})
        print("歌曲 {videourl} 更新成功...".format(videourl=video_url))      
        client.publish("music/youtubeurl", userId +'~'+ video_url, 2, retain=True) #發佈訊息 
        print("message published")
        time.sleep(1)
        client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息          
        message = nlu_text + '\n' + video_url       
        return [TextSendMessage(text=message_list[1]), message_list[0]]                                                                
               
     if action == 'playsinger': #播放指定歌手
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text) 
        singername = temp['data']['nli'][0]['semantic'][0]['slots'][0]['value']       
        message_list = yt_search(singername, userId)
        video_url = message_list[1]
        ref.child(base_users_userId + userId + '/youtube_music/').update({"songkind":singername})        
        ref.child(base_users_userId + userId + '/youtube_music/').update({"videourl":video_url})
        print("歌曲 {videourl} 更新成功...".format(videourl=video_url))      
        client.publish("music/youtubeurl", userId +'~'+ video_url, 2, retain=True) #發佈訊息 
        print("message published")
        time.sleep(1)
        client.publish("music/youtubeurl", '', 2, retain=True) #發佈訊息         
        message = nlu_text + '\n' + video_url              
        return message_list[0]                              

     if action == 'playpause': #播放暫停/繼續
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text)
        mqttmsg ='playpause'
        client.publish("music/pause_play", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息              
        print("message published")
        message = nlu_text
        return  TextSendMessage(text=message)        

     if action == 'adjust': #調整音量
         #userId = 'Ubf2b9f4188d45848fb4697d41c962591'
         users_userId_ref = ref.child(base_users_userId + userId + '/youtube_music/volume')
         volume_str = users_userId_ref.get()         
         volume = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value']         
         nlu_text = temp['data']['nli'][0]['desc_obj']['result']
         print('nlu', nlu_text)
         if volume == '大聲':
             print("volume....",volume_str)
             volume_num = int(volume_str) + 10            
             print("volume_num ", volume_num )             
             mqttmsg = str(volume_num )           
             client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息                             
         elif volume == '小聲':
              volume_num = int(volume_str) - 10             
              mqttmsg = str(volume_num )           
              client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息              
         elif volume == '最小聲':
              volume_num = 50                          
              mqttmsg = str(volume_num )           
              client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息   
         elif volume == '最大聲':
              volume_num = 100
              mqttmsg = str(volume_num )               
              client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息           
         elif volume == '適中' or volume == '剛好':
              volume_num = 70              
              mqttmsg = str(volume_num)               
              client.publish("music/volume", userId+'~'+ mqttmsg, 0, retain=False) #發佈訊息
         print('volume....', volume_num)      
         message = nlu_text + '至 ' + str(volume_num) + '%' 
         return TextSendMessage(text=message)            
   
     if action == 'query':
        solt_item1 = temp['data']['nli'][0] ['semantic'][0]['slots'][0]['value']
        print(solt_item1)
        if solt_item1 == '天氣':
            cityname = temp['data']['nli'][0] ['semantic'][0]['slots'][1]['value']
            print(cityname)
            weather_info = get_weather(cityname)
            print(weather_info)
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
                    uri = host + '/airbox'  
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
                    label = '翻譯設定', # 在按鈕模板上顯示的名稱
                    data = 'translator'  
                ),                    
                PostbackAction(
                    label = '音量設定', # 在按鈕模板上顯示的名稱
                    data = 'volume'  
                )        
            ]
         )
        )
    return buttons_template_message

# Setup YouTube API
KEY = 'AIzaSyCXdlB7xy9F2YJn7sYsNkmA4dE3PvbHVhw'
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'  
def yt_search(video_keywords, userId):
    youtube = build('youtube', 'v3', developerKey=KEY)

    # Get YouTube API results
    search_response = youtube.search().list(
        q=video_keywords, # 查詢文字
        type='video',
        part='id,snippet', # 把需要的資訊列出來
        maxResults=10 # 預設為五筆資料，可以設定1~50
    ).execute()
    items = search_response['items']
    #print(items)
    if not items:
      return 'Error: No YouTube results'
    else:
      videos = list(map(video_filter, items)) 
      carouselitems = []
     # 動態加入歌手清單  
      num = random.randint(0,len(videos))
      print(num)
      youtube_url = f'{videos[num]["影片網址"]}'      
      print(youtube_url)
      video_thumbnail = f'{videos[num]["封面照片"]}'
      video_title = f'{videos[num]["影片名稱"]}'
      print(youtube_url, video_thumbnail, video_title)
      time.sleep(1) 
      items = gen_carouseltemplate_items(videos, video_keywords)      
      carousel_template_message = TemplateSendMessage(
        alt_text = '這是一個輪播模板',  # 通知訊息的名稱
        template = CarouselTemplate(
           columns = items
       )
     )      
      
      yt_search_message = [
        carousel_template_message, 
        youtube_url 
      ]
      
      return  yt_search_message 

def gen_carouseltemplate_items(videos, video_keywords):
      items = []
    # 動態加入影片清單
      for key in range(len(videos)):
        youtube_url = f'{videos[key]["影片網址"]}'      
        print(youtube_url)
        video_thumbnail = f'{videos[key]["封面照片"]}'
        video_title = f'{videos[key]["影片名稱"]}'
        print(youtube_url, video_thumbnail, video_title)        
        items.append(CarouselColumn(         
          thumbnail_image_url = video_thumbnail,  # 呈現圖片
          #title = video_keywords,  # 你要顯示的標題 
          title = video_title[0:20]+'...',  # 你要顯示的標題          
          text = '想聽就直接點選...',  # 你想問的問題或是敘述
          actions = [
            PostbackAction(
             label = '播放器播放',  # 顯示的文字                           
             data = f"mqtt_publish~{youtube_url}~{video_keywords}~{userId}"  # 取得控制資料             
            ),                        
            URIAction(
             label = '本機播放',  # 顯示的文字 
             uri = youtube_url   # 跳轉的url
            )
           ]                         
        ))
      return items          
  
# Sent an HTML page with the top ten videos
def video_filter(api_video):
  title = api_video['snippet']['title']         
  kind = api_video['id']['kind']
  videoid = api_video['id']['videoId']
  url = f'https://youtu.be/{videoid}'
  thumbnails = api_video['snippet']['thumbnails']['medium']['url']
  return {
            '影片名稱': title,
            '影片種類': kind,
            '影片網址': url,
            '封面照片':thumbnails
  }
    
    
def linenotify_menu():
    buttons_template_message = TemplateSendMessage(
         alt_text = '我是LineNotify連動設定按鈕選單模板',
         template = ButtonsTemplate(
            thumbnail_image_url = 'https://i.imgur.com/he05XcJ.png', 
            title = 'LineNotify 連動設定選單',  # 你的標題名稱
            text = '請選擇：',  # 你要問的問題，或是文字敘述            
            actions = [ # action 最多只能4個喔！
                URIAction(
                    label = 'LineNotify 連動設定', # 在按鈕模板上顯示的名稱
                    uri = 'https://liff.line.me/1654118646-4ANQr5B3'  # 跳轉到的url，看你要改什麼都行，只要是url                    
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
                    uri = host +'/appliances' # 跳轉到的url，看你要改什麼都行，只要是url                    
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
                ),
                PostbackAction(
                    label = '影像辨識', # 在按鈕模板上顯示的名稱
                    data = 'AIImage' 
                )            
            ]
         )
        )
    return buttons_template_message 
    
# 資料推播至 LineNotify    
def lineNotifyMessage(token, msg):
      headers = {
          "Authorization": "Bearer " + token,
          "Content-Type" : "application/x-www-form-urlencoded"
      }
      payload = {'message': msg}
      r = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
      return r.status_code
          
#定義任務的內容
def scheduled_job():
   now_datetime = datetime.datetime.now()
   print("顯示目前時間: ", now_datetime) 
   result = subprocess.getoutput("sh ./twstockGet.sh")  
   lineNotifyMessage(line_token, "股票資訊\n: " + result)     
    
def scheduler_task():
    scheduler = APScheduler()
    scheduler.init_app(app)
    #定時任務，每隔10s執行1次
    scheduler.add_job(func=scheduled_job, trigger='interval', minutes=30,id='my_job_id' )
    #scheduler.add_job(func=scheduled_job, trigger='cron', day_of_week='mon-fri', hour='9-14', minute='0-59',id='my_job_id' )
    scheduler.start()
    
def on_connect(client, userdata, flags, rc):  
    print("Connected with result code "+str(rc))
    #client.subscribe("music/genurl", 0) 
    client.subscribe("homesecurity/ngrokurl", 2)       

def on_message(client, userdata, msg): 
    global camera_url, camera_id         
    print(msg.topic + " " + str(msg.payload))     
                
#寫在 main 裏面，IIS不會運行
scheduler_task()
client = mqtt.Client()    
client.on_connect = on_connect  
client.on_message = on_message  
client.connect("broker.mqttdashboard.com", 1883) 
client.loop_start()

if __name__ == "__main__":           
  app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)    

    
    
