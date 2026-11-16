# update.py — v23: NetLab полностью переписан (самодостаточный, всё работает сразу)
import ast, json, os, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v23_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()

NEW = r'''NETLAB_HTML = """<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NetLab — схемы ЛВС + симуляция</title>
<style>
:root{--bg:#0d1420;--panel:#141d2e;--panel2:#1b2740;--line:#26365a;--ink:#e8eefb;--mut:#8fa2c4;
--acc:#38bdf8;--acc2:#818cf8;--ok:#34d399;--warn:#fbbf24;--bad:#f87171;--mag:#f472b6;--pon:#2dd4bf}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:radial-gradient(1200px 600px at 80% -10%,#1a2742 0%,var(--bg) 60%);color:var(--ink);
font:14px/1.45 'Segoe UI',system-ui,Arial,sans-serif;overflow:hidden}
#top{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 12px;
background:linear-gradient(90deg,#101a2c,#182741 60%,#101a2c);border-bottom:1px solid var(--line);position:relative;z-index:5}
#top .brand{font-weight:700;letter-spacing:.4px;margin-right:8px;font-size:15px}
#top .brand em{color:var(--acc);font-style:normal}
button{font:600 12.5px 'Segoe UI',Arial;color:var(--ink);background:var(--panel2);border:1px solid var(--line);
border-radius:9px;padding:7px 11px;cursor:pointer;transition:transform .12s,filter .12s,background .12s}
button:hover{transform:translateY(-1px);filter:brightness(1.18)}
button:active{transform:translateY(0)}
button.p{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent}
button.g{background:linear-gradient(135deg,#059669,#10b981);border-color:transparent}
button.w{background:linear-gradient(135deg,#d97706,#f59e0b);border-color:transparent;color:#1a1206}
button.d{background:linear-gradient(135deg,#dc2626,#ef4444);border-color:transparent}
button.on{outline:2px solid var(--acc);outline-offset:1px}
#hint{color:var(--mut);font-size:12px;margin-left:auto}
#ctrl{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:7px 12px;background:var(--panel);
border-bottom:1px solid var(--line);position:relative;z-index:4}
#ctrl label{display:flex;align-items:center;gap:6px;color:var(--mut);font-size:12px;white-space:nowrap}
#ctrl input[type=range]{width:92px;accent-color:var(--acc)}
#ctrl input[type=checkbox]{accent-color:var(--ok);width:15px;height:15px}
#ctrl select{background:var(--panel2);color:var(--ink);border:1px solid var(--line);border-radius:7px;padding:4px 6px;font-size:12px}
#ctrl .val{color:var(--acc);font-variant-numeric:tabular-nums;min-width:30px;text-align:right}
#wrap{display:flex;gap:8px;padding:8px;height:calc(100% - 96px)}
#pal{width:186px;flex:none;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:10px;overflow-y:auto}
#pal h4{margin:4px 0 6px;font-size:11px;letter-spacing:1.2px;color:var(--mut);text-transform:uppercase}
#pal button{display:flex;width:100%;align-items:center;gap:8px;margin:4px 0;text-align:left;background:var(--panel2)}
#pal button i{font-style:normal;font-size:16px;width:20px;text-align:center}
#pal .tpl{border-color:#3b4c78;background:linear-gradient(135deg,#1c2a4a,#23345c)}
#stage{flex:1;position:relative;border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#0f1726}
#stage.light{background:#f4f7fc}
#stage.blue{background:#0b2036}
#stage.grid{background-image:linear-gradient(rgba(120,150,210,.14) 1px,transparent 1px),linear-gradient(90deg,rgba(120,150,210,.14) 1px,transparent 1px);background-size:24px 24px}
#stage.light.grid{background-image:linear-gradient(rgba(40,70,130,.10) 1px,transparent 1px),linear-gradient(90deg,rgba(40,70,130,.10) 1px,transparent 1px)}
#cv{width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#side{width:318px;flex:none;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:12px;overflow-y:auto}
#side h3{margin:2px 0 8px;font-size:13px;letter-spacing:.6px;color:var(--acc)}
#side h3.sim{color:var(--mag)}
#side .fld{margin:6px 0}
#side .fld span{display:block;color:var(--mut);font-size:11.5px;margin-bottom:3px}
#side input,#side select,#side textarea{width:100%;background:var(--panel2);border:1px solid var(--line);color:var(--ink);
border-radius:8px;padding:7px 9px;font-size:13px}
#side input:focus,#side select:focus,#side textarea:focus{outline:2px solid rgba(56,189,248,.4);border-color:var(--acc)}
#side hr{border:none;border-top:1px solid var(--line);margin:12px 0}
#log{background:#050a14;border:1px solid #1c2a44;border-radius:10px;color:#7dd3fc;font:12px/1.5 Consolas,monospace;
height:190px;overflow-y:auto;padding:8px;white-space:pre-wrap;margin-top:8px}
#log .ok{color:var(--ok)} #log .bad{color:var(--bad)} #log .warn{color:var(--warn)} #log .info{color:var(--mut)}
#status{display:flex;gap:16px;align-items:center;padding:6px 14px;background:var(--panel);border-top:1px solid var(--line);
color:var(--mut);font-size:12px;position:relative;z-index:4}
#status b{color:var(--acc);font-variant-numeric:tabular-nums}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;background:var(--panel2);border:1px solid var(--line)}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-track{background:var(--panel)}
::-webkit-scrollbar-thumb{background:#2c3d63;border-radius:8px;border:2px solid var(--panel)}
::-webkit-scrollbar-thumb:hover{background:var(--acc)}
*{scrollbar-width:thin;scrollbar-color:#2c3d63 var(--panel)}
#toast{position:fixed;left:50%;bottom:52px;transform:translateX(-50%) translateY(20px);opacity:0;pointer-events:none;
background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;font-weight:700;padding:10px 18px;border-radius:12px;
box-shadow:0 10px 30px rgba(14,165,233,.4);transition:all .25s;z-index:50}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
@media (max-width:980px){
 body{overflow:auto}
 #wrap{flex-direction:column;height:auto}
 #pal{width:100%;display:flex;flex-wrap:wrap;gap:4px;order:2}
 #pal h4{width:100%}
 #pal button{width:auto;flex:1 1 45%}
 #stage{order:1;height:56vh;min-height:380px}
 #side{width:100%;order:3}
 #hint{display:none}
}
@media print{#top,#ctrl,#pal,#side,#status,#toast{display:none!important}
 body{overflow:visible;background:#fff}
 #wrap{height:auto;padding:0}#stage{border:none;height:92vh;background:#fff!important}
}
</style></head>
<body>
<div id="top">
<span class="brand">🧪 <em>NetLab</em> · схемы ЛВС и симуляция трафика</span>
<button class="g" id="bSave">💾 Сохранить</button>
<button class="p" id="bOpen">📂 Открыть</button>
<button id="bDelScheme">🗑Scheme</button>
<button id="bSvg">⬇ SVG</button>
<button id="bPng">⬇ PNG</button>
<button id="bPrint">🖨</button>
<button class="w" id="bLink">🔗 Соединить</button>
<button id="bSel" class="on">🖱 Выбор</button>
<button id="bUndo">↩ Отмена</button>
<button class="d" id="bDel">✕ Удалить</button>
<span id="hint">ЛКМ по устройству — выбрать/тащить · фон — панорама · колесо — зум · Del — удалить · Ctrl+Z — отмена</span>
</div>
<div id="ctrl">
<label>Зум <input type="range" id="cZoom" min="30" max="260" value="100"><span class="val" id="vZoom">100%</span></label>
<label>Сетка <input type="checkbox" id="cGrid" checked></label>
<label>Привязка <input type="checkbox" id="cSnap" checked></label>
<label>Скорость <input type="range" id="cSpeed" min="20" max="300" value="100"><span class="val" id="vSpeed">1.0x</span></label>
<label>Свечение <input type="range" id="cGlow" min="0" max="12" value="6"><span class="val" id="vGlow">6</span></label>
<label>Подписи <input type="range" id="cLabel" min="8" max="18" value="11"><span class="val" id="vLabel">11</span></label>
<label>Изгиб линий <input type="range" id="cCurve" min="0" max="60" value="22"><span class="val" id="vCurve">22</span></label>
<label>Hop, мс <input type="range" id="cHop" min="80" max="1200" value="420"><span class="val" id="vHop">420</span></label>
<label>Тема <select id="cTheme"><option value="dark">тёмная</option><option value="light">светлая</option><option value="blue">blueprint</option></select></label>
<label>Цвет VLAN <input type="checkbox" id="cVcol" checked></label>
<button id="bReset">🎯 Сброс вида</button>
<button id="bRand">🧹 Автораскладка</button>
<button id="bCfg">♻ Настройки</button>
</div>
<div id="wrap">
<div id="pal">
<h4>Устройства</h4><div id="palDev"></div>
<h4>Шаблоны</h4><div id="palTpl"></div>
<h4>Схема</h4>
<button id="bDemo">📦 Пример: БР + PON</button>
<button id="bClear">🧽 Очистить холст</button>
</div>
<div id="stage" class="grid"><svg id="cv" xmlns="http://www.w3.org/2000/svg">
<defs><filter id="glow" x="-80%" y="-80%" width="260%" height="260%">
<feGaussianBlur id="glowBlur" stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter></defs>
<g id="world"><g id="geo"></g><g id="pk"></g></g></svg></div>
<div id="side">
<h3>🔧 Свойства</h3><div id="props"><span style="color:var(--mut)">Выберите устройство или линию на холсте.</span></div>
<hr><h3 class="sim">📡 Симуляция трафика</h3>
<div class="fld"><span>Источник</span><select id="simSrc"></select></div>
<div class="fld"><span>Приёмник</span><select id="simDst"></select></div>
<div class="fld"><span>Режим</span><select id="simMode">
<option value="unicast">unicast · A → B</option>
<option value="multicast">multicast · камера → viewers</option>
<option value="broadcast">broadcast / flood (поиск петли)</option>
<option value="pon">PON downstream · OLT → все ONU</option></select></div>
<div class="fld"><span>VLAN</span><input id="simVlan" value="135"></div>
<div style="display:flex;gap:6px"><button class="g" id="bRun" style="flex:1">▶ Пуск</button><button id="bStop" style="flex:1">⏹ Стоп</button></div>
<div id="log"></div>
</div>
</div>
<div id="status">
<span>Устройств: <b id="stDev">0</b></span><span>Линий: <b id="stLink">0</b></span>
<span>Зум: <b id="stZoom">100%</b></span><span>Выбрано: <b id="stSel">—</b></span>
<span id="stSim" class="chip">симуляция: остановлена</span>
<span style="margin-left:auto">VLAN-цвета: <span class="chip" style="color:#f472b6">135 камеры</span> <span class="chip" style="color:#fbbf24">1151 IPTV</span> <span class="chip" style="color:#34d399">абоненты</span></span>
</div>
<div id="toast"></div>
<script>
(function(){
'use strict';
var TYPES={
 core:{i:'🌐',n:'Ядро / роутер',c:'#f87171'},
 switch:{i:'🖧',n:'Коммутатор доступа',c:'#38bdf8'},
 agg:{i:'🔀',n:'Агрегация',c:'#818cf8'},
 olt:{i:'🏢',n:'OLT',c:'#c084fc'},
 split:{i:'🌳',n:'Сплиттер PON',c:'#2dd4bf'},
 onu:{i:'📡',n:'ONU / ONT',c:'#34d399'},
 camera:{i:'📹',n:'IP-камера',c:'#fb923c'},
 pc:{i:'🖥️',n:'ПК / терминал',c:'#94a3b8'},
 nvr:{i:'🗄️',n:'NVR / сервер',c:'#f472b6'},
 ap:{i:'📶',n:'Точка доступа',c:'#60a5fa'},
 printer:{i:'🖨️',n:'Принтер',c:'#a3a3a3'}
};
var cfg={grid:true,snap:true,speed:1,glow:6,label:11,curve:.22,hop:420,theme:'dark',vcol:true};
var S, view={x:70,y:50,k:1}, sel=null, selLink=null, tool='select', linkFrom=null;
var drag=null, pan=null, undoStack=[], timers=[], running=false, raf=null;
function $(id){return document.getElementById(id);}
function geo(){return $('geo');}
function pk(){return $('pk');}
function world(){return $('world');}
function dev(id){for(var i=0;i<S.devices.length;i++)if(S.devices[i].id===id)return S.devices[i];return null;}
function lnk(id){for(var i=0;i<S.links.length;i++)if(S.links[i].id===id)return S.links[i];return null;}
function hue(v){var h=(parseInt(v,10)||0)*47%360;return 'hsl('+h+' 85% 62%)';}
function toast(t){var el=$('toast');el.textContent=t;el.classList.add('show');clearTimeout(el._t);el._t=setTimeout(function(){el.classList.remove('show');},1800);}
function log(t,cls){var l=$('log');var d=document.createElement('div');if(cls)d.className=cls;d.textContent=t;l.appendChild(d);l.scrollTop=l.scrollHeight;}
function snap(v){return cfg.snap?Math.round(v/12)*12:v;}
function pushUndo(){undoStack.push(JSON.stringify(S));if(undoStack.length>60)undoStack.shift();}
function autosave(){try{localStorage.setItem('netlab_auto',JSON.stringify(S));}catch(e){}}
function demo(){
 return {nid:13,lid:13,devices:[
  {id:1,type:'core',x:430,y:60,name:'Ядро S6330',ip:'10.163.100.8',vlan:'',model:'Huawei S6330'},
  {id:2,type:'nvr',x:640,y:60,name:'NVR видеонаблюдение',ip:'10.135.0.10',vlan:'135',model:'NVR-64'},
  {id:3,type:'switch',x:250,y:210,name:'DES-3200 Михеенко 15',ip:'10.163.202.13',vlan:'',model:'DES-3200-28'},
  {id:4,type:'camera',x:120,y:360,name:'Камера БР-6 подъезд',ip:'10.135.1.232',vlan:'135',model:'BEWARD B2710'},
  {id:5,type:'pc',x:330,y:360,name:'Абонент кв.12',ip:'10.163.202.12',vlan:'2201',model:'ONT+PC'},
  {id:6,type:'olt',x:620,y:210,name:'OLT Жучки',ip:'10.163.206.8',vlan:'',model:'PON OLT'},
  {id:7,type:'split',x:620,y:330,name:'Сплиттер 1:8',ip:'',vlan:'',model:'1x8'},
  {id:8,type:'onu',x:520,y:450,name:'ONU камера PON',ip:'',vlan:'2603',model:'ONT-1G'},
  {id:9,type:'camera',x:520,y:560,name:'Камера PON Жучки',ip:'10.135.2.10',vlan:'2603',model:'BEWARD'},
  {id:10,type:'onu',x:730,y:450,name:'ONU абонент',ip:'',vlan:'2601',model:'ONT-1G'},
  {id:11,type:'pc',x:730,y:560,name:'Абонент Жучки',ip:'10.163.206.21',vlan:'2601',model:'PC'},
  {id:12,type:'switch',x:60,y:210,name:'DES-3200 Лихачева 6',ip:'10.163.202.32',vlan:'',model:'DES-3200-28'}
 ],links:[
  {id:1,a:1,b:3,pa:'4',pb:'28',mode:'trunk',vlans:'135,1151,2201,2208',media:'fiber',cost:1},
  {id:2,a:1,b:2,pa:'6',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1},
  {id:3,a:3,b:4,pa:'21',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1},
  {id:4,a:3,b:5,pa:'12',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1},
  {id:5,a:1,b:6,pa:'8',pb:'uplink',mode:'trunk',vlans:'135,1151,2601,2603',media:'fiber',cost:2},
  {id:6,a:6,b:7,pa:'pon1',pb:'in',mode:'trunk',vlans:'2601,2603',media:'pon',cost:3},
  {id:7,a:7,b:8,pa:'3',pb:'pon',mode:'trunk',vlans:'2601,2603',media:'pon',cost:1},
  {id:8,a:8,b:9,pa:'lan1',pb:'1',mode:'access',vlans:'2603',media:'copper',cost:1},
  {id:9,a:7,b:10,pa:'5',pb:'pon',mode:'trunk',vlans:'2601,2603',media:'pon',cost:1},
  {id:10,a:10,b:11,pa:'lan1',pb:'1',mode:'access',vlans:'2601',media:'copper',cost:1},
  {id:11,a:1,b:12,pa:'2',pb:'28',mode:'trunk',vlans:'135,2208',media:'fiber',cost:1},
  {id:12,a:3,b:12,pa:'26',pb:'26',mode:'trunk',vlans:'135,2208',media:'copper',cost:1}
 ]};
}
function render(){
 var light=cfg.theme==='light';
 var ink=light?'#1e293b':'#e8eefb', mut=light?'#64748b':'#9fb2d4';
 var h='';
 S.links.forEach(function(L){
  var a=dev(L.a),b=dev(L.b);if(!a||!b)return;
  var mx=(a.x+b.x)/2,my=(a.y+b.y)/2,dx=b.x-a.x,dy=b.y-a.y,len=Math.sqrt(dx*dx+dy*dy)||1;
  var cx=mx-dy/len*cfg.curve*len*0.5, cy=my+dx/len*cfg.curve*len*0.5;
  var col=cfg.vcol?hue(String(L.vlans).split(',')[0]):(L.media==='fiber'?'#fbbf24':L.media==='pon'?'#2dd4bf':'#7c93b8');
  var on=selLink===L.id;
  h+='<path data-l="'+L.id+'" d="M'+a.x+' '+a.y+' Q'+cx+' '+cy+' '+b.x+' '+b.y+'" fill="none" stroke="'+(on?'#f472b6':col)+'" stroke-width="'+(on?4:2.4)+'" stroke-dasharray="'+(L.media==='pon'?'7 4':'none')+'" style="cursor:pointer" opacity="'+(on?1:.85)+'"/>';
  h+='<text x="'+cx+'" y="'+(cy-5)+'" text-anchor="middle" font-size="'+cfg.label+'" fill="'+mut+'" style="pointer-events:none">'+(L.pa||'?')+'→'+(L.pb||'?')+' · '+(L.mode==='trunk'?'trunk['+L.vlans+']':'acc'+L.vlans)+'</text>';
 });
 S.devices.forEach(function(d){
  var t=TYPES[d.type]||TYPES.switch, on=sel===d.id;
  h+='<g data-d="'+d.id+'" style="cursor:move">';
  h+='<rect x="'+(d.x-52)+'" y="'+(d.y-32)+'" width="104" height="64" rx="12" fill="'+t.c+'" fill-opacity="'+(light?0.92:0.20)+'" stroke="'+(on?'#f472b6':t.c)+'" stroke-width="'+(on?3:1.6)+'"/>';
  if(on)h+='<rect x="'+(d.x-56)+'" y="'+(d.y-36)+'" width="112" height="72" rx="14" fill="none" stroke="#f472b6" stroke-opacity=".35" stroke-width="6"/>';
  h+='<text x="'+d.x+'" y="'+(d.y-8)+'" text-anchor="middle" font-size="19">'+t.i+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+9)+'" text-anchor="middle" font-size="'+cfg.label+'" font-weight="700" fill="'+(light?'#0f172a':ink)+'">'+esc((d.name||t.n).slice(0,18))+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+24)+'" text-anchor="middle" font-size="'+(cfg.label-1)+'" fill="'+(light?'#475569':mut)+'">'+esc(d.ip||'')+(d.vlan?' · v'+d.vlan:'')+'</text>';
  h+='</g>';
 });
 geo().innerHTML=h;
 world().setAttribute('transform','translate('+view.x+','+view.y+') scale('+view.k+')');
 $('glowBlur').setAttribute('stdDeviation',cfg.glow);
 $('stDev').textContent=S.devices.length; $('stLink').textContent=S.links.length;
 $('stZoom').textContent=Math.round(view.k*100)+'%'; $('vZoom').textContent=Math.round(view.k*100)+'%';
 $('cZoom').value=Math.round(view.k*100);
 $('stSel').textContent=sel!=null?('#'+sel+' '+(dev(sel).name||'')):(selLink!=null?('линия #'+selLink):'—');
 fillSim();
}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fillSim(){
 var o=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+' · '+(d.ip||'#'+d.id)+'</option>';}).join('');
 var a=$('simSrc'),b=$('simDst'),av=a.value,bv=b.value;
 a.innerHTML=o;b.innerHTML=o;
 if(av&&dev(+av))a.value=av; else if(S.devices[0])a.value=S.devices[0].id;
 if(bv&&dev(+bv))b.value=bv; else if(S.devices[3])b.value=S.devices[3].id;
}
function palette(){
 $('palDev').innerHTML=Object.keys(TYPES).map(function(k){
  return '<button data-add="'+k+'"><i>'+TYPES[k].i+'</i>'+TYPES[k].n+'</button>';}).join('');
 $('palTpl').innerHTML=
  '<button class="tpl" data-tpl="pod">🏠 Подъезд: DES + камера + абонент</button>'+
  '<button class="tpl" data-tpl="pon">🌳 PON: OLT + сплиттер + 2 ONU</button>'+
  '<button class="tpl" data-tpl="core">🌐 Ядро + NVR + 2 доступа</button>';
}
function center(){var r=$('cv').getBoundingClientRect();return {x:(r.width/2-view.x)/view.k, y:(r.height/2-view.y)/view.k};}
function addDev(k){
 pushUndo();var c=center();
 S.devices.push({id:S.nid++,type:k,x:snap(c.x+(Math.random()*120-60)),y:snap(c.y+(Math.random()*90-45)),name:'',ip:'',vlan:(k==='camera'||k==='pc'||k==='onu')?'135':'',model:''});
 autosave();render();toast('Добавлено: '+TYPES[k].n);
}
function addTpl(k){
 pushUndo();var c=center(),ids={},mk=function(t,dx,dy,name,ip,vlan){var id=S.nid++;ids[t+dx+dy]=id;
  S.devices.push({id:id,type:t,x:snap(c.x+dx),y:snap(c.y+dy),name:name,ip:ip,vlan:vlan||'',model:''});return id;};
 var L=function(a,b,pa,pb,mode,vlans,media){S.links.push({id:S.lid++,a:a,b:b,pa:pa,pb:pb,mode:mode,vlans:vlans,media:media||'copper',cost:1});};
 if(k==='pod'){var sw=mk('switch',0,-60,'DES-3200 подъезд','','');var cam=mk('camera',-110,70,'Камера БР','','135');var pc=mk('pc',110,70,'Абонент','','2201');
  L(sw,cam,'21','1','access','135');L(sw,pc,'12','1','access','2201');}
 if(k==='pon'){var olt=mk('olt',0,-110,'OLT','','');var sp=mk('split',0,-10,'Сплиттер 1:8','','');var o1=mk('onu',-110,90,'ONU-1','','2603');var o2=mk('onu',110,90,'ONU-2','','2601');
  var c1=mk('camera',-110,190,'Камера PON','','2603');var p2=mk('pc',110,190,'Абонент PON','','2601');
  L(olt,sp,'pon1','in','trunk','2601,2603','pon');L(sp,o1,'3','pon','trunk','2601,2603','pon');L(sp,o2,'5','pon','trunk','2601,2603','pon');
  L(o1,c1,'lan1','1','access','2603');L(o2,p2,'lan1','1','access','2601');}
 if(k==='core'){var co=mk('core',0,-120,'Ядро','','');var nv=mk('nvr',170,-120,'NVR','','135');var s1=mk('switch',-140,20,'DES доступ-1','','');var s2=mk('switch',140,20,'DES доступ-2','','');
  L(co,nv,'6','1','access','135');L(co,s1,'4','28','trunk','135,1151,2201','fiber');L(co,s2,'8','28','trunk','135,1151,2601','fiber');}
 autosave();render();toast('Шаблон добавлен');
}
function pt(e){var r=$('cv').getBoundingClientRect();return {x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k};}
$('cv').addEventListener('pointerdown',function(e){
 var g=e.target.closest?e.target.closest('[data-d]'):null;
 var l=e.target.closest?e.target.closest('[data-l]'):null;
 if(g){var id=+g.getAttribute('data-d');
  if(tool==='link'){
   if(linkFrom==null){linkFrom=id;log('🔗 линия от #'+id+' — кликните второе устройство','info');}
   else if(linkFrom!==id){pushUndo();S.links.push({id:S.lid++,a:linkFrom,b:id,pa:'',pb:'',mode:'trunk',vlans:'135,1151',media:'copper',cost:1});
    linkFrom=null;setTool('select');autosave();render();toast('Линия создана — задайте порты справа');}
   return;}
  sel=id;selLink=null;props();var p=pt(e),d=dev(id);drag={id:id,dx:p.x-d.x,dy:p.y-d.y};pushUndo();render();return;}
 if(l){selLink=+l.getAttribute('data-l');sel=null;props();render();return;}
 sel=null;selLink=null;props();pan={x:e.clientX-view.x,y:e.clientY-view.y};render();
});
window.addEventListener('pointermove',function(e){
 if(drag){var p=pt(e),d=dev(drag.id);if(d){d.x=snap(p.x-drag.dx);d.y=snap(p.y-drag.dy);render();}}
 else if(pan){view.x=e.clientX-pan.x;view.y=e.clientY-pan.y;render();}
});
window.addEventListener('pointerup',function(){if(drag){autosave();}drag=null;pan=null;});
$('cv').addEventListener('wheel',function(e){
 e.preventDefault();var r=$('cv').getBoundingClientRect();
 var mx=e.clientX-r.left,my=e.clientY-r.top;
 var f=e.deltaY<0?1.12:0.89,nk=Math.max(.3,Math.min(2.6,view.k*f));
 view.x=mx-(mx-view.x)*(nk/view.k);view.y=my-(my-view.y)*(nk/view.k);view.k=nk;render();
},{passive:false});
function setTool(t){tool=t;linkFrom=null;$('bLink').classList.toggle('on',t==='link');$('bSel').classList.toggle('on',t==='select');
 $('hint').textContent=t==='link'?'РЕЖИМ ЛИНИИ: кликните устройство A, затем устройство B':'ЛКМ по устройству — выбрать/тащить · фон — панорама · колесо — зум · Del — удалить · Ctrl+Z — отмена';}
function props(){
 var p=$('props');
 if(selLink!=null){var L=lnk(selLink);if(!L){selLink=null;p.innerHTML='';return;}
  p.innerHTML='<div class="fld"><span>Линия #'+L.id+' · '+esc((dev(L.a)||{}).name||'')+' ↔ '+esc((dev(L.b)||{}).name||'')+'</span></div>'+
  '<div class="fld"><span>Порт A</span><input data-lf="pa" value="'+esc(L.pa)+'"></div>'+
  '<div class="fld"><span>Порт B</span><input data-lf="pb" value="'+esc(L.pb)+'"></div>'+
  '<div class="fld"><span>Режим</span><select data-lf="mode"><option value="trunk"'+(L.mode==='trunk'?' selected':'')+'>trunk</option><option value="access"'+(L.mode==='access'?' selected':'')+'>access</option></select></div>'+
  '<div class="fld"><span>VLAN-ы (через запятую)</span><input data-lf="vlans" value="'+esc(L.vlans)+'"></div>'+
  '<div class="fld"><span>Среда</span><select data-lf="media"><option value="copper"'+(L.media==='copper'?' selected':'')+'>медь</option><option value="fiber"'+(L.media==='fiber'?' selected':'')+'>оптика</option><option value="pon"'+(L.media==='pon'?' selected':'')+'>PON</option></select></div>'+
  '<div class="fld"><span>Задержка, мс</span><input type="number" data-lf="cost" value="'+(L.cost||1)+'"></div>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-lf]'),function(inp){
   inp.addEventListener('input',function(){pushUndo();L[inp.getAttribute('data-lf')]=inp.value;autosave();render();});});
  return;}
 if(sel!=null){var d=dev(sel);if(!d){sel=null;p.innerHTML='';return;}
  var conns=S.links.filter(function(L){return L.a===sel||L.b===sel;}).map(function(L){
   var other=dev(L.a===sel?L.b:L.a);return '<div style="color:var(--mut);font-size:12px">↔ '+esc(other?other.name:'?')+' · '+(L.a===sel?L.pa:L.pb)+'→'+(L.a===sel?L.pb:L.pa)+' · '+L.mode+'['+L.vlans+']</div>';}).join('');
  p.innerHTML='<div class="fld"><span>Тип</span><select data-df="type">'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'"'+(d.type===k?' selected':'')+'>'+TYPES[k].i+' '+TYPES[k].n+'</option>';}).join('')+'</select></div>'+
  '<div class="fld"><span>Имя</span><input data-df="name" value="'+esc(d.name)+'"></div>'+
  '<div class="fld"><span>IP</span><input data-df="ip" value="'+esc(d.ip)+'"></div>'+
  '<div class="fld"><span>Access-VLAN</span><input data-df="vlan" value="'+esc(d.vlan)+'"></div>'+
  '<div class="fld"><span>Модель</span><input data-df="model" value="'+esc(d.model)+'"></div>'+
  '<div class="fld"><span>Подключения</span>'+ (conns||'<div style="color:var(--mut);font-size:12px">нет линий</div>')+'</div>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-df]'),function(inp){
   inp.addEventListener('input',function(){pushUndo();d[inp.getAttribute('data-df')]=inp.value;autosave();render();});});
  return;}
 p.innerHTML='<span style="color:var(--mut)">Выберите устройство или линию на холсте.</span>';
}
function delSel(){
 pushUndo();
 if(selLink!=null){S.links=S.links.filter(function(L){return L.id!==selLink;});selLink=null;toast('Линия удалена');}
 else if(sel!=null){S.links=S.links.filter(function(L){return L.a!==sel&&L.b!==sel;});S.devices=S.devices.filter(function(d){return d.id!==sel;});sel=null;toast('Устройство удалено');}
 autosave();props();render();
}
function undo(){if(!undoStack.length){toast('Нечего отменять');return;}S=JSON.parse(undoStack.pop());sel=null;selLink=null;autosave();props();render();toast('Отменено');}
/* ---------- симуляция ---------- */
function allows(L,v){var list=String(L.vlans||'').split(',').map(function(x){return x.trim();});
 return L.mode==='trunk'?list.indexOf(String(v))>=0:String(L.vlans)===String(v);}
function nbrs(id,v){var out=[];S.links.forEach(function(L){
 if(L.a===id&&allows(L,v))out.push({to:L.b,L:L});
 if(L.b===id&&allows(L,v))out.push({to:L.a,L:L});});return out;}
function path(s,d,v){var prev={},seen={},q=[s];seen[s]=1;
 while(q.length){var c=q.shift();if(c===d)break;
  nbrs(c,v).forEach(function(n){if(!seen[n.to]){seen[n.to]=1;prev[n.to]={f:c,L:n.L};q.push(n.to);}});}
 if(!seen[d])return null;var hops=[],cur=d;
 while(cur!==s){var p=prev[cur];hops.unshift({from:p.f,to:cur,L:p.L});cur=p.f;}return hops;}
function packet(a,b,color,dur,cb){
 var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
 c.setAttribute('r',6);c.setAttribute('fill',color);c.setAttribute('filter','url(#glow)');c.setAttribute('stroke','#fff');c.setAttribute('stroke-width','1');
 pk().appendChild(c);var t0=performance.now();
 function step(t){var k=Math.min(1,(t-t0)/dur);
  c.setAttribute('cx',a.x+(b.x-a.x)*k);c.setAttribute('cy',a.y+(b.y-a.y)*k);
  if(k<1){raf=requestAnimationFrame(step);}else{c.remove();if(cb)cb();}}
 raf=requestAnimationFrame(step);
}
function runHops(hops,v,label,done){
 var col=hue(v),i=0;
 function next(){
  if(i>=hops.length){if(done)done();return;}
  var h=hops[i],a=dev(h.from),b=dev(h.to);
  packet(a,b,col,600/cfg.speed,function(){
   log(label+' hop'+(i+1)+': '+(a.name||a.id)+' → '+(b.name||b.id)+'  ['+(h.L.mode==='trunk'?'trunk v'+v+' OK':'access v'+v+' OK')+'] +'+(h.L.cost||1)+'ms','ok');
   i++;timers.push(setTimeout(next,cfg.hop/cfg.speed));});
 }
 next();
}
function stopSim(){timers.forEach(clearTimeout);timers=[];if(raf)cancelAnimationFrame(raf);pk().innerHTML='';running=false;
 $('stSim').textContent='симуляция: остановлена';$('stSim').style.color='';}
function run(){
 stopSim();$('log').innerHTML='';running=true;$('stSim').textContent='симуляция: идёт…';$('stSim').style.color='var(--ok)';
 var s=+$('simSrc').value,d=+$('simDst').value,mode=$('simMode').value,v=$('simVlan').value||'1';
 var sd=dev(s);if(!sd){log('нет источника','bad');stopSim();return;}
 log('▶ '+mode+' · VLAN '+v+' · от '+(sd.name||sd.id),'info');
 if(mode==='unicast'){
  var dd=dev(d);
  if(dd&&dd.vlan&&String(dd.vlan)!==String(v)){log('❌ приёмник '+(dd.name||d)+' в VLAN '+dd.vlan+', а пакет в VLAN '+v — '','bad');}
  var hops=path(s,d,v);
  if(!hops){log('❌ пути нет: VLAN '+v+' не пропущен на транке или access-VLAN не совпадает. Проверьте trunk-списки!','bad');stopSim();return;}
  var ms=hops.reduce(function(t,h){return t+(+h.L.cost||1);},0);
  runHops(hops,v,'📨',function(){log('✅ доставлено за '+ms+' мс через '+hops.length+' hop(s)','ok');stopSim();});
 } else if(mode==='multicast'){
  var viewers=S.devices.filter(function(x){return x.id!==s&&String(x.vlan)===String(v)&&(x.type==='pc'||x.type==='nvr'||x.type==='printer'||x.type==='camera');});
  if(!viewers.length){log('❌ нет получателей с VLAN '+v,'bad');stopSim();return;}
  var left=viewers.length;
  viewers.forEach(function(x){var h=path(s,x.id,v);
   if(h){runHops(h,v,'📺→'+(x.name||x.id),function(){if(--left===0){log('✅ multicast доставлен '+viewers.length+' получателям','ok');stopSim();}});}
   else{log('❌ '+(x.name||x.id)+': VLAN '+v+' не доходит','bad');if(--left===0)stopSim();}});
 } else if(mode==='pon'){
  var onus=S.devices.filter(function(x){return x.type==='onu';});
  if(!onus.length){log('❌ на схеме нет ONU','bad');stopSim();return;}
  var left2=onus.length;
  onus.forEach(function(x){var h=path(s,x.id,v);
   if(h){runHops(h,v,'🌊PON→'+(x.name||x.id),function(){log('ℹ️ '+(x.name||x.id)+': '+(String(x.vlan)===String(v)?'принимает поток (VLAN совпал)':'отбрасывает (VLAN '+x.vlan+' ≠ '+v+')'),String(x.vlan)===String(v)?'ok':'warn');if(--left2===0)stopSim();});}
   else{log('❌ '+(x.name||x.id)+': нет пути PON','bad');if(--left2===0)stopSim();}});
 } else {
  var seen={},q=[s],edges=[],storm=false;seen[s]=1;
  while(q.length){var c=q.shift();nbrs(c,v).forEach(function(n){edges.push({from:c,to:n.to,L:n.L});
   if(seen[n.to])storm=true;else{seen[n.to]=1;q.push(n.to);}});}
  edges.forEach(function(e,i){timers.push(setTimeout(function(){
   var a=dev(e.from),b=dev(e.to);packet(a,b,hue(v),500/cfg.speed,null);
   log('🌊 '+(a.name||a.id)+' → '+(b.name||b.id),'info');},i*140/cfg.speed));});
  timers.push(setTimeout(function(){
   log(storm?'⚠️ ПЕТЛЯ ОБНАРУЖЕНА → broadcast-шторм! Включите loopdetect / RSTP':'🌊 flood дошёл до '+Object.keys(seen).length+' устройств',storm?'warn':'ok');
   stopSim();},edges.length*140/cfg.speed+800));
 }
}
/* ---------- сохранение / экспорт ---------- */
function pin(){return localStorage.getItem('swhpin')||prompt('PIN админки:')||'';}
function save(){
 var name=prompt('Название схемы:','Схема ЛВС '+(new Date().toLocaleDateString('ru')));
 if(!name)return;
 fetch('/api/schemes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin(),name:name,data:JSON.stringify(S)})})
 .then(function(r){return r.json();}).then(function(res){toast(res.ok?('Сохранено #'+res.id):('Ошибка: '+(res.error||'')));})
 .catch(function(e){toast('Ошибка: '+e.message);});
}
function openList(){
 fetch('/api/schemes').then(function(r){return r.json();}).then(function(rows){
  if(!rows.length){toast('Сохранённых схем нет');return;}
  var pick=prompt('Открыть схему (ID):\n'+rows.map(function(r){return r.id+': '+r.name+' ('+r.updated_at+')';}).join('\n'),String(rows[0].id));
  if(!pick)return;
  fetch('/api/schemes/'+pick).then(function(r){return r.json();}).then(function(sc){
   if(sc&&sc.data){pushUndo();S=JSON.parse(sc.data);sel=null;selLink=null;autosave();props();render();toast('Открыто: '+sc.name);}});
 }).catch(function(e){toast('Ошибка: '+e.message);});
}
function delScheme(){
 var id=prompt('ID схемы для удаления:');if(!id)return;
 if(!confirm('Удалить схему #'+id+'?'))return;
 fetch('/api/schemes/'+id,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin()})})
 .then(function(r){return r.json();}).then(function(res){toast(res.ok?'Схема удалена':'Ошибка');});
}
function exportSvg(){
 var clone=$('cv').cloneNode(true);
 clone.setAttribute('width',1600);clone.setAttribute('height',1000);
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
 bg.setAttribute('width',1600);bg.setAttribute('height',1000);bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0f1726');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
 var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='netlab-scheme.svg';a.click();toast('SVG скачан');
}
function exportPng(){
 var clone=$('cv').cloneNode(true);clone.setAttribute('width',1600);clone.setAttribute('height',1000);
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
 bg.setAttribute('width',1600);bg.setAttribute('height',1000);bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0f1726');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
 var img=new Image();
 img.onload=function(){var c=document.createElement('canvas');c.width=1600;c.height=1000;
  var ctx=c.getContext('2d');ctx.drawImage(img,0,0);
  var a=document.createElement('a');a.href=c.toDataURL('image/png');a.download='netlab-scheme.png';a.click();toast('PNG скачан');};
 img.onerror=function(){toast('PNG не удалось — используйте SVG');};
 img.src=URL.createObjectURL(blob);
}
function tidy(){
 pushUndo();
 var parent={},hasP={};
 S.links.forEach(function(L){if(!hasP[L.b]){hasP[L.b]=1;parent[L.b]=L.a;}});
 var roots=S.devices.filter(function(d){return !hasP[d.id];}).map(function(d){return d.id;});
 if(!roots.length&&S.devices[0])roots=[S.devices[0].id];
 var lvl={},q=roots.map(function(r){return [r,0];}),seen={};
 while(q.length){var it=q.shift();if(seen[it[0]])continue;seen[it[0]]=1;lvl[it[0]]=it[1];
  S.links.forEach(function(L){if(L.a===it[0])q.push([L.b,it[1]+1]);});}
 var by={};S.devices.forEach(function(d){var l=lvl[d.id]==null?4:lvl[d.id];(by[l]=by[l]||[]).push(d);});
 Object.keys(by).forEach(function(l){by[l].forEach(function(d,i){d.x=120+i*230;d.y=70+(+l)*150;});});
 autosave();render();toast('Автораскладка по уровням');
}
/* ---------- контролы ---------- */
function bindCtrl(){
 $('cZoom').addEventListener('input',function(){view.k=this.value/100;render();});
 $('cGrid').addEventListener('change',function(){cfg.grid=this.checked;$('stage').classList.toggle('grid',cfg.grid);});
 $('cSnap').addEventListener('change',function(){cfg.snap=this.checked;});
 $('cSpeed').addEventListener('input',function(){cfg.speed=this.value/100;$('vSpeed').textContent=cfg.speed.toFixed(1)+'x';});
 $('cGlow').addEventListener('input',function(){cfg.glow=+this.value;$('vGlow').textContent=this.value;render();});
 $('cLabel').addEventListener('input',function(){cfg.label=+this.value;$('vLabel').textContent=this.value;render();});
 $('cCurve').addEventListener('input',function(){cfg.curve=this.value/100;$('vCurve').textContent=this.value;render();});
 $('cHop').addEventListener('input',function(){cfg.hop=+this.value;$('vHop').textContent=this.value;});
 $('cTheme').addEventListener('change',function(){cfg.theme=this.value;
  $('stage').className=(cfg.grid?'grid ':'')+cfg.theme;render();});
 $('cVcol').addEventListener('change',function(){cfg.vcol=this.checked;render();});
 $('bReset').addEventListener('click',function(){view={x:70,y:50,k:1};render();toast('Вид сброшен');});
 $('bRand').addEventListener('click',tidy);
 $('bCfg').addEventListener('click',function(){cfg={grid:true,snap:true,speed:1,glow:6,label:11,curve:.22,hop:420,theme:'dark',vcol:true};
  $('cZoom').value=100;$('cGrid').checked=true;$('cSnap').checked=true;$('cSpeed').value=100;$('cGlow').value=6;$('cLabel').value=11;
  $('cCurve').value=22;$('cHop').value=420;$('cTheme').value='dark';$('cVcol').checked=true;
  $('vSpeed').textContent='1.0x';$('vGlow').textContent='6';$('vLabel').textContent='11';$('vCurve').textContent='22';$('vHop').textContent='420';
  $('stage').className='grid dark';view={x:70,y:50,k:1};render();toast('Настройки сброшены');});
}
function bindTop(){
 $('bSave').addEventListener('click',save);
 $('bOpen').addEventListener('click',openList);
 $('bDelScheme').addEventListener('click',delScheme);
 $('bSvg').addEventListener('click',exportSvg);
 $('bPng').addEventListener('click',exportPng);
 $('bPrint').addEventListener('click',function(){window.print();});
 $('bLink').addEventListener('click',function(){setTool(tool==='link'?'select':'link');});
 $('bSel').addEventListener('click',function(){setTool('select');});
 $('bUndo').addEventListener('click',undo);
 $('bDel').addEventListener('click',delSel);
 $('bRun').addEventListener('click',run);
 $('bStop').addEventListener('click',function(){stopSim();log('⏹ остановлено','info');});
 $('bDemo').addEventListener('click',function(){pushUndo();S=demo();sel=null;selLink=null;autosave();props();render();toast('Пример загружен');});
 $('bClear').addEventListener('click',function(){if(!confirm('Очистить холст?'))return;pushUndo();S={nid:1,lid:1,devices:[],links:[]};sel=null;selLink=null;autosave();props();render();});
 $('palDev').addEventListener('click',function(e){var b=e.target.closest('[data-add]');if(b)addDev(b.getAttribute('data-add'));});
 $('palTpl').addEventListener('click',function(e){var b=e.target.closest('[data-tpl]');if(b)addTpl(b.getAttribute('data-tpl'));});
 window.addEventListener('keydown',function(e){
  if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT'||e.target.tagName==='TEXTAREA')return;
  if(e.key==='Delete'||e.key==='Backspace'){delSel();e.preventDefault();}
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='z'){undo();e.preventDefault();}
  if(e.key==='Escape'){setTool('select');sel=null;selLink=null;props();render();}
 });
}
/* ---------- boot ---------- */
palette();bindTop();bindCtrl();
var saved=null;try{saved=localStorage.getItem('netlab_auto');}catch(e){}
S=saved?JSON.parse(saved):demo();
if(!S||!S.devices)S=demo();
$('stage').className='grid dark';
props();render();
log('🧪 NetLab готов. Устройств: '+S.devices.length+', линий: '+S.links.length,'info');
log('Добавляйте устройства слева, соединяйте кнопкой «🔗 Соединить», затем ▶ Пуск.','info');
})();
</script>
</body></html>"""
'''

i = src.find('NETLAB_HTML = """')
if i < 0:
    raise SystemExit('NETLAB_HTML не найден — примените сначала v21/v22')
j = src.find('"""', i + len('NETLAB_HTML = """'))
if j < 0:
    raise SystemExit('NETLAB_HTML не закрыт')
src = src[:i] + NEW + src[j+3:]

if 'return render_template_string(NETLAB_HTML)' in src:
    src = src.replace('return render_template_string(NETLAB_HTML)', "return Response(NETLAB_HTML, mimetype='text/html')", 1)

try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v23_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v23',
           'fixes': ['netlab full rewrite: palette, templates, drag/connect/delete/undo, live controls x10, sim unicast/multicast/broadcast/PON, save/load/delete schemes, SVG/PNG/print, autosave, mobile']},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v23: NetLab полностью рабочий (палитра, шаблоны, рисование, симуляция, контролы, сохранение).')
