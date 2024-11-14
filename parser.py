import requests
from bs4 import BeautifulSoup


def parse_data():
    url = "https://example.com"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    items = []
    for element in soup.select(".item-class"):
        name = element.select_one(".name-class").text
        description = element.select_one(".description-class").text
        link = element.select_one("a")["href"]
        items.append({"name": name, "description": description, "url": link})
    return items
