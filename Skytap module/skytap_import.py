#!/usr/bin/python

# 
# 2021-06-09 - M.Measel - initial build

DOCUMENTATION = '''
---
module: skytap_import
short_description: Import Virtual Machines into Skytap
'''

import json
import requests
import sys
import time
import pysftp

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
			username = dict(required=False),
			token = dict(required=False),
			action = dict(default='create', choices=['create', 'upload', 'process', 'status']),
			template_name = dict(required=False),
			import_id = dict(required=False),
			import_directory = dict(required=False),
			site = dict(required=False),
			ftp_user = dict(required=False),
			ftp_password = dict(required=False),
			vm_id = dict(required=False),
			region = dict(required=False),
			md5 = dict(required=False),
			includes_power = dict(required=False, choices=['true', 'false']),
			state = dict(required=False, choices=['running', 'stopped', 'suspended', 'halted', 'reset'])
		),
		supports_check_mode=False
	)
	auth = (module.params.get('username'), module.params.get('token'))

	if module.params.get('action') == 'create':
		if not module.params.get('template_name'):
			module.fail_json(msg="template_name is required param when action=create")
		request_data = {"template_name": module.params.get('template_name')}
		if module.params.get('region'):
			request_data['region'] = module.params.get('region')
		if module.params.get('md5'):
			request_data['md5'] = module.params.get('md5')
		if module.params.get('includes_power'):
			request_data['includes_power'] = module.params.get('includes_power')
		status, result = restCall(auth, 'POST', '/v2/imports', data=json.dumps(request_data))

	
	if module.params.get('action') == 'process':
		if not module.params.get('import_id'):
			module.fail_json(msg="import_id is required param when action=process")
		status, result = restCall(auth, 'PUT', '/v2/imports/'+str(module.params.get('import_id')))
		
	if module.params.get('action') == 'delete':
		if not module.params.get('import_id'):
			module.fail_json(msg="import_id is required param when action=delete")
		status, result = restCall(auth, 'DELETE', '/v2/imports/'+str(module.params.get('import_id')))

	if module.params.get('action') == 'list':
		status, result = restCall(auth, 'GET', '/v2/imports')

	if module.params.get('action') == 'status':
		if not module.params.get('import_id'):
			module.fail_json(msg="import_id is required param when action=status")
		status, result = restCall(auth, 'GET', '/v2/imports')
		
	if module.params.get('action') == 'upload':
		if not module.params.get('site'):
			module.fail_json(msg="site is required param when action=upload")
		if not module.params.get('ftp_user'):
			module.fail_json(msg="ftp_user is required param when action=upload")
		if not module.params.get('ftp_password'):
			module.fail_json(msg="ftp_password is required param when action=upload")
		if not module.params.get('import_directory'):
			module.fail_json(msg="import_directory is required param when action=upload")
		usite = module.params.get('site')
		uname = module.params.get('ftp_user')
		upwd = module.params.get('ftp_password')
		upload_directory = module.params.get('import_directory')
			
		with pysftp.Connection(usite,username=uname, password=upwd) as sftp:    
			sftp.put_r(upload_directory, '/upload/') 
		

	# Check results and exit
	if status != requests.codes.ok:
		err = "No error message given, likely connection or network failure"
		if result != None and result.has_key('error'): err = result['error']
		module.fail_json(msg="API call failed, HTTP status: "+str(status)+", error: "+err)
	else:
		module.exit_json(changed=True, api_result=result, status_code=status)

	module.exit_json(changed=False)

if __name__ == '__main__':
	main()
