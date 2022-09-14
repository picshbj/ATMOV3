import json
import websockets
import asyncio
import os
import datetime
import random
import time 
import shutil
        
RELAY1_PIN = 17
RELAY2_PIN = 27
RELAY3_PIN = 22
RELAY4_PIN = 18
RELAY5_PIN = 25
RELAY6_PIN = 8
RELAY7_PIN = 12
RELAY8_PIN = 13
DIP1_PIN_2 = 19
DIP2_PIN_1 = 16
DIP3_PIN_4 = 26
DIP4_PIN_3 = 20

global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, RELAYS_PARAM, SERVER_STATUS, SENSOR_STATUS
Channel = CO2 = TVOC = PM25 = TEMP = HUMID = LIGHT = WATER1 = WATER2 = WATER3 = 0
SERVER_STATUS = True
SENSOR_STATUS = False

VERSION = '1.3'

IS_PI = True

if IS_PI:
    import RPi.GPIO as GPIO

    while True:
        try:
            import serial_asyncio
            print('serial_asyncio import succeed!')
            break
        except Exception as e:
            print('This system has no serial_asyncio module..')
            print('Installing serial_asyncio module..')
            os.system('pip3 install pyserial-asyncio')
            time.sleep(5)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(RELAY1_PIN, GPIO.OUT)
    GPIO.setup(RELAY2_PIN, GPIO.OUT)
    GPIO.setup(RELAY3_PIN, GPIO.OUT)
    GPIO.setup(RELAY4_PIN, GPIO.OUT)
    GPIO.setup(RELAY5_PIN, GPIO.OUT)
    GPIO.setup(RELAY6_PIN, GPIO.OUT)
    GPIO.setup(RELAY7_PIN, GPIO.OUT)
    GPIO.setup(RELAY8_PIN, GPIO.OUT)
    GPIO.setup(DIP1_PIN_2, GPIO.IN)
    GPIO.setup(DIP2_PIN_1, GPIO.IN)
    GPIO.setup(DIP3_PIN_4, GPIO.IN)
    GPIO.setup(DIP4_PIN_3, GPIO.IN)

    f = open('/home/pi/Desktop/settings.txt', 'r')
    setting_id = ''
    for line in f:
        d = line.split(':')
        if d[0] == 'DEVICE_ID':
            setting_id = d[1]
            setting_id = setting_id.replace(' ', '')
            setting_id = setting_id.replace('\n', '')
    f.close()

    uri = 'ws://v3.atmo.kr/atmo_ws?%s' % (setting_id)

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
    
    class InputChunkProtocol(asyncio.Protocol):
        def __init__(self):
            self.line = ''
            self.serial_watchdog = 0
            self.watchdog_cnt = 0
            
        def connection_made(self, transport):
            self.transport = transport
        
        def data_received(self, data):
            global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS
            
            if len(data) > 0:
                self.line += str(data, 'utf-8')
            print('\n[Sensor sData]', self.line)
                            
            if ('{' in self.line and '}' in self.line) and (self.line.find('{') < self.line.find('}')):
                line = self.line[self.line.find('{'):self.line.find('}')+1]
                self.line = ''
                print('[Sensor Data]', line)
                try:
                    if len(line) > 0:
                        d = json.loads(line)
                        Channel = d['CH']
                        
                        if int(Channel) == readDipSW():
                            CO2 = int(d['CO2'])
                            TVOC = int(d['TVOC'])
                            PM25 = int(d['PM25'])
                            TEMP = float(d['TEMP'])
                            HUMID = float(d['HUMID'])
                            LIGHT = int(d['LIGHT'])
                            self.serial_watchdog = time.time()
                            SENSOR_STATUS = True
                            self.watchdog_cnt = 0
                        
                except Exception as e:
                    SERVER_STATUS = False
                    print('Serial Error:', e)
            elif ('{' in self.line and '}' in self.line) and (self.line.find('{') > self.line.find('}')):
                self.line = self.line[self.line.find('{'):]
                
            if time.time() - self.serial_watchdog > 10.0:
                SENSOR_STATUS = False
                self.watchdog_cnt += 1
                if self.watchdog_cnt > 10:
                    SERVER_STATUS = False
            
            self.pause_reading()
            
        def pause_reading(self):
            self.transport.pause_reading()
            
        def resume_reading(self):
            self.transport.resume_reading()

    async def reader():
        global SERVER_STATUS
        transport, protocol = await serial_asyncio.create_serial_connection(loop, InputChunkProtocol, '/dev/serial0', baudrate=9600)
        
        while True:
            if not SERVER_STATUS: break
            await asyncio.sleep(1)
            try:
                protocol.resume_reading()
                
            except Exception as e:
                SERVER_STATUS = False
                print('Serial Reader Error:', e)
                
        raise RuntimeError('Serial Read Error')    

else:
    class GPIO():
        def output(pin, value):
            if pin == 17:
                print('RELAY1 set', value)
            elif pin == 27:
                print('RELAY2 set', value)
            elif pin == 22:
                print('RELAY3 set', value)
            elif pin == 18:
                print('RELAY4 set', value)
            elif pin == 25:
                print('RELAY5 set', value)
            elif pin == 8:
                print('RELAY6 set', value)
            elif pin == 12:
                print('RELAY7 set', value)
            elif pin == 13:
                print('RELAY8 set', value)
            else:
                print('Wrong pin number')
        
        def input(pin):
            return 1
    
    setting_id = '8d3cd'
    uri = 'ws://127.0.0.1/atmo_ws?%s' % (setting_id)

    async def reader():
        global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS
        
        while True:
            if not SERVER_STATUS: break
            await asyncio.sleep(1)
            try:
                CO2 = random.randint(20,25)
                TVOC = random.randint(100,110)
                PM25 = random.randint(10,20)
                TEMP = 26.6
                HUMID = 54.2
                LIGHT = random.randint(550,560)
                SENSOR_STATUS = True

            except Exception as e:
                SERVER_STATUS = False
                print('Serial Reader Error:', e)
                
        raise RuntimeError('Serial Read Error')



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
    global RELAYS_PARAM
    RELAYS_PARAM = []
    if os.path.exists('./saved.json'):
        with open('./saved.json', 'r', encoding='utf-8') as read_file:
            d = json.load(read_file)
            for relay in d['CONTROL']:
                RELAYS_PARAM.append(json.dumps(relay))
                
    else:
        RELAYS_PARAM = ['{"RELAY":"1", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"2", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"3", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"4", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"5", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"6", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"7", "MODE":"onoff", "SETINFO":"off"}', '{"RELAY":"8", "MODE":"onoff", "SETINFO":"off"}']
    

def runManualMode(SETINFO):
    if SETINFO == 'on': return True
    else: return False
                
def runPeriodictMode(SETINFO):
    # "SETINFO": {"START_DT": "20220909", "REPEAT_DAY": "15", "START_TIME": "0030", "END_TIME": "0100"}}
    scheduled_date = datetime.datetime.strptime(SETINFO['START_DT'], '%Y%m%d').replace(tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
    diff = now - scheduled_date

    if diff.days % int(SETINFO['REPEAT_DAY']) == 0:
        if int(SETINFO['START_TIME']) <= now.hour*100 + now.minute < int(SETINFO['END_TIME']):
            return True

    return False

def runWeeklyRepeatMode(SETINFO):
    # "SETINFO": [{"WEEK_INFO": "1", "START_TIME": "0100", "END_TIME": "0200"}, {"WEEK_INFO": "2", "START_TIME": "0100", "END_TIME": "0200"}]
    # Mon(1), Tue(2), Wed(3), Thu(4), Fri(5), Sat(6), Sun(7)
    now = datetime.datetime.now(tz=datetime.timezone(datetime.timedelta(hours=9)))
    
    for element in SETINFO:
        if int(element['WEEK_INFO']) == now.weekday()+1:
            if int(element['START_TIME']) <= now.hour*100 + now.minute < int(element['END_TIME']):
                return True
    
    return False

def readDipSW():
    num = 0
    if GPIO.input(DIP2_PIN_1) == 0:
        num += 8
    if GPIO.input(DIP1_PIN_2) == 0:
        num += 4
    if GPIO.input(DIP4_PIN_3) == 0:
        num += 2
    if GPIO.input(DIP3_PIN_4) == 0:
        num += 1
    
    return num

def updateRelay():
    global RELAYS_PARAM
    
    try:
        print('\n--------------- checking relay params ---------------')
        for relay in RELAYS_PARAM:
            result = False

            relay = json.loads(relay)
            print(relay)
            
            if relay['MODE'] == 'onoff':   # manual mode
                result = runManualMode(relay['SETINFO'])
            
            elif relay['MODE'] == 'repeat':   # weekly repeat mode
                result = runWeeklyRepeatMode(relay['SETINFO'])

            elif relay['MODE'] == 'week': # periodic mode
                result = runPeriodictMode(relay['SETINFO'])

            if result:
                if relay['RELAY'] == '1': GPIO.output(RELAY1_PIN, True)
                if relay['RELAY'] == '2': GPIO.output(RELAY2_PIN, True)
                if relay['RELAY'] == '3': GPIO.output(RELAY3_PIN, True)
                if relay['RELAY'] == '4': GPIO.output(RELAY4_PIN, True)
                if relay['RELAY'] == '5': GPIO.output(RELAY5_PIN, True)
            else:
                if relay['RELAY'] == '1': GPIO.output(RELAY1_PIN, False)
                if relay['RELAY'] == '2': GPIO.output(RELAY2_PIN, False)
                if relay['RELAY'] == '3': GPIO.output(RELAY3_PIN, False)
                if relay['RELAY'] == '4': GPIO.output(RELAY4_PIN, False)
                if relay['RELAY'] == '5': GPIO.output(RELAY5_PIN, False)
        print('-----------------------------------------------------\n')
    except Exception as e:
        print(e)
    
async def send_sensor_data(ws):
    global Channel, CO2, TVOC, PM25, TEMP, HUMID, LIGHT, WATER1, WATER2, WATER3, SERVER_STATUS, SENSOR_STATUS

    DB_time_check = 0
    WEB_time_check = 0
    relay_time_check = 0
    
    while True:
        await asyncio.sleep(0)
        if not SERVER_STATUS: break
        try:
            if SENSOR_STATUS:
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
                    print('[DB PUSH]', pData)
                    await ws.send(pData)
                    
                if int(time.time()) - WEB_time_check > 60:   # web update per every 60 sec
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
                    print('[WEB PUSH]', pData)
                    await ws.send(pData)
            else:
                if int(time.time()) - WEB_time_check > 1:   # DO NOT CHANGE THE VALUE
                    WEB_time_check = int(time.time())
                    print('Sensor Status False')
                
            
            if int(time.time()) - relay_time_check > 5: # check relay every 5 sec
                relay_time_check = int(time.time())
                updateRelay()
                
        except Exception as e:
            SERVER_STATUS = False
            print('Sender Error', e)

async def recv_handler(ws):
    global RELAYS_PARAM, SERVER_STATUS, SENSOR_STATUS
    
    while True:
        await asyncio.sleep(0)
        if not SERVER_STATUS: break
        try:
            data = await ws.recv()
            d = json.loads(data)
            print('recieved:', d)
            
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
                    # print(relay)
                    if relay['RELAY'] == "1":
                        RELAYS_PARAM[0] = json.dumps(relay)
                    elif relay['RELAY'] == "2":
                        RELAYS_PARAM[1] = json.dumps(relay)
                    elif relay['RELAY'] == "3":
                        RELAYS_PARAM[2] = json.dumps(relay)
                    elif relay['RELAY'] == "4":
                        RELAYS_PARAM[3] = json.dumps(relay)
                    elif relay['RELAY'] == "5":
                        RELAYS_PARAM[4] = json.dumps(relay)
                    elif relay['RELAY'] == "6":
                        RELAYS_PARAM[5] = json.dumps(relay)
                    elif relay['RELAY'] == "7":
                        RELAYS_PARAM[6] = json.dumps(relay)
                    elif relay['RELAY'] == "8":
                        RELAYS_PARAM[7] = json.dumps(relay)
                saveParams(RELAYS_PARAM)

            elif d['METHOD'] == 'TOTAL_STATUS':
                params = {
                    "METHOD": "TOTAL_STATUS",
                    "DEVICE_ID": setting_id,
                    "SENSOR_STATUS": SENSOR_STATUS,
                    "VERSION": VERSION
                }
                pData = json.dumps(params)
                await ws.send(pData)

            elif d['METHOD'] == 'REBOOT':
                params = {
                    "METHOD": "REBOOT",
                    "RESULT": True
                }
                pData = json.dumps(params)
                await ws.send(pData)
                await asyncio.sleep(5)
                os.system('shutdown -r now')
            
            elif d['METHOD'] == 'OTA':
                os.system('wget -P /home/pi/ https://raw.githubusercontent.com/picshbj/ATMOV3/main/main.py')
                
                path_src = '/home/pi/main.py'
                path_dest = '/home/pi/Documents/main.py'

                if os.path.isfile(path_src):
                    shutil.move(path_src, path_dest)
                
                await asyncio.sleep(10)

                params = {
                    "METHOD": "OTA",
                    "RESULT": True
                }
                pData = json.dumps(params)
                await ws.send(pData)

                os.system('shutdown -r now')
                    

        except Exception as e:
            SERVER_STATUS = False
            print('Recieve Error', e)
            
            

async def main():
    global SERVER_STATUS
    readParams()
    
    while True:
        print('Creating a new websockets..')
        SERVER_STATUS = True
        
        try:
            async with websockets.connect(uri) as ws:
                await asyncio.gather(
                    send_sensor_data(ws),
                    recv_handler(ws),
                    reader()
                )
        except Exception as e:
            print('Main Error:', e)
            await asyncio.sleep(5)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()
