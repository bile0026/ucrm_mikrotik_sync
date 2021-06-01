import json
import requests
from configparser import ConfigParser
from requests.api import head, request

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
    if device.status_code == 200:
        return device.json()[0]
    else:
        return "No client device found" + device.status_code


def getAllClients():
    clients = requests.get(clients_url, headers=unms_headers)
    if clients.status_code == 200:
        return clients.json()
    else:
        return "No clients found" + clients.status_code

# custom customer class to store custome information


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
        self.customerDeviceIP = getClientDevice(self.customerSiteId)[
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


# print a bunch of stuff for testing
router_dict = buildRouterDict(json.loads(sites))

router_ip = getRouterIP(json.loads(
    devices), "17ae69fd-63e2-4ad3-8882-7498bbb015f3")

customer_name = getCustomerNameFromSite(json.loads(customers), json.loads(
    client_services), "17ae69fd-63e2-4ad3-8882-7498bbb015f3")

print(router_dict)
print(router_ip)

for key in router_dict.keys():
    print((getRouterIP(json.loads(devices), key)).split('/')[0])

print(customer_name)
