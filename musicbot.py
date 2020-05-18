# -*- coding: UTF-8 -*-

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

from flask import render_template
import paho.mqtt.client as mqtt

import os
import json
import random
import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

#取得通行憑證
cred = credentials.Certificate("serviceAccount.json")
firebase_admin.initialize_app(cred, {
    'databaseURL' : 'https://line-bot-test-77a80.firebaseio.com/'
})

access_token = "x5LS9O8T8tfm7A2lSeiEpLx6j2u9ZUj5z6mhg1l/gO6pC2BLIJh5NCf2/mwmj88iIiS7hrn8mNAsgPU9tFCDIB3jtOCqHirPrfcjBiftdZZ2C7eQ93iPCfDwY5tAE1Qq7CSUZsDMMBgutdADEiBnGQdB04t89/1O/w1cDnyilFU="
channel_secret = "f19d907284bd9d7332e034c3adf60b3c"
volume_num = 80
mqttmsg = str(volume_num )+'%'

app = Flask(__name__)

line_bot_api = LineBotApi(access_token)
handler = WebhookHandler(channel_secret)

@app.route('/')
def showPage():
 return render_template('index.html')

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

# 處理訊息
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
  elif event.message.text == 'music_play':
      ref = db.reference('/') # 參考路徑      
      videourl = users_userId_ref.get()['videourl'] 
      line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="馬上播放 " + videourl))
      client.publish("youtube_url", videourl, 0, True)
  elif event.message.text == '歌曲資訊':      
      users_userId_ref = ref.child('youtube_music/'+ userId)
      videourl = users_userId_ref.get()['videourl']   	        
      line_bot_api.reply_message(
      event.reply_token,
      TextSendMessage(text="歌曲資訊 " + videourl)) 
  elif event.message.text == 'menu':
      QuickReply_text_message = TextSendMessage(
       text="點選你想要的操作功能",
       quick_reply = QuickReply(
        items = [
          QuickReplyButton(
            action = MessageAction(label = "使用說明", text = "help"),
            image_url = 'https://i.imgur.com/iIZYTVw.png'
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
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message) 
  elif event.message.text == 'favor':
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
          )                    
        ]
       )
      )
      line_bot_api.reply_message(event.reply_token, QuickReply_text_message)     
  elif event.message.text == 'help':
      with open('help.txt', mode='r', encoding = "utf-8") as f:
        content = f.read()
        print(content)      
        line_bot_api.reply_message(
         event.reply_token,
         TextSendMessage(text=content))     
  else:             
      musicplay(event.message.text)
      line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=nlu_text))           
            
def random_int_list(num):
  list = range(1, num)
  random_list = [*list]
  random.shuffle(random_list)
  return random_list

def musicplay(text):
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

    if action == 'playpause': #播放暫停/繼續
        nlu_text = temp['data']['nli'][0]['desc_obj']['result']
        print('nlu', nlu_text)
        mqttmsg ='playpause'
        client.publish("pause_play", mqttmsg, 0, retain=False) #發佈訊息
        print("message published")      

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
           
    if action == 'shutdown':            
      nlu_text = temp['data']['nli'][0]['desc_obj']['result']      
      mqttmsg = "shutdown"               
      client.publish("shutdown", mqttmsg, 0, retain=False) #發佈訊息                
      
  else:
      nlu_text = temp['data']['nli'][0]['desc_obj']['result']

  print("播放NLU結果的語音......"+ nlu_text)
  
def on_connect(client, userdata, flags, rc):  
    print("Connected with result code "+str(rc))
    client.subscribe("genurl", 0)    
  
def on_message(client, userdata, msg):      
    print(msg.topic + " " + str(msg.payload))         

client = mqtt.Client()  
client.on_connect = on_connect  
client.on_message = on_message  
client.connect("broker.mqttdashboard.com", 1883) 
client.publish("volume", mqttmsg, 0, retain=False) #發佈訊息 
client.loop_start()

if __name__ == "__main__":           
    app.run(debug=True, host='0.0.0.0', port=5000)    

    
    
