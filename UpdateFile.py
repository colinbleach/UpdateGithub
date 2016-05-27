from urllib.request import urlopen
import re
import json
import base64
import requests

#declare variables
user = 'colinbleach'
authKey = '2052b29434542041f3ae476fd39062197139e170'
isUser = True

#call the url
def callApi(url):
    return json.loads(urlopen(url).read().decode("utf-8"))

#remove prefix before version number
def updateContent(content):
    result = re.sub('^.*?(?=[1-9])', '', content)
    return result

#get all repositories for user
def getRepos(user, isUser):
    if(isUser):
        url = 'https://api.github.com/users/' + user + '/repos'
    else:
        url = 'https://api.github.com/orgs/' + user + '/repos'

    return callApi(url)

#base 64 decode values
def decode(content):
    return base64.b64decode(content)

#base 64 encode values
def encode(content):
    return base64.b64encode(content)

repos = getRepos(user, isUser)

for repo in repos:
    try:
        url = 'https://api.github.com/repos/' + user + '/' + repo['name'] + '/contents/VERSION.txt'
        data = callApi(url)

        content = decode(bytes(data['content'], encoding='UTF-8')).decode("utf-8")

        newContent = encode(bytes(updateContent(content), encoding='UTF-8')).decode("utf-8")

        payload = {"path": "VERSION.txt", "message": "update version file", "content": newContent, "sha": data['sha']}
        json_data = json.dumps(payload)
        headers = {"Authorization": "token " + authKey, "Content-Type": "application/json"}
        r = requests.put(url, data=json_data, headers = headers)
    except:
        continue