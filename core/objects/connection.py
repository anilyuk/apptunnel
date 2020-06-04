# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from core.common import KEEP_ALIVE_TIME


class Connection:

    def __init__(self, received_address, received_port, socket, connection_id=0):

        self.received_address = received_address
        self.received_port = received_port
        self.socket = socket
        self.proxy_session = []
        self.apptunnel_address = ""
        self.apptunnel_port = 0
        self.keepalive_timer = KEEP_ALIVE_TIME
        self.remove_connection = False
        self.connection_id = connection_id
        self.error_count = 0

    def get_received_address(self):
        return self.received_address

    def get_received_port(self):
        return self.received_port

    def get_socket(self):
        return self.socket

    def get_connection_id(self):
        return self.connection_id

    def get_apptunnel_address(self):
        return self.apptunnel_address

    def set_apptunnel_address(self, apptunnel_address):
        self.apptunnel_address = apptunnel_address

    def get_apptunnel_port(self):
        return self.apptunnel_port

    def set_apptunnel_port(self, apptunnel_port):
        self.apptunnel_port = apptunnel_port

    def get_proxy_session(self):
        return self.proxy_session

    def add_proxy_session(self, proxy_session):
        self.proxy_session.append(proxy_session)

    def remove_proxy_session(self, proxy_session):
        self.proxy_session.remove(proxy_session)

    def set_remove_connection(self, remove_connection):
        self.remove_connection = remove_connection

    def get_remove_connection(self):
        return self.remove_connection

    def set_keepalive_timer(self, keepalive_timer):
        self.keepalive_timer = keepalive_timer

    def get_keepalive_timer(self):
        return self.keepalive_timer

    def increment_error_count(self):
        self.error_count = self.error_count + 1

    def get_error_count(self):
        return self.error_count

    def reset_error_count(self):
        self.error_count = 0