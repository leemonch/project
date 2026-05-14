from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json
import os

class SportObject(BaseModel):
    id: int
    name: str
    type: str
    lat: float
    lon: float
    description: str

app = FastAPI()

DATA_FILE = "sports.json" # Хранить данные в sports.json (список объектов)]

def load_data() -> List[dict]:
    """Загружает данные из JSON файла"""
    if not os.path.exists(DATA_FILE):
        save_data([])  # Сохраняем пустой список
        return []      # Возвращаем пустой список
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def save_data(data: List[dict]): #принимает список словарей
    """Сохраняет данные в JSON файл"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_next_id(data: List[dict]) -> int:
    """Генерирует следующий ID"""
    if not data:
        return 1
    return max(item['id'] for item in data) + 1

class SportObjectCreate(BaseModel):
    """Модель для создания нового объекта (без ID)"""
    name: str
    type: str
    lat: float
    lon: float
    description: str = ""  # description опционально

class SportObjectUpdate(BaseModel):
    """Модель для обновления объекта (все поля опциональны)"""
    name: Optional[str] = None
    type: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    description: Optional[str] = None

@app.get("/objects", response_model=List[SportObject])
async def get_objects():
    """Возвращает список всех спортивных объектов"""
    data = load_data()
    return data
