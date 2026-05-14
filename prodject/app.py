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


class SportObject(BaseModel):
    name: str
    type: str
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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            photos TEXT DEFAULT '[]'  -- 👈 ДОБАВИТЬ ЭТУ СТРОКУ (храним JSON)
        )
    ''')
    conn.commit()
    conn.close()

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
        obj_dict['photos'] = json.loads(obj_dict['photos']) if obj_dict['photos'] else []
        result.append(obj_dict)
    
    return result

@app.post("/api/objects/")
async def add_object(obj: SportObject):
    """Добавить новый объект"""
    conn = get_db()
    
    
    photos_json = json.dumps(obj.photos, ensure_ascii=False)
    
    cursor = conn.execute(
        'INSERT INTO objects (name, type, lat, lon, photos) VALUES (?, ?, ?, ?, ?)',  
        (obj.name, obj.type, obj.lat, obj.lon, photos_json)
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
    """
    Обновить объект (нужно для добавления фото)
    Фронт вызывает этот метод при добавлении нового фото
    """
    conn = get_db()
    
   
    cursor = conn.execute('SELECT id FROM objects WHERE id = ?', (object_id,))
    existing = cursor.fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Объект не найден")
    
    # Превращаем фото в JSON
    photos_json = json.dumps(obj.photos, ensure_ascii=False)
    

    conn.execute(
        'UPDATE objects SET name = ?, type = ?, lat = ?, lon = ?, photos = ? WHERE id = ?',
        (obj.name, obj.type, obj.lat, obj.lon, photos_json, object_id)
    )
    conn.commit()
    conn.close()
    
    return {"message": "Объект обновлён"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)  