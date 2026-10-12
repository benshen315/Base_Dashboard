<script setup>
import {ref,onMounted,onBeforeUnmount,watch,nextTick} from 'vue';
import {init,use} from 'echarts/core';
import {BarChart} from 'echarts/charts';
import {GridComponent,TooltipComponent} from 'echarts/components';
import {CanvasRenderer} from 'echarts/renderers';
use([BarChart,GridComponent,TooltipComponent,CanvasRenderer]);
const props=defineProps({component:Object});const graph=ref(null);let chart,observer;
async function render(){await nextTick();if(props.component.type!=='bar'||!graph.value)return;chart||=init(graph.value);chart.setOption({grid:{left:40,right:20,top:30,bottom:35},tooltip:{trigger:'axis',backgroundColor:'#122235',borderColor:'#35516a',textStyle:{color:'#d9e6f5'}},xAxis:{type:'category',axisLabel:{color:'#a6bdd3'},axisLine:{lineStyle:{color:'#35516a'}},data:props.component.data.labels||[]},yAxis:{type:'value',axisLabel:{color:'#a6bdd3'},splitLine:{lineStyle:{color:'#26394e'}}},series:[{type:'bar',data:props.component.data.values||[],itemStyle:{color:'#50bfe9',borderRadius:[7,7,0,0]},barMaxWidth:36}]});}
onMounted(()=>{render();observer=new ResizeObserver(()=>chart?.resize());if(graph.value)observer.observe(graph.value)});watch(()=>props.component,render,{deep:true});onBeforeUnmount(()=>{observer?.disconnect();chart?.dispose()});
</script>
<template>
 <div v-if="component.type==='metric'" class="metric"><span class="eyebrow">{{component.title}}</span><strong>{{component.data.value??'—'}}</strong><span>{{component.data.unit}}</span><p>{{component.data.description}}</p></div>
 <div v-else-if="component.type==='bar'" ref="graph" class="chart" role="img" :aria-label="component.title+' 長條圖'"></div>
 <div v-else-if="component.type==='text'" class="note-content"><i class="pi pi-file-edit"></i><p>{{component.data.text}}</p></div>
 <div v-else-if="component.type==='list'" class="object-list"><div v-for="(item,i) in component.data.items" :key="i"><span><i class="pi pi-box"></i> {{item.label}}</span><b>{{item.value}}</b></div></div>
 <iframe v-else-if="component.type==='iframe'" :src="component.data.url" :title="component.title" sandbox="allow-scripts allow-forms" referrerpolicy="no-referrer" class="embed"></iframe>
 <div v-else class="map-preview"><div class="map-grid"></div><i class="pi pi-map-marker marker m1"></i><i class="pi pi-map-marker marker m2"></i><span class="map-caption">場域地圖 · 示意<br>{{component.data.caption}}</span></div>
</template>
