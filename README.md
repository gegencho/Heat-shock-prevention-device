# Heat-shock protection system
本システムは高齢者を対象とした、ヒートショック対策を行う
親機用ソフト(Heatshock_P)と子機用ソフト(Heatshock_C)から成り立つ

## [ソフト名]Heatshock_P

##### [制作日]2023/2/25

##### [制作者]gegencho

##### [動作環境]  
	RaspberryPi 3 Model B  
	Python  
	温湿度センサーDHT22
	入力ボタン  
	RGB LED
	アクティブブザー

##### [GPIOピン番号の定義]  
	DHT_PIN = 26  
	LED_R_PIN = 17  
	LED_G_PIN = 18  
	LED_B_PIN = 27  
	BUZZER_PIN = 13  
	BUTTON_PIN = 24  
 
##### [外部制御対象]	
	Google スプレッドシート GAS
	SwitchBot Hub mini + Dyson Pure Hot+cool
	LINE

## [ソフト名]Heatshock_C

##### [制作日]2023/2/23

##### [制作者]gegencho

##### [動作環境]  
	RaspberryPizero 2w  
	Python  
	温湿度センサーDHT22

##### [GPIOピン番号の定義]  
	DHT_PIN = 26
 
##### [外部制御対象]
	Google スプレッドシート GAS


