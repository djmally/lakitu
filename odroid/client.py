import argparse
import os
import socket
import subprocess


#TODO: change this back
PWM_BASE = "./soft_pwm"
#PWM_BASE = '/sys/class/soft_pwm'
OS_PULSE = "./pulse"
#OS_PULSE = '{}/pwm{}/pulse'

PWM_PORTS = [200, 204]

GIMBAL_MIN = 900
GIMBAL_MAX = 2100

SOCKET_HOST = '50.191.183.184' #TODO: figure out DNS or something
#SOCKET_PORT = 50007
SOCKET_PORT = 50007
SOCKET_MAX_CONNECTIONS = 5

#use manual input, can be set with --manual flag
use_manual = False

def mk_server_socket():
    out = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket_hostname = socket.gethostname()
    print(socket_hostname)
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
        print (repr(x).rjust(2), repr(y).rjust(2))
        return (int(x), int(y))


def socket_read(connection):
    data = connection.recv(1024)
    if not data:
        return False

    #TODO: FIX THIS IT DOESN'T REALLY WORK
    # just need to get the numeric values of the bytes coming over the socket`

    x,y = str_data.split(',')
    print('{},{}'.format(x,y))
    return (int(x), int(y))


def normalize(raw_value):
    ''' Converts raw_value input in [0, 100] to the appropriate value in [MIN_GIMBAL, MAX_GIMBAL] '''
    gimbal_range = GIMBAL_MAX- GIMBAL_MIN
    normalized_value = (raw_value * gimbal_range) / 180
    return int(normalized_value + GIMBAL_MIN)

def main():
    horizontal = os.fdopen(os.open(OS_PULSE.format(PWM_BASE, PWM_PORTS[0]), os.O_RDWR|os.O_CREAT), 'w+')
    vertical   = os.fdopen(os.open(OS_PULSE.format(PWM_BASE, PWM_PORTS[1]), os.O_RDWR|os.O_CREAT), 'w+')
    if not use_manual:
        serversocket = mk_server_socket() 

    while True:
        if use_manual:
            inputs = read()
        else:
            MESSAGE_LENGTH = 2
            (clientsocket, address) = serversocket.accept()
            chunks = []
            bytes_recieved = 0
            while bytes_recieved < MESSAGE_LENGTH:
                chunk = clientsocket.recv(MESSAGE_LENGTH - bytes_recieved)
                chunks.append(chunk)
                chunk_size = len(chunk)
                bytes_recieved = bytes_recieved + chunk_size
                if chunk_size == 0:
                    break
            inputs = (chunks[0], chunks[1])
        if not inputs:
            #TODO: BE BETTER
            break
        x, y = inputs
        normalized_x = normalize(x)
        normalized_y = normalize(y)
        horizontal.write(str(normalized_x))
        vertical.write(str(normalized_y))
        horizontal.flush()
        vertical.flush()
        print(inputs)
    horizontal.close()
    vertical.close()
    connection.close()


def setup():
    parser = argparse.ArgumentParser(description='Client for socket connection to Oculus Rift')
    parser.add_argument('--setup', dest='setup', action='store_const',
                        const=True, default=False,
                        help='Setup the PWM outputs on pins 200 and 204, 200 will be the horizontal axis, 204 will be the vertical')
    parser.add_argument('--manual', dest='manual', action='store_const',
                        const=True, default=False,
                        help='Use manual keyboard-written input values for pan and tilt rather than those sent over the socket')
    args = parser.parse_args()

    global use_manual
    use_manual = args.manual
    if args.setup:
        for port in PWM_PORTS:
            init_cmd = 'echo {} > {}/export'.format(port, PWM_BASE)
            period_cmd = 'echo 20000 > {}/pwm{}/period'.format(PWM_BASE, port)
            subprocess.Popen(init_cmd, shell=True, preexec_fn=os.setsid)
            subprocess.Popen(period_cmd, shell=True, preexec_fn=os.setsid)

if __name__ == '__main__':
    setup()
    main()
