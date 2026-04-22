from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import sqlite3
from typing import List, Optional
from pydantic import BaseModel
import os

app = FastAPI()

# Настройка CORS (разрешаем запросы с фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель данных для объекта
class SportObject(BaseModel):
    name: str
    type: str
    lat: float
    lon: float

class SportObjectDB(SportObject):
    id: int

# Подключение к БД
def get_db():
    conn = sqlite3.connect('sports.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создаём таблицу при старте
def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- API endpoints ---

@app.get("/api/objects", response_model=List[SportObjectDB])
async def get_objects():
    """Получить все спортивные объекты"""
    conn = get_db()
    cursor = conn.execute('SELECT * FROM objects')
    objects = cursor.fetchall()
    conn.close()
    return [dict(obj) for obj in objects]

@app.post("/api/objects/")
async def add_object(obj: SportObject):
    """Добавить новый объект"""
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO objects (name, type, lat, lon) VALUES (?, ?, ?, ?)',
        (obj.name
, obj.type, obj.lat
, obj.lon)
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

# Запуск сервера (для прямого запуска файла)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)