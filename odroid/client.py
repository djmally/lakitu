import argparse
import os
import socket
import struct
import subprocess

PWM_BASE = '/sys/class/soft_pwm'
OS_PULSE = '{}/pwm{}/pulse'
#PWM_BASE = "./soft_pwm" # a dummy value
#OS_PULSE = "./pulse" # dummy value as well

PWM_PORTS = [200, 204]

GIMBAL_MIN_X = 900
GIMBAL_MIN_Y = 900
GIMBAL_MAX_X = 2100
GIMBAL_MAX_Y = 2100

#SOCKET_HOST = '50.191.183.184' #TODO: figure out DNS or something
SOCKET_PORT = 50007
SOCKET_MAX_CONNECTIONS = 5

# Minimum change in position before moving servos
MIN_DELTA = 20

#use manual input, can be set with --manual flag
use_manual = False
# Calibration flag, can be set with --calibrate
calibrate = False

def calibrate_gimbal(sock):
    raw_input('Left calibration. Look directly to your left. (Press enter when ready)')
    left = socket_read(sock)
    raw_input('Right calibration. Look directly to your right. (Press enter when ready)')
    right = socket_read(sock)
    raw_input('Downward calibration. Look directly down. (Press enter when ready)')
    down = socket_read(sock)
    raw_input('Upward calibration. Look directly up. (Press enter when ready)')
    up = socket_read(sock)
    GIMBAL_MIN_X, GIMBAL_MAX_X = left[0], right[0]
    GIMBAL_MIN_Y, GIMBAL_MAX_Y = down[1], up[1]


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
        #print (repr(x).rjust(2), repr(y).rjust(2))
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
    gimbal_range = GIMBAL_MAX_X - GIMBAL_MIN_X if horiz else GIMBAL_MAX_Y - GIMBAL_MIN_Y
    normalized_value = (raw_value * gimbal_range) / 180
    return int(normalized_value + GIMBAL_MIN_X) if horiz else int(normalized_value + GIMBAL_MIN_Y)

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
        if use_manual:
            inputs = read()
        else:
            inputs = socket_read(serversocket)
        if inputs:
            y, x = inputs[0][0], inputs[0][1]
            normalized_x = normalize(x, True)
            normalized_y = normalize(y, False)
            if abs(normalized_x - old_x) > MIN_DELTA:
                horizontal.write(str(normalized_x))
            if abs(normalized_y - old_y) > MIN_DELTA:
                vertical.write(str(normalized_y))
            horizontal.flush()
            vertical.flush()
            print(normalized_x, normalized_y)
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
