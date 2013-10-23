import socket
import atexit
import trl_constants

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_HUB, trl_constants.UDP_PORT_HUB_RESPONSE))

def log(msg):
	osock.sendto('trl_hub.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def process_token(osock, token):
	osock.sendto(token, (trl_constants.UDP_IP_NEW_TOKEN, trl_constants.UDP_PORT_NEW_TOKEN_IN))
	log( 'sent token <' + trl_constants.UDP_IP_NEW_TOKEN + ':' + str(trl_constants.UDP_PORT_NEW_TOKEN_IN) + '>:' + token)

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_HUB, trl_constants.UDP_PORT_HUB_IN))

	atexit.register(cleanup, sock, osock)
	log('trl_hub LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

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