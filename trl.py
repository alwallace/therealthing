# The major file that starts it all!

import subprocess
import socket
import atexit
import time
import trl_constants

init_process_list_names = [ \
					'trl_db.py', \
					'trl_short_mem.py', \
					'trl_new_token.py', \
					'trl_hub.py', \
					'trl_action_manager.py', \
					'trl_state_manager.py'
					]

process_list = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('127.0.0.1', 9997))

def log(msg):
	sock.sendto('trl.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	sock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def cleanup(sock):
	log( 'Cleaned.')
	sock.close()

def addProcess(process_name):
	global process_list

	line = 'python ' + process_name

	try:
		process_list[process_name] = subprocess.Popen(line, shell=True)
		time.sleep(0.200)
		print 'Added ' + process_name + '.'
	except:
		print 'COULT NOT ADD ', process_name

def removeProcess(process_name):
	global process_list

	process_list[process_name].terminate()
	del process_list[process_name]

def main():
	global process_list

	atexit.register(cleanup, sock)

	print " <(''<) Welcome Root (>'')> " 
	print "Use 'exit' to close me."
	print 'Use \'add\' to add a process'
	print 'Use \'remove\' to remove a process'
	print ''

	log('\n')
	log('------------------------------')
	log('-     NEW SESSION CREATED    -')
	log('------------------------------')

	for process_name in init_process_list_names:
		addProcess(process_name)
		data, addr = sock.recvfrom(1024)
		while data != 'loaded':
			data, addr = sock.recvfrom(1024)

	print ''

	user_input = ''
	while user_input != 'exit':
		print 'Running:'
		for i in process_list.keys():
			print '   ', i
		print ''

		user_input = raw_input('$:')

		if user_input == 'add':
			print 'Which process would you like to add:',
			user_input = raw_input('')

			if user_input in process_list.keys():
				print 'That process is already running!'
			else:
				addProcess(user_input)

			user_input = ''

		elif user_input == 'remove':
			print 'Which process would you like to remove:',
			user_input = raw_input('')

			if user_input in process_list.keys():
				removeProcess(user_input)
			else:
				print 'That process is not running!'

			user_input = ''

		elif user_input == 'reload':
			print 'Which process would you like to reload:',
			user_input = raw_input('')

			if user_input in process_list.keys():
				removeProcess(user_input)
				addProcess(user_input)
			else:
				print 'That process is not running!'

			user_input = ''

	
	for process_name in process_list.keys():
		removeProcess(process_name)
	
	print ""
	print " ^('')^ Done ^('')^ "

main()