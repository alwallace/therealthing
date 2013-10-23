import sqlite3
import socket
import atexit
import trl_constants

last_ping_id = -1
last_relation_id = -1

TIME_ELAPSED =  0

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((trl_constants.UDP_IP_DB, trl_constants.UDP_PORT_DB_RESPONSE))

def log(msg):
	osock.sendto('trl_db.py: ', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))
	osock.sendto(msg+'\n', (trl_constants.UDP_IP_LOG, trl_constants.UDP_PORT_LOG_IN))

def initializeDB(c):
	c.execute('DROP TABLE nodes')
	c.execute('DROP TABLE relations')
	c.execute('CREATE TABLE nodes (id INTEGER PRIMARY KEY, value BLOB)')
	c.execute('CREATE TABLE relations (id INTEGER PRIMARY KEY, nid1 INTEGER, nid2 INTEGER, tid INTEGER, timestamp INTEGER)')

	c.execute('INSERT INTO nodes (value) VALUES ("UNDEFINED_RELATION")')
	log('constant DB_UNDEFINED_RELATION_ID = ' + str(c.lastrowid))

	c.execute('INSERT INTO nodes (value) VALUES ("1_SPACES_FORWARD")')
	log('constant 1_SPACES_FORWARD_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("2_SPACES_FORWARD")')
	log('constant 2_SPACES_FORWARD_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("3_SPACES_FORWARD")')
	log('constant 3_SPACES_FORWARD_ID = ' + str(c.lastrowid))

	c.execute('INSERT INTO nodes (value) VALUES ("IS_STATE")')
	log('constant IS_STATE_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("IS_ACTION")')
	log('constant IS_ACTION_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("IS_TIME")')
	log('constant IS_TIME_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("IS_POSSIBLE_ACTION")')
	log('constant IS_POSSIBLE_ACTION_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("IS_POSSIBLE_STATE")')
	log('constant IS_POSSIBLE_STATE_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("CURRENT")')
	log('constant CURRENT_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("TIME_ELAPSED")')
	log('constant TIME_ELAPSED_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("DECISION")')
	log('constant DECISION_ID = ' + str(c.lastrowid))

	c.execute('INSERT INTO nodes (value) VALUES ("THIS")')
	log('constant THIS_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("THEN")')
	log('constant THEN_ID = ' + str(c.lastrowid))
	c.execute('INSERT INTO nodes (value) VALUES ("VIA")')
	log('constant VIA_ID = ' + str(c.lastrowid))

def pingvalue(node_value, c):
	global last_ping_id
	c.execute('INSERT INTO nodes (value) VALUES (?)', (node_value,))
	nid = c.lastrowid

	last_ping_id = int(nid)

	log(' -> PING: ' + str(nid) + ' ' + node_value)


def getid(osock, addr, node, c):
	c.execute('SELECT id FROM nodes WHERE value=?', (node,))
	rows = c.fetchall()
	if len(rows) != 0:
		for row in rows:
			osock.sendto(str(row[0]), addr)
			log( ' -> GETID: ' + str(row[0]))
	else:
		log(' -> GETID: not valid id')

	osock.sendto('.', addr)

def getvalue(osock, addr, node_id, c):
	c.execute('SELECT value FROM nodes WHERE id=?', (node_id,))
	row = c.fetchone()
	if row == None:
		nvalue = ''
	else:
		nvalue = str(row[0])

	osock.sendto(nvalue, addr)

	log( ' -> GETVALUE: ' + nvalue)

def getlastpingid(osock, addr):
	log('GETLASTPINGID -> ' + str(last_ping_id))

	osock.sendto(str(last_ping_id), addr)

def getlastrelationid(osock, addr):
	log('GETLASTRELATIONID -> ' + str(last_relation_id))

	osock.sendto(str(last_relation_id), addr)

def relate(node1_id, node2_id, relation_type_id, c):
	global last_relation_id

	c.execute('SELECT id, nid1, nid2, tid FROM relations WHERE nid1=? AND nid2=? AND tid=?', (node1_id, node2_id, relation_type_id,))
	row = c.fetchone()
	rid = 0
	if row == None:
		c.execute('INSERT INTO relations (nid1, nid2, tid, timestamp) VALUES (?, ?, ?, ?)', (node1_id, node2_id, relation_type_id, TIME_ELAPSED,))
		rid = int(c.lastrowid)

	last_relation_id = rid
	log(  ' -> RELATE: (' + str(rid) + ') ' + str(node1_id) + ' ==(' + str(relation_type_id) + ')>> ' + str(node2_id) + ' @ ' + str(TIME_ELAPSED))

def getrrelated(osock, addr, node1_id, relation_type_id, c):
	c.execute('SELECT nid2 FROM relations WHERE nid1=? AND tid=?', (node1_id, relation_type_id, ))
	nids = c.fetchall()

	

	if len(nids) != 0:
		nids = nids[0]
		log(' -> GETRRELATED: ' + str(nids))
		for nid in nids:
			osock.sendto(str(nid), addr)
	else:
		log(' -> GETRRELATED: not valid id')

	osock.sendto('.', addr)

def destroynode(node_id, c):
	c.execute('DELETE FROM nodes WHERE id=?', (node_id, ))
	c.execute('DELETE FROM relations WHERE nid1=?', (node_id, ))

	log(  ' -> DESTROYNODE:' + str(node_id))

def destroyrelation(relation_id, c):
	c.execute('DELETE FROM relations WHERE id=?', (relation_id, ))

	log(' -> DESTROYRELATION:' + str(relation_id))

def cleanup(sock, osock):
	log(  'Cleaned.' )
	sock.close()
	osock.close()
	

def main():
	global TIME_ELAPSED

	conn = sqlite3.connect('./database.sqlite')
	c = conn.cursor()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((trl_constants.UDP_IP_DB, trl_constants.UDP_PORT_DB_IN))

	atexit.register(cleanup, sock, osock)
	initializeDB(c)
	log('trl_db LOADED')
	osock.sendto('loaded', trl_constants.TRL_PROCESS_NET)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log('received message <' + str(addr) + '>:' + data)

		split_data = data.split(' ', 1)

		# syntax: PING <NODE_VALUE>
		# function: add token to database if it does not exist. Also set last ping to this new value
		if split_data[0] == 'PING':
			pingvalue(split_data[1], c)

		# syntax: GETID <NODE_VALUE>
		# function: get the id of the 'value', maybe a list of id's, come one per line finished by a '.' packet
		elif split_data[0] == 'GETID':
			getid(osock, addr, split_data[1], c)

		# syntax: GETLASTPINGID 
		# function: get the last ping id
		elif split_data[0] == 'GETLASTPINGID':
			getlastpingid(osock, addr)

		# syntax: GETLASTRELATIONID
		# function: get the last relation id
		elif split_data[0] == 'GETLASTRELATIONID':
			getlastrelationid(osock, addr)

		# syntax: GETVALUE <NODE_ID>
		# function: get the 'value' based on the id
		elif split_data[0] == 'GETVALUE':
			getvalue(osock, addr, split_data[1], c)

		# syntax: RELATE <NODE1_ID> <NODE2_ID> <RELATION_TYPE_ID>
		# function: create a new relation of relation type between the nodes.
		elif split_data[0] == 'RELATE':
			split_data = split_data[1].split()
			relate(split_data[0], split_data[1], split_data[2], c)

		# syntax: GETRRELATED <NODE1_ID> <RELATION_TYPE_ID>
		# function: get the nodes that are related to NODE1 via relation type, may be a list of id's. come one per line finished by a '.' packet
		elif split_data[0] == 'GETRRELATED':
			split_data = split_data[1].split()
			getrrelated(osock, addr, split_data[0], split_data[1], c)

		# syntax: DESTROYNODE <NODE_ID>
		# function: remove a node and all of its immediate relations
		elif split_data[0] == 'DESTROYNODE':
			destroynode(split_data[1], c)

		# syntax: DESTROYRELATION <RELATION_ID>
		# function: remove a relation between two nodes by the id
		elif split_data[0] == 'DESTROYRELATION':
			destroyrelation(split_data[1], c)

		# syntax: TICK <elapsed>
		# function: increases the time that has elapsed for managing timestamp data
		elif split_data[0] == 'TICK':
			TIME_ELAPSED = float(split_data[1])

		conn.commit()

main()