# APPTUNNEL

***AppTunnel*** is a powerful tool for creating application-level tunnels that conceal network traffic by mimicking legitimate ***HTTP and HTTPS applications***. To function, AppTunnel requires two components: a ***server*** placed outside the network and a ***client*** located within the network. This setup allows ***AppTunnel*** to hide traffic behind common, trusted applications, effectively bypassing many network security mechanisms.

When using HTTPS mode, ***AppTunnel*** is able to bypass ***SSL inspection*** by disguising traffic as encrypted HTTPS connections. However, for HTTPS tunneling to be successful, the firewall must be configured to allow ***self-signed certificates***. If the firewall blocks self-signed certificates, HTTPS traffic will not be able to pass through the tunnel.

To access the internet through AppTunnel, users must first start a proxy server (Dante, Burp Suite, ZAP etc) at the AppTunnel server location. Then, the AppTunnel server must be configured to connect to the proxy server. Once this is set up, users can route their internet traffic through AppTunnel by configuring their web browser to use the AppTunnel server as a proxy. This approach allows internet traffic to flow through the tunnel, making it appear as if it originates from trusted applications and bypassing restrictive network policies.

Change Log:
- v1.1: Apptunnel now supports both directions, internal to internet and internet to internal
- v1.0: Apptunnel is currently allow you to access internet from internal network.

Access modes; 

    - Access internal: Access internal network from internet.
    - Access internet: Access internet from internal network

Server; listens for apptunnel connections.

    - tunnelip and tunnelport parameters are IP address and port to listen as apptunnel server.
    - proxyip and proxyport parameters are IP address and port to listen or connect.

Client; connects to both apptunnel server and target server.

    - tunnelip and tunnelport parameters are IP address and port of apptunnel server instance.
    - proxyip and proxyport parameters are IP address and port to listen or connect.
    

Flow of accessing internet from internal network;
![Access internal targer server](logic_flow.jpg)


#### Usage: ####

    -h, --help              Show this help message and exit
    -c, --client            Run as client
    -ai, --access_internal  Access internal network from internet.
                            Default: Access to internet from internal network.
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


#### Sample applications ####
Some sample application can be found at [sample_module_options.json](sample_module_options.json).



