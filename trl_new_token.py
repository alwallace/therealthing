import socket
import atexit
import trl_constants

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
osock.bind((trl_constants.UDP_IP_NEW_TOKEN, trl_constants.UDP_PORT_NEW_TOKEN_RESPONSE))

def log(msg):
	osock.sendto('trl_new_token.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def process_token(token, osock):

	# NOW PING THE TOKEN IN THE DB TO CREATE/GET THE ID
	osock.sendto('PING ' + token, trl_constants.DB_NET)
	osock.sendto('GETLASTPINGID', trl_constants.DB_NET)
	data, addr = osock.recvfrom(1024)
	if data != '':
		token_id = int(data)
	else:
		token_id = -1


	# NOW MANAGE THE SHORT TERM MEMORY SECTION
	# 	MANAGE THE SPATIAL RELATIONSHIPS OF THE TOKEN IN STATEMENTS
	osock.sendto('GET SPATIAL_TOKEN_COUNT', trl_constants.SHORT_MEM_NET)
	data, addr = osock.recvfrom(1024)
	if data == '':
		token_count = 0
	else:
		token_count = int(data)

	osock.sendto('GET SPATIAL_LAST_TOKEN_LOCATION', trl_constants.SHORT_MEM_NET)
	data, addr = osock.recvfrom(1024)
	if data == '':
		last_token_location = 0
	else:
		last_token_location = int(data)

	osock.sendto('GET SPATIAL_TOKEN_COUNT_MAX', trl_constants.SHORT_MEM_NET)
	data, addr = osock.recvfrom(1024)
	if data == '':
		token_count_max = 0
	else:
		token_count_max = int(data)

	if token_count == 0:
		osock.sendto('STORE SPATIAL_TOKEN_ID_0 ' + str(token_id), trl_constants.SHORT_MEM_NET)
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION 0', trl_constants.SHORT_MEM_NET)

	elif last_token_location > MAX_SPATIAL_TOKEN_COUNT_MAX:
		osock.sendto('STORE SPATIAL_TOKEN_ID_0 ' + str(token_id), trl_constants.SHORT_MEM_NET)
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION 0', trl_constants.SHORT_MEM_NET)
	else:
		osock.sendto('STORE SPATIAL_TOKEN_ID_' + str(last_token_location + 1) + ' ' + str(token_id), trl_constants.SHORT_MEM_NET)
		osock.sendto('STORE SPATIAL_LAST_TOKEN_LOCATION ' + str(last_token_location + 1), trl_constants.SHORT_MEM_NET)
	last_token_location = last_token_location + 1

	if token_count < token_count_max:
		osock.sendto('STORE SPATIAL_TOKEN_COUNT ' + str(token_count + 1), trl_constants.SHORT_MEM_NET)
	token_count = token_count + 1
	
	if token == '.' or token == '!' or token == '?':
		osock.sendto('STORE SPATIAL_TOKEN_COUNT 0', trl_constants.SHORT_MEM_NET)


	# NOW CREATE DATABASE RELATIONS
	i = 1
	temp_token_location = last_token_location

	log( 'INSERTING RELATIONS: ' + str(i) + ' - ' + str(token_count) + " FROM: " + str(temp_token_location))
	while i < token_count:
		temp_token_location = temp_token_location - 1
		if temp_token_location < 0:
			temp_token_location = MAX_SPATIAL_TOKEN_COUNT_MAX

		osock.sendto('GET SPATIAL_TOKEN_ID_' + str(temp_token_location), trl_constants.SHORT_MEM_NET)
		data, addr = osock.recvfrom(1024)
		token2_id = int(data)

		spaces_forward_temp = str(i) + '_SPACES_FORWARD'
		osock.sendto('GETID ' + spaces_forward_temp, trl_constants.DB_NET)
		data, addr = osock.recvfrom(1024)
		trashdata = ''
		while trashdata != '.':
			trashdata, addr = osock.recvfrom(1024)

		spaces_forward_temp_id = data

		osock.sendto('RELATE ' + str(token_id) + ' ' + str(token2_id) + ' ' + spaces_forward_temp_id, trl_constants.DB_NET)
		log( 'RELATE ' + str(token_id) + ' ' + str(token2_id) + ' ' + spaces_forward_temp_id)

		i = i+1


	log( 'Processed token:' + token)

def cleanup(sock, osock):
	log( 'Cleaned.')
	sock.close()
	osock.close()
	

def main():
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_NEW_TOKEN, trl_constants.UDP_PORT_NEW_TOKEN_IN))

	atexit.register(cleanup, sock, osock)
	log('trl_new_token LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log( 'Received message <' + str(addr) + '>:' + data)

		process_token(data, osock)

main()


# THINGS THAT BREAK
# 1. If you try to set SPATIAL_TOKEN_COUNT_MAX (short_mem) > MAX_SPATIAL_TOKEN_COUNT_MAX (local) then things break! DO NOT DO.