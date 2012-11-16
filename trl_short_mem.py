import socket
import atexit

UDP_IP='127.0.0.1'
UDP_PORT_IN=7201
UDP_PORT_RESPONSE=6201

UDP_LOG_IP = '127.0.0.1'
UDP_LOG_PORT = 9999

memory = {}

# DEFAULT SETTINGS!
memory['SPATIAL_TOKEN_COUNT_MAX'] = '3'

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((UDP_IP, UDP_PORT_RESPONSE))

def log( msg):
	osock.sendto('trl_short_mem.py: ', (UDP_LOG_IP, UDP_LOG_PORT))
	osock.sendto(msg+'\n', (UDP_LOG_IP, UDP_LOG_PORT))

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
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock, osock)

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