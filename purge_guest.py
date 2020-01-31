#!/usr/bin/env python3
import requests, sys, json, re, time
from datetime import datetime
requests.packages.urllib3.disable_warnings()


###################
### Script Settings - modify these
############

fgtip = '192.168.1.99'
fgtuser = 'administrator'
fgtsecret = ''
group_name = 'Guest-Group'
vdom_name = 'root'

###################
# Setup
##########

session = requests.session()
startTime = datetime.now()
purge_url = '/api/v2/cmdb/user/group/' + group_name + '/guest?vdom=' + vdom_name + '&filter='
keys = ''
count = 0
grpcount = 0
othercount = 0


###################
### Login to API
############


res = session.post('https://' + fgtip + '/logincheck',
                        data='username=' + fgtuser + '&secretkey=' + fgtsecret,
                        verify=False)


for cookie in session.cookies:
    if cookie.name == 'ccsrftoken':
        csrftoken = cookie.value[1:-1] # token stored as a list
        session.headers.update({'X-CSRFTOKEN': csrftoken})

# Fetch data
url = 'https://' + fgtip + '/api/v2/cmdb/user/group?vdom=' + vdom_name + '&skip=1&filter=group-type%3D%3Dguest'
res = session.get(url, verify=False)
json1 = json.loads(res.text)
if not res.ok:
    exit('ERROR: VDOM not found')

# Iterate results
for i in json1['results']:

    ### Iterate guest groups
    if group_name in i['name'].strip():

        #print('Group located. Name: ' + group_name + '.')
        gid = i['id']

        for z in i['guest']:
            compare_date = datetime.strptime(z['expiration'], "%Y-%m-%d %H:%M:%S")
            if compare_date < startTime:
                keys += 'id%3D%3D' + str(z['id']) + '%2C'
                count += 1
            else:
                othercount += 1

        if count == 0:
            print('No expired accounts to remove. ' + str(othercount) + ' others found.')
        else:
            url = 'https://' + fgtip + purge_url + keys[:-3]
            res = session.delete(url, verify=False)
            if res.ok:
                print(str(count) + ' expired accounts removed successfully.')
            else:
                code = str(res.status_code)
                print('An error (' + code + ') occurred removing expired guest accounts.')

        grpcount += 1

if grpcount == 0:
    print('ERROR: Group not found.')


### Cleanup
session.get('https://' + fgtip + '/logout')
difference = datetime.now() - startTime
print("script took %s seconds to run" % difference)
