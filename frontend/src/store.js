import { defineStore } from 'pinia';
import { createRegistry } from './registry';
export async function api(path,options={}){
 const response=await fetch(path,{...options,headers:{'Content-Type':'application/json',...options.headers}});
 if(!response.ok){let detail;try{detail=(await response.json()).detail}catch{};throw new Error(typeof detail==='string'?detail:`請求失敗 (${response.status})，請檢查輸入格式或連線`);}
 return response.json();
}
function preferences(){try{const p=JSON.parse(localStorage.getItem('olit.preferences')||'{}');return {dock:Array.isArray(p.dock)?p.dock.filter(x=>typeof x==='string'):['dashboard','map','trend','manager'],wallpaper:p.wallpaper==='dusk'?'dusk':'ocean'}}catch{return {dock:['dashboard','map','trend','manager'],wallpaper:'ocean'}}}
export const useOS=defineStore('os',{
 state:()=>({config:null,windows:[],serial:0,z:10,loading:true,error:'',...preferences()}),
 getters:{apps:s=>createRegistry(s.config?.components||[]),dockApps(){return this.apps.filter(a=>this.dock.includes(a.id))},active:s=>s.windows.filter(w=>!w.minimized).sort((a,b)=>b.z-a.z)[0]},
 actions:{
  async load(){this.loading=true;this.error='';try{this.config=await api('/api/components');this.windows=this.windows.filter(w=>this.apps.some(a=>a.id===w.appId))}catch(e){this.error=e.message}finally{this.loading=false}},
  open(appId,newInstance=false){if(!this.apps.some(a=>a.id===appId))return;const existing=this.windows.find(w=>w.appId===appId);if(existing&&!newInstance){existing.minimized=false;this.focus(existing.id);return existing}const offset=(this.serial%5)*28;const w={id:++this.serial,appId,x:Math.min(100+offset,Math.max(0,innerWidth-400)),y:100+offset,width:Math.min(700,innerWidth-32),height:Math.min(490,innerHeight-210),z:++this.z,minimized:false,maximized:false};this.windows.push(w);return this.windows[this.windows.length-1]},
  focus(id){const w=this.windows.find(w=>w.id===id);if(w)w.z=++this.z},
  close(id){this.windows=this.windows.filter(w=>w.id!==id)},
  minimize(id){const w=this.windows.find(w=>w.id===id);if(w)w.minimized=true},
  toggleMax(id){const w=this.windows.find(w=>w.id===id);if(w){w.maximized=!w.maximized;this.focus(id)}},
  showDesktop(){this.windows.forEach(w=>w.minimized=true)},
  pin(id){this.dock=this.dock.includes(id)?this.dock.filter(x=>x!==id):[...this.dock,id];this.savePreferences()},
  savePreferences(){try{localStorage.setItem('olit.preferences',JSON.stringify({dock:this.dock,wallpaper:this.wallpaper}))}catch{this.error='瀏覽器無法保存桌面偏好'}},
  async rename(id,title){this.config=await api(`/api/components/${id}`,{method:'PATCH',body:JSON.stringify({title})})},
  async register(value){this.config=await api('/api/components/register',{method:'POST',body:JSON.stringify(value)})},
  async remove(id){this.config=await api(`/api/components/${id}`,{method:'DELETE'});this.windows=this.windows.filter(w=>w.appId!==id);this.dock=this.dock.filter(x=>x!==id);this.savePreferences()}
 }
});
