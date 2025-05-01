from machine import Pin, I2C
import time
import urtc

# Pin setup for SQW pin and LED
CLOCK_INTERRUPT_PIN = 3  # Adjust to your specific GPIO pin for SQW

# Initialize RTC (connected to I2C)
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
rtc = urtc.DS3231(i2c)

# Setup GPIO for SQW and LED
clkPin = Pin(CLOCK_INTERRUPT_PIN, Pin.IN, Pin.PULL_UP)

# Add days to a datetime tuple and return a new datetime tuple
def addDayToTime(dt, days):
    timestamp = time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0))
    new_timestamp = timestamp + (days * 24 * 60 * 60)  # Add days in seconds wanna add minutes just do minute * 60
    new_time = time.localtime(new_timestamp)
    return urtc.datetime_tuple(new_time[0], new_time[1], new_time[2], None, new_time[3], new_time[4], new_time[5], 0)

def nowTime():
    current_datetime = rtc.datetime()
    formatted_datetime = (
        f"{current_datetime.year:04d}-{current_datetime.month:02d}-{current_datetime.day:02d} "
        f"{current_datetime.hour:02d}:{current_datetime.minute:02d}:{current_datetime.second:02d} "
    )
    return formatted_datetime

def alarmSet(timeSpend):
    #set alarm from now to next count
    rtc.alarm(False, 0)     #clear all the alarm
    rtc.no_interrupt()

    #get the time and setting the alarm to wake up from now
    now  = rtc.datetime()
    alarmTime = addDayToTime(now,timeSpend)
    rtc.alarm_time(alarmTime, alarm=0)
    #enable interrupt for alarm 0
    rtc.interrupt(0)


#handle when alarm on 
if not clkPin.value():
    sleep_ms(100)
    if not clkPin.value():
        #reset the alarm
        rtc.alarm(False, alarm=0)
        now = rtc.datetime()
        next_alarm_time = addDayToTime(now, 1)
        rtc.alarm_time(next_alarm_time, alarm=0)  # Set new alarm
        #continue doing things





from device import SIMCom, ultraS, device, DS3231
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

#init ultraS module
ULTRAS = UART(CONS.ULTRAS_UART_PORT,9600, tx = Pin(CONS.ULTRAStx), rx = Pin(CONS.ULTRASrx)) 
ultraS = ultraS(ULTRAS)
wakeUp = Pin(14, Pin.IN, Pin.PULL_UP)
#init set up
device.mainPower1.low()
device.mainPower2.low()

i2ct = I2C(1, scl=Pin(11), sda=Pin(10))
timer = DS3231(i2ct)
timeOut = 3000







def setup_alarm():
    # Clear any existing alarms
    rtc.alarm(False, 0)
    rtc.no_interrupt()
    # Get the current time and set the first alarm 1 day from now
    now = rtc.datetime()
    first_alarm_time = add_days_to_time(now, 1)  # Set first alarm for 1 day from now
    rtc.alarm_time(first_alarm_time, alarm=0)  # Alarm 0

    # Enable the interrupt for Alarm 0
    rtc.interrupt(0)

    print(f"Alarm set for: {first_alarm_time}")



try:
    # Sync time to compile time if RTC lost power
    if rtc.lost_power():
        initial_time_tuple = time.localtime()  # tuple (MicroPython)
        initial_time_seconds = time.mktime(initial_time_tuple)  # local time in seconds
        initial_time = urtc.seconds2tuple(initial_time_seconds)  # Convert to tuple compatible with the library
        rtc.datetime(initial_time)  # Sync the RTC

    print("RTC initialized. Setting up the periodic alarm...")
    setup_alarm()

    while True:
        print_current_time()
        time.sleep(5)
except KeyboardInterrupt:
    print("Exiting program.")


from machine import Pin, I2C
import time
import urtc

# Pin setup for SQW pin and LED
CLOCK_INTERRUPT_PIN = 3  # Adjust to your specific GPIO pin for SQW


# Initialize RTC (connected to I2C)
i2c = I2C(0, scl=Pin(5), sda=Pin(4))
rtc = urtc.DS3231(i2c)

# Setup GPIO for SQW and LED
sqw_pin = Pin(CLOCK_INTERRUPT_PIN, Pin.IN, Pin.PULL_UP)


# Add minutes to a datetime tuple and return a new datetime tuple
def add_minutes_to_time(dt):
    timestamp = time.mktime((dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0, 0))
    new_timestamp = timestamp + 5
    new_time = time.localtime(new_timestamp)
    return urtc.datetime_tuple(new_time[0], new_time[1], new_time[2], None, new_time[3], new_time[4], new_time[5], 0)

# Print the current time from the RTC
def print_current_time():
    now = rtc.datetime()
    formatted_time = f"{now.year}-{now.month:02}-{now.day:02} {now.hour:02}:{now.minute:02}:{now.second:02}"
    print(f"Current time: {formatted_time}")

# Callback for handling alarm interrupt
def on_alarm(pin):
    print("Alarm triggered! Toggling the LED.")

    # Clear the alarm flag and schedule the next alarm
    if rtc.alarm(alarm=0):  # Check if Alarm 0 triggered
        print("Clearing Alarm 0 flag.")
        rtc.alarm(False, alarm=0)  # Clear alarm flag

        # Schedule the alarm to repeat 10 minutes from now
        now = rtc.datetime()
        next_alarm_time = add_minutes_to_time(now)  # Add 10 minutes
        rtc.alarm_time(next_alarm_time, alarm=0)  # Set new alarm
        rtc.interrupt(0)  # Ensure Alarm 0 interrupt is enabled
        print(f"Next alarm set for: {next_alarm_time}")


def setup_alarm():
    # Clear any existing alarms
    rtc.alarm(False, 0)
    rtc.no_interrupt()

    # Get the current time and set the first alarm 1 minute from now
    now = rtc.datetime()
    first_alarm_time = add_minutes_to_time(now)  # Set first alarm for 1 minute from now
    rtc.alarm_time(first_alarm_time, alarm=0)  # Alarm 0

    # Enable the interrupt for Alarm 0
    rtc.interrupt(0)

    print(f"Alarm set for: {first_alarm_time}")

# Attach the interrupt callback
sqw_pin.irq(trigger=Pin.IRQ_FALLING, handler=on_alarm)

