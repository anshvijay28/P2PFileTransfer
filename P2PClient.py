import socket
import argparse
import threading
import sys
import hashlib
import time
import logging
import os 


# TODO: Implement P2PClient that connects to P2PTracker


def parse_args():
	# python3 P2PClient.py -folder <my-folder-full-path> -transfer_port <transfer-port> -name <name>
	parser = argparse.ArgumentParser(description="Client for P2P File Sharing")

	# positional -folder, -transfer_port, -name arguments
	parser.add_argument(
		"-folder", metavar="<folder_path>", type=str, help="specify folder path"
	)
	parser.add_argument(
		"-transfer_port",
		metavar="<transfer_port_num>",
		type=int,
		help="specify transfer port number",
	)
	parser.add_argument(
		"-name", metavar="<client_name>", type=str, help="specify client name"
	)

	args = parser.parse_args()

	folder_path = args.folder
	transfer_port = args.transfer_port
	name = args.name

	return folder_path, transfer_port, name


def setup_p2p_socket(ip, port):
	p2p_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	p2p_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	p2p_socket.bind((ip, port))
	return p2p_socket


def check_chunks_owned():
	for chunk in chunks:
		if not chunk:
			return False
	return True


def read_chunks(folder_path):
	file_path = folder_path + "/local_chunks.txt"
	with open(file_path, "r") as file:
		lines = file.readlines()
		total_chunks = int(lines[-1].split(",")[0])
		chunks = [None] * total_chunks
		for line in lines:
			chunk_index, chunk_name = line.split(",")
			if chunk_name != "LASTCHUNK\n":
				chunks[int(chunk_index) - 1] = chunk_name.replace("\n", "")
	return chunks


def inform_tracker(c):
	if type(c) == list:
		for i in range(len(c)):
			if c[i]:
				message = f"LOCAL_CHUNKS,{i + 1},localhost,{transfer_port}"
				logger.info(f"{name},{message}")
				client.sendall(message.encode())
				time.sleep(1.0)
	elif type(c) == int:
		if chunks[c]:
			message = f"LOCAL_CHUNKS,{c + 1},localhost,{transfer_port}"
			logger.info(f"{name},{message}")
			client.sendall(message.encode())
			time.sleep(1.0)  # don't send messages without a space in between


def handle_missing_chunks():
	# sleep because need to wait for other clients to get connected 
	# time.sleep(2.0)
	i = 0
	while not check_chunks_owned():
		if not chunks[i]:
			message = f"WHERE_CHUNK,{i + 1}"
			logger.info(f"{name},{message}")
			client.sendall(message.encode())  # we send message to tracker
			time.sleep(1.0)
			recv_message = client.recv(1024).decode()  # tracker sends message to us

			if recv_message[: len("GET_CHUNK_FROM")] == "GET_CHUNK_FROM":
				if get_chunks(recv_message):
					inform_tracker(i)
					time.sleep(1.0)
				else:
					time.sleep(1.0) 
			elif (
				recv_message[: len("CHUNK_LOCATION_UNKNOWN")]
				== "CHUNK_LOCATION_UNKNOWN"
			):
				time.sleep(1.0)  
		i = (i + 1) % len(chunks)


def get_chunks(message):
	message = message.split(",")
	chunk_index = message[1]
	ipport = message[2:]
	success = False

	i = 0

	while i < len(ipport):
		# current ip and port
		ip = ipport[i]
		port = int(ipport[i + 1])  # these are transfer ports from command line
		try:
			# set up client socket, which just connects to a server socket
			req_peer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			req_peer.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			req_peer.connect((ip, port))

			logger.info(f"{name} successfully connected to peer at port {port}")

			# ask for data
			message = f"REQUEST_CHUNK,{chunk_index}"
			logger.info(f"{name},{message},{ip},{port}")
			req_peer.sendall(message.encode())
			time.sleep(1.0)
			# receive data, this function also closes req_peer socket
			success = client_recv_chunks(req_peer, chunk_index)
			if success:
				break
			i += 2

		except ConnectionRefusedError:
			logger.info(f"{name} tried to connect to ({ip, port}), but the connection refused!")
			req_peer.close()
			return False

	# update chunks
	if success:
		chunks[int(chunk_index) - 1] = "chunk_" + str(chunk_index)
		logger.info(f"{name} now has {chunks}")
	return success


def client_recv_chunks(p2p_conn, chunk_index):
	try:
		# receive file chunk
		chunk = b""
		
		while True:
			data = p2p_conn.recv(1024)
			if not data:
				break
			chunk += data

		chunk_file_path = folder_path + "/chunk_" + str(chunk_index)

		# turn binary chunk data into a file
		with open(chunk_file_path, "wb") as f:
			f.write(chunk)
		return True
	except:
		return False
	finally:
		p2p_conn.close()


def client_send_chunks(new_peer):
	try:
		# check for correct message
		message_recv = new_peer.recv(1024).decode()
		if message_recv[: len("REQUEST_CHUNK")] == "REQUEST_CHUNK":
			# get the chunk from the peer requesting the chunk
			_, chunk_index = message_recv.split(",")

			# send the chunk new_peer wants
			chunk_file_name = chunks[int(chunk_index) - 1]
			chunk_path = folder_path + "/" + chunk_file_name

			# extract and send data in file
			with open(chunk_path, "rb") as chunk_file:
				chunk = chunk_file.read()
			new_peer.sendall(chunk)
	except:
		pass
	finally:
		new_peer.close()


if __name__ == "__main__":
	folder_path, transfer_port, name = parse_args()
	chunks = read_chunks(folder_path)

	# set up logging
	logging.basicConfig(filename="logs.log", format="%(message)s", filemode="a")
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# set up client socket, which just connects to a server socket
	client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	client.connect(("localhost", 5100))

	logger.info(f"{name} with transfer port {transfer_port} is connected to Tracker")

	# init tracker with info
	inform_tracker(chunks)

	# peer thread to continuously request chunks and update tracker
	peer_req_thread = threading.Thread(target=handle_missing_chunks)
	peer_req_thread.start()
 
	# make it a regular loop instead of a thread 
	# handle_missing_chunks()

	# set up p2p socket that is ALWAYS listening for other clients
	p2p_socket = setup_p2p_socket("localhost", transfer_port)
	p2p_socket.listen()

	# while loop to continuously start threads for other peers that want to connect
	while True:
		# accept the new connection, later to be ended
		new_conn, _ = p2p_socket.accept()

		# client sending thread that accepts connections from other clients using p2p socket
		p2p_send_thread = threading.Thread(target=client_send_chunks, args = (new_conn,))
		p2p_send_thread.start()
