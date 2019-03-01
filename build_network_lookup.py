#!/usr/bin/python
import json

with open('/home/skytap/ansiblebase/tmp/env_networks.json','r') as input:
    r = json.load(input)
   
envlist = r['results']

etable = {}

for env in envlist:
	env_id = env['_ansible_item_label']['id']
	ttable = {}
	for networks in env['api_result']:	
		#print networks['id'], networks['name']
		for tunnels in networks['tunnels']:
			src_env_id = tunnels['source_network']['url'].split('/')[5]
			tgt_env_id = tunnels['target_network']['url'].split('/')[5]
			src_subnet = tunnels['source_network']['subnet_addr']
			tgt_subnet = tunnels['target_network']['subnet_addr']
			if tgt_env_id == env_id:
				continue
			ttable[src_subnet] = tgt_env_id + ':' + tgt_subnet				


			
	etable[env_id] = ttable

#print "etable ", json.dumps(etable, indent=4)


with open('/home/skytap/ansiblebase/tmp/new_workgroup.json','r') as in2:
	w = json.load(in2)
	
new_env_result = w['results']

oldref = {}
envs = []
for env in new_env_result:
	env_id = env['api_result']['id']
	envs.append(env_id)
	
	tags = env['_ansible_item_label']['tag_list'].split(',')
	for tag in tags:
		if tag[:6] == 'origin':
			old_id = tag.split('-')[1]
			oldref[env_id] = old_id

new_nets = {}
for env in new_env_result:
	old_id = oldref[env['api_result']['id']]
	nets = env['api_result']['networks']
	for net in nets:
		subnet = net['subnet_addr']
		new_nets[old_id + ':' + subnet] = net['id']
			
#print new_nets

plist = []
for env in envs:

	old_nets = etable[ oldref[env]]
	
	for s, t in old_nets.items():	
		src = new_nets[oldref[env] + ':' + s]
		
		if t in new_nets:
			tgt = new_nets[t]
			plist.append ({"env":env,"source":src,"target":tgt})
        
print json.dumps(plist)


	
	
	
	