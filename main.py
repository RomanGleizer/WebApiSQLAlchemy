from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
from crud import get_items, get_item, create_item, update_item, delete_item
from parser import parse_data

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def background_parse_data(db: Session, url: str):
    try:
        items = parse_data(url)
        for item in items:
            create_item(db, item["name"], item["price"])
    except ValueError as e:
        print(f"Ошибка парсинга данных: {e}")

@app.post("/parse")
@app.get("/parse")
async def start_parsing(background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db),
                        url: str = None):
    if request.method == "POST":
        body = await request.json()
        url = body.get("url", url)
    if not url:
        raise HTTPException(status_code=400, detail="URL сайта обязателен для парсинга!")

    try:
        parse_data(url)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    background_tasks.add_task(background_parse_data, db, url)
    return {"message": f"Парсинг запущен для сайта: {url}"}

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
async def create_new_item(name: str, price: int, db: Session = Depends(get_db)):
    return create_item(db, name, price)

@app.put("/items/{item_id}")
async def update_existing_item(item_id: int, name: str, price: int, db: Session = Depends(get_db)):
    item = update_item(db, item_id, name, price)
    if not item:
        raise HTTPException(status_code=404, detail="Товар для обновления не найден")
    return {"message": "Товар успешно обновлен"}

@app.delete("/items/{item_id}")
async def delete_existing_item(item_id: int, db: Session = Depends(get_db)):
    if not delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Товар не найден")
    return {"message": "Товар успешно удален"}
