import json
import time

import requests
from lxml import html
from urllib.parse import urlparse
import re
import datetime

base_url = 'https://herogame.vn/danh-muc/mo-hinh-one-piece'
root_url = 'https://herogame.vn'
response = requests.get(base_url).text
tree = html.fromstring(response)
links = tree.xpath('//a/@href')

new_links = []
data = []
for link in links:
    if re.compile(r'^\/(?!danh-muc).*').match(link):
        new_links.append(root_url + link)
    if root_url in link and 'danh-muc' not in link:
        new_links.append(link)
new_links = list(set(new_links))

for link in new_links:
    try:
        product = requests.get(link).text
        root = html.fromstring(product)
        name = root.xpath("//div[@class='title']/h1/text()")[0]
        img = root_url + root.xpath("//div[@id='productMainPhoto']/@data-zoom-image")[0]
        price = root.xpath("(//strong[@class='price-a']/text()"
                           "|//span[@id='selected_price_sales']/text())[normalize-space()]")[0]
        try:
            price = re.findall(r"[0-9]", price)
            price = int(''.join(price))
        except Exception:
            price = 100000

        description = root.xpath("//div[@class='title']/h2//text()[normalize-space()]")[0]
        type = root.xpath("//div[@class='intro']//a/strong/text()")[0]

        with open("data3.json", "r+", encoding='UTF-8') as jsonFile:
            data = json.load(jsonFile)

        data.append({
            'name': name,
            'link': link,
            'img': img,
            'price': price,
            'description': description,
            'type': type
        })

        with open('data3.json', 'w', encoding='UTF-8') as f:
            json.dump(data, f, indent=4, separators=(',', ': '), ensure_ascii=False)

    except Exception as e:
        print(e, link)



