from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
from pydantic import BaseModel
import sqlite3

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели
class SportObject(BaseModel):
    name: str
    type: str
    lat: float
    lon: float
    description: Optional[str] = ""

class SportObjectDB(SportObject):
    id: int

# База данных
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
            description TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ========== HTML СТРАНИЦА ==========
@app.get("/", response_class=HTMLResponse)
async def index():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>СпортОбъекты</title>
    <meta charset="utf-8">
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        #map { height: 400px; width: 100%; }
        button { margin: 5px; cursor: pointer; padding: 5px 15px; }
        .del { background-color: #ff4444; color: white; border: none; padding: 5px 10px; cursor: pointer; }
        .deleteAll { background-color: #ff4444; color: white; border: none; padding: 5px 15px; margin-left: 10px; font-weight: bold; cursor: pointer; }
        input, select { margin: 5px; padding: 5px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h2>🏟️ Спортивные объекты</h2>
    <div id="map"></div>

    <div style="margin: 20px 0;">
        <input id="name" placeholder="Название">
        <input id="type" placeholder="Тип">
        <input id="lat" placeholder="Широта">
        <input id="lon" placeholder="Долгота">
        <button onclick="addObject()" style="background-color: #4CAF50; color: white;">➕ Добавить</button>
        <button onclick="deleteAllObjects()" class="deleteAll">🗑 Удалить всё</button>
    </div>

    <h3>Список объектов</h3>
    <table border="1">
        <thead><tr><th>Название</th><th>Тип</th><th>Широта</th><th>Долгота</th><th>Действие</th></tr></thead>
        <tbody id="list"></tbody>
    </table>

    <script>
        // Карта
        var map = L.map('map').setView([55.75, 37.62], 12);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(map);
        
        var markers = L.layerGroup().addTo(map);

        // Загрузка данных
        async function loadData() {
            try {
                let res = await fetch('/api/objects');
                let objects = await res.json();
                
                markers.clearLayers();
                let html = '';
                
                for (let o of objects) {
                    let m = L.marker([o.lat, o.lon]).addTo(markers);
                    m.bindPopup('<b>' + o.name + '</b><br>' + o.type + '<br><button onclick="deleteObject(' + o.id + ')">Удалить</button>');
                    
                    html += '<tr>' +
                        '<td>' + o.name + '</td>' +
                        '<td>' + o.type + '</td>' +
                        '<td>' + o.lat + '</td>' +
                        '<td>' + o.lon + '</td>' +
                        '<td><button class="del" onclick="deleteObject(' + o.id + ')">🗑 Удалить</button></td>' +
                    '</tr>';
                }
                
                document.getElementById('list').innerHTML = html || '<tr><td colspan="5">Нет объектов</td></tr>';
            } catch(e) {
                console.error(e);
                document.getElementById('list').innerHTML = '<tr><td colspan="5">Ошибка загрузки. Запустите сервер</td></tr>';
            }
        }

        // Добавление
        async function addObject() {
            let name = document.getElementById('name').value;
            let type = document.getElementById('type').value;
            let lat = parseFloat(document.getElementById('lat').value);
            let lon = parseFloat(document.getElementById('lon').value);
            
            if (!name || !type) { alert('❌ Заполните название и тип'); return; }
            if (isNaN(lat) || isNaN(lon)) { alert('❌ Введите координаты числами'); return; }
            if (lat < -90 || lat > 90) { alert('❌ Широта от -90 до 90'); return; }
            if (lon < -180 || lon > 180) { alert('❌ Долгота от -180 до 180'); return; }
            
            let res = await fetch('/api/objects');
            let objects = await res.json();
            if (objects.some(o => o.name === name)) { alert('❌ Объект с таким названием уже есть'); return; }
            
            await fetch('/api/objects', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, type, lat, lon, description: ""})
            });
            
            document.getElementById('name').value = '';
            document.getElementById('type').value = '';
            document.getElementById('lat').value = '';
            document.getElementById('lon').value = '';
            alert('✅ Объект добавлен!');
            loadData();
        }

        // Удаление одного
        async function deleteObject(id) {
            if (confirm('Удалить объект?')) {
                await fetch('/api/objects/' + id, {method: 'DELETE'});
                loadData();
            }
        }
        
        // Удаление всех
        async function deleteAllObjects() {
            if (confirm('Удалить все объекты?')) {
                let res = await fetch('/api/objects');
                let objects = await res.json();
                for (let obj of objects) {
                    await fetch('/api/objects/' + obj.id, {method: 'DELETE'});
                }
                alert('✅ Все объекты удалены');
                loadData();
            }
        }

        loadData();
    </script>
</body>
</html>
    """

# ========== API ==========
@app.get("/api/objects", response_model=List[SportObjectDB])
async def get_objects():
    conn = get_db()
    cursor = conn.execute('SELECT * FROM objects')
    objects = cursor.fetchall()
    conn.close()
    return [dict(obj) for obj in objects]

@app.post("/api/objects")
async def add_object(obj: SportObject):
    conn = get_db()
    cursor = conn.execute(
        'INSERT INTO objects (name, type, lat, lon, description) VALUES (?, ?, ?, ?, ?)',
        (obj.name, obj.type, obj.lat, obj.lon, obj.description)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "message": "OK"}

@app.delete("/api/objects/{object_id}")
async def delete_object(object_id: int):
    conn = get_db()
    cursor = conn.execute('DELETE FROM objects WHERE id = ?', (object_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"message": "OK"}

# Запуск
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=3000)