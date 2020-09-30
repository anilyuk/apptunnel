# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

try:
    from pybase64 import b64encode, b64decode
    use_builtin_base64 = False
except:
    from base64 import b64encode, b64decode
    use_builtin_base64 = True
from time import sleep
from threading import Thread, Event
from core.common import add_logger
from core.servers.common import create_session_id
from core.objects.session import Session


class Workers(Thread):

    def __init__(self, proxy_connections, apptunnel_connections,
                 apptunnel_queue, proxy_queue, apptunnel_send_queue, proxy_send_queue,
                 app_instance, proxy_server_thread, is_client, proxy_ip = None, proxy_port = None, access_internal = True):

        Thread.__init__(self)

        self._stop = Event()

        self.proxy_connections = proxy_connections
        self.apptunnel_connections = apptunnel_connections
        self.apptunnel_queue = apptunnel_queue
        self.apptunnel_send_queue = apptunnel_send_queue
        self.proxy_queue = proxy_queue
        self.proxy_send_queue = proxy_send_queue
        self.app_instance = app_instance
        self.proxy_server_thread = proxy_server_thread
        self.is_client = is_client
        self.access_internal = access_internal
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port
        self.logger = add_logger("main.workers")
        self.payload_with_problem = ""
        if use_builtin_base64: self.logger.debug("Using builtin base64 library. To increase connection "
                                                 "speed use pybase64 library.")

    def run(self):

        while True:

            sleep(0.001)

            # Process every item from proxy_queue
            while not self.proxy_queue.empty():

                queue_object = self.proxy_queue.get()
                self.proxy_handler(queue_object)

            # Process every item from apptunnel_queue
            while not self.apptunnel_queue.empty():

                queue_object = self.apptunnel_queue.get()
                self.apptunnel_handler(queue_object)

    def proxy_handler(self, queue_object):

        # Parse queue_object
        address, port, payload, connection_id = queue_object

        # Create new session
        new_session = Session(create_session_id())

        new_session.set_payload(payload)

        if len(self.apptunnel_connections) == 1:

            # Encode payload to send it through apptunnel
            encoded_payload = b64encode(payload, altchars=None) if not use_builtin_base64 else b64encode(payload)

            # Create payload list
            payload_list, session_id = self.app_instance.create_payloads(encoded_payload, connection_id, new_session.get_session_id())

            self.logger.debug("Sending data through apptunnel")
            self.logger.debug("Last payload length: {}".format(len(payload_list)))

            # Send payload list to apptunnel_send_queue. Send_data thread will send it
            self.apptunnel_send_queue.put((self.apptunnel_connections[0], self.apptunnel_connections[0], payload_list))


    def apptunnel_handler(self, queue_object):

        if not self.proxy_server_thread:
            self.logger.info("Proxy thread not found!")
        # Parse queue object
        address, port, payload, connection_id = queue_object
        # Check if received apptunnel data is ok
        ok = self.app_instance.check_payload(payload)

        if not ok[1]:

            self.payload_with_problem += payload
            self.logger.debug("Problem with tunnel packet end. Recovering it!")

        elif not ok[0]:

            self.payload_with_problem += payload
            payload = self.payload_with_problem
            self.logger.debug("Problem with tunnel packet head. Recovering it!")

        # If received apptunnel data is ok, process it and send it to proxy
        if ok[0] and ok[1]:

            self.payload_with_problem = ""

            # Parse data from apptunnel packets
            parsed_payloads = self.app_instance.parse_payloads(payload)

            for parsed_payload in parsed_payloads:

                self.logger.debug("Proxy connection count: {} - ConnectionID: {}".format(len(self.proxy_connections), parsed_payload.get_connection_id()))
                is_new_session = True

                # First create received apptunnel packet and get connectionid
                is_new_connection = True
                related_connection = None
                if self.proxy_server_thread:
                    self.proxy_connections = self.proxy_server_thread.get_connection_list()

                # Find related proxy connection
                if len(self.proxy_connections) > 0:

                    for connection in self.proxy_connections:

                        if parsed_payload.get_connection_id() == connection.get_connection_id():

                            is_new_connection = False
                            related_connection = connection
                            break

                # If new connection, create connection object and connect to proxy
                if is_new_connection and ((self.is_client and self.access_internal) or (not self.is_client and not self.access_internal)):

                    self.logger.info("Connecting to proxy server {}:{} for ConnectionID: {}".format(self.proxy_ip, self.proxy_port, parsed_payload.get_connection_id()))

                    # Connect to proxy
                    related_connection = self.proxy_server_thread.connect_remote(self.proxy_ip, self.proxy_port,
                                                                                 parsed_payload.get_connection_id())

                    # Get proxy connection list
                    self.proxy_connections = self.proxy_server_thread.get_connection_list()

                # If related connection available, add parsed payload to connection
                if related_connection:

                    # Check every session to find related one
                    for session in related_connection.get_proxy_session():

                        if session.get_session_id() == int(parsed_payload.get_session_id()):

                            is_new_session = False

                            # Check if last packet
                            if not parsed_payload.get_is_last_packet():

                                session.add_apptunnel_payload(parsed_payload)

                            else:

                                # Get sorted payload based on packet id
                                sorted_payload = session.get_sorted_apptunnel_payload()

                                try:
                                    self.logger.debug("Last payload length: {}".format(len(sorted_payload)))
                                    # Decode payload

                                    decoded_payload = b64decode(sorted_payload, validate=True, altchars=None) \
                                        if not use_builtin_base64 else b64decode(sorted_payload)

                                except Exception as e:

                                    self.logger.exception("Problem with base64 decoded string: {}".format(str(sorted_payload)))

                                else:

                                    # Add decoded payload to session
                                    session.add_decoded_apptunnel_payload(decoded_payload)

                                    self.logger.debug("Sending data to proxy. Connection ID: {}".format(related_connection.get_connection_id()))

                                    # Put connection and decoded payload to proxy_send_queue. Proxy send thread will send it
                                    self.proxy_send_queue.put((related_connection, related_connection,
                                                               decoded_payload))

                                    # Remove session because response is received
                                    session.set_remove_session(True)

                    # Create new session object if session doesn't exists
                    if is_new_session and not parsed_payload.get_is_last_packet():

                        # Create session object
                        new_session = Session(int(parsed_payload.get_session_id()))

                        try:

                            # Add payload to session
                            new_session.add_apptunnel_payload(parsed_payload)

                        except Exception as e:

                            self.logger.exception("Problem: {}".format(str(e)))

                        else:

                            self.logger.debug("New session found")
                            # Add session to related connection
                            related_connection.add_proxy_session(new_session)

    def set_apptunnel_connection_list(self, apptunnel_connections):

        self.apptunnel_connections = apptunnel_connections

    def set_proxy_connection_list(self, proxy_connections):

        self.proxy_connections = proxy_connections
