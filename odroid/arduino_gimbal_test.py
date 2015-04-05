import serial

def setup_serial():
    global SERIAL_PORT
    SERIAL_PORT = serial.Serial('/dev/ttyUSB0', 9600)

if __name__ == '__main__':
    for i in range(181):
        SERIAL_PORT.write(str(i))
    for i in range(180,-1,-1):
        SERIAL_PORT.write(str(i))
