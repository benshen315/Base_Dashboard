import {beforeEach,describe,it,expect,vi} from 'vitest';
import {createPinia,setActivePinia} from 'pinia';
import {useOS} from './store';
beforeEach(()=>{setActivePinia(createPinia());vi.stubGlobal('innerWidth',1440);vi.stubGlobal('innerHeight',900);vi.stubGlobal('localStorage',{getItem:()=>null,setItem:vi.fn()})});
describe('Window manager',()=>{
 it('focuses existing instance, explicitly opens another, restores and closes',()=>{const os=useOS();const a=os.open('dashboard');expect(os.open('dashboard').id).toBe(a.id);expect(os.windows).toHaveLength(1);const b=os.open('dashboard',true);expect(b.id).not.toBe(a.id);os.minimize(b.id);expect(os.active.id).toBe(a.id);os.open('dashboard');os.focus(b.id);b.minimized=false;expect(os.active.id).toBe(b.id);os.toggleMax(b.id);expect(b.maximized).toBe(true);os.close(b.id);expect(os.windows).toHaveLength(1);os.showDesktop();expect(os.active).toBeUndefined()});
 it('rejects unknown apps and updates component registry without remounting identity',async()=>{const os=useOS();expect(os.open('unknown')).toBeUndefined();os.config={components:[{id:'note',title:'Old',type:'text',data:{}}]};os.open('note');vi.stubGlobal('fetch',vi.fn(async()=>({ok:true,json:async()=>({components:[{id:'note',title:'New',type:'text',data:{}}]})})));await os.rename('note','New');expect(os.apps.find(a=>a.id==='note').title).toBe('New');expect(os.windows[0].appId).toBe('note')});
 it('persists pin preferences and reports failed backend requests',async()=>{const os=useOS();os.pin('settings');expect(os.dock).toContain('settings');expect(localStorage.setItem).toHaveBeenCalled();vi.stubGlobal('fetch',vi.fn(async()=>({ok:false,status:409,json:async()=>({detail:'組件 ID 已註冊'})})));await expect(os.register({components:[]})).rejects.toThrow('組件 ID 已註冊')});
});
