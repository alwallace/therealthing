import socket
import atexit
import random

UDP_IP="127.0.0.1"
UDP_PORT_IN=10000

STATE_SIZE = 20
ACTION_SIZE = 5

CURRENT_STATE = 0

random.seed()

# initialize the environment w/ a random set of states and actions
# that take you to differernt states

state_action_array = []


def makeActionStateArray(state_count, action_count):
	state_action_array = []

	i = 0
	while i < state_count:
		state_action_array.append([])

		j = 0
		while j < action_count:
			state_action_array[i].append(random.randint(0,state_count-1))
			j = j + 1

		print str(i), state_action_array[i]
		i = i + 1

	return state_action_array

def sendActionList(addr, osock):
	i = 0
	action_list = str(i)
	i = i + 1
	while i < ACTION_SIZE:
		action_list = action_list + ' ' + str(i)
		i = i + 1

	osock.sendto(action_list, addr)

def takeAction(action):
	global CURRENT_STATE
	if action >= 0 and action < ACTION_SIZE:
		CURRENT_STATE = state_action_array[CURRENT_STATE][action]

def sendCurrentState(addr, osock):
	osock.sendto(str(CURRENT_STATE), addr)

def cleanup(sock):
	sock.close()
	print 'Cleaned.'

def main():
	global CURRENT_STATE
	global state_action_array

	state_action_array = makeActionStateArray(STATE_SIZE, ACTION_SIZE)

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock)

	print 'CURRENT_STATE:', str(CURRENT_STATE)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		print 'received message <', addr, '>:', data

		if data == 'action_list':
			print 'Get ACTION_LIST'
			sendActionList(addr, sock)
		elif data == 'current_state':
			print 'CURRENT_STATE:', str(CURRENT_STATE), '<' + data + '>'
			sendCurrentState(addr, sock)
		else:
			data = data.split(' ')

			if data[0] == 'perform_action':
				print 'PERFORM_ACTION:', str(data[1])
				takeAction(int(data[1]))

main()