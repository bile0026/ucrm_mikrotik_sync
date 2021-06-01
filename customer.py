import requests
import json
from configparser import ConfigParser

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

# custom customer class to store custom information


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
