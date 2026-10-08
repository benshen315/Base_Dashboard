'use strict';
const $=s=>document.querySelector(s);
const status=$('#status');
const detached=new Map();
let grid,config,catalog=new Map(),locked=false,pendingPopup=null,dragging=false,lastPointer=null;
const singleId=location.pathname.startsWith('/widget/')?decodeURIComponent(location.pathname.slice(8)):null;
const channel='BroadcastChannel' in window?new BroadcastChannel('olit-dashboard'):null;
function node(tag,className,text){const n=document.createElement(tag);if(className)n.className=className;if(text!==undefined)n.textContent=String(text);return n}
function message(s){status.textContent=s}
async function api(url,options={}){
 const r=await fetch(url,options);if(!r.ok){let detail;try{detail=(await r.json()).detail}catch{}throw Error(typeof detail==='string'?detail:'JSON 資料格式不正確或 API 失敗（'+r.status+'）')}return r.json();
}
function drawBody(c,body){
 body.replaceChildren();const d=c.data||{};
 if(c.type==='metric'){body.append(node('div','metric',d.value??'—'),node('p','muted',d.unit??''),node('p','muted',d.description??''));}
 else if(c.type==='text'){body.append(node('p','',d.text??''));}
 else if(c.type==='list'){for(const item of Array.isArray(d.items)?d.items:[]){const row=node('div','row');row.append(node('span','',item.label??''),node('span','pill',item.value??''));body.append(row)}}
 else if(c.type==='bar'){
  const bars=node('div','bars');const values=Array.isArray(d.values)?d.values:[];const numbers=values.map(v=>Number.isFinite(Number(v))?Math.max(0,Number(v)):0);const max=Math.max(1,...numbers);
  numbers.forEach((v,i)=>{const bar=node('div','bar');const fill=node('i');fill.style.height=(v/max*85)+'%';fill.title=String(v);bar.append(fill,node('span','',d.labels?.[i]??i+1));bars.append(bar)});body.append(bars);
 }else if(c.type==='iframe'){
  const url=String(d.url||'');if(!/^(https?:\/\/|\/(?!\/))/.test(url)){body.append(node('p','muted','iframe URL 無效'));return}
  const frame=node('iframe','frame');frame.src=url;frame.title=c.title;frame.setAttribute('allow','fullscreen');body.append(frame);
 }else if(c.type==='map'){
  const map=node('div','map');map.style.height='100%';
  // Fixed illustration; imported JSON is never evaluated as HTML or JavaScript.
  map.innerHTML='<svg viewBox="0 0 600 220" aria-label="示意地圖"><path d="M-20 170 Q120 30 270 110 T620 50" fill="none" stroke="#214c64" stroke-width="30"/><path d="M-20 170 Q120 30 270 110 T620 50" fill="none" stroke="#65ddd0" stroke-width="4" stroke-dasharray="10 5"/><g fill="#fbb66c"><circle cx="120" cy="98" r="7"/><circle cx="300" cy="119" r="7"/><circle cx="475" cy="102" r="7"/></g></svg>';
  map.append(node('span','map-label',d.caption??'靜態地圖示意'));body.append(map);
 }
}
async function full(panel){
 try{if(document.fullscreenElement){await document.exitFullscreen();return}if(panel.classList.contains('expanded')){panel.classList.remove('expanded');return}if(panel.requestFullscreen){await panel.requestFullscreen()}else{panel.classList.add('expanded');message('已放大至網頁範圍，Esc 可退出。')}}catch{panel.classList.add('expanded');message('瀏覽器未允許全螢幕，已放大至網頁範圍；Esc 可退出。')}
}
function button(text,action){const b=node('button','',text);b.type='button';b.addEventListener('pointerdown',e=>e.stopPropagation());b.addEventListener('mousedown',e=>e.stopPropagation());b.onclick=e=>{e.stopPropagation();action()};return b}
function panel(c,instanceId,standalone=false){
 const p=node('div','grid-stack-item-content');const head=node('div','panel-head');head.append(node('span','panel-title',c.title));const actions=node('div','actions');const body=node('div','body');
 if(c.fullscreen!==false)actions.append(button('全螢幕',()=>full(p)));
 if(standalone){actions.append(button('返回工作台',()=>{if(channel&&new URLSearchParams(location.search).get('owner')){channel.postMessage({action:'return',instance:instanceId,owner:new URLSearchParams(location.search).get('owner')});window.close();setTimeout(()=>location.assign('/'),100)}else location.assign('/')}));}
 else{
  if(c.popout!==false)actions.append(button('獨立視窗',()=>popout(instanceId)));
  const remove=button('×',()=>{if(locked)return;closeDetached(instanceId);grid.removeWidget(p.closest('.grid-stack-item'));message('已移除組件。')});remove.className='remove';remove.disabled=locked;actions.append(remove);
 }
 head.append(actions);p.append(head,body);drawBody(c,body);return p;
}
const owner=crypto.randomUUID?crypto.randomUUID():String(Date.now())+Math.random();
function findItem(id){return Array.from(document.querySelectorAll('.grid-stack-item')).find(e=>e.gridstackNode?.id===id)}
function closeDetached(id){const state=detached.get(id);if(state){try{state.win.close()}catch{}detached.delete(id)}}
function restore(id){const el=findItem(id);const state=detached.get(id);detached.delete(id);if(el){const c=catalog.get(el.dataset.component);if(c)el.querySelector('.body')&&drawBody(c,el.querySelector('.body'))}if(state)message('組件已返回工作台。')}
function popout(id){
 const el=findItem(id);if(!el)return;const c=catalog.get(el.dataset.component);if(!c||c.popout===false)return;
 if(detached.has(id)){detached.get(id).win.focus();return}
 const url='/widget/'+encodeURIComponent(c.id)+'?instance='+encodeURIComponent(id)+'&owner='+encodeURIComponent(owner);
 const win=window.open(url,'olit_'+owner+'_'+id,'popup,width=1000,height=700,resizable=yes,scrollbars=yes');
 if(!win){pendingPopup=id;$('#retry-popup').hidden=false;message('新視窗被瀏覽器阻擋，請點「點此開啟獨立視窗」。');return}
 detached.set(id,{win});pendingPopup=null;$('#retry-popup').hidden=true;
 const body=el.querySelector('.body');body.replaceChildren();const placeholder=node('div','detached');placeholder.append(node('p','','此組件已移至獨立視窗'),button('切換至視窗',()=>win.focus()),button('收回組件',()=>{closeDetached(id);restore(id)}));body.append(placeholder);message('已開啟獨立視窗，可手動移到另一個螢幕。');
}
if(channel)channel.onmessage=e=>{const d=e.data;if(d?.action==='return'&&d.owner===owner){closeDetached(d.instance);restore(d.instance)}};
setInterval(()=>{for(const [id,state]of detached){if(state.win.closed)restore(id)}},800);
window.addEventListener('pagehide',()=>{for(const id of detached.keys())closeDetached(id)});
$('#retry-popup').onclick=()=>{if(pendingPopup)popout(pendingPopup)};
function clearPanels(){for(const id of detached.keys())closeDetached(id);grid.removeAll()}
function add(w){
 const c=catalog.get(w.component);if(!c)throw Error('組件不存在：'+w.component);
 const el=node('div','grid-stack-item');el.dataset.component=w.component;
 for(const name of ['id','x','y','w','h'])if(w[name]!==undefined)el.setAttribute('gs-'+name,String(w[name]));
 el.append(panel(c,w.id));grid.el.append(el);grid.makeWidget(el);
}
function render(items){clearPanels();grid.batchUpdate();try{items.forEach(add)}finally{grid.batchUpdate(false)}syncLock()}
function layout(){return grid.save(false).map(({id,x,y,w,h})=>({id,component:findItem(id).dataset.component,x,y,w,h}))}
function syncLock(){grid.setStatic(locked);$('#add').disabled=locked;$('.grid-stack').querySelectorAll('.remove').forEach(b=>b.disabled=locked)}
function setConfig(data){config=data;catalog=new Map(data.components.map(c=>[c.id,c]));$('#title').textContent=data.title;$('#catalog').replaceChildren(...data.components.map(c=>{const o=node('option','',c.title);o.value=c.id;return o}));}
function inZone(p){if(!p)return false;const r=$('#drop-zone').getBoundingClientRect();return p.x>=r.left&&p.x<=r.right&&p.y>=r.top&&p.y<=r.bottom}
function pointer(e){const point=e.touches?.[0]??e;lastPointer={x:point.clientX,y:point.clientY};if(dragging)$('#drop-zone').classList.toggle('active',inZone(lastPointer))}
['pointermove','mousemove','touchmove'].forEach(type=>document.addEventListener(type,pointer,{passive:true,capture:true}));
async function start(){
 try{
  const data=await api('/api/components');setConfig(data);
  if(singleId){
   document.body.classList.add('standalone');const c=catalog.get(singleId);if(!c)throw Error('組件不存在');$('#title').textContent=c.title;const single=$('#single');single.hidden=false;single.className='single-panel';single.append(panel(c,new URLSearchParams(location.search).get('instance')||singleId,true));single.firstChild.style.height='100%';message('獨立組件頁面 · 內容由 components.json 載入');return;
  }
  if(!window.GridStack)throw Error('GridStack 本地資源載入失敗，請確認 static/vendor/gridstack 檔案完整');
  grid=GridStack.init({column:12,cellHeight:88,margin:8,minRow:6,draggable:{handle:'.panel-head',cancel:'button,iframe,input,select,textarea'},resizable:{handles:'se'}});
  render(config.widgets);message('已載入 components.json。拖曳標題列，或按全螢幕／獨立視窗。');
  grid.on('dragstart',()=>{dragging=true;lastPointer=null;$('#drop-zone').classList.remove('idle')});
  grid.on('dragstop',(event,el)=>{const hit=inZone(lastPointer);dragging=false;$('#drop-zone').className='popout-zone idle';if(hit)popout(el.gridstackNode.id)});
  grid.on('change',()=>message('版面已變更，按保存版面保留設定。'));
  $('#add').onclick=()=>{const id=$('#catalog').value;add({id:id+'-'+Date.now(),component:id,w:4,h:3});syncLock();message('已加入組件。')};
  $('#save').onclick=async()=>{try{await api('/api/layout',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({widgets:layout()})});message('版面已保存至伺服器。')}catch(e){message(e.message)}};
  $('#load').onclick=async()=>{try{const d=await api('/api/layout');render(d.widgets);message('已還原伺服器版面。')}catch(e){message(e.message)}};
  $('#reset').onclick=()=>{render(config.widgets);message('已還原 JSON 預設版面，保存後才覆寫已保存版面。')};
  $('#lock').onclick=e=>{locked=!locked;syncLock();e.target.textContent=locked?'解鎖版面':'鎖定版面';message(locked?'版面已鎖定。':'版面已解鎖。')};
  $('#dashboard-full').onclick=()=>full(document.documentElement);
  $('#import').onclick=()=>$('#file').click();
  $('#file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>2*1024*1024)throw Error('JSON 檔案不可超過 2 MB');const d=JSON.parse(await file.text());const validated=await api('/api/components',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});setConfig(validated);render(validated.widgets);message('已匯入組件 JSON 並保存至 data/components.json。')}catch(error){message(error.message)}finally{e.target.value=''}};
  $('#config-export').onclick=()=>{const payload={...config,widgets:layout()};const url=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));const a=node('a');a.href=url;a.download='dashboard.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
 }catch(e){message(e.message);document.querySelectorAll('nav button').forEach(b=>b.disabled=true)}
}
window.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll('.expanded').forEach(el=>el.classList.remove('expanded'))});
start();
