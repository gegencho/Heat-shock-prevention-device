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
import datetime

import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import json

# for Switchbot
OPEN_TOKEN = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
API_HOST = 'https://api.switch-bot.com'
DEBIVELIST_URL = f"{API_HOST}/v1.0/devices"
HEADERS = {
    'Authorization': OPEN_TOKEN,
    'Content-Type': 'application/json; charset=utf8'
}

# google.oauth2認証
# Googleスプレッドへの読み込み・書き込み
KEY_NAME = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google認証キー
GOOGLE_FOLDER_ID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google DriveのフォルダーID
GOOGLE_SHEET_ID = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX' # Google SheetのID
TERMINAL_ID = '脱衣所' # 端末ID

# LINE Notifyのアクセストークンを設定 (GEN LINE)
access_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

# 温度センサーの補正
hosei = 4.0 

# GPIOピン番号の定義
DHT_PIN = 26
LED_R_PIN = 17
LED_G_PIN = 18
LED_B_PIN = 27
BUZZER_PIN = 13
BUTTON_PIN = 24

# GPIO初期化
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_R_PIN, GPIO.OUT)
GPIO.setup(LED_G_PIN, GPIO.OUT)
GPIO.setup(LED_B_PIN, GPIO.OUT)
GPIO.setup(BUZZER_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 温湿度センサーのセットアップ
DHT_SENSOR = Adafruit_DHT.DHT22

def get_temperature():
    humidity, ima_temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return ima_temperature

def set_led_color(color):
    GPIO.output(LED_R_PIN, color[0])
    GPIO.output(LED_G_PIN, color[1])
    GPIO.output(LED_B_PIN, color[2])

def buzz(duration): 
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.LOW)
    time.sleep(duration)
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
    
def setup():
    # Set the GPIO modes to BCM Numbering
    GPIO.setmode(GPIO.BCM)
    # Set LedPin's mode to output,
    # and initial level to High(3.3v)
    GPIO.setup(BUZZER_PIN, GPIO.OUT, initial=GPIO.HIGH)
    
def linemsg(message):
    payload = {'message': message}
    headers = {'Authorization': 'Bearer ' + access_token}
    requests.post('https://notify-api.line.me/api/notify', data=payload, headers=headers)

def _get_request(url):
    res = requests.get(url, headers=HEADERS)
    data = res.json()
    if data['message'] == 'success':
        return res.json()
    return {}

def _post_request(url, params):
    res = requests.post(url, data=json.dumps(params), headers=HEADERS) 
    data = res.json()
    if data['message'] == 'success':
        return res.json()
    return {}

def get_device_list():
    try:
        return _get_request(DEBIVELIST_URL)["body"]
    except:
        return

def get_virtual_device_list():
    devices = get_device_list()
    return devices['infraredRemoteList']

def send_dyson_on(deviceId):
    url = f"{API_HOST}/v1.0/devices/{deviceId}/commands"
    params = {
        "command":"turnOn",
        "parameter":"default",
        "commandType":"command"
    }
    res = _post_request(url, params)
    if res['message'] == 'success':
        return res
    return {}

def send_dyson_off(deviceId):
    url = f"{API_HOST}/v1.0/devices/{deviceId}/commands"
    params = {
        "command":"turnOff",
        "parameter":"default",
        "commandType":"command"
    }
    res = _post_request(url, params)
    if res['message'] == 'success':
        return res
    return {}
    
    
def main():
    # 初期化
    set_led_color((0, 0, 0)) # LED 白色に
    ima_temperature = float(get_temperature()-hosei)
    last_update_time = time.time()
    button_state = 0
    gyo_count = 2
    bus_ok = 0
    dyson_on = 0
   
    while True:
        # 測定温度の取得
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
        
            now = datetime.datetime.now() # 現在の日時を取得
            formatted_now = now.strftime("%Y-%m-%d %H:%M:%S") # 日時表示フォーマット
            ima_temperature = float(get_temperature()-hosei) # 居間の測定温度を取得
            print("Button pushed") # ボタンが押された事をコマンドラインに表示
            print("{}".format(formatted_now)) # 日時をコマンドラインに表示
            print("Living room  : {:.1f} C".format(ima_temperature)) # 居間の測定温度をコマンドラインに表示

            if button_state == 0:
                set_led_color((1, 1, 1)) # LEDを白色に点灯
                button_state = 1 # ボタンが押された:button_state=1

                linemsg('お風呂入るよ') # 1回目のボタンが押されたので「お風呂入るよ」のLINE通知
                
                # 20秒おきに測定温度を取得し、LEDを点灯
                while(bus_ok == 0):
                    if time.time() - last_update_time > 20:
                        ima_temperature = float(get_temperature()-hosei)  # 居間の測定温度を取得
                        now = datetime.datetime.now() # 現在の日時を取得
                        formatted_now = now.strftime("%H:%M:%S") # 時間表示フォーマット
                        last_update_time = time.time() # 20秒経過
                        print("{}".format(formatted_now)) # 日時をコマンドラインに表示
                        print("Living room  : {:.1f} C".format(ima_temperature)) # 居間の測定温度をコマンドラインに表示

                        # 脱衣所の測定値をスプレッドシートから読込                        
                        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'] # スプレッドシートとドライブに対するフルアクセス権限
                        credentials = service_account.Credentials.from_service_account_file(filename=KEY_NAME, scopes=scope)
                        gc = gspread.authorize(credentials) # Google Sheet認証
                        wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
                        records = wks.get_all_values() # 中身を取り出して配列に保存

                        wks.update_cell(gyo_count, 1, formatted_now) # 現在時刻を更新する(行、列で指定)                        
                        wks.update_cell(gyo_count, 2, ima_temperature) # 居間の測定値を更新する(行、列で指定)
                        time.sleep(10)
                        
                        # da_temperature = float(records[gyo_count][2])  # 脱衣所の測定値を読み込む
                        da_temperature = float(wks.cell(gyo_count, 3).value) # 脱衣所の測定値を読み込む
                        # print("Dressing room: {:.1f} C".format(da_temperature))
                        
                        while True:
                            if da_temperature is not None: # 脱衣所の測定温度がセルに入っているなら
                                gyo_count = gyo_count+1
                                print("da_temp get") # 脱衣所の温度をゲット　コマンドラインに表示   
                                print("Dressing room: {:.1f} C".format(da_temperature))
                           
                                # 測定差（居間温度-脱衣所温度）が3.1℃以上ならLEDを赤点灯 			
                                if ima_temperature - da_temperature > 3.0:
                                    set_led_color((1, 0, 0)) # 赤

                                    # SwitchbotからダイソンをON 			
                                    sbdata = get_virtual_device_list()
                                    for device in sbdata:
                                        if device['remoteType'] == 'DIY Fan':
                                            status = send_dyson_on(device['deviceId'])
                                            #print(status)
                                            break
                                    dyson_on = 1
                                    break

                                # 測定差が3.0℃以下ならLEDを緑点灯、ブザーを鳴らす、「お風呂準備OK！」のLINEK通知  	
                                else:
                                    set_led_color((0, 1, 0)) # 緑
                                    buzz(1)            
                                    linemsg('お風呂準備OK！')
                                    bus_ok = 1
                                    break   
                                break 
                            else:                        
                                print("da_temp not get")
                                      
            else:
                # 再度ボタンが押されたら、LEDを消す、「お風呂出たよ」のLINE通知、ダイソンをOFF  	
                set_led_color((0, 0, 0)) # LED OFF
                bus_ok = 0
                linemsg('お風呂出たよ')    
                button_state = 0   
                
                if dyson_on == 1:
                    # SwitchbotからダイソンをOFF 			
                    sbdata = get_virtual_device_list()
                    for device in sbdata:
                        if device['remoteType'] == 'DIY Fan':
                            status = send_dyson_off(device['deviceId'])
                            #print(status)
                            break
                    dyson_on = 0

             
        time.sleep(0.1)


def destroy():
    # Turn off buzzer
    GPIO.output(BUZZER_PIN, GPIO.HIGH)
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
