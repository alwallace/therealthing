import socket
import atexit
import trl_constants

memory = {}

# DEFAULT SETTINGS!
memory['SPATIAL_TOKEN_COUNT_MAX'] = '3'

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_SHORT_MEM, trl_constants.UDP_PORT_SHORT_MEM_RESPONSE))

def log( msg):
	osock.sendto('trl_short_mem.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def store(name, value):
	global memory
	log( ' -> STORED:' + name + value)

	if value == '':
		del memory[name]
	else:
		memory[name] = value

def get(name, osock, addr):
	global memory
	if name in memory:
		log( ' -> GOT:' + name + memory[name])
		osock.sendto(memory[name], addr)
		
	else:
		log( ' -> GOT:' + name)
		osock.sendto('', addr)

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()
	

def main():
	global memory
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind(trl_constants.SHORT_MEM_NET)

	atexit.register(cleanup, sock, osock)
	log('trl_short_mem LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log( 'received message <' + str(addr) + '>:' + data)

		split_data = data.split(' ', 1)

		# syntax: STORE <NAME> <VALUE>
		if split_data[0] == 'STORE':
			split_data = split_data[1].split(' ', 1)
			store(split_data[0], split_data[1])

		# syntax: GET <NAME>
		elif split_data[0] == 'GET':
			get(split_data[1].strip(), osock, addr)

main()