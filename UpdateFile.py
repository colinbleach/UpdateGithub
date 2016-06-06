from urllib.request import urlopen
import re
import json
import base64
import requests
import configparser

#declare variables
config = configparser.ConfigParser()
config.read('settings.ini')
user = config['DEFAULT']['user']
authKey = config['DEFAULT']['auth_key']
is_user = config['DEFAULT'].getboolean('is_user')
branch = config['DEFAULT']['current_branch']
new_branch_name = config['DEFAULT']['new_branch']

#call the url
def call_api(url):
    return json.loads(urlopen(url).read().decode('utf-8'))

#remove prefix before version number
def updateContent(content):
    result = re.sub('^.*?(?=[1-9])', '', content)
    return result

#get all repositories for user
def getRepos(user, is_user):
    print('Getting list of repositories for user ' + user)
    if(is_user):
        url = 'https://api.github.com/users/' + user + '/repos'
    else:
        url = 'https://api.github.com/orgs/' + user + '/repos'

    return call_api(url)

#base 64 decode values
def decode(content):
    return base64.b64decode(content)

#base 64 encode values
def encode(content):
    return base64.b64encode(content)

repos = getRepos(user, is_user)

for repo in repos:
    print('Updating file in repo ' + repo['name'])
    try:
        #check if file exists in repo
        get_file_url = 'https://api.github.com/repos/' + user + '/' + repo['name'] + '/contents/VERSION.txt?ref=' + branch
        call_api(get_file_url)

        #create auth headers
        headers = {'Authorization': 'token ' + authKey, 'Content-Type': 'application/json'}

        #get current branch reference
        branch_url = 'https://api.github.com/repos/colinbleach/battery_count/git/refs/heads/' + branch
        branch_data = call_api(branch_url)

        #create new branch
        create_branch_data = json.dumps({'ref': 'refs/heads/' + new_branch_name , 'sha': branch_data['object']['sha']})
        create_branch_url = 'https://api.github.com/repos/' + user + '/' + repo['name'] + '/git/refs'

        r = requests.post(create_branch_url, data=create_branch_data, headers=headers)

        if (r.status_code != 201):
            print('Oops was unable to create branch, hint: check you are authorized to do so or that the branch does not already exist')
            continue

        # get version.txt contents from new branch
        get_file_new_branch_url = 'https://api.github.com/repos/' + user + '/' + repo['name'] + '/contents/VERSION.txt?ref=' + new_branch_name
        file_data = call_api(get_file_new_branch_url)

        #get version.txt file contents
        content = decode(bytes(file_data['content'], encoding='UTF-8')).decode('utf-8')

        # update contents to new version naming scheme
        new_content = encode(bytes(updateContent(content), encoding='UTF-8')).decode('utf-8')

        # update file in the newly created branch
        update_file_data = json.dumps({'path': 'VERSION.txt', 'message': 'update version file', 'content': new_content, 'sha': file_data['sha'], 'branch': new_branch_name})

        r = requests.put(get_file_new_branch_url, data=update_file_data, headers = headers)

        if (r.status_code != 200):
            print('Oops something went wrong updating file, hint: check authorization token permits this action')
            continue

        # submit pull request to merge changes to current branch
        pull_request_url = 'https://api.github.com/repos/' + user + '/' + repo['name'] + '/pulls'
        pull_request_data = json.dumps({'title': 'Update version.txt', 'head': new_branch_name, 'base': branch})
        r = requests.post(pull_request_url, data=pull_request_data, headers=headers)

        if (r.status_code != 201):
            print('Oops could not submit pull request, please check you are authorized to do so')
            continue

    except Exception as e:
        print('No such file Version.txt in repo ' + repo['name'] + 'or branch ' + new_branch_name + 'already exists')
        continue