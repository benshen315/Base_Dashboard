import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
import pytest
from playwright.sync_api import expect

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture
def server(tmp_path_factory):
    data=tmp_path_factory.mktemp('dashboard-data')
    (data/'components.json').write_bytes((ROOT/'dashboard.example.json').read_bytes())
    with socket.socket() as s:
        s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    url=f'http://127.0.0.1:{port}'
    env={**os.environ,'BASE_DASHBOARD_DATA_DIR':str(data)}
    proc=subprocess.Popen([sys.executable,'-m','uvicorn','main:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            if proc.poll() is not None:raise RuntimeError('FastAPI startup failed')
            try:
                urllib.request.urlopen(url+'/api/components',timeout=1).close();break
            except OSError:time.sleep(.1)
        else:raise RuntimeError('FastAPI startup timed out')
        yield url
    finally:
        proc.terminate()
        try:proc.wait(timeout=5)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()

def open_dashboard(page,server):
    page.set_viewport_size({'width':1440,'height':1200})
    cfg=json.loads((ROOT/'dashboard.example.json').read_text())
    assert page.request.put(server+'/api/components',data=cfg).ok
    page.goto(server)
    page.locator('#workspace-tab').click()
    expect(page.locator('.grid-stack-item')).to_have_count(6)
    page.wait_for_function('Math.abs(document.querySelector("[gs-id=map]").getBoundingClientRect().height - 264) < 1')
    return cfg

def item(page,id='map'):
    return page.locator(f'.grid-stack-item[gs-id="{id}"]')

def test_add_remove_and_json_file_import(page,server,tmp_path):
    cfg=open_dashboard(page,server)
    page.locator('#catalog').select_option('note');page.locator('#add').click()
    expect(page.locator('.grid-stack-item')).to_have_count(7)
    page.locator('.grid-stack-item').last.locator('.remove').click()
    expect(page.locator('.grid-stack-item')).to_have_count(6)
    cfg['title']='Imported JSON';cfg['components'][0]['title']='Map from JSON'
    path=tmp_path/'config.json';path.write_text(json.dumps(cfg))
    page.locator('#file').set_input_files(path)
    expect(page.locator('#title')).to_have_text('Imported JSON')
    expect(item(page).locator('.panel-title')).to_have_text('Map from JSON')

def test_drag_resize_and_save_restore(page,server):
    open_dashboard(page,server)
    card=item(page,'note');before=card.bounding_box()
    head=card.locator('.panel-title').bounding_box()
    page.mouse.move(head['x']+10,head['y']+10);page.mouse.down();page.mouse.move(head['x']-240,head['y']+190,steps=20);page.mouse.up()
    page.wait_for_timeout(300)
    after=card.bounding_box()
    assert (before['x'],before['y'])!=(after['x'],after['y'])
    handle=card.locator('.ui-resizable-se').bounding_box()
    old_width=after['width']
    page.mouse.move(handle['x']+handle['width']/2,handle['y']+handle['height']/2);page.mouse.down();page.mouse.move(handle['x']+handle['width']/2+140,handle['y']+handle['height']/2+90,steps=20);page.mouse.up()
    page.wait_for_timeout(300)
    assert card.bounding_box()['width']>old_width
    page.locator('#save').click();expect(page.locator('#status')).to_contain_text('版面已保存')
    saved=page.request.get(server+'/api/layout').json()
    page.locator('#reset').click();page.locator('#load').click();expect(page.locator('#status')).to_have_text('已還原伺服器版面。')
    current=page.evaluate('grid.save(false).map(({id,x,y,w,h})=>({id,component:findItem(id).dataset.component,x,y,w,h}))')
    assert sorted(current,key=lambda w:w['id'])==sorted(saved['widgets'],key=lambda w:w['id'])

def test_lock_prevents_layout_drag(page,server):
    open_dashboard(page,server)
    page.locator('#lock').click();expect(page.locator('#add')).to_be_disabled()
    expect(item(page).locator('.remove')).to_be_disabled()
    before=item(page).bounding_box();head=item(page).locator('.panel-title').bounding_box()
    page.mouse.move(head['x']+10,head['y']+10);page.mouse.down();page.mouse.move(head['x']+200,head['y']+100,steps=10);page.mouse.up()
    assert item(page).bounding_box()==before

def test_fullscreen_and_exit(page,server):
    open_dashboard(page,server)
    card=item(page)
    card.get_by_role('button',name='全螢幕',exact=True).click()
    page.wait_for_function('document.fullscreenElement || document.querySelector(".expanded")')
    fullscreen=page.evaluate('!!document.fullscreenElement')
    if fullscreen:card.get_by_role('button',name='全螢幕',exact=True).click()
    else:page.keyboard.press('Escape')
    page.wait_for_function('!document.fullscreenElement && !document.querySelector(".expanded")')

def test_popout_close_restores_component(page,server):
    open_dashboard(page,server)
    with page.expect_popup() as popup_info:
        item(page).get_by_role('button',name='獨立視窗',exact=True).click()
    popup=popup_info.value;popup.wait_for_load_state()
    expect(popup.locator('.single-panel .panel-title')).to_have_text('場域地圖（示意）')
    expect(item(page).locator('.detached')).to_be_visible()
    popup.close()
    expect(item(page).locator('.map')).to_be_visible(timeout=5000)

def test_popout_return_button(page,server):
    open_dashboard(page,server)
    with page.expect_popup() as info:item(page).get_by_role('button',name='獨立視窗',exact=True).click()
    popup=info.value
    popup.get_by_role('button',name='返回工作台').click()
    expect(item(page).locator('.map')).to_be_visible(timeout=5000)

def test_blocked_popup_retries_without_losing_component(page,server):
    open_dashboard(page,server)
    page.evaluate('window.originalOpen=window.open;window.open=()=>null')
    item(page).get_by_role('button',name='獨立視窗',exact=True).click()
    expect(page.locator('#retry-popup')).to_be_visible()
    expect(item(page).locator('.map')).to_be_visible()
    page.evaluate('window.open=window.originalOpen')
    with page.expect_popup() as info:page.locator('#retry-popup').click()
    info.value.close()
    expect(item(page).locator('.map')).to_be_visible(timeout=5000)

def test_drag_zone_removed(page,server):
    open_dashboard(page,server)
    expect(page.locator('#drop-zone')).to_have_count(0)
    expect(item(page).get_by_role('button',name='獨立視窗',exact=True)).to_be_visible()

def test_invalid_json_import_keeps_dashboard_usable(page,server,tmp_path):
    original=open_dashboard(page,server)
    bad=json.loads(json.dumps(original))
    bad['components'][0].update(type='list',data={'items':[None]})
    path=tmp_path/'invalid.json';path.write_text(json.dumps(bad))
    page.locator('#file').set_input_files(path)
    expect(page.locator('#status')).to_contain_text('清單每一筆必須是物件')
    expect(page.locator('.grid-stack-item')).to_have_count(6)
    expect(item(page).locator('.map')).to_be_visible()
    assert page.request.get(server+'/api/components').json()['components']==[
        {**component,'fullscreen':True,'popout':True} for component in original['components']
    ]
    page.locator('#catalog').select_option('note');page.locator('#add').click()
    expect(page.locator('.grid-stack-item')).to_have_count(7)

def test_refresh_automatically_restores_saved_layout(page,server):
    cfg=open_dashboard(page,server)
    expect(page.locator('#status')).to_have_text('已載入 JSON 預設版面。')
    saved=json.loads(json.dumps(cfg['widgets']))
    next(w for w in saved if w['id']=='note')['h']=3
    assert page.request.put(server+'/api/layout',data={'widgets':saved}).ok
    page.reload()
    page.locator('#workspace-tab').click()
    expect(page.locator('#status')).to_have_text('已自動還原保存的版面。')
    expect(item(page,'note')).to_have_attribute('gs-h','3')

def test_saved_empty_dashboard_stays_empty_after_refresh(page,server):
    open_dashboard(page,server)
    assert page.request.put(server+'/api/layout',data={'widgets':[]}).ok
    page.reload()
    page.locator('#workspace-tab').click()
    expect(page.locator('#status')).to_have_text('已自動還原保存的版面。')
    expect(page.locator('.grid-stack-item')).to_have_count(0)
    page.locator('#catalog').select_option('note');page.locator('#add').click()
    expect(page.locator('.grid-stack-item')).to_have_count(1)

def test_stale_saved_layout_uses_config_defaults(page,server):
    cfg=open_dashboard(page,server)
    assert page.request.put(server+'/api/layout',data={'widgets':cfg['widgets']}).ok
    cfg['components']=[c for c in cfg['components'] if c['id']!='map']
    cfg['widgets']=[w for w in cfg['widgets'] if w['component']!='map']
    assert page.request.put(server+'/api/components',data=cfg).ok
    page.reload()
    page.locator('#workspace-tab').click()
    expect(page.locator('#status')).to_contain_text('保存版面引用了已移除的組件')
    expect(page.locator('.grid-stack-item')).to_have_count(5)
    assert page.request.get(server+'/api/layout').status==409
    page.locator('#save').click();expect(page.locator('#status')).to_contain_text('版面已保存')
    assert page.request.get(server+'/api/layout').ok

def test_menu_upload_register_and_add_preserves_layout(page,server,tmp_path):
    open_dashboard(page,server)
    original=page.evaluate('layout()')
    page.locator('#menu-open').click()
    component={'id':'uploaded-note','title':'Uploaded note','type':'text','data':{'text':'Registered content'}}
    path=tmp_path/'component.json';path.write_text(json.dumps(component))
    page.locator('#component-file').set_input_files(path)
    expect(page.locator('#upload-preview')).to_be_visible()
    page.locator('#component-register').click()
    expect(page.locator('#menu-status')).to_contain_text('已成功註冊 1 個組件')
    assert page.evaluate('layout()')==original
    row=page.locator('.registry-row').filter(has_text='Uploaded note')
    row.get_by_role('button',name='加入工作台').click()
    expect(page.locator('.grid-stack-item')).to_have_count(7)
    expect(page.locator('.grid-stack-item').last.locator('.body')).to_have_text('Registered content')
    page.locator('#save').click()
    expect(page.locator('#status')).to_contain_text('版面已保存')
    page.reload()
    page.locator('#workspace-tab').click()
    expect(page.locator('.grid-stack-item')).to_have_count(7)
    page.locator('#menu-open').click()
    page.locator('#component-file').set_input_files(path)
    page.locator('#component-register').click()
    expect(page.locator('#menu-status')).to_contain_text('組件 ID 已註冊')
    expect(page.locator('.registry-row')).to_have_count(7)

def test_menu_invalid_upload_and_lock(page,server,tmp_path):
    open_dashboard(page,server)
    page.locator('#lock').click();page.locator('#menu-open').click()
    expect(page.locator('.registry-row button').first).to_be_disabled()
    path=tmp_path/'bad.json';path.write_text(json.dumps({'id':'bad','title':'Bad data','type':'bar','data':{'values':['wrong']}}))
    page.locator('#component-file').set_input_files(path);page.locator('#component-register').click()
    expect(page.locator('#menu-status')).to_contain_text('values 必須是有限數字')
    expect(page.locator('.registry-row')).to_have_count(6)
    page.keyboard.press('Escape')
    expect(page.locator('#component-menu')).not_to_be_visible()

def test_app_desktop_launcher_and_mobile(page,server):
    open_dashboard(page,server)
    page.locator('#desktop-tab').click()
    expect(page.locator('#desktop')).to_be_visible()
    expect(page.locator('#workspace')).not_to_be_visible()
    expect(page.locator('.app-tile')).to_have_count(6)
    page.screenshot(path='test-results/app-desktop.png',full_page=True)
    page.locator('.app-tile[data-component="note"]').click()
    expect(page.locator('#workspace')).to_be_visible()
    expect(page.locator('.grid-stack-item')).to_have_count(6)
    page.locator('#desktop-tab').click()
    page.locator('#lock').click()
    expect(page.locator('.app-tile').first).to_be_disabled()
    page.locator('#lock').click()
    page.set_viewport_size({'width':390,'height':844})
    expect(page.locator('.app-tile').first).to_be_visible()
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    page.screenshot(path='test-results/app-mobile.png',full_page=True)
    page.locator('#menu-open').click()
    expect(page.locator('#component-menu')).to_be_visible()


def test_component_manager_rename_cancel_and_popout_sync(page,server):
    open_dashboard(page,server)
    before=page.evaluate('layout()')
    with page.expect_popup() as info:item(page,'note').get_by_role('button',name='獨立視窗',exact=True).click()
    popup=info.value
    expect(popup.locator('.panel-title')).to_have_text('工作備註')
    page.get_by_role('button',name='組件管理',exact=True).click()
    expect(page.locator('#menu-title')).to_have_text('組件管理')
    row=page.locator('.registry-row[data-component="note"]')
    row.get_by_role('button',name='改名',exact=True).click()
    row.get_by_role('textbox',name='組件名稱').fill('Cancelled')
    row.get_by_role('button',name='取消',exact=True).click()
    expect(row).to_contain_text('工作備註')
    row.get_by_role('button',name='改名',exact=True).click()
    row.get_by_role('textbox',name='組件名稱').fill('   ')
    row.get_by_role('button',name='儲存名稱',exact=True).click()
    expect(row.locator('.rename-error')).to_have_text('組件名稱不可空白')
    row.get_by_role('textbox',name='組件名稱').fill('我的新筆記')
    row.get_by_role('button',name='儲存名稱',exact=True).click()
    expect(page.locator('#menu-status')).to_have_text('已更新組件名稱。')
    expect(row).to_contain_text('我的新筆記')
    expect(item(page,'note').locator('.panel-title')).to_have_text('我的新筆記')
    expect(popup.locator('.panel-title')).to_have_text('我的新筆記')
    assert page.evaluate('layout()')==before
    popup.close()
    page.locator('#menu-close').click()
    page.reload()
    expect(page.locator('.app-tile[data-component="note"]')).to_contain_text('我的新筆記')
