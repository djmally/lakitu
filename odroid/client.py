import argparse
import os
import socket
import subprocess
from time import sleep

PWM_BASE = '/sys/class/soft_pwm'
OS_PULSE = '{}/pwm{}/pulse'

#              INSIDE
#     |  X  |  X  |  X  | POW |
#     | 199 | 200 | 204 | GRD |
#              OUTSIDE
PWM_PORTS = [199, 204]

GIMBAL_MIN = 900
GIMBAL_MAX = 2100
GIMBAL_RANGE = GIMBAL_MAX - GIMBAL_MIN

NORMALIZE_MIN_X = 0
NOMRALIZE_MAX_X = 180
NORMALIZE_MIN_Y = 0
NORMALIZE_MAX_Y = 180

SOCKET_PORT = 50007
SOCKET_MAX_CONNECTIONS = 5

# Minimum change in position before moving servos
MIN_DELTA = 50

#use manual input, can be set with --manual flag
use_manual = False
# Calibration flag, can be set with --calibrate
calibrate = False

def calibrate_gimbal(sock):
    input('Left calibration. Look directly to your left. (Press enter when ready)')
    left = socket_read(sock)[0][0]
    input('Right calibration. Look directly to your right. (Press enter when ready)')
    right = socket_read(sock)[0][0]
    input('Downward calibration. Look directly down. (Press enter when ready)')
    down = socket_read(sock)[0][1]
    input('Upward calibration. Look directly up. (Press enter when ready)')
    up = socket_read(sock)[0][1]
    global NORMALIZE_MIN_X, NORMALIZE_MIN_Y, NORMALIZE_MAX_X, NORMALIZE_MAX_Y
    NORMALIZE_MIN_X, NORMALIZE_MAX_X = left, right
    NORMALIZE_MIN_Y, NORMALIZE_MAX_Y = down, up
    print("x range is {} - {}, y range is {} - {}".format(NORMALIZE_MIN_X, NORMALIZE_MAX_X, NORMALIZE_MIN_Y, NORMALIZE_MAX_Y))


def mk_server_socket():
    out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #socket_hostname = socket.gethostname()
    socket_hostname = ''
    #print(socket_hostname)
    out.bind((socket_hostname, SOCKET_PORT))
    out.listen(SOCKET_MAX_CONNECTIONS)
    return out

#TODO: Replace with socket read
def read():
    ''' Inputs are given in [0, 100] '''
    inputs = input('x, y: ')
    if inputs == 'quit' or inputs == 'q' or inputs == 'exit':
        return False
    else:
        x, y = inputs.split(',')
        return (int(x), int(y))


def socket_read(serversocket):
    MESSAGE_LENGTH = 2
    (clientsocket, address) = serversocket.accept()
    chunks = []
    bytes_received = 0
    while len(chunks) < MESSAGE_LENGTH + 1:
        chunk = clientsocket.recv(MESSAGE_LENGTH - bytes_received)
        chunks.append(chunk)
        bytes_received += len(chunk)
        if len(chunk) == 0:
            break
    inputs = None if len(chunks) < 2 else chunks
    clientsocket.close()
    return inputs


def normalize(raw_value, horiz):
    ''' Converts raw_value input in [0, 100] to the appropriate value in [MIN_GIMBAL, MAX_GIMBAL] '''
    normalize_range = NORMALIZE_MAX_X - NORMALIZE_MIN_X if horiz else NORMALIZE_MAX_Y - NORMALIZE_MIN_Y
    raw_value -= NORMALIZE_MIN_X if horiz else NORMALIZE_MIN_Y
    normalized_value = (raw_value * GIMBAL_RANGE) / normalize_range
    return int(normalized_value + NORMALIZE_MIN_X) if horiz else int(normalized_value + NORMALIZE_MIN_Y)

def main():
    horizontal = os.fdopen(os.open(OS_PULSE.format(PWM_BASE, PWM_PORTS[0]), os.O_RDWR|os.O_CREAT), 'w+')
    vertical   = os.fdopen(os.open(OS_PULSE.format(PWM_BASE, PWM_PORTS[1]), os.O_RDWR|os.O_CREAT), 'w+')
    if not use_manual:
        serversocket = mk_server_socket()
        if calibrate:
            calibrate_gimbal(serversocket)

    old_x = 0
    old_y = 0
    while True:
        try:
            if use_manual:
                inputs = read()
            else:
                inputs = socket_read(serversocket)
            if inputs and not use_manual:
                x, y = inputs[0][0], inputs[0][1]
                normalized_x = normalize(x, True)
                normalized_y = normalize(y, False)
                if abs(normalized_x - old_x) > MIN_DELTA:
                    horizontal.write(str(abs(180 - normalized_x)))
                    horizontal.flush()
                if abs(normalized_y - old_y) > MIN_DELTA:
                    vertical.write(str(normalized_y))
                    vertical.flush()
                print(normalized_x, normalized_y)
            elif inputs and use_manual:
                x, y = inputs
                normalized_x = normalize(x, True)
                normalized_y = normalize(y, False)
                horizontal.write(str(normalized_x))
                vertical.write(str(normalized_y))
                horizontal.flush()
                vertical.flush()
                print(normalized_x, normalized_y)
            sleep(.5)
        except KeyboardInterrupt:
            horizontal.close()
            vertical.close()
            serversocket.close()

def setup():
    parser = argparse.ArgumentParser(description='Client for socket connection to Oculus Rift')
    parser.add_argument('--setup', dest='setup', action='store_const',
                        const=True, default=False,
                        help='Setup the PWM outputs on pins 200 and 204, 200 will be the horizontal axis, 204 will be the vertical')
    parser.add_argument('--manual', dest='manual', action='store_const',
                        const=True, default=False,
                        help='Use manual keyboard-written input values for pan and tilt rather than those sent over the socket')
    parser.add_argument('--calibrate', dest='calibrate', action='store_const',
                        const=True, default=False,
                        help='Calibrate the gimbal using the Oculus Rift')
    args = parser.parse_args()

    global use_manual
    global calibrate
    use_manual = args.manual
    calibrate = args.calibrate
    if args.setup:
        for port in PWM_PORTS:
            init_cmd = 'echo {} > {}/export'.format(port, PWM_BASE)
            period_cmd = 'echo 20000 > {}/pwm{}/period'.format(PWM_BASE, port)
            subprocess.Popen(init_cmd, shell=True, preexec_fn=os.setsid)
            subprocess.Popen(period_cmd, shell=True, preexec_fn=os.setsid)

if __name__ == '__main__':
    setup()
    main()
