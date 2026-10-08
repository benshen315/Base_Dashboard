"""Run: python -m uvicorn main:app --reload"""
import json
import os
import tempfile
from threading import Lock
from pathlib import Path
from typing import Annotated, Literal
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

BASE = Path(__file__).resolve().parent
DATA = Path(os.environ.get('BASE_DASHBOARD_DATA_DIR', str(BASE / 'data')))
DATA.mkdir(exist_ok=True)
LAYOUT = DATA / 'layout.json'
CONFIG = DATA / 'components.json'
CONFIG_LOCK = Lock()
app = FastAPI(title='Base Dashboard', version='0.1')
app.mount('/static', StaticFiles(directory=BASE / 'static'), name='static')
Identifier = Annotated[str, Field(min_length=1, max_length=100, pattern=r'^[A-Za-z0-9_-]+$')]

class Component(BaseModel):
    id: Identifier
    title: str = Field(min_length=1, max_length=200)
    type: Literal['metric', 'map', 'bar', 'list', 'text', 'iframe']
    data: dict = Field(default_factory=dict)
    fullscreen: bool = True
    popout: bool = True

    @model_validator(mode='after')
    def valid_data(self):
        def fail(message):
            raise ValueError(f'「{self.title}」：{message}')

        def number(value):
            return isinstance(value, (int, float)) and not isinstance(value, bool) and -1.7976931348623157e308 <= value <= 1.7976931348623157e308

        def scalar(value):
            return value is None or isinstance(value, (str, bool)) or number(value)

        text_fields = {'metric': ('unit', 'description'), 'text': ('text',), 'map': ('caption',)}
        for field in text_fields.get(self.type, ()):
            if field in self.data and not isinstance(self.data[field], str):
                fail(f'{field} 必須是文字')
        if self.type == 'metric' and 'value' in self.data:
            value = self.data['value']
            if value is not None and not (isinstance(value, str) or number(value)):
                fail('value 必須是數字或文字')
        if self.type == 'list':
            items = self.data.get('items', [])
            if not isinstance(items, list):
                fail('items 必須是清單陣列')
            for item in items:
                if not isinstance(item, dict) or any(not scalar(item.get(field)) for field in ('label', 'value')):
                    fail('清單每一筆必須是物件，label/value 使用文字或單一數值')
        if self.type == 'bar':
            values = self.data.get('values', [])
            labels = self.data.get('labels', [])
            if not isinstance(values, list) or any(not number(value) for value in values):
                fail('values 必須是有限數字的陣列')
            if not isinstance(labels, list) or any(not isinstance(label, str) for label in labels):
                fail('labels 必須是文字陣列')
        if self.type == 'iframe':
            url = self.data.get('url', '')
            if not isinstance(url, str) or not (url.startswith('/') and not url.startswith('//') or url.startswith('https://') or url.startswith('http://')):
                raise ValueError('iframe URL 必須是相對絕對路徑或 http(s) URL')
        return self

class Widget(BaseModel):
    id: Identifier
    component: Identifier
    x: int = Field(ge=0, le=11)
    y: int = Field(ge=0, le=10000)
    w: int = Field(ge=1, le=12)
    h: int = Field(ge=1, le=100)
    @model_validator(mode='after')
    def within_grid(self):
        if self.x + self.w > 12:
            raise ValueError('面板不得超出 12 欄')
        return self

class Layout(BaseModel):
    widgets: Annotated[list[Widget], Field(max_length=100)]
    @model_validator(mode='after')
    def unique(self):
        if len({w.id for w in self.widgets}) != len(self.widgets):
            raise ValueError('面板 ID 必須唯一')
        return self

class DashboardConfig(BaseModel):
    schema_version: Literal[1] = 1
    title: str = Field(default='工程 Dashboard', max_length=200)
    components: Annotated[list[Component], Field(min_length=1, max_length=100)]
    widgets: Annotated[list[Widget], Field(max_length=100)]
    @model_validator(mode='after')
    def references(self):
        ids = [c.id for c in self.components]
        if len(set(ids)) != len(ids):
            raise ValueError('組件 ID 必須唯一')
        Layout(widgets=self.widgets)
        if any(w.component not in ids for w in self.widgets):
            raise ValueError('面板引用了不存在的組件')
        return self

class ComponentRegistration(BaseModel):
    components: Annotated[list[Component], Field(min_length=1, max_length=100)]

class ComponentRename(BaseModel):
    title: str = Field(min_length=1, max_length=200)

    @model_validator(mode='after')
    def meaningful_title(self):
        self.title = self.title.strip()
        if not self.title:
            raise ValueError('組件名稱不可空白')
        return self

def atomic_write(path, value):
    temp = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=DATA, delete=False) as f:
            temp = f.name
            json.dump(value, f, ensure_ascii=False, indent=2)
        os.replace(temp, path)
    except OSError:
        raise HTTPException(500, '檔案保存失敗')
    finally:
        if temp and Path(temp).exists():
            Path(temp).unlink()

def read_config():
    try:
        return DashboardConfig.model_validate_json(CONFIG.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise HTTPException(500, 'components.json 無法讀取或格式不正確')

@app.get('/', include_in_schema=False)
@app.get('/widget/{component_id}', include_in_schema=False)
def index(component_id: str | None = None):
    if component_id and component_id not in {c.id for c in read_config().components}:
        raise HTTPException(404, '組件不存在')
    return FileResponse(BASE / 'static' / 'index.html')

@app.get('/api/components', response_model=DashboardConfig)
def components():
    return read_config()

@app.put('/api/components', response_model=DashboardConfig)
def import_components(config: DashboardConfig):
    with CONFIG_LOCK:
        atomic_write(CONFIG, config.model_dump())
    return config

@app.post('/api/components/register', response_model=DashboardConfig, status_code=201)
def register_components(upload: ComponentRegistration):
    with CONFIG_LOCK:
        config = read_config()
        ids = [c.id for c in upload.components]
        if len(set(ids)) != len(ids):
            raise HTTPException(409, '上傳檔案的組件 ID 重複')
        existing = {c.id for c in config.components}
        conflicts = existing.intersection(ids)
        if conflicts:
            raise HTTPException(409, '組件 ID 已註冊：' + ', '.join(sorted(conflicts)))
        if len(config.components) + len(upload.components) > 100:
            raise HTTPException(422, '最多可註冊 100 個組件')
        config.components.extend(upload.components)
        atomic_write(CONFIG, config.model_dump())
        return config

@app.patch('/api/components/{component_id}', response_model=DashboardConfig)
def rename_component(component_id: str, update: ComponentRename):
    with CONFIG_LOCK:
        config = read_config()
        component = next((c for c in config.components if c.id == component_id), None)
        if component is None:
            raise HTTPException(404, '組件不存在')
        component.title = update.title
        atomic_write(CONFIG, config.model_dump())
        return config

@app.get('/api/layout', response_model=Layout)
def get_layout():
    if not LAYOUT.exists():
        raise HTTPException(404, '尚未保存版面')
    try:
        layout = Layout.model_validate_json(LAYOUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        raise HTTPException(500, '版面檔案無法讀取')
    if any(w.component not in {c.id for c in read_config().components} for w in layout.widgets):
        raise HTTPException(409, '保存版面引用了已移除的組件，請重設版面')
    return layout

@app.put('/api/layout', response_model=Layout)
def save_layout(layout: Layout):
    if any(w.component not in {c.id for c in read_config().components} for w in layout.widgets):
        raise HTTPException(422, '組件不存在')
    atomic_write(LAYOUT, layout.model_dump())
    return layout
