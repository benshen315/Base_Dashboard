<script setup>
import {ref} from 'vue';
import Button from 'primevue/button';import InputText from 'primevue/inputtext';import Textarea from 'primevue/textarea';
import {useOS} from '../store';
const os=useOS(),message=ref(''),busy=ref(false),names=ref({}),file=ref(null),source=ref(JSON.stringify({components:[{id:'new-note',title:'新備註',type:'text',data:{text:'開始記錄工作'}}]},null,2));
async function run(action){busy.value=true;message.value='';try{await action();message.value='已保存'}catch(e){message.value=e.message}finally{busy.value=false}}
function upload(e){const f=e.target.files[0];if(f)run(async()=>{source.value=await f.text();await os.register(JSON.parse(source.value))});e.target.value=''}
function download(){const url=URL.createObjectURL(new Blob([JSON.stringify(os.config,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='components.json';a.click();URL.revokeObjectURL(url)}
const deleting=ref(null);
</script>
<template><div class="manager"><div class="flex justify-between items-center gap-3"><div><h2>組件管理</h2><p class="muted">APP Registry · {{os.config?.components.length}} 個組件</p></div><Button label="匯出" icon="pi pi-download" severity="secondary" @click="download"/></div>
 <p class="feedback" role="status">{{message}}</p>
 <div v-for="c in os.config?.components" :key="c.id" class="component-row"><div><b>{{c.title}}</b><small>{{c.id}} · {{c.type}}</small></div><InputText :model-value="names[c.id]??c.title" @update:model-value="names[c.id]=$event" :aria-label="'名稱 '+c.id"/><Button icon="pi pi-check" :aria-label="'保存 '+c.id" :disabled="busy" @click="run(()=>os.rename(c.id,names[c.id]??c.title))"/><Button icon="pi pi-trash" severity="danger" :aria-label="'刪除 '+c.id" :disabled="busy" @click="deleting=c.id"/></div>
 <div v-if="deleting" class="delete-confirm"><p>刪除 {{deleting}} 及其面板？</p><Button label="確認刪除" severity="danger" :disabled="busy" @click="run(async()=>{await os.remove(deleting);deleting=null})"/><Button label="取消" text @click="deleting=null"/></div>
 <h3>註冊新組件</h3><p class="muted">使用 JSON 註冊；每個 ID 必須唯一，內容由後端驗證。</p><Textarea v-model="source" rows="7" class="w-full font-mono" aria-label="組件 JSON"/><div class="flex gap-2 mt-3 flex-wrap"><Button label="註冊組件" icon="pi pi-plus" :disabled="busy" @click="run(()=>os.register(JSON.parse(source)))"/><Button label="上傳 JSON" severity="secondary" :disabled="busy" @click="file.click()"/><input ref="file" type="file" accept=".json,application/json" hidden @change="upload"/></div>
</div></template>
