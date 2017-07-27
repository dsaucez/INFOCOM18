#!/usr/bin/env python

"""
@author Sunil Mallya
Sample code to show a parent - child like process communication model where parent listens on a port and passes the pickled file descriptor
to the child process to read the bytes off the socket. The communication in this snippet is via a Queue which is thread/process safe
Just to be clear, the parent process is still accepting the connection and we are sending a live fd to the child
"""
import os
import sys
import SocketServer
import Queue
import time
import socket
import multiprocessing
from multiprocessing.reduction import reduce_handle
from multiprocessing.reduction import rebuild_handle 

#Refer for more multiprocessing info http://docs.python.org/2/library/multiprocessing.html
class MultiprocessWorker(multiprocessing.Process):

	def __init__(self, sq):

		# base class initialization
		multiprocessing.Process.__init__(self)

		# job management stuff
		self.socket_queue = sq
		self.kill_received = False

        def recvall(self, sock):
            l = 0
            while True:
                chunck = sock.recv(4096)
                if not chunck:
                    break
                l = l + len(chunck)
            return l
                


	def run(self):
		while not self.kill_received:
			try:
				h = self.socket_queue.get()
				fd=rebuild_handle(h)
				client_socket=socket.fromfd(fd,socket.AF_INET,socket.SOCK_STREAM)
                                print self.recvall(client_socket), "on", client_socket.getsockname()[1]
				client_socket.close()

			except Queue.Empty:
                                print "WHAT1?"
				pass
                        except Exception as e:
                                print "WHAT2?"
                                pass

class MyTCPHandler(SocketServer.BaseRequestHandler):
	"""
	The RequestHandler class for our server.

	It is instantiated once per connection to the server, and must
	override the handle() method to implement communication to the
	client.
	"""

	def handle(self):
		# self.request is the TCP socket connected to the client
		#self.data = self.request.recv(1024).strip()
		#print "{} wrote:".format(self.client_address[0])
		#print self.data
		# just send back the same data, but upper-cased
		#self.request.sendall(self.data.upper())

		#Either pipe it to worker directly like this
		#pipe_to_worker.send(h) #instanceofmultiprocessing.Pipe
		#or use a Queue :)
		
		h = reduce_handle(self.request.fileno())
		socket_queue.put(h)


if __name__ == "__main__":

	#Mainprocess
	address =  ('0.0.0.0', int(sys.argv[1]))
	server = SocketServer.TCPServer(address, MyTCPHandler)
	socket_queue = multiprocessing.Queue()

 	for i in range(500):
		worker = MultiprocessWorker(socket_queue)
		worker.start()

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		sys.exit(0)

