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

@pytest.fixture(scope='session')
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
    expect(page.locator('.grid-stack-item')).to_have_count(6)
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
    page.locator('#reset').click();page.locator('#load').click();expect(page.locator('#status')).to_contain_text('已還原')
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

def test_drag_to_popout_zone(page,server):
    open_dashboard(page,server)
    head=item(page).locator('.panel-title').bounding_box()
    page.mouse.move(head['x']+20,head['y']+10);page.mouse.down()
    page.mouse.move(head['x']+30,head['y']+25,steps=4)
    zone=page.locator('#drop-zone').bounding_box()
    page.mouse.move(zone['x']+zone['width']/2,zone['y']+zone['height']/2,steps=20);page.mouse.up()
    page.wait_for_function('document.querySelector(".detached") || !document.querySelector("#retry-popup").hidden')
    if page.locator('#retry-popup').is_visible():
        with page.expect_popup() as info:page.locator('#retry-popup').click()
        info.value.close()
    else:
        item(page).get_by_role('button',name='收回組件').click()
    expect(item(page).locator('.map')).to_be_visible(timeout=5000)
