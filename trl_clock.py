# clock that runs evaluation of the mind / body

import socket
import atexit
import time
import trl_constants

TIME_SINCE_INCEPTION = 0
SLEEP_INTERVAL = 2.000

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_CLOCK, trl_constants.UDP_PORT_CLOCK_RESPONSE))

def log(msg):
	osock.sendto('trl_clock.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()
	
def main():
	global TIME_SINCE_INCEPTION
	global SLEEP_INTERVAL

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_CLOCK, trl_constants.UDP_PORT_CLOCK_IN))

	atexit.register(cleanup, sock, osock)
	log('trl_clock LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	while True:
		time.sleep(SLEEP_INTERVAL) # sleep interval in seconds
		TIME_SINCE_INCEPTION = TIME_SINCE_INCEPTION + SLEEP_INTERVAL
		msg = 'TICK ' + str(TIME_SINCE_INCEPTION)
		osock.sendto(msg, trl_constants.DB_NET)
		osock.sendto(msg, (trl_constants.UDP_IP_STATE_MANAGER, trl_constants.UDP_PORT_STATE_MANAGER_IN))

main()

# USE CASES THAT BREAK THIS
# 1. Sending a 1024 size block that ends in a split word.
#		This will be interpreted as two words: ex. bart\nender
#		would be = "bart" and "ender" not "bartender"