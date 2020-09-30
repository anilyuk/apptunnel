# Apptunnel v1.0
# Author: Anil YUKSEL
# E-mail: anil [ . ] yksel [ @ ] gmail [ . ] com
# URL: https://github.com/anilyuk/apptunnel

import logging

CONNECTION_REMOVE_TIMEOUT = 1200
CONNECTION_RECEIVE_TIMEOUT = 20
KEEP_ALIVE_TIME = 20
VERSION = "1.1"
BANNER = """
  ____  ____  ____  ______  __ __  ____   ____     ___  _     
 /    ||    \|    \|      ||  |  ||    \ |    \   /  _]| |    
|  o  ||  o  )  o  )      ||  |  ||  _  ||  _  | /  [_ | |    
|     ||   _/|   _/|_|  |_||  |  ||  |  ||  |  ||    _]| |___ 
|  _  ||  |  |  |    |  |  |  :  ||  |  ||  |  ||   [_ |     |
|  |  ||  |  |  |    |  |  |     ||  |  ||  |  ||     ||     |
|__|__||__|  |__|    |__|   \__,_||__|__||__|__||_____||_____|
                                                               v{}""".format(VERSION)

# Check user supplied arguments
def check_user_arguments(args):

    if not args.tunnelip:

        raise Exception("Apptunnel IP not specified!")

    if not args.tunnelport:

        raise Exception("Apptunnel Port not specified!")

    if not args.proxyport:

        raise Exception("Proxy Port not specified!")

    if not args.proxyip:

        raise Exception("Proxy IP not specified!")

# Check if appmodule has proper methods
def check_modules(appmodule):

    if not hasattr(appmodule, "AppProxyMain"):
        raise Exception("Application module has not \"AppProxyMain\" class!")

    if not hasattr(appmodule.AppProxyMain, "create_payloads"):
        raise Exception("Application module has not \"create_payloads\" class!")

    if not hasattr(appmodule.AppProxyMain, "parse_payloads"):
        raise Exception("Application module has not \"parse_payloads\" class!")

    if not hasattr(appmodule.AppProxyMain, "create_last_packet"):
        raise Exception("Application module has not \"create_last_packet\" class!")


def start_logger(logger_name, silent, debuglevel=False):

    # Create logger
    logger = logging.getLogger(logger_name)
    # If debug level, set level to debug and set format
    if debuglevel:

        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')

    # Set level to info and set format
    else:

        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(levelname)s - %(message)s')

    if silent:
        logger.setLevel(logging.WARN)

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def add_logger(logger_name):

    return logging.getLogger(logger_name)
