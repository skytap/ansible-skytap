#!/usr/bin/python
# 
# 2020-04-20 - M.Measel 

DOCUMENTATION = '''
---
module: skytap_vm
short_description: Build and control Skytap cloud vms
'''

import json
import requests
import sys
import time
from ansible.module_utils.basic import AnsibleModule

# API endpoint for Skytap REST API
API_BASE = 'https://cloud.skytap.com/'
API_HEADERS = {'accept': 'application/json', 'content-type': 'application/json'}

#  Basic REST call to Skytap API
def restCall(auth, method, path, data=None):
	try:
		if(method == 'GET'):
			result = requests.get(API_BASE + path, headers=API_HEADERS, auth=auth)
		if(method == 'POST'):
			result = requests.post(API_BASE + path, headers=API_HEADERS, auth=auth, data=data)
		if(method == 'PUT'):
			result = requests.put(API_BASE + path, headers=API_HEADERS, auth=auth, data=data)
		if(method == 'DELETE'):
			result = requests.delete(API_BASE + path, headers=API_HEADERS, auth=auth, allow_redirects=True)

		if len(result.content) > 0:
			return result.status_code, result.json()
		else:
			return result.status_code, None
	except:
		return -1, None

# Main module code here
def main():
	module = AnsibleModule(
		argument_spec = dict(
			username = dict(required=True),
			token = dict(required=True),
			action = dict(default='create', choices=['create', 'modify', 'delete', 'read', 'list_interfaces', 'list_credentials', 'wait_ratelimit']),
			template_id = dict(required=False),
			environment_id = dict(required=False),
			name = dict(required=False),
			edit = dict(required=False),
			component = dict(required=False),
			component_json = dict(required=False),
			vm_id = dict(required=True),
			tag = dict(required=False),
			disk_size = dict(required=False),
			cpu_count = dict(required=False),
			interface_id = dict(required=False),
			internal_port = dict(required=False),
			state = dict(required=False, choices=['running', 'stopped', 'suspended', 'halted', 'reset'])
		),
		supports_check_mode=False
	)
	auth = (module.params.get('username'), module.params.get('token'))

	if module.params.get('action') == 'create':
		if not module.params.get('template_id'):
			module.fail_json(msg="template_id is required param when action=create")
		request_data = {"template_id": module.params.get('template_id')}
		if module.params.get('name'):
			request_data['name'] = module.params.get('name')

		status, result = restCall(auth, 'POST', '/v1/configurations', data=json.dumps(request_data))

	if module.params.get('action') == 'modify':
		request_data = {}
		if not module.params.get('vm_id'):
			module.fail_json(msg="vm_id is required param when action=modify")
		if module.params.get('state'):
			request_data['runstate'] = module.params.get('state')
		if module.params.get('name'):
			request_data['name'] = module.params.get('name')
		if module.params.get('cpu_count'):
			hardware_params = '{"hardware":{"cpus":' + module.params.get('cpu_count') + '}}'	
			request_data = json.loads(hardware_params)
		if module.params.get('disk_size'):
			hardware_params = '{"hardware":{"disks":{"new":[' + module.params.get('disk_size') + ']}}}'
			request_data = json.loads(hardware_params)
		if module.params.get('internal_port'):
			ps_params = '{"internal_port":' + module.params.get('internal_port') + '}'
			request_data = json.loads(ps_params)
		if not module.params.get('component'):
			status, result = restCall(auth, 'PUT', '/v1/vms/'+str(module.params.get('vm_id')), data=json.dumps(request_data))
		else:
			component = module.params.get('component')
			request_data = json.loads(ps_params)
			status, result = restCall(auth, 'POST', '/v2/configurations/'+str(module.params.get('environment_id'))+'/vms/'+str(module.params.get('vm_id'))+'/'+component+'/'+str(module.params.get('interface_id'))+'/services', data=json.dumps(request_data))
		
	if module.params.get('action') == 'delete':
		if not module.params.get('vm_id'):
			module.fail_json(msg="vm_id is required param when action=delete")

		status, result = restCall(auth, 'DELETE', '/v1/vms/'+str(module.params.get('vm_id')))

	if module.params.get('action') == 'read':
		if not module.params.get('vm_id'):
			module.fail_json(msg="vm_id is required param when action=read")
		if not module.params.get('environment_id'):
			status, result = restCall(auth, 'GET', '/v1/vms/'+str(module.params.get('vm_id')))
		else:
			status, result = restCall(auth, 'GET', '/v2/configurations/'+str(module.params.get('environment_id'))+'/vms/'+str(module.params.get('vm_id')))
		
	if module.params.get('action') == 'list_interfaces':
		status, result = restCall(auth, 'GET', '/v2/vms/' +str(module.params.get('vm_id')) + '/interfaces')
		
	
	if module.params.get('action') == 'list_credentials':
		status, result = restCall(auth, 'GET', '/v2/vms/' +str(module.params.get('vm_id')) + '/credentials')


	if module.params.get('action') == 'wait_ratelimit':
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=wait_ratelimit")

		tries = 0
		status = -1
		while True:
			status, result = restCall(auth, 'GET', '/v1/configurations/'+str(module.params.get('environment_id')))
			tries = tries + 1
			if (status != 423 or status != 422) or tries > 30:
				time.sleep(5)
				break
			time.sleep(5)

    # Check results and exit
    if status == requests.codes.ok:
        module.exit_json(changed=True, api_result=result, status_code=status)
        
	if result != None:
       	if result.has_key('error'): 
       		err = result['error']
       	else:
       		err = "No error message given, likely connection or network failure"
     else:
     	 err = result
        		
    module.fail_json(msg="API call failed, HTTP status: "+str(status)+", error: "+err)
       	

    module.exit_json(changed=False)
    
if __name__ == '__main__':
	main()
