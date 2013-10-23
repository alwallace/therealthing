# state manager of the state of TRL
# possible needs: potential future states, manages when action is appropriate (are we satisfied with current state or not?)

import socket
import atexit
import trl_constants

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_STATE_MANAGER, trl_constants.UDP_PORT_STATE_MANAGER_RESPONSE))

# DB state constant nodes
DB_TIME_ELAPSED_ID = 0
DB_CURRENT_ID = 0

STATE_INDICATORS = {}
SATISFIED_MINIMUM = 100
PREVIOUS_STATE = '-1'
PREVIOUS_STATE_ID = -1
CURRENT_STATE = '-1'
CURRENT_STATE_ID = -1
CURRENT_RELATION_ID = -1
LAST_TIME = 0
LAST_ACTION_ID = 0

def log(msg):
	osock.sendto('trl_state_manager.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()

def defineInitialState():
	global CURRENT_STATE_ID
	global CURRENT_RELATION_ID

	# create the "undefined" state (born state with nothing prior)
	osock.sendto('PING ' + CURRENT_STATE, trl_constants.DB_NET)
	osock.sendto('GETLASTPINGID', trl_constants.DB_NET)
	data, addr = osock.recvfrom(1024)
	temp_id = data

	CURRENT_STATE_ID = int(temp_id)

	# then add the new relationship move the CURRENT pointer
	osock.sendto('RELATE ' + str(DB_CURRENT_ID) + ' ' + str(CURRENT_STATE_ID) + ' ' + str(DB_CURRENT_ID), trl_constants.DB_NET)
	osock.sendto('GETLASTRELATIONID', trl_constants.DB_NET)
	data, addr = osock.recvfrom(1024)
	CURRENT_RELATION_ID = int(data)

def updateState(time):
	global CURRENT_STATE
	global PREVIOUS_STATE
	global CURRENT_STATE_ID
	global PREVIOUS_STATE_ID
	global CURRENT_RELATION_ID
	global LAST_TIME

	osock.sendto('CURRENT_STATE', trl_constants.ENVIRONMENT_NET)
	data, addr = osock.recvfrom(1024)
	PREVIOUS_STATE = CURRENT_STATE
	CURRENT_STATE = data

	log('TICK ' + str(time))

	# if the state is the same then don't bother to update the db cause everything is the same
#	if CURRENT_STATE != PREVIOUS_STATE:
	PREVIOUS_STATE_ID = CURRENT_STATE_ID
	LAST_TIME = time

	# check for a state that is exactly the same as this one
	osock.sendto('GETID ' + CURRENT_STATE, trl_constants.DB_NET)
	data, addr = osock.recvfrom(1024)

	if data == '.':
		# if not then make a new state in db
		osock.sendto('PING ' + CURRENT_STATE, trl_constants.DB_NET)
		osock.sendto('GETLASTPINGID', trl_constants.DB_NET)
		data, addr = osock.recvfrom(1024)
	else:
		# Clear out the rest of the IDs
		trashdata = ''
		while trashdata != '.':
			trashdata, addr = osock.recvfrom(1024)

	CURRENT_STATE_ID = int(data)

	# then add the new relationship using a time chagne and move the CURRENT pointer
	osock.sendto('RELATE ' + str(PREVIOUS_STATE_ID) + ' ' + str(CURRENT_STATE_ID) + ' ' + str(DB_TIME_ELAPSED_ID), trl_constants.DB_NET)
	osock.sendto('DESTROYRELATION ' + str(CURRENT_RELATION_ID), trl_constants.DB_NET)
	osock.sendto('RELATE ' + str(DB_CURRENT_ID) + ' ' + str(CURRENT_STATE_ID) + ' ' + str(DB_CURRENT_ID), trl_constants.DB_NET)
	osock.sendto('GETLASTRELATIONID', trl_constants.DB_NET)
	data, addr = osock.recvfrom(1024)

	if data != '.':
		CURRENT_RELATION_ID = int(data)

	# update the causal status with relationship: (previous state, current state, last action performed)
	osock.sendto('RELATE ' + str(PREVIOUS_STATE_ID) + ' ' + str(CURRENT_STATE_ID) + ' ' + str(LAST_ACTION_ID), trl_constants.DB_NET)

def evaluateState():
	global STATE_INDICATORS
	STATE_INDICATORS['satisfaction'] = CURRENT_STATE
	
def takeAction():
	global LAST_ACTION_ID
	log('Taking action!')
	osock.sendto('GO', trl_constants.ACTION_MANAGER_NET)

	# get the action that was taken back from action manager!
	data, addr = osock.recvfrom(1024)
	LAST_ACTION_ID = int(data)

	log('Performed action: ' + str(LAST_ACTION_ID))

def takeNoAction():
	global LAST_ACTION_ID
	log('Taking no action')
	LAST_ACTION_ID = 0

def main():
	global LAST_ACTION_ID
	global DB_CURRENT_ID
	global DB_TIME_ELAPSED_ID

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_STATE_MANAGER, trl_constants.UDP_PORT_STATE_MANAGER_IN))

	atexit.register(cleanup, sock, osock)

	# get the id for the CURRENT pointer in the db
	data = trl_constants.request(osock, trl_constants.DB_NET, 'GETID CURRENT')
	DB_CURRENT_ID = int(data[0])

	# get the id for the ELAPSED_TIME pointer in the db
	data = trl_constants.request(osock, trl_constants.DB_NET, 'GETID TIME_ELAPSED')
	DB_TIME_ELAPSED_ID = int(data[0])

	# initialize
	defineInitialState()
	updateState(0)

	log('trl_state_manager LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	# Get started!
	while True:
		data, addr = sock.recvfrom(1024)
		log( 'received message <' + str(addr) + '>:' + data)

		data = data.rstrip().split()
		if data[0] == 'TICK':
			updateState(float(data[1]))
			evaluateState()

			if int(STATE_INDICATORS['satisfaction']) < SATISFIED_MINIMUM:
				takeAction()
			else:
				takeNoAction()

main()

# USE CASES THAT BREAK THIS
# 1. Sending a 1024 size block that ends in a split word.
#		This will be interpreted as two words: ex. bart\nender
#		would be = "bart" and "ender" not "bartender"