from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.CommandLineAuth() #透過授權碼認證
drive = GoogleDrive(gauth)

file1 = drive.CreateFile({'title': 'Hello.txt'})  # 建立檔案
file1.SetContentString('Hello World!') # 編輯檔案內容
file1.Upload() #檔案上傳
