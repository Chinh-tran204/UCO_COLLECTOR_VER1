# UCO_COLLECTOR_VER1
used oil collector machine, that have an ultra sonic sensor that measure the amount of oil in the machine and feed back to the server. using pi pico with http handle through SIMCom module, wake Up trigger from deep sleep using the DS3231 RTC and button.
Sensor use: RCWL - 1670 sensor
- Trigger and echo measure method
- Having another function for UART conmmunicate sensor type in the device.py

SIMCom module: A7680C
- AT command handle
- HandShake function for checking vailability of the SIMCom
- HTPP_GET and HTTP_POST

Deep Sleep handle
- Wake Up button trigger and interupt handle
- RTC WakeUp and Function to handle arlarm set up and time setting and time getting function

One button handle:
- Wake Up fucntion
- Openning function
- Update state after press
