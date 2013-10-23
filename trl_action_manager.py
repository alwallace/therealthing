import socket
import atexit
import random
import trl_constants
import time

action_list = []  # [[ID, action]]
RELATION_TYPE_ACTIONS_ID = 1
action_generators = []
TOTAL_WAIT_TIME = 0.500

CURRENT_STATE_ID = 0

DB_CURRENT_ID = 0
DB_TIME_ELAPSED_ID = 0
DB_DECISION_ID = 0

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_ACTION_MANAGER, trl_constants.UDP_PORT_ACTION_MANAGER_RESPONSE))

random.seed()

def log(msg):
	osock.sendto('trl_action_manager.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()

def randomAction():
	return action_list[random.randint(0, len(action_list) - 1)]

def greedyAction():
	global CURRENT_STATE_ID
	# Get the current state id
	results = trl_constants.request(osock, trl_constants.DB_NET, 'GETRRELATED ' + str(DB_CURRENT_ID) + ' ' + str(DB_CURRENT_ID))
	CURRENT_STATE_ID = results[0]

	# Get all state id's that have ever spawned off of each action of the current state
	action_qualities = {}
	for action_couple in action_list:
		action_qualities[action_couple[0]] = trl_constants.request(osock, trl_constants.DB_NET, 'GETRRELATED ' + CURRENT_STATE_ID + ' ' + str(action_couple[0]))

	# for each action, determine which action has the highest "value" for the state IDs
	best_action = randomAction() # returns [ID, action]
	best_value = -1
	for action_couple in action_list:
		for state_id in action_qualities[action_couple[0]]:
			value = trl_constants.request_one(osock, trl_constants.DB_NET, 'GETVALUE ' + state_id)
			log('From state_id ' + str(CURRENT_STATE_ID) + ' via action_id ' + str(action_couple[0]) + ' to state_id ' + str(state_id) + ' yields value: ' + str(value))
			if value > best_value:
				best_value = value
				best_action = action_couple

	log('Best action: ' + str(best_action[0]) + '/' + str(best_action[1]))
	log('Value determined: ' + str(best_value))

	return [best_action, best_value]


def chooseBestAction():
	for generator in action_generators:
		osock.sendto('GET', (generator[0], generator[1]))
		log(generator[0] + ' : GET')

	
	endtime = time.time() + TOTAL_WAIT_TIME
	osock.settimeout(endtime - time.time())

	bestAction = [-1, trl_constants.request_one(osock, trl_constants.DB_NET, 'GETVALUE ' + str(DB_CURRENT_ID))]
	greediestAction = greedyAction()
	randomestAction = [randomAction(), 1]

	# take the greedy option if its better or 25% chance rolling the die
	if bestAction[1] > greediestAction[1] or random.randint(0, 100) < 25:
		bestAction = greediestAction
		log('Taking greedy action')
	# sometimes it pays to be random
	if random.randint(0,100) < 10:
		bestAction = randomestAction
		log('Taking random action')

	while time.time() < endtime:
		try:
			data, addr = osock.recvfrom(1024)
			temp = data.rstrip().split()
			if bestAction[1] <= temp[1]:
				print bestAction
				bestAction = temp

			osock.settimeout(endtime - time.time())
		except:
			pass

	osock.settimeout(None)
	return bestAction[0]

def registerActionGenerator(ip, port):
	action_generators.append([ip, port])

def main():
	global action_list
	global DB_CURRENT_ID
	global DB_TIME_ELAPSED_ID


	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_ACTION_MANAGER, trl_constants.UDP_PORT_ACTION_MANAGER_IN))

	atexit.register(cleanup, sock, osock)


	# Query the action list from the environment
	osock.sendto('ACTION_LIST', (trl_constants.UDP_IP_ENVIRONMENT, trl_constants.UDP_PORT_ENVIRONMENT_IN))
	data, addr = osock.recvfrom(1024)
	if data != '':
		action_list = data.split()

	# Assign all appropriate values in the DATABASE
	#	remove the old action web
	osock.sendto('PING _actions', trl_constants.DB_NET)
	osock.sendto('GETLASTPINGID', trl_constants.DB_NET)

	data, addr = osock.recvfrom(1024)
	avail_action_node_id = -1
	if data != '':
		avail_action_node_id = int(data)

	osock.sendto('DESTROYNODE ' + str(avail_action_node_id), trl_constants.DB_NET)

	#	create the new action web
	osock.sendto('PING _actions', trl_constants.DB_NET)
	osock.sendto('GETLASTPINGID', trl_constants.DB_NET)

	data, addr = osock.recvfrom(1024)
	avail_action_node_id = -1
	if data != '':
		avail_action_node_id = int(data)

	#	add all the new actions to the web center
	temp = []
	for i in action_list:
		osock.sendto('PING _' + str(i), trl_constants.DB_NET)
		osock.sendto('GETLASTPINGID', trl_constants.DB_NET)

		data, addr = osock.recvfrom(1024)
		temp.append([data, i])

	action_list = temp

	# get the id for the CURRENT pointer in the db
	data = trl_constants.request(osock, trl_constants.DB_NET, 'GETID CURRENT')
	DB_CURRENT_ID = int(data[0])

	# get the id for the ELAPSED_TIME pointer in the db
	data = trl_constants.request(osock, trl_constants.DB_NET, 'GETID TIME_ELAPSED')
	DB_TIME_ELAPSED_ID = int(data[0])

	# get the id for the DECISION pointer in the db
	data = trl_constants.request(osock, trl_constants.DB_NET, 'GETID DECISION')
	DB_DECISION_ID = int(data[0])

	log('trl_action_manager LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	# Start it up
	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log( 'received message <' + str(addr) + '>:' + data)
		data = data.split()

		if data[0] == 'GO':
			bestAction = chooseBestAction()
			if bestAction[0] == -1:
				log('No action performed, no better actions than standing still')
			else:
				osock.sendto('PERFORM_ACTION ' + bestAction[1], trl_constants.ENVIRONMENT_NET)
				# send the action performed back to the module that sent "GO"
				osock.sendto(bestAction[0], addr)
				# update the memory to say that you did the action from state current
				osock.sendto('RELATE ' + str(CURRENT_STATE_ID) + ' ' + str(bestAction[0]) + ' ' + str(DB_DECISION_ID), trl_constants.DB_NET)
				log('Performed action: ' + bestAction[0] + ' , ' + bestAction[1])
		elif data[0] == 'REGISTER':
			registerActionGenerator(data[1], int(data[2]))
			log('REGISTERED: ' + data[1] + ' ' + data[2])



main()
