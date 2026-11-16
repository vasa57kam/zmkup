# update.py — v24: NetLab как отдельный самодостаточный файл (без Jinja, без внешних зависимостей,
# literal-цвета, ES5, seeded абонентская локалка, палитра click+drag, реестр с поиском/фильтром/сортировкой,
# симуляция unicast/multicast/broadcast/PON, 12 живых контролов, save/load/delete, SVG/PNG/print, undo, mobile)
import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
os.makedirs('static', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v24_' + TS + '.py')

HTML = r'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NetLab — проектирование локальной сети абонента</title>
<style>
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:#0b1220;color:#eaf2ff;font:14px/1.45 "Segoe UI",system-ui,Arial,sans-serif;overflow:hidden}
#errbar{display:none;position:fixed;top:0;left:0;right:0;z-index:99;background:#7f1d1d;color:#ffe4e6;padding:8px 14px;font:12px Consolas,monospace}
#top{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 12px;background:linear-gradient(90deg,#0e1a2f,#132441 55%,#0e1a2f);border-bottom:1px solid #22345c;position:relative;z-index:6}
#top .brand{font-weight:700;font-size:15px;letter-spacing:.3px;margin-right:8px;color:#eaf2ff}
#top .brand em{font-style:normal;color:#4cc3ff}
button{font:600 12.5px "Segoe UI",Arial;color:#eaf2ff;background:#1a2740;border:1px solid #2c3f6b;border-radius:9px;padding:7px 11px;cursor:pointer;transition:transform .12s,filter .12s,background .12s}
button:hover{transform:translateY(-1px);filter:brightness(1.2)}
button:active{transform:translateY(0)}
button.p{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent;color:#ffffff}
button.g{background:linear-gradient(135deg,#059669,#10b981);border-color:transparent;color:#ffffff}
button.w{background:linear-gradient(135deg,#d97706,#f59e0b);border-color:transparent;color:#221503}
button.d{background:linear-gradient(135deg,#dc2626,#ef4444);border-color:transparent;color:#ffffff}
button.on{outline:2px solid #4cc3ff;outline-offset:1px}
#hint{margin-left:auto;color:#93a6c9;font-size:12px}
#ctrl{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding:7px 12px;background:#101b30;border-bottom:1px solid #22345c;position:relative;z-index:5}
#ctrl label{display:flex;align-items:center;gap:6px;color:#93a6c9;font-size:12px;white-space:nowrap}
#ctrl input[type=range]{width:92px;accent-color:#4cc3ff}
#ctrl input[type=checkbox]{width:15px;height:15px;accent-color:#3ddc97}
#ctrl select{background:#16233c;color:#eaf2ff;border:1px solid #2c3f6b;border-radius:7px;padding:4px 6px;font-size:12px}
#ctrl .val{color:#4cc3ff;min-width:34px;text-align:right;font-variant-numeric:tabular-nums}
#wrap{display:flex;gap:8px;padding:8px;height:calc(100% - 100px)}
#left{width:236px;flex:none;background:#101b30;border:1px solid #22345c;border-radius:14px;padding:10px;overflow-y:auto}
#left h4{margin:6px 0 6px;font-size:11px;letter-spacing:1.2px;color:#7f93b8;text-transform:uppercase}
#palDev button,#palTpl button{display:flex;width:100%;align-items:center;gap:8px;margin:4px 0;text-align:left;background:#16233c;border:1px solid #263a63;color:#dfe9ff}
#palDev button:hover,#palTpl button:hover{background:#1d2f4f}
#palDev button i,#palTpl button i{font-style:normal;font-size:16px;width:20px;text-align:center}
#palTpl button{background:linear-gradient(135deg,#182a4a,#20335c);border-color:#3b4c78}
#regSearch,#regType,#regSort{width:100%;background:#0e1a2e;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:6px 8px;font-size:12.5px;margin:3px 0}
#regList{margin-top:6px}
.regRow{display:flex;align-items:center;gap:6px;padding:6px 6px;border:1px solid #22345c;border-radius:9px;margin:4px 0;background:#132038;cursor:pointer}
.regRow:hover{background:#1a2b4a}
.regRow.sel{outline:2px solid #ff6bb5}
.regRow input{accent-color:#3ddc97}
.regRow .nm{flex:1;font-size:12.5px;color:#eaf2ff;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.regRow .vl{font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:999px;background:#0e1a2e;border:1px solid #2c3f6b;color:#4cc3ff}
#regCount{color:#7f93b8;font-size:11.5px;margin:4px 0}
#stage{flex:1;position:relative;border:1px solid #22345c;border-radius:14px;overflow:hidden;background:#0d1728}
#stage.grid{background-image:linear-gradient(rgba(90,130,200,.16) 1px,transparent 1px),linear-gradient(90deg,rgba(90,130,200,.16) 1px,transparent 1px);background-size:24px 24px}
#stage.light{background:#f2f6fc}
#stage.light.grid{background-image:linear-gradient(rgba(30,60,120,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(30,60,120,.12) 1px,transparent 1px)}
#stage.blue{background:#0a2038}
#stage.blue.grid{background-image:linear-gradient(rgba(80,180,255,.14) 1px,transparent 1px),linear-gradient(90deg,rgba(80,180,255,.14) 1px,transparent 1px)}
#cv{width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#side{width:320px;flex:none;background:#101b30;border:1px solid #22345c;border-radius:14px;padding:12px;overflow-y:auto}
#side h3{margin:2px 0 8px;font-size:13px;letter-spacing:.5px;color:#4cc3ff}
#side h3.sim{color:#ff6bb5}
#side .fld{margin:6px 0}
#side .fld span{display:block;color:#93a6c9;font-size:11.5px;margin-bottom:3px}
#side input,#side select,#side textarea{width:100%;background:#0e1a2e;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:7px 9px;font-size:13px}
#side input:focus,#side select:focus,#side textarea:focus{outline:2px solid rgba(76,195,255,.4);border-color:#4cc3ff}
#side hr{border:none;border-top:1px solid #22345c;margin:12px 0}
#log{background:#060b16;border:1px solid #1c2a44;border-radius:10px;color:#6fd3ff;font:12px/1.5 Consolas,monospace;height:190px;overflow-y:auto;padding:8px;white-space:pre-wrap;margin-top:8px}
#log .ok{color:#3ddc97}#log .bad{color:#ff6b6b}#log .warn{color:#ffc857}#log .info{color:#8fa2c4}
#status{display:flex;gap:16px;align-items:center;flex-wrap:wrap;padding:6px 14px;background:#101b30;border-top:1px solid #22345c;color:#93a6c9;font-size:12px;position:relative;z-index:5}
#status b{color:#4cc3ff;font-variant-numeric:tabular-nums}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;background:#16233c;border:1px solid #2c3f6b;color:#dfe9ff}
#modal{display:none;position:fixed;inset:0;z-index:40;background:rgba(4,8,18,.72);align-items:center;justify-content:center}
#modal.open{display:flex}
#modalBox{width:min(560px,92vw);max-height:80vh;overflow-y:auto;background:#101b30;border:1px solid #2c3f6b;border-radius:16px;padding:16px}
#modalBox h3{margin:0 0 10px;color:#4cc3ff}
.mRow{display:flex;align-items:center;gap:8px;padding:8px;border:1px solid #22345c;border-radius:10px;margin:6px 0;background:#132038}
.mRow .t{flex:1;color:#eaf2ff;font-size:13px}
.mRow .d{color:#7f93b8;font-size:11.5px}
#toast{position:fixed;left:50%;bottom:52px;transform:translateX(-50%) translateY(20px);opacity:0;pointer-events:none;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#ffffff;font-weight:700;padding:10px 18px;border-radius:12px;box-shadow:0 10px 30px rgba(14,165,233,.4);transition:all .25s;z-index:60}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
#left,#side,#log,#modalBox{scrollbar-width:thin;scrollbar-color:#2c3f6b #0e1a2e}
#left::-webkit-scrollbar,#side::-webkit-scrollbar,#log::-webkit-scrollbar,#modalBox::-webkit-scrollbar{width:10px}
#left::-webkit-scrollbar-track,#side::-webkit-scrollbar-track,#log::-webkit-scrollbar-track,#modalBox::-webkit-scrollbar-track{background:#0e1a2e;border-radius:8px}
#left::-webkit-scrollbar-thumb,#side::-webkit-scrollbar-thumb,#log::-webkit-scrollbar-thumb,#modalBox::-webkit-scrollbar-thumb{background:#2c3f6b;border-radius:8px;border:2px solid #0e1a2e}
#left::-webkit-scrollbar-thumb:hover,#side::-webkit-scrollbar-thumb:hover,#log::-webkit-scrollbar-thumb:hover,#modalBox::-webkit-scrollbar-thumb:hover{background:#4cc3ff}
@media (max-width:1020px){
 body{overflow:auto}
 #wrap{flex-direction:column;height:auto}
 #left{width:100%;order:2;max-height:340px}
 #stage{order:1;height:56vh;min-height:380px}
 #side{width:100%;order:3}
 #hint{display:none}
}
@media print{
 #top,#ctrl,#left,#side,#status,#toast,#modal,#errbar{display:none!important}
 body{overflow:visible;background:#ffffff}
 #wrap{height:auto;padding:0}
 #stage{border:none;height:92vh;background:#ffffff!important}
}
</style></head>
<body>
<div id="errbar"></div>
<div id="top">
<span class="brand">🧪 <em>NetLab</em> · локалка абонента и симуляция трафика</span>
<button class="g" id="bSave">💾 Сохранить</button>
<button class="p" id="bOpen">📂 Открыть</button>
<button id="bSvg">⬇ SVG</button>
<button id="bPng">⬇ PNG</button>
<button id="bPrint">🖨 Печать</button>
<button class="w" id="bLink">🔗 Соединить</button>
<button id="bSel" class="on">🖱 Выбор</button>
<button id="bUndo">↩ Отмена</button>
<button class="d" id="bDel">✕ Удалить</button>
<span id="hint">клик по палитре = добавить · тяни из палитры на холст · 2×клик по холсту = добавить · фон = панорама · колесо = зум</span>
</div>
<div id="ctrl">
<label>Зум <input type="range" id="cZoom" min="30" max="260" value="100"><span class="val" id="vZoom">100%</span></label>
<label>Сетка <input type="checkbox" id="cGrid" checked></label>
<label>Привязка <input type="checkbox" id="cSnap" checked></label>
<label>Скорость <input type="range" id="cSpeed" min="20" max="300" value="100"><span class="val" id="vSpeed">1.0x</span></label>
<label>Свечение <input type="range" id="cGlow" min="0" max="12" value="6"><span class="val" id="vGlow">6</span></label>
<label>Подписи <input type="range" id="cLabel" min="8" max="18" value="11"><span class="val" id="vLabel">11</span></label>
<label>Изгиб <input type="range" id="cCurve" min="0" max="60" value="22"><span class="val" id="vCurve">22</span></label>
<label>Hop, мс <input type="range" id="cHop" min="80" max="1200" value="420"><span class="val" id="vHop">420</span></label>
<label>Тема <select id="cTheme"><option value="dark">тёмная</option><option value="light">светлая</option><option value="blue">blueprint</option></select></label>
<label>Цвет VLAN <input type="checkbox" id="cVcol" checked></label>
<button id="bFit">🎯 Вписать</button>
<button id="bRand">🧹 Автораскладка</button>
<button id="bCfg">♻ Настройки</button>
</div>
<div id="wrap">
<div id="left">
<h4>Устройства · клик или тяни</h4><div id="palDev"></div>
<h4>Шаблоны</h4><div id="palTpl"></div>
<h4>Реестр устройств</h4>
<input id="regSearch" placeholder="🔍 поиск: имя, IP, VLAN, модель">
<select id="regType"><option value="">все типы</option></select>
<select id="regSort"><option value="name">сортировка: имя</option><option value="ip">сортировка: IP</option><option value="vlan">сортировка: VLAN</option><option value="type">сортировка: тип</option></select>
<div id="regCount"></div>
<div id="regList"></div>
<button class="d" id="bBulkDel" style="width:100%;margin-top:6px">✕ Удалить отмеченные</button>
<h4>Схема</h4>
<button id="bDemo" style="width:100%;margin:4px 0">📦 Пример: абонент + PON</button>
<button id="bClear" style="width:100%;margin:4px 0">🧽 Очистить холст</button>
</div>
<div id="stage" class="grid">
<svg id="cv" xmlns="http://www.w3.org/2000/svg">
<defs><filter id="glow" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur id="glowBlur" stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g id="world"><g id="geo"></g><g id="pk"></g></g>
</svg>
</div>
<div id="side">
<h3>🔧 Свойства</h3>
<div id="props"><span style="color:#93a6c9">Выберите устройство или линию на холсте — здесь появятся поля редактирования.</span></div>
<hr>
<h3 class="sim">📡 Симуляция трафика</h3>
<div class="fld"><span>Источник</span><select id="simSrc"></select></div>
<div class="fld"><span>Приёмник</span><select id="simDst"></select></div>
<div class="fld"><span>Режим</span><select id="simMode">
<option value="unicast">unicast · A → B</option>
<option value="multicast">multicast · камера → viewers</option>
<option value="broadcast">broadcast / flood · поиск петли</option>
<option value="pon">PON downstream · OLT → все ONU</option>
</select></div>
<div class="fld"><span>VLAN (реальные VLAN сети — в подсказках поля)</span><input id="simVlan" value="135" list="vlanList"></div>
<div style="display:flex;gap:6px"><button class="g" id="bRun" style="flex:1">▶ Пуск</button><button id="bStop" style="flex:1">⏹ Стоп</button></div>
<div id="log"></div>
</div>
</div>
<div id="status">
<span>Устройств: <b id="stDev">0</b></span>
<span>Линий: <b id="stLink">0</b></span>
<span>Зум: <b id="stZoom">100%</b></span>
<span>Выбрано: <b id="stSel">—</b></span>
<span id="stSim" class="chip">симуляция: остановлена</span>
<span style="margin-left:auto"><span class="chip" style="color:#ff9f43">135 камеры</span> <span class="chip" style="color:#ffc857">1151 IPTV</span> <span class="chip" style="color:#3ddc97">2201 абоненты</span></span>
</div>
<div id="modal"><div id="modalBox"><h3>📂 Сохранённые схемы</h3><div id="modalList"></div><button id="modalClose" style="margin-top:10px">Закрыть</button></div></div>
<div id="toast"></div>
<datalist id="vlanList"></datalist>
<script>
(function(){
'use strict';
window.onerror=function(m){var e=document.getElementById('errbar');e.style.display='block';e.textContent='JS: '+m;};
var TYPES={
 router:{i:'📶',n:'Роутер абонента',c:'#f472b6'},
 switch:{i:'🖧',n:'Коммутатор',c:'#4cc3ff'},
 agg:{i:'🔀',n:'Агрегация',c:'#8b9dff'},
 core:{i:'🌐',n:'Ядро / роутер провайдера',c:'#ff6b6b'},
 olt:{i:'🏢',n:'OLT',c:'#c084fc'},
 split:{i:'🌳',n:'Сплиттер PON',c:'#2dd4bf'},
 onu:{i:'📡',n:'ONU / ONT',c:'#3ddc97'},
 camera:{i:'📹',n:'IP-камера',c:'#ff9f43'},
 pc:{i:'🖥️',n:'ПК / терминал',c:'#9fb2d4'},
 tv:{i:'📺',n:'TV / приставка',c:'#ffd166'},
 nvr:{i:'🗄️',n:'NVR / сервер',c:'#ff6bb5'},
 ap:{i:'📡',n:'Wi-Fi точка',c:'#60a5fa'},
 printer:{i:'🖨️',n:'Принтер',c:'#b8c2d9'}
};
var VLANS=[['135','Камеры ОТТ'],['1151','IPTV multicast'],['2101','Тура · красный'],['2103','Тура · жёлтый'],['2117','Тура · ЖК Клевер к1'],['2201','Михеенко · красный'],['2208','Михеенко · Лихачева 6'],['2301','Королёва · красный'],['2402','Черняховка · оранжевый'],['2601','Жучки · красный'],['2603','Жучки · PON 1'],['2704','Горбуновка · PON'],['2803','ГОП · PON 1'],['2020','Сегмент 02 · МКД'],['2050','Сегмент 05 · МКД'],['2054','Сегмент 05 · PON'],['2080','Сегмент 08 · PON запад'],['2110','Сегмент 11 · МКД'],['2122','Сегмент 12 · PON Кировка'],['2150','Сегмент 15 · PON'],['2171','Сегмент 17 · PON']];
var cfg={grid:true,snap:true,speed:1,glow:6,label:11,curve:0.22,hop:420,theme:'dark',vcol:true};
var S=null,view={x:70,y:50,k:1},sel=null,selLink=null,tool='select',linkFrom=null,lastType='pc';
var drag=null,pan=null,undoStack=[],timers=[],raf=null,hl=[],running=false;
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function dev(id){for(var i=0;i<S.devices.length;i++){if(S.devices[i].id===id)return S.devices[i];}return null;}
function lnk(id){for(var i=0;i<S.links.length;i++){if(S.links[i].id===id)return S.links[i];}return null;}
function hue(v){var h=((parseInt(v,10)||0)*47)%360;return 'hsl('+h+',85%,62%)';}
function toast(t){var el=$('toast');el.textContent=t;el.className='show';clearTimeout(el._t);el._t=setTimeout(function(){el.className='';},1900);}
function log(t,cls){var l=$('log');var d=document.createElement('div');if(cls)d.className=cls;d.textContent=t;l.appendChild(d);l.scrollTop=l.scrollHeight;}
function snap(v){return cfg.snap?Math.round(v/12)*12:v;}
function pushUndo(){undoStack.push(JSON.stringify(S));if(undoStack.length>60)undoStack.shift();}
function autosave(){try{localStorage.setItem('netlab_auto',JSON.stringify(S));}catch(e){}}
function demo(){
 return {nid:13,lid:13,devices:[
  {id:1,type:'core',x:430,y:40,name:'Ядро S6330',ip:'10.163.100.8',vlan:'',model:'S6330',notes:''},
  {id:2,type:'nvr',x:660,y:40,name:'NVR провайдера',ip:'10.135.0.10',vlan:'135',model:'NVR-64',notes:''},
  {id:3,type:'olt',x:430,y:170,name:'OLT Михеенко',ip:'10.163.202.13',vlan:'',model:'PON OLT',notes:''},
  {id:4,type:'split',x:430,y:290,name:'Сплиттер 1:8',ip:'',vlan:'',model:'1x8',notes:''},
  {id:5,type:'onu',x:430,y:410,name:'ONU абонент кв.12',ip:'',vlan:'2201',model:'ONT-1G',notes:'bridge mode'},
  {id:6,type:'router',x:430,y:530,name:'Роутер абонента',ip:'192.168.1.1',vlan:'',model:'Keenetic',notes:''},
  {id:7,type:'switch',x:430,y:650,name:'Свитч квартиры',ip:'192.168.1.2',vlan:'',model:'DES-1008',notes:''},
  {id:8,type:'pc',x:180,y:780,name:'ПК кабинет',ip:'192.168.1.10',vlan:'2201',model:'PC',notes:''},
  {id:9,type:'camera',x:360,y:780,name:'Камера прихожая',ip:'192.168.1.20',vlan:'135',model:'BEWARD',notes:''},
  {id:10,type:'tv',x:540,y:780,name:'TV приставка',ip:'192.168.1.30',vlan:'1151',model:'IPTV STB',notes:''},
  {id:11,type:'printer',x:700,y:780,name:'Принтер',ip:'192.168.1.40',vlan:'2201',model:'HP',notes:''},
  {id:12,type:'ap',x:860,y:780,name:'Wi-Fi точка',ip:'192.168.1.3',vlan:'2201',model:'AP',notes:''}
 ],links:[
  {id:1,a:1,b:3,pa:'4',pb:'uplink',mode:'trunk',vlans:'135,1151,2201',media:'fiber',cost:1},
  {id:2,a:1,b:2,pa:'6',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1},
  {id:3,a:3,b:4,pa:'pon1',pb:'in',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:3},
  {id:4,a:4,b:5,pa:'3',pb:'pon',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:1},
  {id:5,a:5,b:6,pa:'lan1',pb:'wan',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1},
  {id:6,a:6,b:7,pa:'lan1',pb:'1',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1},
  {id:7,a:7,b:8,pa:'2',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1},
  {id:8,a:7,b:9,pa:'3',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1},
  {id:9,a:7,b:10,pa:'4',pb:'1',mode:'access',vlans:'1151',media:'copper',cost:1},
  {id:10,a:7,b:11,pa:'5',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1},
  {id:11,a:7,b:12,pa:'6',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1}
 ]};
}
function render(){
 var light=cfg.theme==='light';
 var ink=light?'#12203a':'#eaf2ff',mut=light?'#5a6b8c':'#9fb2d4';
 var h='';
 S.links.forEach(function(L){
  var a=dev(L.a),b=dev(L.b);if(!a||!b)return;
  var mx=(a.x+b.x)/2,my=(a.y+b.y)/2,dx=b.x-a.x,dy=b.y-a.y,len=Math.sqrt(dx*dx+dy*dy)||1;
  var cx=mx-dy/len*cfg.curve*len*0.5,cy=my+dx/len*cfg.curve*len*0.5;
  var on=selLink===L.id,hot=hl.indexOf(L.id)>=0;
  var col=hot?'#ff6bb5':(on?'#ff6bb5':(cfg.vcol?hue(String(L.vlans).split(',')[0]):(L.media==='fiber'?'#ffc857':(L.media==='pon'?'#2dd4bf':'#7c93b8'))));
  h+='<path data-l="'+L.id+'" d="M'+a.x+' '+a.y+' Q'+cx+' '+cy+' '+b.x+' '+b.y+'" fill="none" stroke="'+col+'" stroke-width="'+((on||hot)?4:2.4)+'" stroke-dasharray="'+(L.media==='pon'?'7 4':'none')+'" style="cursor:pointer" opacity="'+((on||hot)?1:0.85)+'"/>';
  h+='<text x="'+cx+'" y="'+(cy-6)+'" text-anchor="middle" font-size="'+cfg.label+'" fill="'+mut+'" style="pointer-events:none">'+esc(L.pa||'?')+'→'+esc(L.pb||'?')+' · '+(L.mode==='trunk'?'trunk['+esc(L.vlans)+']':'acc'+esc(L.vlans))+'</text>';
 });
 S.devices.forEach(function(d){
  var t=TYPES[d.type]||TYPES.switch,on=sel===d.id;
  h+='<g data-d="'+d.id+'" style="cursor:move">';
  if(on)h+='<rect x="'+(d.x-58)+'" y="'+(d.y-38)+'" width="116" height="76" rx="16" fill="none" stroke="#ff6bb5" stroke-opacity="0.35" stroke-width="6"/>';
  h+='<rect x="'+(d.x-52)+'" y="'+(d.y-32)+'" width="104" height="64" rx="12" fill="'+t.c+'" fill-opacity="'+(light?0.9:0.2)+'" stroke="'+(on?'#ff6bb5':t.c)+'" stroke-width="'+(on?3:1.6)+'"/>';
  h+='<text x="'+d.x+'" y="'+(d.y-8)+'" text-anchor="middle" font-size="19">'+t.i+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+9)+'" text-anchor="middle" font-size="'+cfg.label+'" font-weight="700" fill="'+(light?'#0d1728':ink)+'">'+esc((d.name||t.n).slice(0,18))+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+24)+'" text-anchor="middle" font-size="'+(cfg.label-1)+'" fill="'+(light?'#41537a':mut)+'">'+esc(d.ip||'')+(d.vlan?' · v'+esc(d.vlan):'')+'</text>';
  h+='</g>';
 });
 $('geo').innerHTML=h;
 $('world').setAttribute('transform','translate('+view.x+','+view.y+') scale('+view.k+')');
 $('glowBlur').setAttribute('stdDeviation',cfg.glow);
 $('stDev').textContent=S.devices.length;
 $('stLink').textContent=S.links.length;
 $('stZoom').textContent=Math.round(view.k*100)+'%';
 $('vZoom').textContent=Math.round(view.k*100)+'%';
 $('cZoom').value=Math.round(view.k*100);
 $('stSel').textContent=sel!=null?('#'+sel+' '+(dev(sel)?dev(sel).name:'')):(selLink!=null?('линия #'+selLink):'—');
 fillSim();
 fillReg();
}
function fillSim(){
 var o=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+' · '+(esc(d.ip||('#'+d.id)))+'</option>';}).join('');
 var a=$('simSrc'),b=$('simDst'),av=a.value,bv=b.value;
 a.innerHTML=o;b.innerHTML=o;
 if(av&&dev(+av))a.value=av;else{var nvr=null;S.devices.forEach(function(d){if(d.type==='nvr')nvr=d.id;});a.value=nvr||(S.devices[0]?S.devices[0].id:'');}
 if(bv&&dev(+bv))b.value=bv;else{var cam=null;S.devices.forEach(function(d){if(d.type==='camera')cam=d.id;});b.value=cam||(S.devices[1]?S.devices[1].id:'');}
}
function fillReg(){
 var q=($('regSearch').value||'').toLowerCase(),ft=$('regType').value,sort=$('regSort').value;
 var rows=S.devices.filter(function(d){
  if(ft&&d.type!==ft)return false;
  if(!q)return true;
  return ((d.name||'')+' '+(d.ip||'')+' '+(d.vlan||'')+' '+(d.model||'')+' '+TYPES[d.type].n).toLowerCase().indexOf(q)>=0;
 });
 rows.sort(function(a,b){
  var ka,kb;
  if(sort==='ip'){ka=a.ip||'';kb=b.ip||'';return ka.localeCompare(kb,'ru',{numeric:true});}
  if(sort==='vlan'){return (parseInt(a.vlan,10)||0)-(parseInt(b.vlan,10)||0);}
  if(sort==='type'){return (a.type||'').localeCompare(b.type||'');}
  return (a.name||'').localeCompare(b.name||'','ru');
 });
 $('regCount').textContent='показано '+rows.length+' из '+S.devices.length;
 $('regList').innerHTML=rows.map(function(d){
  return '<div class="regRow'+(sel===d.id?' sel':'')+'" data-reg="'+d.id+'"><input type="checkbox" data-chk="'+d.id+'"><i style="font-style:normal">'+TYPES[d.type].i+'</i><span class="nm">'+esc(d.name||TYPES[d.type].n)+'</span><span class="vl">'+(d.vlan?'v'+esc(d.vlan):'—')+'</span></div>';
 }).join('')||'<div style="color:#7f93b8;font-size:12px">ничего не найдено</div>';
}
function palette(){
 $('palDev').innerHTML=Object.keys(TYPES).map(function(k){
  return '<button draggable="true" data-add="'+k+'"><i>'+TYPES[k].i+'</i>'+TYPES[k].n+'</button>';
 }).join('');
 $('palTpl').innerHTML='<button data-tpl="sub"><i>🏠</i>Абонентская локалка</button><button data-tpl="pod"><i>🏢</i>Подъезд: DES + камеры</button><button data-tpl="core"><i>🌐</i>Ядро + агрегация + OLT</button>';
 $('regType').innerHTML='<option value="">все типы</option>'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'">'+TYPES[k].n+'</option>';}).join('');
 $('vlanList').innerHTML=VLANS.map(function(v){return '<option value="'+v[0]+'">'+v[0]+' · '+v[1]+'</option>';}).join('');
}
function center(){var r=$('cv').getBoundingClientRect();return {x:(r.width/2-view.x)/view.k,y:(r.height/2-view.y)/view.k};}
function addDevice(k,x,y){
 pushUndo();lastType=k;var c=center();
 var d={id:S.nid++,type:k,x:snap(x==null?c.x+(Math.random()*120-60):x),y:snap(y==null?c.y+(Math.random()*90-45):y),name:'',ip:'',vlan:(k==='camera'?'135':(k==='tv'?'1151':(k==='pc'||k==='onu'||k==='printer'||k==='ap')?'2201':'')),model:'',notes:''};
 S.devices.push(d);sel=d.id;selLink=null;autosave();props();render();toast('Добавлено: '+TYPES[k].n);
}
function addTpl(k){
 pushUndo();var c=center();
 function mk(t,dx,dy,name,ip,vlan){var id=S.nid++;S.devices.push({id:id,type:t,x:snap(c.x+dx),y:snap(c.y+dy),name:name,ip:ip,vlan:vlan||'',model:'',notes:''});return id;}
 function L(a,b,pa,pb,mode,vlans,media){S.links.push({id:S.lid++,a:a,b:b,pa:pa,pb:pb,mode:mode,vlans:vlans,media:media||'copper',cost:1});}
 if(k==='sub'){
  var r=mk('router',0,-140,'Роутер абонента','192.168.1.1',''),sw=mk('switch',0,-20,'Свитч квартиры','192.168.1.2','');
  var pc=mk('pc',-220,120,'ПК','192.168.1.10','2201'),cam=mk('camera',-70,120,'Камера','192.168.1.20','135'),tv=mk('tv',80,120,'TV','192.168.1.30','1151'),pr=mk('printer',230,120,'Принтер','192.168.1.40','2201');
  L(r,sw,'lan1','1','trunk','135,1151,2201');L(sw,pc,'2','1','access','2201');L(sw,cam,'3','1','access','135');L(sw,tv,'4','1','access','1151');L(sw,pr,'5','1','access','2201');
 }
 if(k==='pod'){
  var s1=mk('switch',0,-120,'DES-3200 подъезд','10.163.202.88',''),c1=mk('camera',-160,20,'Камера БР-1','10.135.1.21','135'),c2=mk('camera',0,20,'Камера БР-2','10.135.1.22','135'),p1=mk('pc',160,20,'Абонент кв.1','10.163.202.11','2201');
  L(s1,c1,'21','1','access','135');L(s1,c2,'22','1','access','135');L(s1,p1,'12','1','access','2201');
 }
 if(k==='core'){
  var co=mk('core',0,-160,'Ядро','10.163.100.8',''),ag=mk('agg',0,-40,'Агрегация','10.163.100.2',''),ol=mk('olt',-160,80,'OLT','10.163.206.8',''),s2=mk('switch',160,80,'DES доступ','10.163.202.13','');
  L(co,ag,'1','1','trunk','135,1151,2201,2601','fiber');L(ag,ol,'2','uplink','trunk','135,1151,2601','fiber');L(ag,s2,'3','28','trunk','135,1151,2201','fiber');
 }
 autosave();props();render();toast('Шаблон добавлен');
}
function pt(e){var r=$('cv').getBoundingClientRect();return {x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k};}
function setTool(t){tool=t;linkFrom=null;$('bLink').className=(t==='link')?'w on':'w';$('bSel').className=(t==='select')?'on':'';
 $('hint').textContent=(t==='link')?'РЕЖИМ ЛИНИИ: кликните устройство A, затем устройство B':'клик по палитре = добавить · тяни из палитры на холст · 2×клик по холсту = добавить · фон = панорама · колесо = зум';}
function props(){
 var p=$('props');
 if(selLink!=null){
  var L=lnk(selLink);if(!L){selLink=null;p.innerHTML='';return;}
  p.innerHTML='<div class="fld"><span>Линия #'+L.id+' · '+esc((dev(L.a)||{}).name||'')+' ↔ '+esc((dev(L.b)||{}).name||'')+'</span></div>'
  +'<div class="fld"><span>Порт A</span><input data-lf="pa" value="'+esc(L.pa)+'"></div>'
  +'<div class="fld"><span>Порт B</span><input data-lf="pb" value="'+esc(L.pb)+'"></div>'
  +'<div class="fld"><span>Режим</span><select data-lf="mode"><option value="trunk"'+(L.mode==='trunk'?' selected':'')+'>trunk</option><option value="access"'+(L.mode==='access'?' selected':'')+'>access</option></select></div>'
  +'<div class="fld"><span>VLAN-ы через запятую</span><input data-lf="vlans" list="vlanList" value="'+esc(L.vlans)+'"></div>'
  +'<div class="fld"><span>Среда</span><select data-lf="media"><option value="copper"'+(L.media==='copper'?' selected':'')+'>медь</option><option value="fiber"'+(L.media==='fiber'?' selected':'')+'>оптика</option><option value="pon"'+(L.media==='pon'?' selected':'')+'>PON</option></select></div>'
  +'<div class="fld"><span>Задержка, мс</span><input type="number" data-lf="cost" value="'+(L.cost||1)+'"></div>'
  +'<button class="d" id="pDel" style="width:100%">✕ Удалить линию</button>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-lf]'),function(inp){inp.addEventListener('input',function(){pushUndo();L[inp.getAttribute('data-lf')]=inp.value;autosave();render();});});
  $('pDel').addEventListener('click',delSel);
  return;
 }
 if(sel!=null){
  var d=dev(sel);if(!d){sel=null;p.innerHTML='';return;}
  var conns=S.links.filter(function(L){return L.a===sel||L.b===sel;}).map(function(L){
   var o=dev(L.a===sel?L.b:L.a);return '<div style="color:#93a6c9;font-size:12px">↔ '+esc(o?o.name:'?')+' · '+(L.a===sel?esc(L.pa):esc(L.pb))+'→'+(L.a===sel?esc(L.pb):esc(L.pa))+' · '+L.mode+'['+esc(L.vlans)+']</div>';
  }).join('');
  p.innerHTML='<div class="fld"><span>Тип</span><select data-df="type">'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'"'+(d.type===k?' selected':'')+'>'+TYPES[k].i+' '+TYPES[k].n+'</option>';}).join('')+'</select></div>'
  +'<div class="fld"><span>Имя</span><input data-df="name" value="'+esc(d.name)+'"></div>'
  +'<div class="fld"><span>IP</span><input data-df="ip" value="'+esc(d.ip)+'"></div>'
  +'<div class="fld"><span>Access-VLAN</span><input data-df="vlan" list="vlanList" value="'+esc(d.vlan)+'"></div>'
  +'<div class="fld"><span>Модель</span><input data-df="model" value="'+esc(d.model)+'"></div>'
  +'<div class="fld"><span>Заметки</span><textarea data-df="notes" rows="2">'+esc(d.notes)+'</textarea></div>'
  +'<div class="fld"><span>Подключения</span>'+(conns||'<div style="color:#7f93b8;font-size:12px">нет линий</div>')+'</div>'
  +'<button class="d" id="pDel" style="width:100%">✕ Удалить устройство</button>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-df]'),function(inp){inp.addEventListener('input',function(){pushUndo();d[inp.getAttribute('data-df')]=inp.value;autosave();render();});});
  $('pDel').addEventListener('click',delSel);
  return;
 }
 p.innerHTML='<span style="color:#93a6c9">Выберите устройство или линию на холсте — здесь появятся поля редактирования.</span>';
}
function delSel(){
 stopSim();pushUndo();
 if(selLink!=null){S.links=S.links.filter(function(L){return L.id!==selLink;});selLink=null;toast('Линия удалена');}
 else if(sel!=null){S.links=S.links.filter(function(L){return L.a!==sel&&L.b!==sel;});S.devices=S.devices.filter(function(d){return d.id!==sel;});sel=null;toast('Устройство удалено');}
 autosave();props();render();
}
function undo(){if(!undoStack.length){toast('Нечего отменять');return;}S=JSON.parse(undoStack.pop());sel=null;selLink=null;autosave();props();render();toast('Отменено');}
function allows(L,v){var list=String(L.vlans||'').split(',').map(function(x){return x.trim();});return L.mode==='trunk'?list.indexOf(String(v))>=0:String(L.vlans)===String(v);}
function nbrs(id,v){var out=[];S.links.forEach(function(L){if(L.a===id&&allows(L,v))out.push({to:L.b,L:L});if(L.b===id&&allows(L,v))out.push({to:L.a,L:L});});return out;}
function path(s,d,v){var prev={},seen={},q=[s];seen[s]=1;
 while(q.length){var c=q.shift();if(c===d)break;var ns=nbrs(c,v);for(var i=0;i<ns.length;i++){var n=ns[i];if(!seen[n.to]){seen[n.to]=1;prev[n.to]={f:c,L:n.L};q.push(n.to);}}}
 if(!seen[d])return null;var hops=[],cur=d;while(cur!==s){var p=prev[cur];hops.unshift({from:p.f,to:cur,L:p.L});cur=p.f;}return hops;}
function packet(a,b,color,dur,cb){
 var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
 c.setAttribute('r','6');c.setAttribute('fill',color);c.setAttribute('filter','url(#glow)');c.setAttribute('stroke','#ffffff');c.setAttribute('stroke-width','1');
 $('pk').appendChild(c);var t0=performance.now();
 function step(t){var k=Math.min(1,(t-t0)/dur);c.setAttribute('cx',a.x+(b.x-a.x)*k);c.setAttribute('cy',a.y+(b.y-a.y)*k);if(k<1){raf=requestAnimationFrame(step);}else{if(c.parentNode)c.parentNode.removeChild(c);if(cb)cb();}}
 raf=requestAnimationFrame(step);
}
function runHops(hops,v,label,done){
 var col=hue(v),i=0;
 function next(){
  if(i>=hops.length){if(done)done();return;}
  var h=hops[i],a=dev(h.from),b=dev(h.to);
  if(!a||!b){if(done)done();return;}
  if(hl.indexOf(h.L.id)<0)hl.push(h.L.id);
  render();
  packet(a,b,col,600/cfg.speed,function(){
   log(label+' hop'+(i+1)+': '+(a.name||a.id)+' → '+(b.name||b.id)+'  ['+(h.L.mode==='trunk'?'trunk v'+v+' OK':'access v'+v+' OK')+'] +'+(h.L.cost||1)+'ms','ok');
   i++;timers.push(setTimeout(next,cfg.hop/cfg.speed));
  });
 }
 next();
}
function stopSim(){for(var i=0;i<timers.length;i++)clearTimeout(timers[i]);timers=[];if(raf)cancelAnimationFrame(raf);raf=null;$('pk').innerHTML='';hl=[];running=false;$('stSim').textContent='симуляция: остановлена';$('stSim').style.color='';render();}
function run(){
 stopSim();$('log').innerHTML='';running=true;$('stSim').textContent='симуляция: идёт…';$('stSim').style.color='#3ddc97';
 var s=+$('simSrc').value,d=+$('simDst').value,mode=$('simMode').value,v=$('simVlan').value||'1';
 var sd=dev(s);if(!sd){log('нет источника','bad');stopSim();return;}
 log('▶ '+mode+' · VLAN '+v+' · от '+(sd.name||sd.id),'info');
 if(mode==='unicast'){
  var dd=dev(d);
  if(dd&&dd.vlan&&String(dd.vlan)!==String(v))log('⚠️ приёмник '+(dd.name||d)+' в VLAN '+dd.vlan+', пакет в VLAN '+v,'warn');
  var hops=path(s,d,v);
  if(!hops){log('❌ пути нет: VLAN '+v+' не пропущен на транке или access-VLAN не совпадает. Проверьте trunk-списки!','bad');stopSim();return;}
  var ms=0;for(var i=0;i<hops.length;i++)ms+=(+hops[i].L.cost||1);
  runHops(hops,v,'📨',function(){log('✅ доставлено за '+ms+' мс через '+hops.length+' hop(s)','ok');stopSim();});
 }else if(mode==='multicast'){
  var viewers=S.devices.filter(function(x){return x.id!==s&&String(x.vlan)===String(v)&&(x.type==='pc'||x.type==='nvr'||x.type==='printer'||x.type==='tv'||x.type==='camera');});
  if(!viewers.length){log('❌ нет получателей с VLAN '+v,'bad');stopSim();return;}
  var left=viewers.length;
  viewers.forEach(function(x){var h=path(s,x.id,v);
   if(h){runHops(h,v,'📺→'+(x.name||x.id),function(){left--;if(left===0){log('✅ multicast доставлен '+viewers.length+' получателям','ok');stopSim();}});}
   else{log('❌ '+(x.name||x.id)+': VLAN '+v+' не доходит','bad');left--;if(left===0)stopSim();}});
 }else if(mode==='pon'){
  var onus=S.devices.filter(function(x){return x.type==='onu';});
  if(!onus.length){log('❌ на схеме нет ONU','bad');stopSim();return;}
  var left2=onus.length;
  onus.forEach(function(x){var h=path(s,x.id,v);
   if(h){runHops(h,v,'🌊PON→'+(x.name||x.id),function(){log('ℹ️ '+(x.name||x.id)+': '+(String(x.vlan)===String(v)?'принимает поток (VLAN совпал)':'отбрасывает (VLAN '+x.vlan+' ≠ '+v+')'),String(x.vlan)===String(v)?'ok':'warn');left2--;if(left2===0)stopSim();});}
   else{log('❌ '+(x.name||x.id)+': нет пути PON','bad');left2--;if(left2===0)stopSim();}});
 }else{
  var seen={},q=[s],edges=[],storm=false;seen[s]=1;
  while(q.length){var c=q.shift();var ns=nbrs(c,v);for(var j=0;j<ns.length;j++){var n=ns[j];edges.push({from:c,to:n.to,L:n.L});if(seen[n.to])storm=true;else{seen[n.to]=1;q.push(n.to);}}}
  edges.forEach(function(e,i){timers.push(setTimeout(function(){var a=dev(e.from),b=dev(e.to);if(a&&b){packet(a,b,hue(v),500/cfg.speed,null);log('🌊 '+(a.name||a.id)+' → '+(b.name||b.id),'info');}},i*140/cfg.speed));});
  timers.push(setTimeout(function(){log(storm?'⚠️ ПЕТЛЯ ОБНАРУЖЕНА → broadcast-шторм! Включите loopdetect / RSTP':'🌊 flood дошёл до '+Object.keys(seen).length+' устройств',storm?'warn':'ok');stopSim();},edges.length*140/cfg.speed+900));
 }
}
function pin(){return localStorage.getItem('swhpin')||prompt('PIN админки:')||'';}
function save(){
 var name=prompt('Название схемы:','Локалка абонента '+new Date().toLocaleDateString('ru'));
 if(!name)return;
 fetch('/api/schemes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin(),name:name,data:JSON.stringify(S)})})
 .then(function(r){return r.json();}).then(function(res){toast(res.ok?('Сохранено #'+res.id):('Ошибка: '+(res.error||'')));})
 .catch(function(e){toast('Ошибка: '+e.message);});
}
function openModal(){
 fetch('/api/schemes').then(function(r){return r.json();}).then(function(rows){
  $('modalList').innerHTML=(rows||[]).map(function(r){
   return '<div class="mRow"><span class="t">'+esc(r.name)+'</span><span class="d">'+esc(r.updated_at||'')+'</span><button class="p" data-open="'+r.id+'">Открыть</button><button class="d" data-mdel="'+r.id+'">✕</button></div>';
  }).join('')||'<div style="color:#93a6c9">Сохранённых схем нет.</div>';
  $('modal').className='open';
 }).catch(function(e){toast('Ошибка: '+e.message);});
}
function exportSvg(){
 var clone=$('cv').cloneNode(true);
 clone.setAttribute('width','1600');clone.setAttribute('height','1000');
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
 bg.setAttribute('width','1600');bg.setAttribute('height','1000');bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0d1728');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
 var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='netlab-scheme.svg';a.click();toast('SVG скачан');
}
function exportPng(){
 var clone=$('cv').cloneNode(true);clone.setAttribute('width','1600');clone.setAttribute('height','1000');
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');
 bg.setAttribute('width','1600');bg.setAttribute('height','1000');bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0d1728');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
 var img=new Image();
 img.onload=function(){var c=document.createElement('canvas');c.width=1600;c.height=1000;var ctx=c.getContext('2d');ctx.drawImage(img,0,0);var a=document.createElement('a');a.href=c.toDataURL('image/png');a.download='netlab-scheme.png';a.click();toast('PNG скачан');};
 img.onerror=function(){toast('PNG не удалось — используйте SVG');};
 img.src=URL.createObjectURL(blob);
}
function fit(){
 if(!S.devices.length){view={x:70,y:50,k:1};render();return;}
 var minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;
 S.devices.forEach(function(d){minX=Math.min(minX,d.x-60);maxX=Math.max(maxX,d.x+60);minY=Math.min(minY,d.y-40);maxY=Math.max(maxY,d.y+40);});
 var r=$('cv').getBoundingClientRect();
 var k=Math.min((r.width-60)/(maxX-minX),(r.height-60)/(maxY-minY));
 k=Math.max(0.3,Math.min(2.2,k));
 view.k=k;view.x=(r.width-(maxX-minX)*k)/2-minX*k;view.y=(r.height-(maxY-minY)*k)/2-minY*k;
 render();toast('Схема вписана');
}
function tidy(){
 pushUndo();
 var hasP={};S.links.forEach(function(L){hasP[L.b]=1;});
 var roots=S.devices.filter(function(d){return !hasP[d.id];}).map(function(d){return d.id;});
 if(!roots.length&&S.devices[0])roots=[S.devices[0].id];
 var lvl={},seen={},q=roots.map(function(r){return [r,0];});
 while(q.length){var it=q.shift();if(seen[it[0]])continue;seen[it[0]]=1;lvl[it[0]]=it[1];
  S.links.forEach(function(L){if(L.a===it[0])q.push([L.b,it[1]+1]);});}
 var by={};S.devices.forEach(function(d){var l=(lvl[d.id]==null)?4:lvl[d.id];(by[l]=by[l]||[]).push(d);});
 Object.keys(by).forEach(function(l){by[l].forEach(function(d,i){d.x=120+i*230;d.y=70+(+l)*150;});});
 autosave();render();fit();toast('Автораскладка по уровням');
}
function bind(){
 $('cv').addEventListener('pointerdown',function(e){
  var t=e.target,g=null,l=null;
  while(t&&t!==$('cv')){if(t.getAttribute){if(t.getAttribute('data-d')){g=t;break;}if(t.getAttribute('data-l')){l=t;break;}}t=t.parentNode;}
  if(g){var id=+g.getAttribute('data-d');
   if(tool==='link'){
    if(linkFrom==null){linkFrom=id;log('🔗 линия от #'+id+' — кликните второе устройство','info');}
    else if(linkFrom!==id){pushUndo();S.links.push({id:S.lid++,a:linkFrom,b:id,pa:'',pb:'',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1});linkFrom=null;setTool('select');autosave();props();render();toast('Линия создана — задайте порты справа');}
    return;}
   sel=id;selLink=null;props();var p=pt(e),d=dev(id);drag={id:id,dx:p.x-d.x,dy:p.y-d.y};pushUndo();render();return;}
  if(l){selLink=+l.getAttribute('data-l');sel=null;props();render();return;}
  sel=null;selLink=null;props();pan={x:e.clientX-view.x,y:e.clientY-view.y};render();
 });
 window.addEventListener('pointermove',function(e){
  if(drag){var p=pt(e),d=dev(drag.id);if(d){d.x=snap(p.x-drag.dx);d.y=snap(p.y-drag.dy);render();}}
  else if(pan){view.x=e.clientX-pan.x;view.y=e.clientY-pan.y;render();}
 });
 window.addEventListener('pointerup',function(){if(drag)autosave();drag=null;pan=null;});
 $('cv').addEventListener('wheel',function(e){
  e.preventDefault();var r=$('cv').getBoundingClientRect();var mx=e.clientX-r.left,my=e.clientY-r.top;
  var f=e.deltaY<0?1.12:0.89,nk=Math.max(0.3,Math.min(2.6,view.k*f));
  view.x=mx-(mx-view.x)*(nk/view.k);view.y=my-(my-view.y)*(nk/view.k);view.k=nk;render();
 },{passive:false});
 $('cv').addEventListener('dblclick',function(e){var p=pt(e);addDevice(lastType||'pc',p.x,p.y);});
 $('cv').addEventListener('dragover',function(e){e.preventDefault();});
 $('cv').addEventListener('drop',function(e){
  e.preventDefault();var k=e.dataTransfer?e.dataTransfer.getData('text/plain'):'';
  if(k&&TYPES[k]){var p=pt(e);addDevice(k,p.x,p.y);}
 });
 $('palDev').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){addDevice(t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palDev').addEventListener('dragstart',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){if(e.dataTransfer)e.dataTransfer.setData('text/plain',t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palTpl').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palTpl')){if(t.getAttribute&&t.getAttribute('data-tpl')){addTpl(t.getAttribute('data-tpl'));return;}t=t.parentNode;}});
 $('regSearch').addEventListener('input',fillReg);
 $('regType').addEventListener('change',fillReg);
 $('regSort').addEventListener('change',fillReg);
 $('regList').addEventListener('click',function(e){
  var t=e.target;
  if(t.getAttribute&&t.getAttribute('data-chk'))return;
  while(t&&t!==$('regList')){if(t.getAttribute&&t.getAttribute('data-reg')){var id=+t.getAttribute('data-reg');sel=id;selLink=null;var d=dev(id);
   if(d){var r=$('cv').getBoundingClientRect();view.x=r.width/2-d.x*view.k;view.y=r.height/2-d.y*view.k;}
   props();render();return;}t=t.parentNode;}
 });
 $('bBulkDel').addEventListener('click',function(){
  var ids=[];Array.prototype.forEach.call($('regList').querySelectorAll('[data-chk]'),function(c){if(c.checked)ids.push(+c.getAttribute('data-chk'));});
  if(!ids.length){toast('Отметьте устройства галочками');return;}
  if(!confirm('Удалить отмеченные устройства ('+ids.length+')?'))return;
  stopSim();pushUndo();
  S.links=S.links.filter(function(L){return ids.indexOf(L.a)<0&&ids.indexOf(L.b)<0;});
  S.devices=S.devices.filter(function(d){return ids.indexOf(d.id)<0;});
  sel=null;selLink=null;autosave();props();render();toast('Удалено: '+ids.length);
 });
 $('bSave').addEventListener('click',save);
 $('bOpen').addEventListener('click',openModal);
 $('modalClose').addEventListener('click',function(){$('modal').className='';});
 $('modal').addEventListener('click',function(e){if(e.target===$('modal'))$('modal').className='';});
 $('modalList').addEventListener('click',function(e){
  var t=e.target;while(t&&t!==$('modalList')){
   if(t.getAttribute&&t.getAttribute('data-open')){var id=t.getAttribute('data-open');
    fetch('/api/schemes/'+id).then(function(r){return r.json();}).then(function(sc){if(sc&&sc.data){pushUndo();S=JSON.parse(sc.data);sel=null;selLink=null;autosave();props();render();fit();$('modal').className='';toast('Открыто: '+sc.name);}});return;}
   if(t.getAttribute&&t.getAttribute('data-mdel')){var did=t.getAttribute('data-mdel');
    if(confirm('Удалить схему #'+did+'?')){fetch('/api/schemes/'+did,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin()})}).then(function(r){return r.json();}).then(function(){openModal();toast('Схема удалена');});}return;}
   t=t.parentNode;}
 });
 $('bSvg').addEventListener('click',exportSvg);
 $('bPng').addEventListener('click',exportPng);
 $('bPrint').addEventListener('click',function(){window.print();});
 $('bLink').addEventListener('click',function(){setTool(tool==='link'?'select':'link');});
 $('bSel').addEventListener('click',function(){setTool('select');});
 $('bUndo').addEventListener('click',undo);
 $('bDel').addEventListener('click',delSel);
 $('bRun').addEventListener('click',run);
 $('bStop').addEventListener('click',function(){stopSim();log('⏹ остановлено','info');});
 $('bDemo').addEventListener('click',function(){pushUndo();S=demo();sel=null;selLink=null;autosave();props();render();fit();toast('Пример загружен');});
 $('bClear').addEventListener('click',function(){if(!confirm('Очистить холст?'))return;stopSim();pushUndo();S={nid:1,lid:1,devices:[],links:[]};sel=null;selLink=null;autosave();props();render();});
 $('bFit').addEventListener('click',fit);
 $('bRand').addEventListener('click',tidy);
 $('cZoom').addEventListener('input',function(){view.k=this.value/100;render();});
 $('cGrid').addEventListener('change',function(){cfg.grid=this.checked;stageClass();});
 $('cSnap').addEventListener('change',function(){cfg.snap=this.checked;});
 $('cSpeed').addEventListener('input',function(){cfg.speed=this.value/100;$('vSpeed').textContent=cfg.speed.toFixed(1)+'x';});
 $('cGlow').addEventListener('input',function(){cfg.glow=+this.value;$('vGlow').textContent=this.value;render();});
 $('cLabel').addEventListener('input',function(){cfg.label=+this.value;$('vLabel').textContent=this.value;render();});
 $('cCurve').addEventListener('input',function(){cfg.curve=this.value/100;$('vCurve').textContent=this.value;render();});
 $('cHop').addEventListener('input',function(){cfg.hop=+this.value;$('vHop').textContent=this.value;});
 $('cTheme').addEventListener('change',function(){cfg.theme=this.value;stageClass();render();});
 $('cVcol').addEventListener('change',function(){cfg.vcol=this.checked;render();});
 $('bCfg').addEventListener('click',function(){
  cfg={grid:true,snap:true,speed:1,glow:6,label:11,curve:0.22,hop:420,theme:'dark',vcol:true};
  $('cZoom').value=100;$('cGrid').checked=true;$('cSnap').checked=true;$('cSpeed').value=100;$('cGlow').value=6;$('cLabel').value=11;$('cCurve').value=22;$('cHop').value=420;$('cTheme').value='dark';$('cVcol').checked=true;
  $('vSpeed').textContent='1.0x';$('vGlow').textContent='6';$('vLabel').textContent='11';$('vCurve').textContent='22';$('vHop').textContent='420';
  stageClass();view={x:70,y:50,k:1};render();toast('Настройки сброшены');
 });
 window.addEventListener('keydown',function(e){
  var tag=e.target?e.target.tagName:'';
  if(tag==='INPUT'||tag==='SELECT'||tag==='TEXTAREA')return;
  if(e.key==='Delete'||e.key==='Backspace'){delSel();e.preventDefault();}
  if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='z'){undo();e.preventDefault();}
  if(e.key==='Escape'){setTool('select');sel=null;selLink=null;props();render();}
 });
 window.addEventListener('resize',function(){render();});
}
function stageClass(){$('stage').className=(cfg.grid?'grid ':'')+cfg.theme;}
palette();bind();
var saved=null;try{saved=localStorage.getItem('netlab_auto');}catch(e){}
try{S=saved?JSON.parse(saved):demo();}catch(e){S=demo();}
if(!S||!S.devices||!S.links)S=demo();
stageClass();props();render();fit();
log('🧪 NetLab готов: абонентская локалка + PON. Устройств: '+S.devices.length+', линий: '+S.links.length,'info');
log('Добавляйте устройства кликом по палитре или перетаскиванием, соединяйте «🔗 Соединить», затем ▶ Пуск.','info');
})();
</script>
</body></html>
'''
open(os.path.join('static', 'netlab.html'), 'w', encoding='utf-8').write(HTML)
print('ok: static/netlab.html записан (' + str(len(HTML)) + ' байт)')

src = open('swh.py', encoding='utf-8').read()
if "static', 'netlab.html'" not in src:
    new_src, n = re.subn(
        r"def netlab_page\(\):\n    return [^\n]+\n",
        "def netlab_page():\n"
        "    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'netlab.html')\n"
        "    r = Response(open(p, encoding='utf-8').read(), mimetype='text/html')\n"
        "    r.headers['Cache-Control'] = 'no-store'\n"
        "    return r\n",
        src, count=1)
    if n:
        src = new_src
        print('ok: /netlab отдаёт файл static/netlab.html (no-store, без Jinja)')
    else:
        print('ПРОПУСК: маршрут netlab_page не найден')
else:
    print('ok: маршрут уже файловый')

try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v24_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v24',
           'fixes': ['netlab standalone file', 'literal colors (видимость текста)', 'seeded subscriber LAN + PON',
                     'palette click+drag+dblclick', 'registry search/filter/sort/bulk delete',
                     'inspector CRUD', 'undo', 'sim unicast/multicast/broadcast/PON', '12 live controls',
                     'save/load/delete schemes modal', 'SVG/PNG/print', 'fit/auto-layout', 'mobile', 'custom scrollbars']},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v24. Бэкап: backups/swh_pre_v24_' + TS + '.py')
