import socket
import atexit

UDP_IP="127.0.0.1"
UDP_PORT_IN=7100
UDP_PORT_RESPONSE=6100

UDP_IP_NEW_TOKEN='127.0.0.1'
UDP_PORT_NEW_TOKEN=7300

UDP_LOG_IP = '127.0.0.1'
UDP_LOG_PORT = 9999

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((UDP_IP, UDP_PORT_RESPONSE))

def log(msg):
	osock.sendto('trl_hub.py: ', (UDP_LOG_IP, UDP_LOG_PORT))
	osock.sendto(msg+'\n', (UDP_LOG_IP, UDP_LOG_PORT))

def process_token(osock, token):
	osock.sendto(token, (UDP_IP_NEW_TOKEN, UDP_PORT_NEW_TOKEN))
	log( 'sent token <' + UDP_IP_NEW_TOKEN + ':' + str(UDP_PORT_NEW_TOKEN) + '>:' + token)

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock, osock)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log( 'received message <' + str(addr) + '>:' + data)

		tokens=data.split()

		for token in tokens:
			if token.endswith('.') or token.endswith('!') or token.endswith('?'):
				process_token(osock, token[:-1])
				process_token(osock, token[-1:])
			else:
				process_token(osock, token)

main()

# USE CASES THAT BREAK THIS
# 1. Sending a 1024 size block that ends in a split word.
#		This will be interpreted as two words: ex. bart\nender
#		would be = "bart" and "ender" not "bartender"