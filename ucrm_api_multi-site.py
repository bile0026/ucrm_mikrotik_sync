import json
import requests
from requests.api import head, request
from customer import Customer
from configparser import ConfigParser
import routeros_api


# import config from .ini
config = ConfigParser()
config.read("ucrm_api.ini")
uisp_config = config['UISP']
mikrotik_config = config['MIKROTIK']

# build variables

base_url = 'https://' + uisp_config['server_fqdn']

# urls to retrieve ucrm client information
clients_url = base_url + '/crm/api/' + \
    uisp_config['ucrm_api_version'] + '/clients'
services_url = base_url + '/crm/api/' + \
    uisp_config['ucrm_api_version'] + '/service-plans'
client_services_url = base_url + '/crm/api/' + \
    uisp_config['ucrm_api_version'] + '/clients/services/'

# urls to retrieve unms device/client information
devices_url = base_url + '/nms/api/' + \
    uisp_config['unms_api_version'] + '/devices'
sites_url = base_url + '/nms/api/' + \
    uisp_config['unms_api_version'] + '/sites'

ucrm_headers = {
    'X-Auth-App-Key': uisp_config["key"], 'Content-Type': 'application/json'}
unms_headers = {
    'X-Auth-Token': uisp_config["key"], 'Content-Type': 'application/json'}

customer_list = []
tower_site_ids = []
customer_site_ids = []
router_dict = {}

# methods for interacting with customers


def getClientServicePlan(customerId):
    clientService = requests.get(clients_url + '/services/?clientId=' +
                                 str(customerId), headers=ucrm_headers)
    if clientService.status_code == 200:
        return clientService.json()[0]
    else:
        return "No Service Plan Found" + clientService.status_code


def getSite(siteId):
    site = requests.get(sites_url + '/' + siteId +
                        '?ucrmDetails=true', headers=unms_headers)
    if site.status_code == 200:
        return site.json()
    else:
        return "No site GUID Found" + site.status_code


def getClientDevice(siteId):
    device = requests.get(devices_url + '?siteId=' +
                          siteId, headers=unms_headers)
    if device.status_code == 200 and len(device.json()[0]) > 0:
        return device.json()[0]
    else:
        return "No client device found" + device.status_code


def getAllClients():
    clients = requests.get(clients_url, headers=ucrm_headers)
    if clients.status_code == 200:
        return clients.json()
    else:
        return "No clients found" + clients.status_code

# custom customer class to store customer information


class Customer():

    def __init__(self, customer):
        self.customerFirstName = customer.get('firstName')
        self.customerLastName = customer.get('lastName')
        self.customerId = customer.get('id')
        self.serviceStatus = getClientServicePlan(
            customer.get('id')).get('status')
        self.serviceId = int(getClientServicePlan(
            customer.get('id')).get('id'))
        self.customerSiteId = getClientServicePlan(
            customer.get('id')).get('unmsClientSiteId')
        if self.serviceStatus == 1 or self.serviceStatus == 3:
            self.maxLimitUpload = str(getSite(
                self.customerSiteId)['qos']['uploadSpeed'])
            self.maxLimitDownload = str(getSite(
                self.customerSiteId)['qos']['downloadSpeed'])
            self.burstLimitUpload = str(
                int(self.maxLimitUpload) * (1 + float(mikrotik_config['burstLimitUpload'])))
            self.burstLimitDownload = str(
                int(self.maxLimitDownload) * (1 + float(mikrotik_config['burstLimitDownload'])))
            self.burstThresholdUpload = str(
                int(self.maxLimitUpload) * (float(mikrotik_config['burstThresholdUpload'])))
            self.burstThresholdDownload = str(
                int(self.maxLimitDownload) * (float(mikrotik_config['burstThresholdDownload'])))
            self.queueName = ((self.customerFirstName) + " " +
                              (self.customerLastName) + " - " + "Service Id: " + str(self.serviceId))
            self.customerDeviceIp = getClientDevice(self.customerSiteId)[
                'ipAddress'].split('/', 1)[0]
            if getSite(self.customerSiteId)['identification']['parent']:
                self.gatewaySiteId = getSite(self.customerSiteId)[
                    'identification']['parent']['id']
                self.gatewayRouterIp = getSite(self.gatewaySiteId)[
                    'description']['ipAddresses'][0].split('/', 1)[0]
                self.siteType = 'Child'
            else:
                self.gatewaySiteId = None
                self.gatewayRouterIP = None
                self.siteType = 'Parent'
        else:
            self.maxLimitUpload = 0
            self.maxLimitDownload = 0
            self.burstLimitUpload = 0
            self.burstLimitDownload = 0
            self.burstThresholdUpload = 0
            self.burstThresholdDownload = 0
            self.queueName = ((self.customerFirstName) + " " +
                              (self.customerLastName) + " - " + "Service Id: " + str(self.serviceId))
            self.customerDeviceIp = getClientDevice(self.customerSiteId)[
                'ipAddress'].split('/', 1)[0]
            if getSite(self.customerSiteId)['identification']['parent']:
                self.gatewaySiteId = getSite(self.customerSiteId)[
                    'identification']['parent']['id']
                self.gatewayRouterIp = getSite(self.gatewaySiteId)[
                    'description']['ipAddresses'][0].split('/', 1)[0]
                self.siteType = 'Child'


customers = getAllClients()
# build list of customers with custom customer class
for customer in customers:
    customer_list.append(Customer(customer))

# print(customer_list)


# builds list of tower/site routers and which customer routers are uplinked.


def buildRouterDict(site_dict):
    for site in site_dict:
        if site['identification']['type'] == 'site':
            for endpoint in site['description']['endpoints']:
                if endpoint['type'] == 'endpoint':
                    if site['identification']['id'] in router_dict:
                        if not isinstance(router_dict[site['identification']['id']], list):
                            router_dict[site['identification']['id']] = [
                                router_dict[site['identification']['id']]]
                        router_dict[site['identification']
                                    ['id']].append(endpoint['id'])
                    else:
                        router_dict[site['identification']['id']
                                    ] = endpoint['id']
    return router_dict

# returns a router's ip address based on the site ID


def getRouterIP(device_dict, site_id):
    for device in device_dict:
        if device['identification']['site']['id'] == site_id:
            return device['ipAddress']

# returns the customer's name based on the customer id


def getCustomerNameFromID(customer_dict, customer_id):
    for customer in customer_dict:
        if customer['id'] == customer_id:
            return customer['firstName'] + " " + customer['lastName']

# returns customer name based on the site id


def getCustomerNameFromSite(customer_dict, client_services_dict, site_id):
    for service in client_services_dict:
        if service['unmsClientSiteId'] == site_id:
            return getCustomerNameFromID(customer_dict, service['clientId'])


# methods for interacting with MikroTik Queues

# returns yes or no whether queue is disabled
def getQueueDisabledStatus(customer):
    if customer.serviceStatus == 1:
        return "no"
    else:
        return "yes"

# disables a given queue on a router


def disableQueue(queues, name):
    print("Disabling queue", name)
    queues.set(id=getQueueID(queues, name), disabled="true")

# enables a given queue on router


def enableQueue(queues, name):
    print("Enabling queue", name)
    queues.set(id=getQueueID(queues, name), disabled="false")

# returns a queue object


def getQueue(queues, name):
    found_queue = {}
    all_queues = queues.get()
    for item in all_queues:
        if name in item['name']:
            found_queue = item
        else:
            continue
    if found_queue:
        return found_queue
    else:
        return None

# returns the id of the mikrotik queue


def getQueueID(queues, name):
    found_queue_id = ""
    all_queues = queues.get()
    for item in all_queues:
        if name in item['name']:
            found_queue_id = item['id']
        else:
            continue
    if found_queue_id != "":
        return found_queue_id
    else:
        return None

# build a new queue on the router


def addQueue(queues, customer):
    queues.add(
        name=customer.queueName, disabled=getQueueDisabledStatus(customer), target=customer.customerDeviceIp, max_limit=customer.maxLimitUpload +
        "/"+customer.maxLimitDownload, burst_limit=customer.burstLimitUpload+"/"+customer.burstLimitDownload,
        burst_threshold=customer.burstThresholdUpload +
        "/"+customer.burstLimitDownload,
        burst_time=mikrotik_config['burstTimeUp']+"s/"+mikrotik_config['burstTimeDown']+"s", place_before=mikrotik_config['catch_all_queue']
    )
    print("Add new queue for", customer.queueName)

# set all configuration for a given queue


def setQueue(queues, customer):
    # queues = queues.get()
    set_queue = getQueue(queues, customer.queueName)
    queues.set(
        id=set_queue['id'], disabled=getQueueDisabledStatus(customer), name=customer.queueName, target=customer.customerDeviceIp, max_limit=customer.maxLimitUpload +
        "/"+customer.maxLimitDownload, burst_limit=customer.burstLimitUpload+"/"+customer.burstLimitDownload,
        burst_threshold=customer.burstThresholdUpload +
        "/"+customer.burstLimitDownload,
        burst_time=mikrotik_config['burstTimeUp'] +
        "s/"+mikrotik_config['burstTimeDown']+"s"
    )
    print("Set queue for", customer.queueName,
          " Disabled? -", getQueueDisabledStatus(customer))

# remove a queue from the router based on the queuename


def removeQueue(queues, queue_id):
    #remove_queue = getQueue(queues, queue_name)
    if queue_id:
        print("Removing ", queue_id)
        queues.remove(id=queue_id)
    else:
        print("Can't remove none queue")

# checks for queues that no longer have services and removes the queues


def cleanupQueues(queues, customer_list):
    service_names = list(str())
    all_queues = queues.get()
    queue_names = list(dict([(d['id'], d['name'])
                             for d in all_queues]).values())
    queue_ids = list(dict([(d['id'], d['name'])
                           for d in all_queues]).keys())

    # build list of service_names
    for customer in customer_list:
        service_names.append(customer.queueName)

    for queue in queue_names:
        if queue in service_names:
            print("Service exists, continuing...", queue)
            continue
        elif queue == mikrotik_config['catch_all_queue']:
            print("Catch all queue, continuing...", queue)
            continue
        elif queue not in service_names:
            print("Service does not exist, remove Queue", queue)
            removeQueue(queues, getQueueID(queues, queue))
        else:
            print("Can't find service, remove Queue", queue)
            removeQueue(queues, queue)


for customer in customer_list:
    if customer.customerDeviceIp:
        # apply queues for each customer to the proper router based on parent/child

        # FIXME #1 - Get SSL Working
        # router_connection = routeros_api.RouterOsApiPool(
        #     str(mikrotik_config['router']),
        #     username=str(mikrotik_config['username']),
        #     password=str(mikrotik_config['password']),
        #     port=int(mikrotik_config['port']),
        #     use_ssl=str(mikrotik_config['use_ssl']),
        #     ssl_verify=str(mikrotik_config['ssl_verify']),
        #     ssl_verify_hostname=str(mikrotik_config['ssl_verify_hostname']),
        #     plaintext_login=str(mikrotik_config['plaintext_login'])
        # )

        router_connection = routeros_api.RouterOsApiPool(
            customer.gatewayRouterIp,
            username=mikrotik_config['username'],
            password=mikrotik_config['password'],
            port=int(mikrotik_config['port']),
            plaintext_login=mikrotik_config['plaintext_login']
        )

        # connect to the router and attempt to create the queues
        try:
            api = router_connection.get_api()
            try:
                # if customer service is ended, remove queue
                if customer.serviceStatus == 2:

                    list_queues = api.get_resource('/queue/simple')

                    if getQueue(list_queues, customer.queueName):
                        removeQueue(list_queues, getQueueID(
                            list_queues, customer.queueName))
                    else:
                        print("Queue for", customer.queueName,
                              "not found, can't delete...")
                # if customer service is any other status, activate or suspend as set in UCRM
                else:
                    list_queues = api.get_resource('/queue/simple')
                    # all_queues = list_queues.get()
                    if getQueue(list_queues, customer.queueName):
                        setQueue(list_queues, customer)
                    else:
                        addQueue(list_queues, customer)

                # cleanup queues and remove queues that no longer have a service attached
                # FIXME #2 - Move cleanup outside customer queue process so it's only done once
                cleanupQueues(list_queues, customer_list)
            except routeros_api.exceptions.RouterOsApiCommunicationError:
                print(mikrotik_config['router'] + '  comms error')

            router_connection.disconnect()

        except routeros_api.exceptions.RouterOsApiConnectionError:
            print(mikrotik_config['router'] + '  NOT done')
    else:
        print("Customer does not yet have a device with an IP address")
