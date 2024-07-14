import threading
import time

def read_chunks(folder_path):
	file_path = folder_path + "/local_chunks.txt"
	with open(file_path, "r") as file:
		lines = file.readlines()
		print(lines)
		total_chunks = int(lines[-1].split(",")[0])
		print(total_chunks)
		chunks = [None] * total_chunks
		for line in lines:
			chunk_index, chunk_name = line.split(",")
			if chunk_name != "LASTCHUNK\n":
				chunks[int(chunk_index) - 1] = chunk_name.replace("\n", "")
	return chunks


print(read_chunks("folder1"))
