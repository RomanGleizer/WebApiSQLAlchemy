import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Base
from crud import get_items, get_item, create_item, delete_item
from parser import parse_data

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def background_parse_data(db: Session):
    items = parse_data()
    for item in items:
        create_item(db, item["name"], item["price"])

@app.post("/parse")
async def start_parsing(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    background_tasks.add_task(background_parse_data, db)
    return {"message": "Парсинг запущен"}

@app.get("/items")
async def read_items(db: Session = Depends(get_db)):
    return get_items(db)

@app.get("/items/{item_id}")
async def read_item(item_id: int, db: Session = Depends(get_db)):
    item = get_item(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.post("/items")
async def create_new_item(name: str, price: int, db: Session = Depends(get_db)):
    return create_item(db, name, price)

@app.delete("/items/{item_id}")
async def delete_existing_item(item_id: int, db: Session = Depends(get_db)):
    if not delete_item(db, item_id):
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}


#if __name__ == "__main__":
#   uvicorn.run(app, host="0.0.0.0", port=8000)