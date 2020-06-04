# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

from argparse import ArgumentParser, RawTextHelpFormatter
from sys import exit
from socket import error
from imp import load_source
from Queue import Queue
from time import sleep
from core.common import check_user_arguments, check_modules, start_logger, BANNER
from core.servers.servers import SendData
from core.workers import Workers
from core.servers.common import create_proxy_thread, create_apptunnel_thread, connect_to_apptunnel, create_certificate

def arg_parser():
    description = """
Apptunnel tool can create application level tunnels to hide traffic. Apptunnel can mimic every HTTP and HTTPS application.
HTTPS mode can bypass default settings of SSL Inspection for several applications. 

Server mode; listens and accepts apptunnel connections.
    - tunnelip and tunnelport parameter is IP address and port to listen.
    - proxyip and proxyport parameter is IP address and port to listen.
    
Client mode; connects to both apptunnel server and target server.
    - tunnelip and tunnelport parameter is IP address and port of apptunnel server instance.
    - proxyip and proxyport parameter is IP address and port of target server and service.
    """
    parser = ArgumentParser(formatter_class=RawTextHelpFormatter, description=description)

    parser.add_argument("-c", "--client", action="store_true", default=False,
                        help="Run as client")

    parser.add_argument("-tip","--tunnelip",
                        help="AppTunnel ip address")

    parser.add_argument("-tp", "--tunnelport", default=80, type=int,
                        help="""AppTunnel port.(default: 80)""")

    parser.add_argument("-pip", "--proxyip",
                        help="Server: IP address to listen as proxy\nClient: IP address of target system")

    parser.add_argument("-pp", "--proxyport", default=80, type=int,
                        help="""Server: Port to listen as proxy\nClient: Port of target system.""")

    parser.add_argument("-hp", "--host_parameter", default="facebook.com", help="Host parameter Eg: \"facebook.com\", ...")

    parser.add_argument("--ssl", action="store_true", default=False,
                        help="Enable ssl mode")

    parser.add_argument("--ssl_cn", default="facebook.com", help="SSL Certificate Canonical Name (CN) Eg: \"*.skype.com\", ...")

    parser.add_argument("-d", "--debug", action="store_true", default=False, help="Enable debug logging")

    parser.add_argument("-s", "--silent", action="store_true", default=False, help="Silent mode")

    args = parser.parse_args()

    try:

        #Check user arguments
        check_user_arguments(args)

    except Exception, e:

        parser.print_help()
        print("\n\n{}\n".format(e))
        exit()

    return args

def main(args):

    try:

        # Print banner
        if not args.silent:
            print "{}\n".format(BANNER)

        # Start logger
        logger = start_logger("main", args.silent, debuglevel=args.debug)

        # Load selected module
        try:

            # Load module from apps folder.
            appmodule = load_source('http_apps', 'apps/http_apps.py')

            # Check if module has proper methods
            check_modules(appmodule)

        except IOError:

            logger.exception("Module not found!")
            exit()
            return

        except Exception, e:

            logger.exception("Module error {}".format(str(e)))
            exit()
            return

        # Create application module
        appmodule_main = appmodule.AppProxyMain(args.client, [args.host_parameter, "/apptunnel/main.html"])

        # Queues used to communicate between threads
        proxy_queue = Queue()
        proxy_send_queue = Queue()
        apptunnel_queue = Queue()
        apptunnel_send_queue = Queue()
        proxy_connection_list = []
        apptunnel_connection_list = []

        # Threads list used by main thread
        threads = []

        if args.client:

            # Running as client. The client will connect to apptunnel server and then connect to target server (proxy server)

            # Create Apptunnel thread as client
            apptunnel_server = create_apptunnel_thread(ip="0.0.0.0", port=0, is_client=args.client, apptunnel_queue=apptunnel_queue,
                                                       apptunnel_send_queue=apptunnel_send_queue,
                                                       name="ApptunnelClient",is_ssl=args.ssl)

            # Try to connect to apptunnel server and if there is a problem, try every N seconds.
            connect_to_apptunnel(logger, apptunnel_server, args)

            # If apptunnel server connection is established, start thread to wait/parse packets from apptunnel
            apptunnel_server.start()
            logger.info("App Tunnel server started!")
            threads.append(apptunnel_server)

            # Create proxy server thread
            # This thread will accept connections and receive packets.
            proxy_server = create_proxy_thread(ip="0.0.0.0", port=0, is_client=args.client, proxy_queue=proxy_queue,
                                               proxy_send_queue=proxy_send_queue, name="ProxyThreadClient")

            logger.info("Proxy server started!")
            logger.info("Connect to {}:{} after a packet received from apptunnel".format(args.proxyip, args.proxyport))
            # Start proxy server thread


            threads.append(proxy_server)

            # Get proxy and apptunnel initial connections
            proxy_connection_list = proxy_server.get_connection_list()
            apptunnel_connection_list = apptunnel_server.get_connection_list()

            # Create worker thread
            # This thread will accept and process packets and send it to apptunnel or proxy threads via send queues
            worker_thread = Workers(proxy_connection_list, apptunnel_connection_list, apptunnel_queue, proxy_queue,
                                    apptunnel_send_queue, proxy_send_queue, appmodule_main, proxy_server,
                                    args.client, args.proxyip, args.proxyport)

            worker_thread.daemon = True
            worker_thread.start()

            threads.append(worker_thread)

        else:

            # Running as server. The server will accept connection from apptunnel server and listen specific port as proxy server.
            # The connection from proxy server will be forwarded through apptunnel connection

            # Create proxy server thread
            proxy_server = create_proxy_thread(ip="127.0.0.1", port=int(args.proxyport), is_client=args.client, proxy_queue=proxy_queue,
                                               proxy_send_queue=proxy_send_queue,
                                               name="ProxyThread")

            logger.info("Proxy server started!")
            logger.info("Waiting proxy connection from TCP/{}".format(args.proxyport))
            proxy_server.start()
            threads.append(proxy_server)

            key_file = ""
            certificate_file = ""

            # Create self-signed certificates for specified application
            if args.ssl:

                logger.info("Creating self-signed certificate for {}".format(args.ssl_cn))

                certificate_file, key_file = create_certificate(args.ssl_cn)

            # Create Apptunnel thread as server
            apptunnel_server = create_apptunnel_thread(ip="0.0.0.0", port=int(args.tunnelport), is_client=args.client,
                                                       apptunnel_queue=apptunnel_queue,
                                                       apptunnel_send_queue=apptunnel_send_queue,
                                                       name="ApptunnelServer", is_ssl=args.ssl, certificate_file=certificate_file, key_file=key_file)

            logger.info("App tunnel server started!")
            logger.info("Waiting app tunnel connection from TCP/{}".format(args.tunnelport))
            apptunnel_server.start()

            threads.append(apptunnel_server)

            # Get proxy and apptunnel initial connections
            proxy_connection_list = proxy_server.get_connection_list()
            apptunnel_connection_list = apptunnel_server.get_connection_list()

            # Create worker thread
            # This thread will accept packets and send it via apptunnel or proxy threads
            worker_thread = Workers(proxy_connection_list, apptunnel_connection_list, apptunnel_queue, proxy_queue,
                                    apptunnel_send_queue, proxy_send_queue, appmodule_main, proxy_server, is_client=args.client)

            worker_thread.daemon = True
            worker_thread.start()

            threads.append(worker_thread)

        send_tunnel_thread = None
        send_proxy_thread = None

        # Main thread loop
        while True:

            sleep(0.01)

            # Update proxy connectionlist to update list at worker thread
            proxy_connection_list = proxy_server.get_connection_list()
            # Update proxy connection list for worker thread
            worker_thread.set_proxy_connection_list(proxy_connection_list)
            # Update apptunnel connectionlist
            apptunnel_connection_list = apptunnel_server.get_connection_list()

            # If there is a apptunnel connection and send threads aren't started, create send data threads
            if len(apptunnel_connection_list) == 1 and not send_tunnel_thread:
                # Thread for sending data through apptunnel
                send_tunnel_thread = SendData(apptunnel_send_queue, apptunnel_connection_list, appmodule_main,
                                              is_tunnel_sender=True, is_client=args.client)

                send_tunnel_thread.daemon = True
                send_tunnel_thread.setName("SendDataTunnel")
                logger.debug("Starting apptunnel sender thread.")
                send_tunnel_thread.start()

            if len(proxy_connection_list) > 0 and not send_proxy_thread:

                # Thread for sending data through proxy
                send_proxy_thread = SendData(proxy_send_queue, proxy_connection_list, appmodule_main,
                                             is_tunnel_sender=False, is_client=args.client)

                send_proxy_thread.daemon = True
                send_proxy_thread.setName("SendDataTunnel")
                logger.debug("Starting proxy sender thread.")
                send_proxy_thread.start()

                if args.client:
                    proxy_server.start()

            elif len(apptunnel_connection_list) == 0 and args.client:

                # Try to connect to apptunnel server and if there is a problem, try every N seconds.

                connect_to_apptunnel(logger, apptunnel_server, args)
                worker_thread.set_apptunnel_connection_list(apptunnel_server.get_connection_list())
                apptunnel_connection_list = apptunnel_server.get_connection_list()
                logger.info("Apptunnel connection count {}".format(len(apptunnel_connection_list)))

    except (KeyboardInterrupt, SystemExit):

        logger.debug("All threads closed")

        exit()

    except error as err:

        logger.exception("Socket error:\n{}".format(err))

    except Exception, e:

        logger.exception("Unknown error:\n{}".format(str(e)))

try:
    if __name__ == '__main__':

        main(arg_parser())

except KeyboardInterrupt:

    exit()