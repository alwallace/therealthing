import socket
import atexit

UDP_IP="127.0.0.1"
UDP_PORT_IN=7400
UDP_PORT_RESPONSE=6400

UDP_IP_DATABASE='127.0.0.1'
UDP_PORT_DATABASE=7200

UDP_IP_ENVIRONMENT='127.0.0.1'
UDP_PORT_ENVIRONMENT=10000

UDP_LOG_IP = '127.0.0.1'
UDP_LOG_PORT = 9999

action_list = []

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((UDP_IP, UDP_PORT_RESPONSE))

def log(msg):
	osock.sendto('trl_action_manager.py: ', (UDP_LOG_IP, UDP_LOG_PORT))
	osock.sendto(msg+'\n', (UDP_LOG_IP, UDP_LOG_PORT))

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()
	

def main():
	global action_list


	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock, osock)

	# Query the action list from the environment
	osock.sendto('action_list', (UDP_IP_ENVIRONMENT, UDP_PORT_ENVIRONMENT))
	data, addr = osock.recvfrom(1024)
	if data != '':
		action_list = data.split()

	# Assign all appropriate values in the DATABASE
	#	remove the old action web
	osock.sendto('PING _available_actions', (UDP_IP_DATABASE, UDP_PORT_DATABASE))
	osock.sendto('GETLASTPINGID', (UDP_IP_DATABASE, UDP_PORT_DATABASE))

	data, addr = osock.recvfrom(1024)
	avail_action_node_id = -1
	if data != '':
		avail_action_node_id = int(data)

	osock.sendto('DESTROYNODE ' + str(avail_action_node_id), (UDP_IP_DATABASE, UDP_PORT_DATABASE))

	#	create the new action web
	osock.sendto('PING _available_actions', (UDP_IP_DATABASE, UDP_PORT_DATABASE))
	osock.sendto('GETLASTPINGID', (UDP_IP_DATABASE, UDP_PORT_DATABASE))

	data, addr = osock.recvfrom(1024)
	avail_action_node_id = -1
	if data != '':
		avail_action_node_id = int(data)

	#	add all the new acitons to the web center
	temp = []
	for i in action_list:
		osock.sendto('PING _' + str(i), (UDP_IP_DATABASE, UDP_PORT_DATABASE))
		osock.sendto('GETLASTPINGID', (UDP_IP_DATABASE, UDP_PORT_DATABASE))

		data, addr = osock.recvfrom(1024)
		temp.append([data, i])

	action_list = temp

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log( 'received message <' + str(addr) + '>:' + data)


main()
