import re
from typing import List

import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, AnyHttpUrl
from sqlalchemy.orm import Session

from crud import get_items, get_item, create_item, update_item, delete_item
from database import SessionLocal, engine
from models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

active_connections: List[WebSocket] = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def send_notification(message: str):
    for connection in active_connections:
        await connection.send_text(message)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Асинхронная функция для парсинга данных
async def fetch_url(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status != 200:
                raise ValueError("Ошибка доступа к сайту. Проверьте URL.")
            return await response.text()

async def parse_data_async(url: str):
    html = await fetch_url(url)
    soup = BeautifulSoup(html, "html.parser")
    names_elements = soup.find_all('div', class_='l-product__name')
    prices_elements = soup.find_all('div', class_='l-product__price')
    products = []

    if len(names_elements) != len(prices_elements):
        raise ValueError("Количество элементов с названиями и ценами не совпадает")

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

async def background_parse_data(url: str):
    db = SessionLocal()  # Создать новую сессию
    try:
        items = await parse_data_async(url)
        for item in items:
            create_item(db, item["name"], item["price"])
        db.commit()
        await send_notification(f"Парсинг завершен для сайта: {url}")
    except Exception as e:
        db.rollback()
        await send_notification(f"Ошибка парсинга: {e}")
    finally:
        db.close()

@app.post("/parse")
async def start_parsing(background_tasks: BackgroundTasks, url: AnyHttpUrl):
    background_tasks.add_task(background_parse_data, str(url))
    return {"message": f"Фоновый парсинг запущен для сайта: {url}"}

# CRUD API
class ItemRequest(BaseModel):
    name: str
    price: int

@app.get("/items")
async def read_items(db: Session = Depends(get_db)):
    return get_items(db)

@app.get("/items/{item_id}")
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return item

@app.post("/items")
async def create_new_item(item: ItemRequest, db: Session = Depends(get_db)):
    new_item = create_item(db, item.name, item.price)
    await send_notification("Добавлен новый товар")
    return new_item

@app.put("/items/{item_id}")
async def update_existing_item(item_id: int, item: ItemRequest, db: Session = Depends(get_db)):
    updated_item = update_item(db, item_id, item.name, item.price)
    if not updated_item:
        raise HTTPException(status_code=404, detail="Товар для обновления не найден")
    await send_notification("Товар обновлен")
    return {"message": "Товар успешно обновлен"}

@app.delete("/items/{item_id}")
async def delete_existing_item(item_id: int, db: Session = Depends(get_db)):
    if not delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Товар не найден")
    await send_notification("Товар удален")
    return {"message": "Товар успешно удален"}
