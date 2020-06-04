# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from core.objects.packet import AppProxyPacket
from core.common import add_logger
from core.servers.common import create_session_id


def get_module_name():

    return "HTTP(s) App Module"


LAST_PACKET_IDENTIFIER = "!lastpacket!lastpacket!"
KEEPALIVE_IDENTIFIER = "!keepalivepacket!keepalivepacket!"
CLOSE_CONNECTION_IDENTIFIER = "!closeconnectionpacket!closeconnectionpacket!"


class HTTPPacket:

    def __init__(self, HTTPPayload="", HTTPHeader=""):

        self.HTTPHeader = HTTPHeader
        self.HTTPPayload = HTTPPayload
        self.logger = add_logger("main.http_apps.packet")

    # Create apptunnel packet
    def to_data(self):

        payload = self.HTTPHeader + "\r\n" + self.HTTPPayload

        return payload

    # Parse content from apptunnel packet
    def from_data(self, data, line_identifier, original_payload):

        session_id = 0
        packet_id = 0
        connection_id = 0
        received_message = 0

        for line in data.split("\n"):

            # Get connection_id, session_id, packet_id from Cookie Header
            if "Cookie" in line:

                try:

                    connection_id = line.split(":")[1].split(",")[0].split("=")[1]
                    session_id = line.split(":")[1].split(",")[1].split("=")[1]
                    packet_id = line.split(":")[1].split(",")[2].split("=")[1]

                except Exception ,e:

                    self.logger.exception("Parse cookie error: {}\n Data: {}".format(str(e), data))

            # Check for line_identifier to parse payload
            elif line_identifier in line:

                try:

                    if LAST_PACKET_IDENTIFIER in line:

                        # Create new packet for last packet
                        packet_object = AppProxyPacket(received_message, int(packet_id), int(session_id), int(connection_id), True, all_payload=original_payload)

                        #self.logger.debug("Last packet received!")

                        return packet_object

                    elif KEEPALIVE_IDENTIFIER in line:

                        # Just keepalive packet, ignore it
                        self.logger.debug("Keep alive received")

                        return None

                    else:

                        # Packet with valuable payload
                        received_message = line.split(line_identifier)[1]

                        if len(str(received_message)) > 0 and int(session_id) != 0 and int(packet_id) != 0:

                            # Create packet object
                            return AppProxyPacket(received_message, int(packet_id), int(session_id), int(connection_id), False, all_payload=original_payload)

                except Exception, e:

                    self.logger.exception("Parse line identifier error: {}".format(str(e)))


class AppProxyMain:

    PACKET_LENGTH = 10000
    SERVER_BUFFER = 4520000
    HTTP_REQUEST = "GET "
    HTTP_TYPE = " HTTP/1.1\r\n"
    HTTP_CONNECTION = "Connection: keep-alive\r\n"
    HTTP_HOST = "Host: "
    HTTP_USER_AGENT = "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.87 Safari/537.36\r\n"
    HTTP_ACCEPT = "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n"
    HTTP_ACCEPT_ENCODING = "Accept-Encoding: gzip, deflate\r\n"
    HTTP_COOKIE = "Cookie: "
    HTTP_COOKIE_CONNECTIONID = "ConnectionID="
    HTTP_COOKIE_SESSIONID = "SessionID="
    HTTP_COOKIE_PACKETID = "PacketID="
    HTTP_RESPONSE = "HTTP/1.1 200 OK\r\n"
    HTTP_SERVER = "Server: "
    HTTP_CONTENT_TYPE = "Content-type: application/octet-stream\r\n"
    HTTP_CONTENT_LENGTH = "Content-Length: "
    LINE_IDENTIFIER = "<img src=\"http:\\\\www.nonexistentdomain.com\" onerror=\""
    HTTP_REFERENCE_PAYLOAD_BEGINNING = "<html>" \
                                       "<body>" \
                                       "Website Homepage" \
                                       "<p> Welcome </p>" \
                                       "<b> HomePage </b>\n"

    HTTP_REFERENCE_PAYLOAD_END = "</body>" \
                                 "</html>"

    def __init__(self, apptunnel_client, parameters = ["facebook.com", "/apptunnel/main.html"]):

        self.session_id = 0
        self.packet_id = 0
        self.apptunnel_client = apptunnel_client
        self.HTTPHostParameter = parameters[0]
        self.HTTPURLParameter = parameters[1]
        self.HTTPHeader = self.create_HTTP_header()
        self.logger = add_logger("main.http_apps")

    def reset_packet_id(self):

        # Reset packet id for session
        self.packet_id = int(10)

    def create_HTTP_header(self):

        # Create HTTP header

        if self.apptunnel_client:
            # Apptunnel client will always send HTTP request packet
            HTTPHeader = AppProxyMain.HTTP_REQUEST + self.HTTPURLParameter + AppProxyMain.HTTP_TYPE + \
                              AppProxyMain.HTTP_HOST + self.HTTPHostParameter + "\r\n" + AppProxyMain.HTTP_CONNECTION + \
                              AppProxyMain.HTTP_USER_AGENT + AppProxyMain.HTTP_ACCEPT + AppProxyMain.HTTP_ACCEPT_ENCODING

        else:

            # Apptunnel server will always send HTTP response packet
            HTTPHeader = AppProxyMain.HTTP_RESPONSE + AppProxyMain.HTTP_SERVER + self.HTTPHostParameter + "\r\n" + \
                              AppProxyMain.HTTP_CONTENT_TYPE

        return HTTPHeader

    # Parse payloads from apptunnel packet
    def parse_payloads(self, payload):

        payload_objects = []

        try:

            payload_objects = self.parse_payload(payload)

        except Exception, e:

            self.logger.exception("Parse payloads exception: {}".format(str(e)))

        if payload_objects is not None:
            return payload_objects

    def parse_payload(self, payloads):

        try:

            payloadsList = []

            # Check if packet is HTTP Request packet and use splitter while splitting packet
            splitter = AppProxyMain.HTTP_REQUEST + self.HTTPURLParameter + AppProxyMain.HTTP_TYPE + \
                              AppProxyMain.HTTP_HOST + self.HTTPHostParameter

            if splitter in payloads:
                # Split packet with splitter
                payloadsList = payloads.split(splitter)

            elif "200 OK" in payloads:
                # Split packet response header
                payloadsList = payloads.split("HTTP/1.1 200 OK")

            packet_list = []

            # original_payload is used for debug purposes.
            original_payload = payloads

            for payload in payloadsList:

                if (payload is not None) or (len(payload) > 0):

                    # Parse content from apptunnel packet
                    packet = HTTPPacket().from_data(payload, AppProxyMain.LINE_IDENTIFIER, original_payload)

                    if packet:

                        packet_list.append(packet)

            return packet_list

        except Exception, e:

            self.logger.exception("Parse payload exception: {}".format(str(e)))

    @staticmethod
    def check_payload(payload):

        if not str(payload).endswith("</html>"):

            end_ok = False

        else:

            end_ok = True

        if str(payload).startswith('HTTP/1.1'):

            start_ok = True

        elif str(payload).startswith('GET'):

            start_ok = True

        else:

            start_ok = False

        return start_ok, end_ok

    # Create appropriate payload for selected application. Returns list of packed payload
    def create_payloads(self, payload, connectionID, sessionID=0):

        if int(sessionID) == 0:

            self.session_id = create_session_id()

        else:

            self.session_id = sessionID

        self.reset_packet_id()

        # Create apptunnel packet from proxy packet
        payloads = self.create_payload_list(payload, self.PACKET_LENGTH, connectionID)

        # Create last packet identifier and add to list
        payloads.append(self.create_last_packet(connectionID, self.session_id))

        return payloads, self.session_id

    # Creates list of apptunnel packets from a proxy packet based on defined packet length
    def create_payload_list(self, seq, num, connectionID):

        packets = []

        for i in xrange(0, len(seq), num):

            chunk = seq[i:i + num]

            # Increment packet id
            self.packet_id += 1
            # Create new packet
            packet = self.create_packet(chunk, connectionID, self.session_id, self.packet_id)
            # Convert packet object to apptunnel packet
            packetData = packet.to_data()
            # Append to packets list
            packets.append(packetData)

        return packets

    def create_last_packet(self, connectionID, sessionID=0):

        packet = self.create_packet(LAST_PACKET_IDENTIFIER, connectionID, sessionID, self.packet_id)

        return packet.to_data()

    def create_keepalive_packet(self):

        packets = []

        packet = self.create_packet(KEEPALIVE_IDENTIFIER, 0, 0, 0)

        self.logger.debug("Creating Keepalive Packet")

        packets.append(packet.to_data())

        return packets

    def create_packet(self, content, connectionID, sessionID, packetID):

        # Create packet
        HTTPPayload = AppProxyMain.HTTP_REFERENCE_PAYLOAD_BEGINNING + AppProxyMain.LINE_IDENTIFIER + \
                      content + \
                      "\n\">" + AppProxyMain.HTTP_REFERENCE_PAYLOAD_END

        # Calculate content length
        content_length = len(HTTPPayload)

        # Create HTTP Header
        HTTPHeader = self.HTTPHeader + AppProxyMain.HTTP_COOKIE + AppProxyMain.HTTP_COOKIE_CONNECTIONID + str(connectionID) + \
                     ", " + AppProxyMain.HTTP_COOKIE_SESSIONID + str(sessionID) + \
                     ", " + AppProxyMain.HTTP_COOKIE_PACKETID + str(packetID) + "\r\n" + \
                     AppProxyMain.HTTP_CONTENT_LENGTH + str(content_length) + "\r\n"

        # Create new HTTP Packet
        packet = HTTPPacket(HTTPHeader=HTTPHeader, HTTPPayload=HTTPPayload)

        return packet
