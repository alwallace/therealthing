import socket
import atexit

UDP_IP='127.0.0.1'
UDP_PORT_IN=7300
UDP_PORT_RESPONSE=6300

UDP_IP_DATABASE='127.0.0.1'
UDP_PORT_DATABASE=7200

UDP_IP_SHORT_MEM='127.0.0.1'
UDP_PORT_SHORT_MEM=7201

UDP_LOG_IP = '127.0.0.1'
UDP_LOG_PORT = 9999

MAX_SPATIAL_TOKEN_COUNT_MAX=100

# _____________________________
# VARIABLES stored in short mem
# _____________________________
# SPATIAL_TOKEN_COUNT
	# current number of tokens in short mem since (not including) last punctuation
# SPATIAL_LAST_TOKEN_LOCATION
	# the id location (0 to TOKEN_COUNT_MAX) of the last token stored in SPATIAL_TOKEN_X
# SPATIAL_TOKEN_COUNT_MAX
	# the maximum number of tokens that can be stored w/o overwritting tokens in the array
# SPATIAL_TOKEN_ID_X (where X = 0 to SPATIAL_TOKEN_COUNT_MAX)
	# the token ID corresponding to DB id
# SPATIAL_TOKEN_VALUE_X (where X = 0 to SPATIAL_TOKEN_COUNT_MAX)
	# the values of the tokens

# ____________________
# RELATIONS used in DB
# ____________________
# X_SPACES_FORWARD
	# X has a max value up to VARIABLES::SPATIAL_TOKEN_COUNT_MAX

VARIABLE_NAME_IDS = {}

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((UDP_IP, UDP_PORT_RESPONSE))

def log(msg):
	osock.sendto('trl_new_token.py: ', (UDP_LOG_IP, UDP_LOG_PORT))
	osock.sendto(msg+'\n', (UDP_LOG_IP, UDP_LOG_PORT))

def process_token(token, osock):

	# NOW PING THE TOKEN IN THE DB TO CREATE/GET THE ID
	osock.sendto('PING ' + token, (UDP_IP_DATABASE, UDP_PORT_DATABASE))
	osock.sendto('GETLASTPINGID', (UDP_IP_DATABASE, UDP_PORT_DATABASE))
	data, addr = osock.recvfrom(1024)
	if data != '':
		token_id = int(data)
	else:
		token_id = -1


	# NOW MANAGE THE SHORT TERM MEMORY SECTION
	# 	MANAGE THE SPATIAL RELATIONSHIPS OF THE TOKEN IN STATEMENTS
	osock.sendto('GET SPATIAL_TOKEN_COUNT', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	data, addr = osock.recvfrom(1024)
	if data == '':
		token_count = 0
	else:
		token_count = int(data)

	osock.sendto('GET SPATIAL_LAST_TOKEN_LOCATION', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	data, addr = osock.recvfrom(1024)
	if data == '':
		last_token_location = 0
	else:
		last_token_location = int(data)

	osock.sendto('GET SPATIAL_TOKEN_COUNT_MAX', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	data, addr = osock.recvfrom(1024)
	if data == '':
		token_count_max = 0
	else:
		token_count_max = int(data)

	if token_count == 0:
		osock.sendto('STORE SPATIAL_TOKEN_ID_0 ' + str(token_id), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION 0', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))

	elif last_token_location > MAX_SPATIAL_TOKEN_COUNT_MAX:
		osock.sendto('STORE SPATIAL_TOKEN_ID_0 ' + str(token_id), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION 0', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	else:
		osock.sendto('STORE SPATIAL_TOKEN_ID_' + str(last_token_location + 1) + ' ' + str(token_id), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION ' + str(last_token_location + 1), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	last_token_location = last_token_location + 1

	if token_count < token_count_max:
		osock.sendto('STORE SPATIAL_TOKEN_COUNT ' + str(token_count + 1), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
	token_count = token_count + 1
	
	if token == '.' or token == '!' or token == '?':
		osock.sendto('STORE SPATIAL_TOKEN_COUNT 0', (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))


	# NOW CREATE DATABASE RELATIONS
	i = 1
	temp_token_location = last_token_location

	log( 'INSERTING RELATIONS: ' + str(i) + ' - ' + str(token_count) + " FROM: " + str(temp_token_location))
	while i < token_count:
		temp_token_location = temp_token_location - 1
		if temp_token_location < 0:
			temp_token_location = MAX_SPATIAL_TOKEN_COUNT_MAX

		osock.sendto('GET SPATIAL_TOKEN_ID_' + str(temp_token_location), (UDP_IP_SHORT_MEM, UDP_PORT_SHORT_MEM))
		data, addr = osock.recvfrom(1024)
		token2_id = int(data)

		osock.sendto('RELATE ' + str(token_id) + ' ' + str(token2_id) + ' ' + str(i) + '_SPACES_FORWARD', (UDP_IP_DATABASE, UDP_PORT_DATABASE))
		log( 'RELATE ' + str(token_id) + ' ' + str(token2_id) + ' ' + str(i) + '_SPACES_FORWARD')

		i = i+1


	log( 'Processed token:' + token)

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
		log( 'Received message <' + str(addr) + '>:' + data)

		process_token(data, osock)

main()


# THINGS THAT BREAK
# 1. If you try to set SPATIAL_TOKEN_COUNT_MAX (short_mem) > MAX_SPATIAL_TOKEN_COUNT_MAX (local) then things break! DO NOT DO.