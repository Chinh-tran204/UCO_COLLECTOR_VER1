from device import SIMCom, device, DS3231, ultraS, wakeUp, clock
from machine import UART, Pin, I2C, deepsleep
from pico_i2c_lcd import I2cLcd
from lcd_api import LcdApi
import CONS
from utime import sleep, sleep_ms
import utime


# #INIT SIMCom Module
SUART = UART(CONS.SIM_UART_PORT, 115200, tx = Pin(CONS.SIMtx), rx = Pin(CONS.SIMrx))
SIMCom = SIMCom(SUART)

# #init password and device module
device = device() #password only avaiable when device not sleep
ultraS = ultraS()

# #init ultraS module
# ULTRAS = UART(CONS.ULTRAS_UART_PORT,9600, tx = Pin(CONS.ULTRAStx), rx = Pin(CONS.ULTRASrx)) 
# ultraS = ultraS()

# #init set up
device.mainPower1.low()
device.mainPower2.low()

#timer init
i2ct = I2C(1, scl=Pin(11), sda=Pin(10))
timer = DS3231(i2ct)
timeOut = 3000

################################################################################################
# device.buzzer(300)
# timer.alarmSet(60)

def unlock(k):
    if not k.value():
        #turn off interupt
        wakeUp.irq(None)
        sleep(100)
        if wakeUp.value() == 0:
            device.buzzer(300)
            startTime = utime.ticks_ms()
            while wakeUp.value() == 0 and utime.ticks_diff(utime.ticks_ms(), startTime) < 5000:
                runTime = utime.ticks_diff(utime.ticks_ms(), startTime)
            if runTime >= 5000:
                sleep_ms(300)
                device.buzzer(1000)
                device.latchOpen()
            if runTime < 5000:
                wakeUp.irq(unlock, Pin.IRQ_FALLING)
#timer func
def timerTrigger(k):
    if not k.value():
        timer.clkPin.irq(None)
        sleep_ms(100)
        if timer.clkPin.value() == 0:
            timer.alarmSet(7200)
            sleep_ms(100)
            device.buzzer(300)
            device.mainPower2.high()
            SUART.read()
            sleep_ms(1000)
            startTime = utime.ticks_ms()
            data = ultraS.distanceCm()
            while utime.ticks_diff(utime.ticks_ms(), startTime) <= timeOut and data == 0 and data == None:
                data = ultraS.distanceCm()
            if data > 76.0:
                percent = 0
            elif data < 15.0:
                percent = 100
            else:
                percent = int(100 - (data*100)/76)
            clock(14)
            conf = SIMCom.postUpdate(percent, device.batteryCap())
#             print(timer.nowTime())
#             print(conf)
            #fail case
            if conf!= 0:
                device.buzzer(300)
                sleep_ms(300)
                device.buzzer(300)
            device.mainPower2.low()
#wake up button func
def wakeUpTrigger(k):
    if not k.value():
        wakeUp.irq(None)
        sleep_ms(100)
        if wakeUp.value() == 0:
            sleep_ms(100)
            wakeUp.irq(unlock, Pin.IRQ_FALLING)
            #init password interrupt
            device.buzzer(300)
            device.mainPower1.high()
            device.mainPower2.high()
            sleep_ms(200)
            ##lcd init and running
            i2c= I2C(0, sda = Pin(20), scl = Pin(21), freq = 400000)
            lcd = I2cLcd(i2c, CONS.I2C_ADDR, CONS.I2C_NUM_ROWS, CONS.I2C_NUM_COLS)
            sleep_ms(200)
            data = ultraS.distanceCm()
            if data > 76.0:
                percent = 0
            elif data < 15.0:
                percent = 100
            else:
                percent = int(100 - (data*100)/76)
            cap = device.batteryCap()
            ##lcd init and running
            lcd.move_to(5,0)
            lcd.putstr('ECO OIL')
            lcd.move_to(2,1)
            lcd.putstr(f'VOLUME: {int(percent)}%')
            clock(10)
            wakeUp.irq(None)
            wakeUp.irq(wakeUpTrigger, Pin.IRQ_FALLING)
            device.mainPower1.low()
            device.buzzer(300)
            clock(2)
            #run SIMCom
            conf = SIMCom.postUpdate(percent,cap)
            #fail case
            if conf != 0 and wakeUp.value():
                device.buzzer(300)
                sleep_ms(300)
                device.buzzer(300)
            device.mainPower2.low()

# print(timer.nowTime())
# while True:
#     #set up interupt
#     wakeUp.irq(wakeUpTrigger, Pin.IRQ_FALLING)
#     timer.clkPin.irq(timerTrigger, Pin.IRQ_FALLING)

wakeUp.irq(wakeUpTrigger, Pin.IRQ_FALLING)
timer.clkPin.irq(timerTrigger, Pin.IRQ_FALLING)


while True:
    if wakeUp.value() == 0:
        sleep_ms(1000)
        wakeUpTrigger(wakeUp)
    if timer.clkPin.value() == 0:
        sleep_ms(1000)
        timerTrigger(timer.clkPin)
#     deepsleep(300)
