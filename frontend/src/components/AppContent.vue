<script setup>
import {useOS} from '../store';import WidgetContent from './WidgetContent.vue';import ComponentManager from './ComponentManager.vue';import Button from 'primevue/button';
defineProps({app:Object});const os=useOS();
</script>
<template>
 <ComponentManager v-if="app.kind==='manager'"/>
 <div v-else-if="app.kind==='settings'" class="settings"><span class="eyebrow">PERSONALIZE YOUR SPACE</span><h2>你的桌面，你的節奏。</h2><p class="muted">壁紙偏好保存在此瀏覽器。</p><h3>桌面壁紙</h3><div class="flex gap-3"><button v-for="theme in ['ocean','dusk']" :key="theme" :class="['wallpaper-option',theme,{selected:os.wallpaper===theme}]" @click="os.wallpaper=theme;os.savePreferences()">{{theme==='ocean'?'海岸藍':'暮光紫'}}</button></div><h3>操作方式</h3><p>點按 APP 開啟；右鍵或長按查看操作選單。電腦可拖曳標題列與視窗邊緣；手機以滿版 APP 呈現，使用底部主畫面按鈕與最近 APP 切換。</p><Button label="返回主畫面" icon="pi pi-home" @click="os.showDesktop()"/><p class="muted mt-4">第一版 · 示意資料 · 尚未連接 OlitGlobal 即時資料</p></div>
 <div v-else-if="app.kind==='dashboard'" class="overview"><span class="eyebrow">WORKSPACE OVERVIEW</span><h2>所有資訊，一眼掌握。</h2><p class="muted">來自 APP Registry 的工作組件 · 示意資料</p><div class="overview-grid"><button v-for="c in os.config?.components" :key="c.id" class="overview-card" @click="os.open(c.id)"><h3>{{c.title}}</h3><WidgetContent :component="c"/></button></div></div>
 <WidgetContent v-else :component="app"/>
</template>
