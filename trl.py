# The major file that starts it all!

import subprocess

init_process_list_names = [ \
					'trl_hub.py', \
					'trl_new_token.py', \
					'trl_short_mem.py', \
					'trl_db.py' \
					]

process_list = {}


def addProcess(process_name):
	global process_list

	line = 'python ' + process_name

	try:
		process_list[process_name] = subprocess.Popen(line, shell=True)
		print 'Added ' + process_name + '.'
	except:
		print 'COULT NOT ADD ', process_name

def removeProcess(process_name):
	global process_list

	process_list[process_name].terminate()
	del process_list[process_name]

def main():
	global process_list

	print " <(''<) Welcome Root (>'')> " 
	print "Use 'exit' to close me."
	print 'Use \'add\' to add a process'
	print 'Use \'remove\' to remove a process'
	print ''

	for process_name in init_process_list_names:
		addProcess(process_name)

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