import sqlite3
import socket
import atexit

UDP_IP='127.0.0.1'
UDP_PORT_IN=7200
UDP_PORT_RESPONSE=6200

UDP_LOG_IP = '127.0.0.1'
UDP_LOG_PORT = 9999

last_ping_id = -1

osock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
osock.bind((UDP_IP, UDP_PORT_RESPONSE))

def log(msg):
	osock.sendto('trl_db.py: ', (UDP_LOG_IP, UDP_LOG_PORT))
	osock.sendto(msg+'\n', (UDP_LOG_IP, UDP_LOG_PORT))

def pingvalue(node_value, c):
	global last_ping_id
	c.execute('SELECT id FROM nodes WHERE value=?', (node_value,))
	row = c.fetchone()
	if row == None:
		c.execute('INSERT INTO nodes (value) VALUES (?)', (node_value,))
		nid = c.lastrowid
	else:
		nid = row[0]

	last_ping_id = int(nid)

	log(' -> PING: ' + str(nid) + node_value)

def rpingvalue(relation_type_value, c):
	global last_ping_id
	c.execute('SELECT id FROM r_type WHERE value=?', (relation_type_value,))
	row = c.fetchone()
	if row == None:
		c.execute('INSERT INTO r_type (value) VALUES (?)', (relation_type_value,))
		tid = c.lastrowid
	else:
		tid = row[0]

	last_ping_id = int(tid)

	log(' -> RPING: ' + str(tid) + relation_type_value)

def getid(osock, addr, node, c):
	c.execute('SELECT id FROM nodes WHERE value=?', (node,))
	row = c.fetchone()
	if row == None:
		nid = '-1'
	else:
		nid = str(row[0])

	osock.sendto(nid, addr)

	log( ' -> GETID: ' + str(nid) + node)

def gettid(osock, addr, relation_type, c):
	c.execute('SELECT id FROM r_type WHERE value=?', (relation_type,))
	row = c.fetchone()
	if row == None:
		nid = '-1'
	else:
		nid = str(row[0])

	osock.sendto(nid, addr)

	log( ' -> GETTID: ' + str(nid) + relation_type)

def getvalue(osock, addr, node_id, c):
	c.execute('SELECT value FROM nodes WHERE id=?', (node_id,))
	row = c.fetchone()
	if row == None:
		nvalue = ''
	else:
		nvalue = str(row[0])

	osock.sendto(nvalue, addr)

	log( ' -> GETVALUE: ' + str(node_id) + nvalue)

def gettvalue(osock, addr, relation_type_id, c):
	c.execute('SELECT value FROM r_type WHERE id=?', (relation_type_id,))
	row = c.fetchone()
	if row == None:
		tvalue = ''
	else:
		tvalue = str(row[0])

	osock.sendto(tvalue, addr)

	log( ' -> GETTVALUE: ' + str(relation_type_id) + tvalue)

def getlastpingid(osock, addr):
	osock.sendto(str(last_ping_id), addr)

def relate(node1_id, node2_id, relation_type_id, c):
	log(  str(node1_id) + str(node2_id) + str(relation_type_id))

	c.execute('SELECT id, nid1, nid2, tid, count FROM relations WHERE nid1=? AND nid2=? AND tid=?', (node1_id, node2_id, relation_type_id,))
	row = c.fetchone()
	if row == None:
		c.execute('INSERT INTO relations (nid1, nid2, tid, count) VALUES (?, ?, ?, ?)', (node1_id, node2_id, relation_type_id, '1',))
		rid = int(c.lastrowid)
	else:
		rid = int(row[0])
		rel_count = int(row[4])
		c.execute('UPDATE relations SET count=? WHERE id=?', (str(rel_count + 1), rid,))

	log(  ' -> RELATE: (' + str(rid) + ') ' + str(node1_id) + ' ==(' + str(relation_type_id) + ')>> ' + str(node2_id))

def getrrelated(osock, addr, node1_id, relation_type_id, c):
	log(  str(node1_id) + str(relation_type_id))

	c.execute('SELECT nid2 FROM relations WHERE nid1=? AND tid=?', (node1_id, relation_type_id, ))
	nids = c.fetchall()

	if nids == None:
		osock.sendto('', addr)
	else:
		outstr = ''
		for nid in nids:
			outstr = outstr + nid + ' '
		osock.sendto(outstr, addr)

def destroynode(node_id, c):
	log(  str(node_id))

	c.execute('DELETE FROM nodes WHERE id=?', (node_id, ))
	c.execute('DELETE FROM relations WHERE nid1=?', (node_id, ))

	log(  ' -> DESTROYNODE:' + str(node_id))


def cleanup(sock, osock):
	log(  'Cleaned.' )
	sock.close()
	osock.close()
	

def main():
	conn = sqlite3.connect('./database.sqlite')
	c = conn.cursor()

	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.bind((UDP_IP, UDP_PORT_IN))

	atexit.register(cleanup, sock, osock)

	while True:
		data, addr = sock.recvfrom(1024)
		data = data.rstrip()
		log('received message <' + str(addr) + '>:' + data)

		split_data = data.split(' ', 1)

		# syntax: PING <NODE_VALUE>
		# function: add token to database if it does not exist. Also set last ping to this new value
		if split_data[0] == 'PING':
			pingvalue(split_data[1], c)

		# syntax: RPING <RELATION_TYPE_VALUE>
		# function: add relation to database if it does not exist. Also set last relation ping to this new value
		elif split_data[0] == 'RPING':
			rpingvalue(split_data[1], c)

		# syntax: GETID <NODE_VALUE>
		# function: get the id of the 'value'
		elif split_data[0] == 'GETID':
			getid(osock, addr, split_data[1], c)

		# syntax: GETTID <RELATION_TYPE_VALUE>
		# function: get the id of the 'relation type'
		elif split_data[0] == 'GETTID':
			gettid(osock, addr, split_data[1], c)	

		# syntax: GETLASTPINGID 
		# function: get the last ping id
		elif split_data[0] == 'GETLASTPINGID':
			getlastpingid(osock, addr)

		# syntax: GETVALUE <NODE_ID>
		# function: get the 'value' based on the id
		elif split_data[0] == 'GETVALUE':
			getvalue(osock, addr, split_data[1], c)

		# syntax: GETTVALUE <RELATION_TYPE_ID>
		# function: get the relation type based on the id
		elif split_data[0] == 'GETTVALUE':
			gettvalue(osock, addr, split_data[1], c)

		# syntax: RELATE <NODE1_ID> <NODE2_ID> <RELATION_TYPE_ID>
		# function: create a new relation of relation type between the nodes. If one exists increment the relation count
		elif split_data[0] == 'RELATE':
			split_data = split_data[1].split()
			log(str(split_data))
			relate(split_data[0], split_data[1], split_data[2], c)

		# syntax: GETRRELATED <NODE1_ID> <RELATION_TYPE_ID>
		# function: get the nodes that are related to NODE1 via relation type, may be a list of id's.
		elif split_data[0] == 'GETRRELATED':
			split_data = split_data[1].split()
			log(str(split_data))
			getrrelated(osock, addr, split_data[0], split_data[1], c)

		# syntax: DESTROYNODE <NODE_ID>
		# function: remove a node and all of its immediate relations
		elif split_data[0] == 'DESTROYNODE':
			destroynode(split_data[1], c)


		conn.commit()

main()