# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

class AppProxyPacket:

    def __init__(self, payload, packet_id, session_id, connection_id, is_lastpacket=False, all_payload=""):

        self.payload = payload
        self.packet_id = packet_id
        self.session_id = session_id
        self.connection_id = connection_id
        self.is_last_packet = is_lastpacket
        self.all_payload = all_payload

    def get_packet_id(self):

        return self.packet_id

    def get_session_id(self):

        return self.session_id

    def get_connection_id(self):

        return self.connection_id

    def get_payload(self):

        return self.payload

    def get_is_last_packet(self):

        return self.is_last_packet

    def get_all_payload(self):

        return self.all_payload
