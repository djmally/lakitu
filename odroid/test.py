import socket

HOST = '165.123.196.139'    # The remote host
PORT = 50007              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(bytes('Hello, world', 'UTF-8'))
data = s.recv(1024)
s.close()
print('Received', repr(data))
