# ucrm_mikrotik_sync
Sync services and clients to MikroTik simple queues

Create Simple Queues on a MikroTik Router from UNMS/UCRM information.

If you have a simple network, you can use `ucrm_api.py` to create single queues on a single gateway router. If you have a more complex network, `ucrm_api_multi-site.py` builds out a list of parent/child sites and places queues on the respective gateway routers. In order for multi-site to work you have to build the data links in UCRM between client sites and "tower" sites, and setup your routers as "tower" sites with IP addresses. Also requires a shared API credential on all "tower" routers for the API to make the updates.

# Current Issues:
1. SSL not yet working. Testing on 6.47.9 and 6.48.3. Haven't found a working combo of SSL options yet.

# If things aren't working
1. Check to make sure api is enabled on the router in `/ip/services`
2. Make sure you allow connections in your firewall from the IP your using to run the sync job (keep in mind this might be a public IP if you are running this remotely).
3. Double check your api keys and FQDNs to make sure they are correct. Don't add things like `http://`

# Notes on Setup
  1. Make sure to assign gateway router to a site
  2. Set the router's IP address (reachable by UISP/this script). Script will use the first/primary IP to try and connect to the router.
  3. Set the routers role to "router" in UISP
  4. Assign client sites to site properly. (data links). If data links aren't created, queues won't be able to be created since there's no way to tell which parent (gateway) site a device belongs to.

# HOW-TO
1. Install requirements.txt `pip3 install -r requirements.txt`
2. Create an .ini file in the same directory as the `ucrm_api.py` script with this format and name it `ucrm_api.ini`.
```
[UISP]
server_fqdn = <your_ucrm_server_fqdn>
key = <your_ucrm_api_key>
ucrm_api_version = v1.0
unms_api_version = v2.1

[MIKROTIK]
port = 8728
use_ssl = False
ssl_verify = False
ssl_verify_hostname = False
plaintext_login = True

# queue that all new queues will be placed before (must be pre-created on the Mikrotik router)
catch_all_queue = CATCH_ALL_QUEUE

username = api
password = api

# burst max in decimal format
burstLimitUpload = 0.05

# burst max in decimal format
burstLimitDownload = 0.05

# burst time in seconds
burstTimeUp = 10

# bust time in seconds
burstTimeDown = 10

# alow burst at percentage in decimal
burstThresholdUpload = 0.95

# alow burst at percentage in decimal
burstThresholdDownload = 0.95
```
3. Setup a cron job or however you'd like to run this.


* Note: Please do your own testing and validation of this script. There is no guarantee that this script won't break your setup. Please open issues or PR's if you have issues or fixes.
