import requests
from urllib.parse import urlencode
from requests.exceptions import RequestException
import json
from bs4 import BeautifulSoup
import re
import os
from hashlib import md5
from json.decoder import JSONDecodeError
from config import *
from multiprocessing import Pool


def get_page_index(offset, keyword):
    data = {
        'offset': offset,
        'format': 'json',
        'keyword': keyword,
        'autoload': 'true',
        'count': '20',
        'cur_tab': 3,
        'from': 'gallery'
    }
    url = 'https://www.toutiao.com/search_content/?' + urlencode(data)
    try:
        res = requests.get(url)
        if res.status_code == 200:
            return res.text
    except RequestException:
        print('请求索引页失败')
        return None


def parse_page_index(html):
    try:
        data = json.loads(html)
        if data and 'data' in data.keys():
            for item in data.get('data'):
                # print(item.get('article_url'))
                yield item.get('article_url')
    except JSONDecodeError:
        return None


def get_page_detail(url):
    try:
        heads = {
            "User-Agent": 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        res = requests.get(url, headers=heads)
        if res.status_code == 200:
            return res.text
    except RequestException:
        print('请求索引页失败')
        return None


def download_image(url):
    print('正在下载图片。。。', url)
    try:
        headers = {
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
        }
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            save_image(res.content)
    except RequestException:
        print('请求图片地址失败')
        return None


def save_image(content):
    image_path = '{0}/{1}.{2}'.format(os.getcwd(), md5(content).hexdigest(), 'jpg')
    if not os.path.exists(image_path):
        with open(image_path, 'wb') as f:
            f.write(content)
            f.close()


def parse_page_detail(html, url):
    soup = BeautifulSoup(html, 'lxml')
    # print(html)
    title = soup.select('title')[0].get_text()
    print(title)
    images_pattern = re.compile('BASE_DATA.galleryInfo = {.*?parse\("(.*?)"\),', re.S)
    result = re.search(images_pattern, html)
    try:
        if result:
            data = json.loads(result.group(1).replace('\\', ''))
            if data and 'sub_images' in data.keys():
                sub_images = data.get("sub_images")
                images = [item.get('url') for item in sub_images]
                for image in images: download_image(image)
                return {
                    'url': url,
                    'title': title,
                    'images': images,
                }
    except JSONDecodeError:
        return None


def main(offset):
    html = get_page_index(offset, KEYWORD)
    for url in parse_page_index(html):
        if url:
            html = get_page_detail(url)
            # print(html)
            if html:
                parse_page_detail(html, url)


if __name__ == '__main__':
    offsets = [x * 20 for x in range(GROUP_START, GROUP_END)]
    pool = Pool()
    pool.map(main,offsets)