import json
#I2C1
I2C_ADDR     = 39
I2C_NUM_ROWS = 2
I2C_NUM_COLS = 16
 


#UART0
SIM_UART_PORT = 1
BAUDRATE_UART0=115200

#SIMCom model: A7680C
SIMtx = 8
SIMrx = 9
PHONE_NUM = '+84399972260'


#UART1
ULTRAS_UART_PORT = 0
ULTRAStx = 16
ULTRASrx = 17

FILENAME = "key_data.json"

def save_key(data):
        with open(FILENAME, "w") as file:
            json.dump(data, file)

def load_key():
    try:
        with open(FILENAME, "r") as file:
            return json.load(file)
    except (OSError, ValueError):
        return []
    
KEY = load_key()