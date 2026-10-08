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

@pytest.mark.parametrize('kind,data',[
    ('list',{'items':[None]}),
    ('list',{'items':{'label':'P01'}}),
    ('list',{'items':[{'label':{'name':'P01'},'value':'normal'}]}),
    ('bar',{'values':[10,'twenty']}),
    ('bar',{'values':[10,True]}),
    ('bar',{'values':[10,20],'labels':'Monday'}),
    ('metric',{'value':{'count':128}}),
    ('text',{'text':['invalid']}),
])
def test_invalid_component_data_preserves_configuration(client,kind,data):
    before=client.get('/api/components').json()
    file_before=main.CONFIG.read_bytes()
    bad=json.loads(json.dumps(before))
    bad['components'][0].update(type=kind,data=data)
    response=client.put('/api/components',json=bad)
    assert response.status_code==422
    assert main.CONFIG.read_bytes()==file_before
    assert client.get('/api/components').json()==before

@pytest.mark.parametrize('kind,data',[
    ('list',{'items':[{'label':'P01','value':'normal'},{'label':'count','value':3}]}),
    ('bar',{'values':[0,12.5,-3],'labels':['A','B','C']}),
    ('metric',{'value':'pending','unit':'status'}),
    ('text',{'text':'line one\nline two'}),
])
def test_valid_component_data_round_trips(client,kind,data):
    cfg=client.get('/api/components').json()
    cfg['components'][0].update(type=kind,data=data)
    assert client.put('/api/components',json=cfg).status_code==200
    assert client.get('/api/components').json()['components'][0]['data']==data


def test_register_appends_and_preserves_saved_layout(client):
    before=client.get('/api/components').json()
    client.put('/api/layout',json={'widgets':before['widgets']})
    saved=main.LAYOUT.read_bytes()
    upload={'components':[{'id':'new-note','title':'New','type':'text','data':{'text':'Hello'}},{'id':'new-metric','title':'Count','type':'metric','data':{'value':42}}]}
    response=client.post('/api/components/register',json=upload)
    assert response.status_code==201
    after=client.get('/api/components').json()
    assert after['components'][:len(before['components'])]==before['components']
    assert len(after['components'])==len(before['components'])+2
    assert after['widgets']==before['widgets']
    assert main.LAYOUT.read_bytes()==saved
    assert client.get('/widget/new-note').status_code==200

@pytest.mark.parametrize('components,status',[
    ([{'id':'note','title':'Conflict','type':'text'}],409),
    ([{'id':'new','title':'One','type':'text'},{'id':'new','title':'Two','type':'text'}],409),
    ([{'id':'new','title':'Bad','type':'list','data':{'items':[None]}}],422),
    ([],422),
])
def test_registration_failure_is_atomic(client,components,status):
    before=main.CONFIG.read_bytes()
    assert client.post('/api/components/register',json={'components':components}).status_code==status
    assert main.CONFIG.read_bytes()==before


def test_rename_preserves_identity_content_and_layout(client):
    before=client.get('/api/components').json()
    client.put('/api/layout',json={'widgets':before['widgets']})
    saved=main.LAYOUT.read_bytes()
    response=client.patch('/api/components/note',json={'title':'  Renamed note  '})
    assert response.status_code==200
    after=client.get('/api/components').json()
    expected=json.loads(json.dumps(before))
    next(c for c in expected['components'] if c['id']=='note')['title']='Renamed note'
    assert after==expected
    assert main.LAYOUT.read_bytes()==saved
    assert client.get('/widget/note').status_code==200

@pytest.mark.parametrize('id,title,status',[('missing','Name',404),('note','   ',422),('note','x'*201,422)])
def test_invalid_rename_preserves_file(client,id,title,status):
    before=main.CONFIG.read_bytes()
    assert client.patch('/api/components/'+id,json={'title':title}).status_code==status
    assert main.CONFIG.read_bytes()==before
