import requests
from bs4 import BeautifulSoup


def get_parsed_html(url):
    response = requests.get(url)
    data = response.text
    soup = BeautifulSoup(data, "lxml")
    return soup
