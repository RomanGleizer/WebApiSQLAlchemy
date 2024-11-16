import re
import requests
from bs4 import BeautifulSoup

def parse_data():
    url = "https://www.maxidom.ru/catalog/elki-elovye-vetki-girlyandy/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    names_elements = soup.find_all('div', class_='l-product__name')
    prices_elements = soup.find_all('div', class_='l-product__price')
    products = []

    if len(names_elements) != len(prices_elements):
        raise ValueError("Количество элементов с названиями и ценами не совпадают.")

    for i in range(len(names_elements)):
        name_element = names_elements[i]
        price_element = prices_elements[i]

        name = name_element.text.strip().split('\n')[0]
        price_text = price_element.text.strip()
        price_match = re.search(r'\d+\s*\d+', price_text)

        if price_match:
            price = int(price_match.group(0).replace('\xa0', '').replace(' ', ''))
        else:
            raise ValueError("Ошибка получения цены товара. Разметка не удовлетворяет текущим настройкам")

        products.append({'name': name, 'price': price})

    return products
