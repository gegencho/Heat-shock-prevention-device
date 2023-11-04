"""
Created on Feb 18 2023
@author: gegencho
"""

import sys
sys.path.insert(0, '/usr/local/lib/python3.9/dist-packages')
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import requests

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# google.oauth2認証
# Googleスプレッドへの読み込み・書き込み
KEY_NAME = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google認証キー
GOOGLE_FOLDER_ID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google DriveのフォルダーID
GOOGLE_SHEET_ID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google SheetのID
#TERMINAL_ID = '脱衣所' # 端末ID

hosei = 2.0 

# GPIOピン番号の定義
DHT_PIN = 26

# GPIO初期化
GPIO.setmode(GPIO.BCM)

# 温湿度センサーのセットアップ
DHT_SENSOR = Adafruit_DHT.DHT22

def setup():
    # Set the GPIO modes to BCM Numbering
    GPIO.setmode(GPIO.BCM)
    # Set LedPin's mode to output,
    # and initial level to High(3.3v)
#    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.HIGH)

def get_temperature():
    humidity, da_temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return da_temperature

def main():
    # 初期化
    da_temperature = float(get_temperature()+hosei)
    last_update_time = time.time()
#    button_state = 0

    ima_cell_row = 2 # 居間測定値のセルの行
    ima_cell_col = 2 # 居間測定値のセルの列　（変わらない）

    dat_cell_row = 2 # 脱衣所測定値のセルの行    
    dat_cell_col = 3 # 脱衣所測定値のセルの列　（変わらない）


    # 脱衣所の測定値をスプレッドシートに書込む                       
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'] # スプレッドシートとドライブに対するフルアクセス権限
    credentials = service_account.Credentials.from_service_account_file(filename=KEY_NAME, scopes=scope)
    gc = gspread.authorize(credentials) # Google Sheet認証
    wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
#            records = wks.get_all_values() # 中身を取り出して配列に保存

    # 居間の測定値B列に入力があった場合、脱衣所の測定値をC列に書き込む
    while True:             
        da_temperature = float(get_temperature()+hosei) # 測定温度を取得
        print("Dressing room: {:.1f} C".format(da_temperature))

        a1_value = wks.cell(ima_cell_row, 2).value # 居間の測定値を読み込む
        print(a1_value)            

        if a1_value is not None:
            print("ima_temp get")             
            wks.update_cell(dat_cell_row, dat_cell_col, da_temperature) # 脱衣所の測定値を更新する(2行、B列で指定)                    
            dat_cell_row = dat_cell_row+1
            ima_cell_row = ima_cell_row+1          
        else:
            print("ima_temp not get")  


        time.sleep(5)

 
def destroy():
    # Turn off buzzer
#    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    # Release resource
    GPIO.cleanup()

# If run this script directly, do:
if __name__ == '__main__':
    setup()
    try:
        main()
    # When 'Ctrl+C' is pressed, the program
    # destroy() will be  executed.
    except KeyboardInterrupt:
        destroy()
