# Peer-to-Peer File Transfer

This project takes advantage of Python's Socket API to create a P2P File Transfer system. File transfer is accomplished through 2 programs: `P2PClient.py` and `P2PTracker.py`. 

## Tracker
The tracker, similar to BitTorrent, will keep track of all clients in the network and keep track of which file chunks each client has. The tracker takes advantage of the socket and thread APIs to accept multiple incoming connections in parallel. This allows the tracker to communicate with multiple clients at once and distribute chunks to every client in the network efficiently. 

## Client 
The client's job is to bind to the tracker's connection socket and register which chunks it has. Then the client will also start its own thread where it creates its own connection socket so that other peers can connect to it for file chunk sharing. From here the client will continuously ask the tracker which peers have the file chunks it is missing to initiate chunk sharing on the other peer's connection socket.

## File chunk folders
There are 3 folders (`folder{n}`) each containing some, but not all file chunks of the file trying to be distributed. Within the folder they contain byte files (`chunk_{i}`) and a `local_chunks.txt` file. This file will be parsed by the tracker so that the tracker knows which chunks that peer has. The format of this file is:
```
{i}, chunk_{i}
{i}, chunk_{i}
{n}, LASTCHUNK
```

$n = $ total number of chunks
LASTCHUNK is just a delimiter letting the Tracker know that $n$ is the total number of chunks.

## Testing 

### Tracker 
To start file sharing start 3 different instances of the client program each with different file chunks, and 1 tracker. 


```
python3 P2PTracker.py
```
### Client(s)
```
python3 P2PClient.py -folder <folder-path> -transfer_port <transfer-port> -name <name>
```

- `folder-path` Path to folder which contains which file chunks this client will have 
- `transfer-port` Port on which this client's p2p connection socket will run. (NOT port for Tracker connection socket)
- `name` Name of client

## Logging
After running the program you can see information about how the chunks were shared in `logs.log`


