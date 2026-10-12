export const builtins=[
 {id:'dashboard',title:'總覽',icon:'pi-th-large',color:'blue',kind:'dashboard'},
 {id:'manager',title:'組件管理',icon:'pi-box',color:'violet',kind:'manager'},
 {id:'settings',title:'桌面設定',icon:'pi-cog',color:'slate',kind:'settings'}
];
const appearance={metric:['pi-chart-pie','blue'],bar:['pi-chart-bar','green'],map:['pi-map','teal'],list:['pi-list','orange'],text:['pi-file-edit','yellow'],iframe:['pi-globe','violet']};
export function createRegistry(components){return [...builtins,...components.map(c=>({...c,kind:'component',icon:appearance[c.type][0],color:c.id==='alerts'?'red':appearance[c.type][1]}))];}
