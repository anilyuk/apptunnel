# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from core.servers.common import sort_tunnel_payload
from core.common import CONNECTION_RECEIVE_TIMEOUT


class Session:

    def __init__(self, session_id):

        self.session_ID = session_id
        self.payload = ""
        self.apptunnel_payload = []
        self.send_again = False
        self.decoded_apptunnel_payload = ""

        self.receive_completed = False
        self.sending_to_apptunnel = False
        self.remove_session = False

        self.receive_timeout = CONNECTION_RECEIVE_TIMEOUT

    def set_payload(self, payload):
        self.payload = payload

    def get_payload(self):
        return self.payload

    def set_apptunnel_payload(self, payload):
        self.apptunnel_payload = payload

    def get_apptunnel_payload(self):
        return self.apptunnel_payload

    def add_apptunnel_payload(self, payload):
        self.apptunnel_payload.append(payload)

    def get_sorted_apptunnel_payload(self):
        return sort_tunnel_payload(self.apptunnel_payload)

    def get_session_id(self):
        return self.session_ID

    def set_send_again(self, send_again):
        self.send_again = send_again

    def get_send_again(self):
        return self.send_again

    def add_decoded_apptunnel_payload(self, apptunnel_payload):
        self.decoded_apptunnel_payload += apptunnel_payload

    def get_decoded_apptunnel_payload(self):
        return self.decoded_apptunnel_payload

    def get_receive_completed(self):
        return self.receive_completed

    def set_receive_completed(self, receive_completed):
        self.receive_completed = receive_completed

    def get_sending_to_apptunnel(self):
        return self.sending_to_apptunnel

    def set_sending_to_apptunnel(self, sending_to_apptunnel):
        self.sending_to_apptunnel = sending_to_apptunnel

    def set_remove_session(self, remove_session):
        self.remove_session = remove_session

    def get_remove_session(self):
        return self.remove_session

    def get_receive_timeout(self):
        return self.receive_timeout

    def set_receive_timeout(self, receive_timeout):
        self.receive_timeout = receive_timeout
