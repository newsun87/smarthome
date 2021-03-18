from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import mimetypes
import os

def uploadfile_gdrive(filepath, filename):   
  gauth = GoogleAuth()
  #gauth.CommandLineAuth() #透過授權碼認證
  drive = GoogleDrive(gauth)  
  try:
    folder_id = '1uYAtUM8wqJ8QdtyQHWobWCWSgtP6KNyu'
    #上傳檔案至指定目錄及設定檔名     
    gfile = drive.CreateFile({"parents":[{"kind": "drive#fileLink", "id": folder_id}], 'title': filename})
    #指定上傳檔案的內容    
    gfile.SetContentFile(filepath)
    gfile.Upload() # Upload the file.
    print("Uploading succeeded!")    
    if gfile.uploaded:
      os.remove(filepath)
      result = '檔案傳送完成...'              
  except:
    print("Uploading failed.")
    result = '檔案傳送失敗...'
  return result 

#basepath = os.path.dirname(__file__)
basepath = os.path.dirname(os.path.realpath(__file__))
print('basepath...', basepath)
filename = 'stream.m4a' 
upload_path = os.path.join(basepath, 'static', filename) 
file_type = mimetypes.guess_type(filename)[0]
file_path = os.path.join(basepath, 'static', filename)
result = uploadfile_gdrive(file_path, filename)

