# APPTUNNEL

Apptunnel tool can create application level tunnels to hide traffic and needs a ***server***, which is outside the network, and a ***client***.
Apptunnel can mimic every ***HTTP and HTTPS application***.
HTTPS mode can bypass default settings of ***SSL Inspection*** for several applications.

v1.0 currently allows you to access internal target from internet. 
Internet access from the internal target mode will be added soon.

Server; listens for apptunnel connections.

    - tunnelip and tunnelport parameter is IP address and port to listen.
    - proxyip and proxyport parameter is IP address and port to listen.

Client; connects to both apptunnel server and target server.

    - tunnelip and tunnelport parameter is IP address and port of apptunnel server instance.
    - proxyip and proxyport parameter is IP address and port of target server and service.


#### Usage: ####

    -h, --help            show this help message and exit
    -c, --client          Run as client
    -tip TUNNELIP, --tunnelip TUNNELIP
                        AppTunnel ip address
    -tp TUNNELPORT, --tunnelport TUNNELPORT
                        AppTunnel port.(default: 80)
    -pip PROXYIP, --proxyip PROXYIP
                        Server: IP address to listen as proxy
                        Client: IP address of target system
    -pp PROXYPORT, --proxyport PROXYPORT
                        Server: Port to listen as proxy
                        Client: Port of target system.
    -hp HOST_PARAMETER, --host_parameter HOST_PARAMETER
                        Host parameter Eg: "facebook.com", ...
    --ssl                 Enable ssl mode
    --ssl_cn SSL_CN       SSL Certificate Canonical Name (CN) Eg: "*.skype.com", ...
    -d, --debug           Enable debug logging
    -s, --silent          Silent mode, logging completely disabled

#### Supported applications/protocols for tunnel traffic ####
Some sample application configuration can be found at "sample_module_options.json".


