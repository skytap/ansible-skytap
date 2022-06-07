#!/usr/bin/python
# 
# 2019-01-23 - M.Measel - added Edit param to Modify action 
# 2019-01-24 - M2       - added list_networks
# 2019-01-25 - M2       - added add_tag action
# 2019-01-29 - M2       - added listByTag action
# 2019-01-29 - M2       - added readVM action
# 2022-06-07 - M2		- fixed wait for ready bug

DOCUMENTATION = '''
---
module: skytap_environment
short_description: Build and control Skytap cloud environments
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
			action = dict(default='create', choices=['create', 'modify', 'delete', 'read', 'readVM', 'list', 'listByTag', 'list_networks', 'wait_ready', 'copy', 'add_tag']),
			template_id = dict(required=False),
			environment_id = dict(required=False),
			name = dict(required=False),
			edit = dict(required=False),
			component = dict(required=False),
			vm_id = dict(required=False),
			tag = dict(required=False),
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
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=modify")
		if module.params.get('state'):
			request_data['runstate'] = module.params.get('state')
		if module.params.get('name'):
			request_data['name'] = module.params.get('name')
		if module.params.get('edit'):
			edparms = module.params.get('edit')
			obj = edparms.split(':')[0]
			val = edparms.split(':')[1]
			request_data[obj] = val
		if not module.params.get('component'):
			status, result = restCall(auth, 'PUT', '/v1/configurations/'+str(module.params.get('environment_id')), data=json.dumps(request_data))
		else:
			component = module.params.get('component')
			status, result = restCall(auth, 'PUT', '/v1/configurations/'+str(module.params.get('environment_id') + '/' + component), data=json.dumps(request_data))
			
	if module.params.get('action') == 'add_tag':
		tag = module.params.get('tag')
		body =  '[{"value":"' + tag + '"}]'
		status, result = restCall(auth, 'PUT', '/v1/configurations/'+str(module.params.get('environment_id') + '/tags'), data=body)
		
	if module.params.get('action') == 'delete':
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=delete")

		status, result = restCall(auth, 'DELETE', '/v1/configurations/'+str(module.params.get('environment_id')))

	if module.params.get('action') == 'read':
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=read")

		status, result = restCall(auth, 'GET', '/v1/configurations/'+str(module.params.get('environment_id')))
		
	if module.params.get('action') == 'readVM':
		if not module.params.get('vm_id'):
			module.fail_json(msg="vm_id is required param when action=readVM")
		if not module.params.get('environment_id'):
			status, result = restCall(auth, 'GET', '/v1/vms/'+str(module.params.get('vm_id')))
		else:
			status, result = restCall(auth, 'GET', '/v2/configurations/'+str(module.params.get('environment_id'))+'/vms/'+str(module.params.get('vm_id')))

	if module.params.get('action') == 'list':
		status, result = restCall(auth, 'GET', '/v2/configurations?scope=me&count=100')
		
	if module.params.get('action') == 'listByTag':
		if not module.params.get('tag'):
			module.fail_json(msg="tag is required param when action=listByTag")
		select_tag = module.params.get('tag')
		status, result = restCall(auth, 'GET', '/v2/configurations?scope=company&query=name:' + select_tag + '*&tags=true' + '&count=100')
		
	if module.params.get('action') == 'list_networks':
		status, result = restCall(auth, 'GET', '/v2/configurations/' +str(module.params.get('environment_id')) + '/networks')

	if module.params.get('action') == 'copy':
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=copy")
		request_data = {"configuration_id": module.params.get('environment_id')}
		if module.params.get('name'):
			request_data['name'] = module.params.get('name')

		status, result = restCall(auth, 'POST', '/v1/configurations', data=json.dumps(request_data))

	if module.params.get('action') == 'wait_ready':
		if not module.params.get('environment_id'):
			module.fail_json(msg="environment_id is required param when action=wait_ready")

		tries = 0
		status = -1
		while True:
			time.sleep(10)
			status, result = restCall(auth, 'GET', '/v1/configurations/'+str(module.params.get('environment_id')))
			tries = tries + 1
			if status == 200:
				if result['runstate'] == 'busy':
					time.sleep(10)
					continue
				else:
					break
			if status == 423:
				time.sleep(10)
				continue
			if status == 422:
				time.sleep(10)
				continue
			if tries > 30:
				break


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
