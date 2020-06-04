# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from select import select
import socket
from threading import Thread
from time import sleep
from core.objects.connection import Connection
from core.common import KEEP_ALIVE_TIME, add_logger
from ssl import wrap_socket
from random import uniform

REMOVE_CONNECTION_ERROR_COUNT = 20

class TcpServer(Thread):

    def __init__(self, address, port, client, apptunnel, receive_queue, send_queue,
                 name="Default", use_ssl=False, certificate_file="", key_file=None):

        Thread.__init__(self)

        self.socket_list = []
        self.connections = []
        self.receive_queue = receive_queue
        self.send_queue = send_queue
        self.address = address
        self.port = port
        # Main socket is used for accepting new connection, not receiving data
        self.new_socket = None
        self.server_state = True
        self.client = client
        self.apptunnel = apptunnel
        self.logger = add_logger("main.servers.{}".format(name))
        self.name = name
        self.use_ssl = use_ssl
        self.certificate_file = certificate_file
        self.key_file = key_file

    def run(self):

        while True:

            sleep(0.02)

            if self.new_socket:

                # Get all available sockets
                read_sockets, write_sockets, error_sockets = select(self.socket_list, [], [],1)

                # Check every socket
                for sock in read_sockets:

                    # If socket is main socket, accept new connection
                    if sock is self.new_socket and not self.client:

                            self.accept_new_connection()

                    # If not main socket, receive data
                    elif len(self.connections) > 0:

                        related_connection = None
                        connection_id = 0

                        # Check every connection to get related connection object
                        for connection in self.connections:

                            if connection.get_socket() is sock:
                                # Get connection ID
                                related_connection = connection
                                connection_id = related_connection.get_connection_id()

                        # Receive data from socket
                        data = self.receive_data(sock, connection_id)

                        if len(data) > 0:

                            # Get host and port of socket
                            host, port = sock.getsockname()
                            self.logger.debug("Packet received from {}:{} - Connection ID: {}".format(host, port, connection_id))
                            related_connection.reset_error_count()
                            # Put received data to recive_queue. It will be processed at worker thread.
                            self.receive_queue.put((host, port, data, connection_id))

                        else:

                            # If empty packet received remove socket from socket list, and connection from connection list
                            host, port = sock.getsockname()
                            self.logger.debug("Empty packet received from {}:{} Connection ID: {} Error count: {}".format(host, port, connection_id, related_connection.get_error_count()))
                            if related_connection.get_error_count() <= REMOVE_CONNECTION_ERROR_COUNT:
                                related_connection.increment_error_count()

                            elif related_connection.get_error_count() > REMOVE_CONNECTION_ERROR_COUNT:
                                self.remove_connection(sock)

    # Creates main socket
    def create_socket(self):

        # Create socket
        self.new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.new_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # If ssl mode enabled, wrap socket with ssl
        if self.apptunnel and not self.client and self.use_ssl:

            tmpSocket = self.new_socket

            # Certificate and key files are provided by main thread.
            self.new_socket = wrap_socket(tmpSocket, certfile=self.certificate_file, keyfile=self.key_file,
                                          server_side=True)

            self.logger.debug("{} - Wrapping socket with ssl!".format(self.name))

        # Add main socket to socket list.
        self.socket_list.append(self.new_socket)

    def bind_server(self):

        try:

            # Bind new socket to provided address and port
            self.new_socket.bind((self.address, self.port))

        except:

            self.logger.exception("Requested port already in use {}:{}!".format(self.address, self.port))

    def start_listening(self):

        # Start listening for new connection
        self.new_socket.listen(20)
        self.new_socket.setblocking(0)

    def connect_remote(self, remote_ip, remote_port, connection_id=0):

        if self.apptunnel and self.client and self.use_ssl:

            # Wrap socket with ssl
            new_socket_temp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket = wrap_socket(new_socket_temp)
            new_socket.connect((remote_ip, remote_port))

            self.logger.debug("{} - Wrapping socket with ssl!".format(self.name))


        else:

            new_socket = socket.create_connection((remote_ip, remote_port))

        # Create new connection object
        new_connection = Connection(new_socket.getsockname()[0],
                                    new_socket.getsockname()[1],
                                    new_socket, connection_id)
        # Add connection to connections list
        self.connections.append(new_connection)
        # Add socket to socket list
        self.socket_list.append(new_socket)
        self.logger.info("Connected to remote {}:{}".format(remote_ip, remote_port))

        return new_connection

    # This method is used by server instance
    def accept_new_connection(self):

        try:

            # Accept new connection
            client, address = self.new_socket.accept()

        except Exception, e:

            self.logger.exception("Can't accept connection: {}".format(str(e)))

        else:

            is_new_connection = True

            for connection in self.connections:

                if connection.get_received_port() == address[1] and connection.get_received_address() == address[0]:

                    is_new_connection = False
                    break

            if is_new_connection:

                if self.apptunnel:

                    self.logger.info("New app tunnel connection from {}".format(address))
                    # connection_id isn't required for apptunnel connections, currently server supports one connection
                    connection_id = 0

                else:

                    # Set connection id, connection_id is used to seperate proxy connections
                    connection_id = self.create_connection_id()
                    self.logger.info("New proxy connection from {} - ConnetionID: {}".format(address, connection_id))

                # Create new connection
                new_connection = Connection(address[0], address[1], client, connection_id)
                self.connections.append(new_connection)
                self.socket_list.append(client)

    # Receive data from active connections
    def receive_data(self, sock, connection_id=0):

        try:

            received_data = sock.recv(80000)

        except:

            self.logger.debug("{} - Recieve data error! Connection ID: {}".format(self.name, connection_id))
            # Remove connection and socket
            self.remove_connection(sock)
            return ""

        else:

            # If connection is alive, return received data
            return received_data

    def get_connection_list(self):

        return self.connections

    # Remove dead connection
    def remove_connection(self, sock):

        for connection in self.connections:

            if connection.get_socket() is sock:

                self.logger.debug("{} - Removing connection {}:{} Connection ID: {}".format(self.name, connection.get_received_address(),
                                                                         connection.get_received_port(), connection.get_connection_id()))
                self.connections.remove(connection)
                self.socket_list.remove(sock)
                try:
                    sock.shutdown(1)
                    sock.close()
                except:
                    self.logger.debug("Socket is not connected")

        self.logger.info("Connection count: {}".format(len(self.connections)))
        self.logger.info("Socket count: {}".format(len(self.socket_list)))

        return

    @staticmethod
    def create_connection_id():

        random_connection_id = int(uniform(10000000, 99999999))
        return random_connection_id


class SendData(Thread):

    def __init__(self, send_queue, connections, appmodule, is_tunnel_sender=False, is_client=False):

        Thread.__init__(self)

        self.send_queue = send_queue
        self.connections = connections
        self.appmodule_main = appmodule
        self.is_tunnel_sender = is_tunnel_sender
        #
        if is_client and is_tunnel_sender:
            self.connections[0].set_keepalive_timer(0)
        self.logger = add_logger("main.servers.senddata")
        self.running = True

    def run(self):

        while self.running:

            sleep(0.01)

            # Check send queue
            if not self.send_queue.empty():

                # Process every queue item
                while not self.send_queue.empty():

                    # Get item from queue
                    queue_socket_object, queue_connection, queue_payload = self.send_queue.get()

                    try:

                        # Send payloads to socket
                        self.send_data(queue_socket_object, queue_payload, self.logger, self.is_tunnel_sender)

                        if self.is_tunnel_sender and len(self.connections) > 0:

                            #self.logger.debug("Sending data to apptunnel.")
                            # Reset keepalive timer
                            self.connections[0].set_keepalive_timer(KEEP_ALIVE_TIME)

                        else:
                            None
                            #self.logger.debug("Sending data to proxy.")

                    except socket.error,e:

                        self.logger.exception("Cant send data removing connection: {}".format(str(e)))
                        # Remove connection
                        queue_connection.set_remove_connection(True)

            # Send keepalive packets if it is a apptunnel sender thread
            elif hasattr(self.appmodule_main, "create_keepalive_packet") and len(self.connections) > 0 \
                    and self.is_tunnel_sender:

                if int(self.connections[0].get_keepalive_timer()) > 0:

                    # Change keepalive timer
                    self.connections[0].set_keepalive_timer(self.connections[0].get_keepalive_timer() - 0.01)

                else:

                    try:

                        # Create keepalive packet
                        payload = self.appmodule_main.create_keepalive_packet()

                        # Send keepalive packet
                        self.send_data(self.connections[0], payload, self.logger)

                        # Reset keepalive timer
                        self.connections[0].set_keepalive_timer(KEEP_ALIVE_TIME)

                    except socket.error, e:
                        # Remove connection
                        self.connections[0].set_remove_connection(True)
                        self.logger.exception("Socket error: {}".format(str(e)))

        self.logger.debug("Stopping sender thread.")

    def stop(self):

        self.running = False

    @staticmethod
    def send_data(socket_object, payload, logger, toTunnel=True):

        try:

            # Get available sockets
            read_sockets, write_sockets, error_sockets = select([socket_object.get_socket()],
                                                                [socket_object.get_socket()], [])

            # Check every socket to find socket_object
            for sock in write_sockets:

                if sock is socket_object.get_socket():

                    # If payload is a list, send every item
                    if isinstance(payload, list):

                        for packet in payload:
                            sleep(0.01)
                            socket_object.get_socket().sendall(packet)
                    else:

                        socket_object.get_socket().sendall(payload)

            if toTunnel:

                logger.debug("All packets send to tunnel")

        except Exception,e:

            logger.debug("Send data error!\n {}".format(e))