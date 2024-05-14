import random
import time

import requests
import json


data = []
url = "http://127.0.0.1:8000/api/product/"


headers = {
  'Content-Type': 'application/json',
  'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzE4MDQ1MTkyLCJpYXQiOjE3MTU0NTMxOTIsImp0aSI6IjVhYjUwMTkzOGJiYzQ1NGE5YjI1ZmQ2NWYwNGI2ZTY0IiwidXNlcl9pZCI6MX0.K0tYZu37TqQEG4io20sxu6czgjArMM4h96te9xZ-lxk'
}


with open("data.json", "r+", encoding='UTF-8') as jsonFile:
    data = json.load(jsonFile)

for item in data:
    payload = json.dumps({
      "name": item['name'],
      "img": item['img'],
      "price": item['price'],
      "description": item['description'],
      "quantity": random.randint(1, 100),
      "type": item['type']
    })
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)
    time.sleep(0.3)


# how to run this file:
# cd .\services\
# python .\set_data.py