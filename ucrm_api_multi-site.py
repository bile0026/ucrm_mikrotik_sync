import json
import requests
from requests.api import head, request
from customer import Customer
from configparser import ConfigParser


# define variables
customer_list = []

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

unms_headers = {
    'X-Auth-Token': uisp_config["key"], 'Content-Type': 'application/json'}

# method to get clients from UISP


def getAllClients():
    clients = requests.get(clients_url, headers=unms_headers)
    if clients.status_code == 200:
        return clients.json()
    else:
        return "No clients found" + clients.status_code


# get all customers from UCRM
customers = getAllClients()

# build list of customers with custom customer class
for customer in customers:
    customer_list.append(Customer(customer))

for customer in customer_list:
    print(customer.queueName + ' - ' + customer.siteType)
