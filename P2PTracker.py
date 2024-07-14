import socket
import argparse
import threading
import sys
import hashlib
import time
import logging


# TODO: Implement P2PTracker


def handle_peer(peer):
    try:
        while True:
            message = peer.recv(1024).decode()
            if message[: len("LOCAL_CHUNKS")] == "LOCAL_CHUNKS":
                logger.info(f"P2PTracker,{message}")
                update_chunk_info(message)
                logger.info(f"chunk_info is now {chunk_info}")
            elif message[: len("WHERE_CHUNK")] == "WHERE_CHUNK":
                logger.info(f"P2PTracker was asked {message}")
                response = handle_missing_chunk_req(message)
                peer.sendall(response.encode())
                time.sleep(1.0)
    except:
        pass
    finally:
        peer.close()


def update_chunk_info(message):
    _, chunk_index, ip, port = message.split(",")
    ip, port = str(ip), str(port)

    if chunk_index in chunk_info:
        chunk_info[chunk_index].append((ip, port))
    else:
        chunk_info[chunk_index] = [(ip, port)]


def handle_missing_chunk_req(message):
    _, chunk_index = message.split(",")
    if chunk_index not in chunk_info:
        logger.info(f"P2PTracker,CHUNK_LOCATION_UNKNOWN,{chunk_index}")
        return f"CHUNK_LOCATION_UNKNOWN,{chunk_index}"
    hosts = chunk_info[chunk_index]
    message = f"GET_CHUNK_FROM,{chunk_index},"
    for i in range(len(hosts)):
        ip, port = hosts[i]
        if i == len(hosts) - 1:
            message += f"{ip},{port}"
        else:
            message += f"{ip},{port},"
    logger.info(f"P2PTracker,{message}")
    return message


if __name__ == "__main__":
    # set up logging
    logging.basicConfig(filename="logs.log", format="%(message)s", filemode="a")
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)


    # establish Tracker Socket
    t_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    t_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    t_socket.bind(("localhost", 5100))
    t_socket.listen()

    logger.info("Tracker is live.")

    chunk_info = {}
    peers = []

    while True:
        peer_sock, addr = t_socket.accept()

        # update peers
        peers.append(peer_sock)

        # starting thread for new client
        client_peer_thread = threading.Thread(target=handle_peer, args=(peer_sock,))
        client_peer_thread.start()
