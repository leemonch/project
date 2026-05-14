from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
import json  
from typing import List, Optional
from pydantic import BaseModel
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель данных с описанием и фото
class SportObject(BaseModel):
    name: str
    type: str
    description: str = ""
    lat: float
    lon: float
    photos: Optional[List[str]] = []  

class SportObjectDB(SportObject):
    id: int

def get_db():
    conn = sqlite3.connect('sports.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Создаём таблицу, если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL
        )
    ''')
    
    # Добавляем колонку description, если её нет
    try:
        cursor.execute('ALTER TABLE objects ADD COLUMN description TEXT')
        print("✅ Добавлена колонка description")
    except sqlite3.OperationalError:
        pass  # колонка уже существует
    
    # Добавляем колонку photos, если её нет
    try:
        cursor.execute('ALTER TABLE objects ADD COLUMN photos TEXT DEFAULT "[]"')
        print("✅ Добавлена колонка photos")
    except sqlite3.OperationalError:
        pass  # колонка уже существует
    
    conn.commit()
    conn.close()
    print("✅ База данных готова к работе")

init_db()

@app.get("/api/objects", response_model=List[SportObjectDB])
async def get_objects():
    """Получить все спортивные объекты"""
    conn = get_db()
    cursor = conn.execute('SELECT * FROM objects')
    objects = cursor.fetchall()
    conn.close()
    
    result = []
    for obj in objects:
        obj_dict = dict(obj)
        # Безопасное получение полей (защита от отсутствия колонок)
        obj_dict['description'] = obj_dict.get('description') or ''
        
        # Безопасное получение photos
        photos_value = obj_dict.get('photos')
        if photos_value and isinstance(photos_value, str):
            try:
                obj_dict['photos'] = json.loads(photos_value)
            except:
                obj_dict['photos'] = []
        else:
            obj_dict['photos'] = []
        
        result.append(obj_dict)
    
    return result

@app.post("/api/objects/")
async def add_object(obj: SportObject):
    """Добавить новый объект"""
    conn = get_db()
    
    photos_json = json.dumps(obj.photos, ensure_ascii=False)
    
    cursor = conn.execute(
        'INSERT INTO objects (name, type, description, lat, lon, photos) VALUES (?, ?, ?, ?, ?, ?)',  
        (obj.name, obj.type, obj.description, obj.lat, obj.lon, photos_json)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "message": "Объект добавлен"}

@app.delete("/api/objects/{object_id}")
async def delete_object(object_id: int):
    """Удалить объект по ID"""
    conn = get_db()
    cursor = conn.execute('DELETE FROM objects WHERE id = ?', (object_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    return {"message": "Объект удалён"}

@app.put("/api/objects/{object_id}")
async def update_object(object_id: int, obj: SportObject):
    """Обновить объект (для добавления фото)"""
    conn = get_db()
    
    cursor = conn.execute('SELECT id FROM objects WHERE id = ?', (object_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    photos_json = json.dumps(obj.photos, ensure_ascii=False)
    
    conn.execute(
        'UPDATE objects SET name = ?, type = ?, description = ?, lat = ?, lon = ?, photos = ? WHERE id = ?',
        (obj.name, obj.type, obj.description, obj.lat, obj.lon, photos_json, object_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Объект обновлён"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)