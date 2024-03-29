#!/usr/bin/python

# 2019-01-22 - M.Measel - added add_user and add_group actions
# 2019-01-23 - M.Measel - added list_envs, read_assets and read_templates actions

DOCUMENTATION = '''
---
module: skytap_project
short_description: Manage Skytap projects
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
			action = dict(default='create', choices=['create', 'delete', 'list', 'read', 'list_envs', 'list_templates', 'list_assets', 'list_users', 'add_env', 'add_asset', 'add_template', 'add_users', 'add_groups']),
			project_id = dict(required=False),
			object_id = dict(required=False),
			role = dict(required=False),
			name = dict(required=False),
		),
		supports_check_mode=False
	)
	auth = (module.params.get('username'), module.params.get('token'))

	if module.params.get('action') == 'create':
		if not module.params.get('name'):
			module.fail_json(msg="name is required param when action=create")
		request_data = {"name": module.params.get('name')}

		status, result = restCall(auth, 'POST', '/v1/projects', data=json.dumps(request_data))

	if module.params.get('action') == 'delete':
		if not module.params.get('project_id'):
			module.fail_json(msg="project_id is required param when action=delete")

		status, result = restCall(auth, 'DELETE', '/v1/projects/' + str(module.params.get('project_id')))

	if module.params.get('action') == 'list':
		status, result = restCall(auth, 'GET', '/v2/projects?scope=me&count=100')

	if module.params.get('action') == 'list_users':
		status, result = restCall(auth, 'GET', '/v2/projects/' + str(module.params.get('project_id')) + '/users' )

	if 'add_' in module.params.get('action'):
		if not module.params.get('project_id'):
			module.fail_json(msg="project_id is required param when action=add")
		if not module.params.get('object_id'):
			module.fail_json(msg="object_id is required param when action=add")
		object_type = ''
		add_action = module.params.get('action').split('_')[1]
		
		if add_action == 'users' or add_action == 'groups': 
			object_type = add_action
			if not module.params.get('role'):
				role = 'participant'
			else:
				role = str(module.params.get('role'))
			status, result = restCall(auth, 'POST', '/v2/projects/' + str(module.params.get('project_id')) + '/'+object_type+'/' + str(module.params.get('object_id')) + '?role=' + role )        
		else:
			if module.params.get('action') == 'add_env': object_type = 'configurations'
			if module.params.get('action') == 'add_asset': object_type = 'assets'
			if module.params.get('action') == 'add_template': object_type = 'templates'

			status, result = restCall(auth, 'POST', '/v2/projects/' + str(module.params.get('project_id')) + '/'+object_type+'/' + str(module.params.get('object_id')) )

	if module.params.get('action') == 'read':
		if not module.params.get('project_id'):
			module.fail_json(msg="project_id is required param when action=read")

		status, result = restCall(auth, 'GET', '/v2/projects/'+str(module.params.get('project_id')))
	
	
	if 'list_' in module.params.get('action'):
		if not module.params.get('project_id'):
			module.fail_json(msg="project_id is required param when action=list_")
		if module.params.get('action') == 'list_envs': object_type = 'configurations'
		if module.params.get('action') == 'list_assets': object_type = 'assets'
		if module.params.get('action') == 'list_templates': object_type = 'templates'
		
		status, result = restCall(auth, 'GET', '/v2/projects/' + str(module.params.get('project_id')) + '/' + object_type )
		
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
