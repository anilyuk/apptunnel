# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from core.servers.servers import TcpServer
from time import sleep
from OpenSSL import crypto
from os.path import join
from random import uniform

TUNNEL_CONNECTION_RETRY = 5


# Create proxy thread
def create_proxy_thread(ip, port, is_client, proxy_queue, proxy_send_queue, name):

    proxy_server = TcpServer(ip, port, is_client, False, proxy_queue,
                             proxy_send_queue, name)

    proxy_server.daemon = True
    # Create socket
    proxy_server.create_socket()
    # Bind socket
    proxy_server.bind_server()

    if not is_client:

        proxy_server.start_listening()

    return proxy_server


# Create apptunnel thread
def create_apptunnel_thread(ip, port, is_client, apptunnel_queue, apptunnel_send_queue, name, is_ssl,
                            certificate_file="", key_file=""):

    apptunnel_server = TcpServer(ip, port, is_client, True, apptunnel_queue,
                                 apptunnel_send_queue, name,
                                 use_ssl=is_ssl, certificate_file=certificate_file, key_file=key_file)

    apptunnel_server.daemon = True
    # Create socket
    apptunnel_server.create_socket()
    # Bind socket
    apptunnel_server.bind_server()

    if not is_client:

        apptunnel_server.start_listening()

    return apptunnel_server


# Connect to apptunnel server
def connect_to_apptunnel(logger, apptunnel_server, args):

    connection_established = False

    # Try to connect apptunnel server
    while not connection_established:
        try:

            logger.info("Connecting to app tunnel {}:{}".format(args.tunnelip, args.tunnelport))
            apptunnel_server.connect_remote(args.tunnelip, args.tunnelport)
            connection_established = True

        except Exception, e:

            connection_established = False
            logger.debug("{}".format(e))
            logger.debug("Problem connecting to server. Waiting {} seconds.".format(TUNNEL_CONNECTION_RETRY))
            sleep(TUNNEL_CONNECTION_RETRY)


CERT_FILE = "server.crt"
KEY_FILE = "server.key"


# Create self signed certificate for ssl mode
def create_certificate(cn):

    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)
    cert_dir = "certs"

    cert = crypto.X509()
    cert.get_subject().C = "US"
    cert.get_subject().ST = "Minnesota"
    cert.get_subject().L = "Minnetonka"
    cert.get_subject().O = "GitHub, Inc."
    cert.get_subject().OU = "GitHub, Inc."
    cert.get_subject().CN = cn
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha1')
    open(join(cert_dir, CERT_FILE), "w").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    open(join(cert_dir, KEY_FILE), "w").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, k))
    return join(cert_dir, CERT_FILE), join(cert_dir, KEY_FILE)


def sort_tunnel_payload(payloads):

    # Get sorted payload object list
    sorted_payloads = sorted(payloads, key=get_key)

    # Get payload data of payload objects
    all_payload = [i.get_payload() for i in sorted_payloads]

    # Join payload data
    total_payload = ''.join(all_payload)

    return total_payload


def get_key(item):

    return int(item.get_packet_id())


def create_session_id():

    return int(uniform(10000000, 99999999))