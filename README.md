# ucrm_mikrotik_sync
Sync services and clients to MikroTik simple queues

Create Simple Queues on a MikroTik Router from UNMS/UCRM information.

# Current Issues:
1. SSL not yet working. Testing on 6.47.9. Haven't found a working combo of SSL options yet.

# If things aren't working
1. Check to make sure api is enabled in `/ip/services`
2. Make sure you allow connections in your firewall from the IP your using to run the sync job (keep in mind this might be a public IP if you are running this remotely).
3. Double check your api keys and FQDNs to make sure they are correct. Don't add things like `http://` 

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
router = <router_ip_or_fqdn>
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
