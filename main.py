import json
import hashlib
import hmac
import base64
import sys

from urllib.parse import quote
from datetime import datetime

import requests

from mysecrets import GLASSDOOR_KEY, PUSHOVER_KEY, PUSHOVER_USER


KEYWORD = ''
LOCATION_ID = 0

HEADERS = {'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}


def send_pushover(title, msg, url):
    data = {'token': PUSHOVER_KEY, 'user': PUSHOVER_USER, 'message': msg, 'title': title, 'url': url}
    requests.post('https://api.pushover.net/1/messages.json', data=data)


def create_signature():
    now = int(datetime.now().timestamp()*1000) + 86400000
    raw = f'fz6JLNgLgVs|{now}'.encode('utf-8')
    hashed = hmac.new(GLASSDOOR_KEY.encode('utf-8'), raw, hashlib.sha1)
    signature = base64.encodebytes(hashed.digest()).decode('utf-8')
    signature = quote(signature)
    return f's.expires={now}&signature={signature}'


def get_location(location):
    signature = create_signature()
    url = 'https://api.glassdoor.com/api-internal/api.htm' + \
        f'?action=popularLocationSearch&version=1.2&term={location}' + \
        '&numOfResults=20&t.k=fz6JLNgLgVs&appVersion=6.5.0&responseType=json' + \
        f'&{signature}&t.p=16&locale=en_US'
    resp = requests.get(url, headers=HEADERS)
    resp = resp.json()
    return resp


url = 'https://api.glassdoor.com/api-internal/api-internal/api.htm?' + \
      'action=graph&version=1&t.p=16&t.k=fz6JLNgLgVs' + \
      '&appVersion=10.0.2&locale=en_US&responseType=json' + \
      f'&{create_signature()}'


# get locations and exit
# print(get_location('Lytham'))
# sys.exit(0)


json_search = json.load(open('search.json', 'rb'))
json_search['variables']['searchParams']['filterParams'].append({'filterKey': 'fromAge', 'values': '7'})
json_search['variables']['searchParams']['filterParams'].append({'filterKey': 'radius', 'values': '5'})
json_search['variables']['searchParams']['locationId'] = LOCATION_ID
json_search['variables']['searchParams']['keyword'] = KEYWORD
response = requests.post(url, json=json_search, headers=HEADERS)
jobs = {}

try:
    jobs = json.load(open('jobs.json', 'r'))
except FileNotFoundError:
    pass

for job in response.json()['data']['jobListings']['jobListings']:
    id = str(job['jobview']['job']['listingId'])
    title = job['jobview']['job']['jobTitleText']
    company = job['jobview']['header']['employerNameFromSearch']
    location_type = job['jobview']['header']['locationType']
    if location_type != 'C':
        continue
    if id not in jobs:
        send_pushover(title, f'{company}', f'https://www.glassdoor.co.uk/job-listing/?jl={id}')
    jobs[id] = {'title': title, 'company': company}

json.dump(jobs, open('jobs.json', 'w'))
