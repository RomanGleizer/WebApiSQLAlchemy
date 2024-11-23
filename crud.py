from sqlalchemy.orm import Session
from models import Item

def get_items(db: Session):
    return db.query(Item).all()

def get_item(db: Session, item_id: int):
    return db.query(Item).filter(Item.id == item_id).first()

def create_item(db: Session, name: str, price: int):
    db_item = Item(name=name, price=price)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_item(db: Session, item_id: int, name: str, price: int):
    item = get_item(db, item_id)
    if item:
        item.name = name
        item.price = price
        db.commit()
        db.refresh(item)
        return item
    return None

def delete_item(db: Session, item_id: int):
    item = get_item(db, item_id)
    if item:
        db.delete(item)
        db.commit()
        return True
    return False
