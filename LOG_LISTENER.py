import socket
import atexit

UDP_IP="127.0.0.1"
UDP_PORT_IN=9999

def cleanup(sock):
	print 'Cleaned.'
	sock.close()

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock)

	while True:
		data, addr = sock.recvfrom(1024)
		
		print data,

main()