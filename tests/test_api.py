import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import main

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, 'DATA', tmp_path)
    monkeypatch.setattr(main, 'CONFIG', tmp_path / 'components.json')
    monkeypatch.setattr(main, 'LAYOUT', tmp_path / 'layout.json')
    main.CONFIG.write_bytes((main.BASE / 'dashboard.example.json').read_bytes())
    with TestClient(main.app) as client:
        yield client

def test_custom_json_component_and_page(client):
    cfg={'title':'Custom','components':[{'id':'custom','title':'Custom card','type':'text','data':{'text':'from JSON'}}],'widgets':[{'id':'custom-1','component':'custom','x':0,'y':0,'w':4,'h':3}]}
    assert client.put('/api/components',json=cfg).status_code==200
    assert client.get('/api/components').json()['components'][0]['data']['text']=='from JSON'
    assert client.get('/widget/custom').status_code==200
    assert client.get('/widget/missing').status_code==404

def test_layout_round_trip_including_empty(client):
    widgets=client.get('/api/components').json()['widgets']
    widgets[0]['w']=6
    assert client.put('/api/layout',json={'widgets':widgets}).status_code==200
    assert client.get('/api/layout').json()=={'widgets':widgets}
    assert client.put('/api/layout',json={'widgets':[]}).status_code==200
    assert client.get('/api/layout').json()=={'widgets':[]}

@pytest.mark.parametrize('change',[{'component':'missing'},{'x':11},{'w':0}])
def test_invalid_layout_does_not_replace_saved_file(client,change):
    widgets=client.get('/api/components').json()['widgets']
    assert client.put('/api/layout',json={'widgets':widgets}).status_code==200
    bad=json.loads(json.dumps(widgets));bad[0].update(change)
    assert client.put('/api/layout',json={'widgets':bad}).status_code==422
    assert client.get('/api/layout').json()['widgets']==widgets

def test_invalid_config_and_stale_layout(client):
    cfg=client.get('/api/components').json()
    assert client.put('/api/layout',json={'widgets':cfg['widgets']}).status_code==200
    bad=json.loads(json.dumps(cfg));bad['components'][0].update(type='iframe',data={'url':'javascript:alert(1)'})
    assert client.put('/api/components',json=bad).status_code==422
    bad=json.loads(json.dumps(cfg));bad['widgets'].append(bad['widgets'][0])
    assert client.put('/api/components',json=bad).status_code==422
    cfg['components']=[c for c in cfg['components'] if c['id']!='map']
    cfg['widgets']=[w for w in cfg['widgets'] if w['component']!='map']
    assert client.put('/api/components',json=cfg).status_code==200
    assert client.get('/api/layout').status_code==409
