from machine import Pin, UART, ADC
import utime
import time
import CONS
import urtc
import json

wakeUp = Pin(14, Pin.IN, Pin.PULL_UP)



def clock_irq(second):
    for _ in range(second*10):
        if wakeUp.value() == 0:
            utime.sleep_ms(50)
            break
        else:
            utime.sleep_ms(100)

class device():
    def __init__(self):
        #Value
        self.unlockAuth = 0
        self.lockOpen = 0
        self.key = CONS.KEY
        #devices control pin
        self.BUZZER =  Pin(12, Pin.OUT)
        self.mainPower1 = Pin(7, Pin.OUT)
        self.mainPower2 = Pin(6, Pin.OUT)
        self.latch = Pin(13, Pin.OUT)
        self.ADCread = ADC(Pin(26))
    def batteryCap(self):
        batteryCapacitor = 0
        for i in range(10):
            readVoltage = self.ADCread.read_u16()
            readVoltage  = readVoltage - 47800
            batteryCapacitor += readVoltage/5650*100
        return int(batteryCapacitor/10)
    def buzzer(self, onTime):
        self.BUZZER.high()
        utime.sleep_ms(onTime)
        self.BUZZER.low()
    #unlock
    def latchOpen(self):
        self.latch.high()
        utime.sleep(3)
        self.latch.low()

### ULTRA SENSOR ###
class ultraS():
    def __init__(self):
        self.percent = 0
        self.trigger = Pin(17, Pin.OUT)
        self.echo = Pin(16, Pin.IN)
    def distanceCm_UART(self, UART):
        #clean the UART
        UART.read()
        utime.sleep_ms(200)
        #take in measure for 10 times 
        if UART.any():
                data = UART.read() # Your hexadecimal string
                startIndex = data.find(b'\xff')  # Find the first 0xff
                while startIndex != -1:  # Loop until no more 0xff is found
                    endIndex = data.find(b'\xff', startIndex + 1)  # Find the next 0xff
                    if endIndex != -1:  # If another 0xff is found
                        data = data[startIndex + 1:endIndex]  # Extract the data
                        dataH = int.from_bytes(data[:1], 'big')
                        dataL = int.from_bytes(data[1:2], 'big')
                        distanceMeasure = (dataH*256 + dataL)/10
                        #reset the loop
                        startIndex = -1
                        return distanceMeasure
        else:
            return 0
        
    def calVolume(self,h):
        Va = 34000
        Vb = 66000
        Vc = 34000
        if h >= 66:
            volume = 0
        elif h > 48:
            volume = Vc - ((1/3)*3.14)*(h-48)*(17.5*17.5 + 17.5*23 + 23*23)
        elif h == 48:
            volume = Vc
        elif h < 48 and h > 18:
            volume = Vc + (3.14*23*23)*(66-h-18)
        elif h == 18:
            volume = Vc + Vb
        elif h < 18:
            volume = Vc + Vb + ((1/3)*3.14)*(18 - h)*(17.5*17.5 + 17.5*23 + 23*23)
        return round(volume*(1/1000),1)
    
    def distanceCm(self):
        sumUp  = 0
        count = 0
        for i in range(5):
            utime.sleep_ms(60)
            signalon = 0
            signaloff = 0
            self.trigger.low()
            utime.sleep_us(20)
            self.trigger.high()
            utime.sleep_us(25)
            self.trigger.low()
            utime.sleep_us(10)
            startTime = utime.ticks_ms()
            while self.echo.value() == 0 and utime.ticks_diff(utime.ticks_ms(), startTime) < 40:
                signaloff = utime.ticks_us()
            while self.echo.value() == 1 and utime.ticks_diff(utime.ticks_ms(), startTime) < 80:
                signalon = utime.ticks_us()
            pulse_duration = signalon - signaloff
            distance = (pulse_duration*0.0343)/2
            distance = round(distance)
            if distance < 0:
                distance = 0
            elif distance > 250:
                distance = 250
            else:
                count += 1
                sumUp += distance
        if count == 0:
            return 0.0
        else:
            print(round(sumUp/count,1))
            return self.calVolume(round(sumUp/count,1))
    

### SIMCom ###
class SIMCom():
    def __init__(self, UART):
        self.UART = UART
        self.NUM = CONS.PHONE_NUM
        self.data = ''
        self.initS = 0
        self.warning = 0
        self.firstHandShake = 1
        self.authorization = 'Basic dnMgMzU6SWpsbE0yTXlZV1JtTFRNNVlqQXROREprTlMwNU9XTXo='
        self.contentType = 'application/json'  
    def handShake(self):                                        #check to see if the SIMCom is ready to commute
        #reset handshake bit
        timeOut = 500
        if self.firstHandShake == 1:
            startTime = utime.ticks_ms()
            while utime.ticks_diff(utime.ticks_ms(), startTime) <= timeOut:
                self.UART.read()                                    
                self.UART.write('AT\r')                             #init heart beat
                #buffer sleep for msg send
                utime.sleep_ms(100)
                if self.UART.any():
                    self.data = self.UART.read().decode().strip()    
                    if self.data == 'AT\r\r\nOK':                   #heart beat success
                        self.UART.write('ATE0\r')                   #turn off echo
                        #clear uart buffer
                        self.UART.read()                            
                        self.initS = 1
                        self.firstHandShake = 0
                        self.UART.read()
                        break                                       #indicate handshake success
        elif self.firstHandShake == 0:
            startTime = utime.ticks_ms()
            while utime.ticks_diff(utime.ticks_ms(), startTime) <= timeOut:
                self.UART.read()                                    
                self.UART.write('AT\r')                             #init heart beat
                #buffer sleep for msg send
                utime.sleep_ms(100)
                if self.UART.any():
                    self.data = self.UART.read().decode().strip()    
                    if self.data == 'OK':                   #heart beat success                           
                        self.initS = 1
                        self.UART.read()
                        break                                       #indicate handshake success
        if self.initS == 0:
            return 1
    def decodeMsg(self, data):
        startIndex = data.find(b'{')
        endIndex = data.find(b'}', startIndex + 1)
        data = data[startIndex:endIndex + 1]
        return data.decode()
    def MSG(self, msg):                                          #sending message to a destinated phone num
        confBit = 0
        timeOut = 1000
        startTime = utime.ticks_ms()
        self.UART.read()
        self.handShake()
        while utime.ticks_diff(utime.ticks_ms(), startTime) <= timeOut and self.initS:                                          #handshake successfully
            self.UART.read()
            self.UART.write('AT+CMGF=1\r')
            utime.sleep_ms(200)
            while not self.UART.any():
                pass
            if self.UART.read().decode().strip() == 'OK':
                numFormat = 'AT+CMGS=\"'+ self.NUM + '\"\r\n'
                self.UART.write(numFormat)
                utime.sleep_ms(100)
                self.UART.write(msg)
                self.UART.write(bytes([26])) #submit to sen the sms
                confBit = 1
                self.initS = 0
                break
            else:
                return 2
        if not confBit:
            return 2
    def HTTP_GET(self):
        trials = 0
        data = ''
        self.UART.read()
        self.handShake()
        if self.initS:
            self.handShake()
            #Enable SNI
            self.UART.write('AT+CSSLCFG="enableSNI",0,1\r')
            utime.sleep_ms(100)
            #clean the UART port
            self.UART.read()
            #start HTTP service and info
            self.UART.write('AT+HTTPINIT\r')
            utime.sleep_ms(100)
            self.UART.write('AT+HTTPPARA="URL","https://api.admin.bi-oil.app/vinschool-machine/get-auth"\r')
            utime.sleep_ms(100)
            self.UART.write(f'AT+HTTPPARA="USERDATA","Authorization: {self.authorization}"\r')
            utime.sleep_ms(200)
            while trials < 3 and (data == '' or data == None):
                utime.sleep_ms(100)
                self.UART.read()
                #get action
                self.UART.write('AT+HTTPACTION=0\r')
                #buffer time
                utime.sleep(3)
                self.UART.read()
                utime.sleep_ms(100)
                #read the respond
                self.UART.write('AT+HTTPREAD=0,300\r')
                utime.sleep(2)
                data = self.UART.read()
                trials = trials + 1
                if data != '' and data != None:
                    data = self.decodeMsg(data)
            self.UART.write('AT+HTTPTERM\r')
            utime.sleep_ms(100)
            self.UART.read()
            if data != '' and data != None:
                if data == '{"success":true,"authorized":true}':
                    return 0.1 
                else:
                    return 4.1
            else:
                return 4
        else:
            return 1
    #update when timer comes
    def postUpdate(self,vol,bat):
        #info
        url = "https://api.admin.bi-oil.app/vinschool-machine/"
        payload = '{"volume": ' + str(vol) + ',"battery": ' + str(bat) + '}'
        data = ''
        trials = 0
        self.UART.read()
        self.handShake()
        if self.initS and wakeUp:
            self.handShake()
            #Enable SNI
            self.UART.write('AT+CSSLCFG="enableSNI",0,1\r')
            utime.sleep_ms(100)
            self.UART.read()
            #start HTTP service and info
            self.UART.write('AT+HTTPINIT\r')
            utime.sleep_ms(200)
            self.UART.read()
            self.UART.write(f'AT+HTTPPARA="URL","{url}"\r')
            utime.sleep_ms(150)
            self.UART.read()
            self.UART.write(f'AT+HTTPPARA="CONTENT","{self.contentType}"\r')
            utime.sleep_ms(100)
            self.UART.read()
            self.UART.write(f'AT+HTTPPARA="USERDATA","Authorization: {self.authorization}"\r')
            utime.sleep_ms(200)
            #try agian of fail
            while trials < 3 and (data == '' or data == None and data != '{"success":true}') and wakeUp:
                if wakeUp.value() == 0:
                    self.UART.write('AT+HTTPTERM\r')
                    utime.sleep_ms(50)
                    break
                utime.sleep_ms(100)
                self.UART.read()
                #set POST data length
                data_length = len(payload)
                self.UART.write(f'AT+HTTPDATA={data_length},10000\r')
                utime.sleep_ms(200)
                self.UART.read()
                #post action
                self.UART.write(payload)
                clock_irq(4)
                self.UART.read()
                #posting
                self.UART.write('AT+HTTPACTION=1\r')
                clock_irq(5)
                utime.sleep_ms(100)
                #read the respond
                self.UART.write('AT+HTTPREAD=0,300\r')
                clock_irq(2)
                data = self.UART.read()
                trials += 1
                if data != '' and data != None:
                    data = self.decodeMsg(data)
            #terminate the http
            self.UART.write('AT+HTTPTERM\r')
            utime.sleep_ms(100)
            self.UART.read()
            if data != '' and data != None:
                if data == '{"success":true}':
                    return 0.1
                else:
                    return 3.1
            else:
                return 3
        else:
            return 1
class DS3231():
    def __init__(self,i2c):
        self.rtc = urtc.DS3231(i2c)
        self.clkPin = Pin(15, Pin.IN, Pin.PULL_UP)
        self.alarmTime = 3600 #time for alarm
    def nowTime(self):
        current_datetime = self.rtc.datetime()
        formatted_datetime = (
        f"{current_datetime.year:04d}-{current_datetime.month:02d}-{current_datetime.day:02d} "
        f"{current_datetime.hour:02d}:{current_datetime.minute:02d}:{current_datetime.second:02d} "
        )
        return formatted_datetime
    def addTime(self, dt):
        timestamp = time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0))
        new_timestamp = timestamp + self.alarmTime # Add days in seconds wanna add minutes just do minute * 60
        new_time = time.localtime(new_timestamp)
        return urtc.datetime_tuple(new_time[0], new_time[1], new_time[2], None, new_time[3], new_time[4], new_time[5], 0)
    def alarmSet(self, data):
        self.alarmTime = data #time for alarm
        #set alarm from now to next count
        self.rtc.alarm(False, 0)     #clear all the alarm
        self.rtc.no_interrupt()
        #get the time and setting the alarm to wake up from now
        now  = self.rtc.datetime()
        nextAlarmTime = self.addTime(now)
        self.rtc.alarm_time(nextAlarmTime, alarm=0)
        #enable interrupt for alarm 0
        self.rtc.interrupt(0)
#         print(f"Alarm set for: {self.alarmTime}")
    def resetAlarm(self):
        self.rtc.alarm(False, 0)
        self.rtc.no_interrupt()
        now = self.rtc.datetime()
        next_alarm_time = self.addTime(now)
        self.rtc.alarm_time(next_alarm_time, alarm = 0)
        self.rtc.interrupt(0)
















