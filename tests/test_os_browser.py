from pathlib import Path
from playwright.sync_api import expect
from test_browser import server

def start(page,server):
    page.set_viewport_size({'width':1440,'height':960})
    page.goto(server)
    expect(page.get_by_test_id('app-dashboard')).to_be_visible()

def test_windows_context_and_geometry(page,server):
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    start(page,server)
    page.get_by_test_id('app-trend').click()
    graph=page.locator('.os-window[data-app=trend]')
    expect(graph.locator('canvas')).to_be_visible()
    page.get_by_test_id('app-note').click()
    expect(page.locator('.os-window')).to_have_count(2)
    note=page.locator('.os-window[data-app=note]')
    before=note.bounding_box()
    head=note.locator('.window-titlebar').bounding_box()
    page.mouse.move(head['x']+220,head['y']+22);page.mouse.down();page.mouse.move(head['x']+350,head['y']+72,steps=15);page.mouse.up()
    after=note.bounding_box()
    assert after['x']>before['x']+80
    page.mouse.move(after['x']+after['width']-3,after['y']+after['height']/2);page.mouse.down();page.mouse.move(after['x']+after['width']+65,after['y']+after['height']/2,steps=15);page.mouse.up()
    assert note.bounding_box()['width']>after['width']+40
    page.get_by_role('button',name='最小化 工作備註',exact=True).click()
    expect(note).to_be_hidden()
    page.get_by_test_id('app-note').click();expect(note).to_be_visible()
    page.get_by_role('button',name='放大 工作備註',exact=True).click()
    assert note.bounding_box()['width']>1400
    page.get_by_role('button',name='放大 工作備註',exact=True).click()
    page.get_by_role('button',name='關閉 工作備註',exact=True).click()
    page.get_by_role('button',name='顯示桌面',exact=True).click()
    page.get_by_test_id('app-note').click(button='right')
    page.get_by_text('開啟新視窗',exact=True).click()
    page.get_by_role('button',name='顯示桌面',exact=True).click()
    expect(page.get_by_role('navigation',name='Dock',exact=True)).to_have_count(0)
    page.reload();expect(page.get_by_role('navigation',name='Dock',exact=True)).to_have_count(0)
    page.get_by_test_id('app-dashboard').click()
    page.screenshot(path='test-results/app-os-desktop.png')
    assert not errors

def test_registry_register_rename_remove(page,server):
    start(page,server);page.get_by_test_id('app-manager').click()
    manager=page.locator('.os-window[data-app=manager]')
    manager.get_by_label('組件 JSON',exact=True).fill('{"components":[{"id":"hello","title":"Hello","type":"text","data":{"text":"hello world"}}]}')
    manager.get_by_role('button',name='註冊組件',exact=True).click()
    expect(page.get_by_test_id('app-hello')).to_be_attached()
    manager.get_by_label('名稱 hello',exact=True).fill('測試組件')
    manager.get_by_role('button',name='保存 hello',exact=True).click()
    expect(page.get_by_test_id('app-hello')).to_contain_text('測試組件')
    manager.get_by_role('button',name='刪除 hello',exact=True).click()
    manager.get_by_role('button',name='確認刪除',exact=True).click()
    expect(page.get_by_test_id('app-hello')).to_have_count(0)

def test_mobile_long_press_and_switch(page,server,browser):
    context=browser.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
    mobile=context.new_page();mobile.goto(server)
    icon=mobile.get_by_test_id('app-note');expect(icon).to_be_visible()
    icon.dispatch_event('pointerdown',{'pointerType':'touch','clientX':150,'clientY':500,'pageX':150,'pageY':500})
    expect(mobile.get_by_text('管理此組件',exact=True)).to_be_visible(timeout=3000)
    icon.dispatch_event('pointerup',{'pointerType':'touch'})
    expect(mobile.locator('.os-window')).to_have_count(0)
    mobile.get_by_text('開啟',exact=True).click()
    win=mobile.locator('.os-window[data-app=note]');expect(win).to_be_visible()
    assert win.bounding_box()['width']==390
    expect(mobile.locator('.traffic')).to_have_count(0)
    expect(mobile.get_by_text('開啟新視窗',exact=True)).to_have_count(0)
    mobile.get_by_role('navigation',name='iPhone 導覽').get_by_role('button',name='返回主畫面',exact=True).click()
    mobile.get_by_test_id('app-trend').tap()
    expect(mobile.locator('.os-window[data-app=trend] canvas')).to_be_visible()
    expect(win).to_be_hidden()
    mobile.get_by_role('button',name='顯示最近 APP',exact=True).click()
    mobile.get_by_role('button',name='返回 工作備註',exact=True).click()
    expect(win).to_be_visible()
    expect(mobile.locator('.os-window[data-app=trend]')).to_be_hidden()
    mobile.get_by_role('button',name='顯示最近 APP',exact=True).click()
    mobile.get_by_role('button',name='結束 工作備註',exact=True).click()
    expect(win).to_have_count(0)
    mobile.get_by_role('button',name='返回 匯入趨勢（示意）',exact=True).click()
    assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
    mobile.screenshot(path='test-results/app-os-mobile.png')
    context.close()
