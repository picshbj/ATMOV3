import json
from requests import ReadTimeout
import websockets
import asyncio
import random
import serial
import time
import os

f = open('/home/pi/Desktop/settings.txt', 'r')
setting_id = ''
for line in f:
    d = line.split(':')
    if d[0] == 'DEVICE_ID':
        setting_id = d[1]
        setting_id = setting_id.replace(' ', '')
        setting_id = setting_id.replace('\n', '')
f.close()

f = open('/etc/xdg/lxsession/LXDE-pi/autostart','r')
data = ''
isChanged = False
for line in f:
    if 'atmo' in line:
        id = line.split('/')[1].replace('\n','')
        if setting_id != id:
            isChanged = True
        
        data += line.split('/')[0] + '/' + setting_id + '\n'
    else:
        data += line

f.close()

if isChanged:
    f = open('/etc/xdg/lxsession/LXDE-pi/autostart','w')
    f.write(data)
    f.close()
    os.system('shutdown -r now')




uri = 'ws://v3.atmo.kr/atmo_ws?%s' % (setting_id)


global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3
Channel = CO2 = TVOC = PM25 = TEMP = HUMID = LIGHT = WATER1 = WATER2 = WATER3 = 0

VERSION = '1.0'

def saveParams(RELAYS_PARAM):
    params = {
        "CONTROL": [json.loads(RELAYS_PARAM[0]),
                    json.loads(RELAYS_PARAM[1]),
                    json.loads(RELAYS_PARAM[2]),
                    json.loads(RELAYS_PARAM[3]),
                    json.loads(RELAYS_PARAM[4])
                    #json.loads(RELAYS_PARAM[5]),
                    #json.loads(RELAYS_PARAM[6]),
                    #json.loads(RELAYS_PARAM[7])
                    ]
        }
    with open('./saved.json', 'w', encoding='utf-8') as make_file:
        json.dump(params, make_file, indent='\t')

def readParams():
    RELAYS_PARAM = []
    if os.path.exists('./saved.json'):
        with open('./saved.json', 'r', encoding='utf-8') as read_file:
            d = json.load(read_file)
            for relay in d['CONTROL']:
                RELAYS_PARAM.append(json.dumps(relay))
                
    else:
        RELAYS_PARAM = ['{"RELAY":"1", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"2", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"3", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"4", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"5", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"6", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"7", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"8", "MODE":"onoff", "SETINFO":"off"}']
    
    return RELAYS_PARAM



def updateRelay(relay):
    pass

async def send_sensor_data():
    global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3
    ser = serial.Serial('/dev/serial0', 9600, timeout=3)
    
    DB_time_check = 0
    WEB_time_check = 0
    while True:
        async with websockets.connect(uri) as w:
            line = ''
            try:
                r = str(ser.read(), 'utf-8')
                if r == '{':
                    line += r
                    
                    while True:
                        r = str(ser.read(), 'utf-8')
                        line += r
                    
                        if r == '}':
                            # {"CH":0,"CO2":256,"TVOC":142,"PM25":11,"TEMP":28.9,"HUMID":46.3,"LIGHT":969}
                            try:
                                d = json.loads(line)
                                Channel = d['CH']
                                CO2 = int(d['CO2'])
                                TVOC = int(d['TVOC'])
                                PM25 = int(d['PM25'])
                                TEMP = float(d['TEMP'])
                                HUMID = float(d['HUMID'])
                                LIGHT = int(d['LIGHT'])
                            except Exception as e:
                                pass
                                
                            print('Sensors:', line)
                            break
            except Exception as e:
                pass
            
            if int(time.time()) - DB_time_check > 60 * 10:   # DB update per every 10 mins
                DB_time_check = int(time.time())
                params = {
                    "METHOD": "DBINIT",
                    "CO2": CO2,
                    "TVOC": TVOC,
                    "PM25": PM25,
                    "TEMP": TEMP,
                    "HUMID": HUMID,
                    "LIGHT": LIGHT
                }

                pData = json.dumps(params)
                print('DBINIT', pData)
                await w.send(pData)
                
            if int(time.time()) - WEB_time_check > 10:   # web update per every 10 sec
                WEB_time_check = int(time.time())
                params = {
                    "METHOD": "SEND_F",
                    "CO2": CO2,
                    "TVOC": TVOC,
                    "PM25": PM25,
                    "TEMP": TEMP,
                    "HUMID": HUMID,
                    "LIGHT": LIGHT,
                    "WATER1": 0,
                    "WATER2": 0,
                    "WATER3": 0
                }

                pData = json.dumps(params)
                print('WEB', pData)
                await w.send(pData)

async def recv_handler():
    async with websockets.connect(uri) as ws:
        RELAYS_PARAM = readParams()
        while True:
            try:
                data = await ws.recv()
                d = json.loads(data)
                
                if d['METHOD'] == 'CALL_A':
                    params = {
                    "METHOD": "CALL_R",
                    "CONTROL": [json.loads(RELAYS_PARAM[0]),
                                json.loads(RELAYS_PARAM[1]),
                                json.loads(RELAYS_PARAM[2]),
                                json.loads(RELAYS_PARAM[3]),
                                json.loads(RELAYS_PARAM[4])
                                #json.loads(RELAYS_PARAM[5]),
                                #json.loads(RELAYS_PARAM[6]),
                                #json.loads(RELAYS_PARAM[7])
                            ]
                    }
                    pData = json.dumps(params)
                    await ws.send(pData)
                    
                
                elif d['METHOD'] == 'UPT_R':
                    for relay in d['CONTROL']:
                        print(relay)
                        if relay['RELAY'] == "1":
                            RELAYS_PARAM[0] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "2":
                            RELAYS_PARAM[1] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "3":
                            RELAYS_PARAM[2] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "4":
                            RELAYS_PARAM[3] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "5":
                            RELAYS_PARAM[4] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "6":
                            RELAYS_PARAM[5] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "7":
                            RELAYS_PARAM[6] = json.dumps(relay)
                            updateRelay(relay)
                        elif relay['RELAY'] == "8":
                            RELAYS_PARAM[7] = json.dumps(relay)
                            updateRelay(relay)
                    saveParams(RELAYS_PARAM)
                
                elif d['METHOD'] == 'OTA':
                    path = '/home/pi/Documents/main.py'

                    if os.path.isfile(path):
                        os.remove(path)

                    os.system('wget -p /home/pi/Documents/ https://raw.githubusercontent.com/picshbj/ecsmartrelay/master/main.py')
                    os.system('mv /home/pi/Documents/raw.githubusercontent.com/picshbj/ecsmartrelay/master/main.py /home/pi/Documents/main.py')
                    time.sleep(20)
                    os.system('shutdown -r now')
                        

            except Exception as e:
                print(e)


async def main():
    task1 = asyncio.create_task(recv_handler())
    task2 = asyncio.create_task(send_sensor_data())
    await asyncio.wait([task1, task2])

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
