# update.py — v25b: NetLab PRO (тот же функционал) + ИСПРАВЛЕННЫЙ self-check (не падает на JS-id)
import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
os.makedirs('static', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v25b_' + TS + '.py')
if os.path.exists('static/netlab.html'):
    shutil.copyfile('static/netlab.html', 'backups/netlab_pre_v25b_' + TS + '.html')

HTML = r'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NetLab PRO — схемы, планы и симуляция трафика</title>
<style>
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:#070d18;color:#eaf2ff;font:14px/1.45 "Segoe UI",system-ui,Arial,sans-serif;overflow:hidden}
#errbar{display:none;position:fixed;top:0;left:0;right:0;z-index:99;background:#7f1d1d;color:#ffe4e6;padding:8px 14px;font:12px Consolas,monospace}
#top{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 12px;background:linear-gradient(90deg,#0b1526,#12233f 45%,#1a1030 80%,#0b1526);border-bottom:1px solid #22345c;position:relative;z-index:6}
#top .brand{font-weight:800;font-size:15px;letter-spacing:.4px;margin-right:6px}
#top .brand em{font-style:normal;color:#4cc3ff}
#top .brand small{color:#8fa2c4;font-weight:600;font-size:11px;margin-left:6px}
button{font:600 12.5px "Segoe UI",Arial;color:#eaf2ff;background:#182741;border:1px solid #2c3f6b;border-radius:9px;padding:7px 11px;cursor:pointer;transition:transform .12s,filter .12s,background .12s}
button:hover{transform:translateY(-1px);filter:brightness(1.22)}
button:active{transform:translateY(0)}
button.p{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent;color:#fff}
button.g{background:linear-gradient(135deg,#059669,#10b981);border-color:transparent;color:#fff}
button.w{background:linear-gradient(135deg,#d97706,#f59e0b);border-color:transparent;color:#221503}
button.d{background:linear-gradient(135deg,#dc2626,#f43f5e);border-color:transparent;color:#fff}
button.m{background:linear-gradient(135deg,#7c3aed,#d946ef);border-color:transparent;color:#fff}
button.on{outline:2px solid #4cc3ff;outline-offset:1px}
button:disabled{opacity:.45;cursor:not-allowed;transform:none}
#hint{margin-left:auto;color:#93a6c9;font-size:11.5px;max-width:340px;text-align:right}
#ctrl{display:flex;align-items:center;gap:13px;flex-wrap:wrap;padding:7px 12px;background:#0e1a2e;border-bottom:1px solid #22345c;position:relative;z-index:5}
#ctrl label{display:flex;align-items:center;gap:6px;color:#93a6c9;font-size:12px;white-space:nowrap}
#ctrl input[type=range]{width:88px;accent-color:#4cc3ff}
#ctrl input[type=checkbox]{width:15px;height:15px;accent-color:#3ddc97}
#ctrl select{background:#16233c;color:#eaf2ff;border:1px solid #2c3f6b;border-radius:7px;padding:4px 6px;font-size:12px}
#ctrl .val{color:#4cc3ff;min-width:34px;text-align:right;font-variant-numeric:tabular-nums}
#wrap{display:flex;gap:8px;padding:8px;height:calc(100% - 104px)}
#left{width:250px;flex:none;background:#0e1a2e;border:1px solid #22345c;border-radius:14px;padding:10px;overflow-y:auto}
#left h4{margin:8px 0 6px;font-size:11px;letter-spacing:1.2px;color:#7f93b8;text-transform:uppercase}
#palDev button,#palTpl button{display:flex;width:100%;align-items:center;gap:8px;margin:4px 0;text-align:left;background:#16233c;border:1px solid #263a63;color:#dfe9ff}
#palDev button:hover,#palTpl button:hover{background:#1d2f4f}
#palDev button i,#palTpl button i{font-style:normal;font-size:16px;width:20px;text-align:center}
#palTpl button{background:linear-gradient(135deg,#182a4a,#2a1f4d);border-color:#3b4c78}
#regSearch,#regType,#regSort,#bulkVlan,#viewName{width:100%;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:6px 8px;font-size:12.5px;margin:3px 0}
#regList{margin-top:6px}
.regRow{display:flex;align-items:center;gap:6px;padding:6px;border:1px solid #22345c;border-radius:9px;margin:4px 0;background:#132038;cursor:pointer}
.regRow:hover{background:#1a2b4a}
.regRow.sel{outline:2px solid #ff6bb5}
.regRow.drag{opacity:.4}
.regRow input{accent-color:#3ddc97}
.regRow .nm{flex:1;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.regRow .vl{font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:999px;background:#0b1526;border:1px solid #2c3f6b;color:#4cc3ff}
.regRow .dn{color:#ff6b6b;font-size:11px}
#regCount,#viewList{color:#7f93b8;font-size:11.5px;margin:4px 0}
.viewRow{display:flex;gap:6px;align-items:center;margin:3px 0}
.viewRow button{flex:1;text-align:left}
#stage{flex:1;position:relative;border:1px solid #22345c;border-radius:14px;overflow:hidden;background:#0a1424}
#stage.grid{background-image:linear-gradient(rgba(90,130,200,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(90,130,200,.15) 1px,transparent 1px);background-size:24px 24px}
#stage.light{background:#f2f6fc}
#stage.light.grid{background-image:linear-gradient(rgba(30,60,120,.12) 1px,transparent 1px),linear-gradient(90deg,rgba(30,60,120,.12) 1px,transparent 1px)}
#stage.blue{background:#082036}
#stage.blue.grid{background-image:linear-gradient(rgba(80,180,255,.14) 1px,transparent 1px),linear-gradient(90deg,rgba(80,180,255,.14) 1px,transparent 1px)}
#cv{width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#storm{display:none;position:absolute;top:10px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#b91c1c,#f43f5e);color:#fff;font-weight:800;padding:8px 16px;border-radius:12px;box-shadow:0 8px 26px rgba(244,63,94,.5);z-index:8;font-size:13px}
#storm.show{display:block;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.35)}}
#side{width:352px;flex:none;background:#0e1a2e;border:1px solid #22345c;border-radius:14px;padding:10px;overflow-y:auto;display:flex;flex-direction:column}
#simBox{background:#132038;border:1px solid #2c3f6b;border-radius:12px;padding:9px;margin-bottom:8px}
#simBox h3{margin:0 0 6px;font-size:13px;color:#ff6bb5;letter-spacing:.4px}
#simBox .row{display:flex;gap:6px;margin:4px 0}
#simBox select,#simBox input{flex:1;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:6px 8px;font-size:12.5px;min-width:0}
#simBox label{color:#93a6c9;font-size:11.5px;display:flex;align-items:center;gap:6px}
#simBox input[type=range]{accent-color:#ff6bb5}
#pingResult{margin-top:6px;font:12px Consolas,monospace;color:#3ddc97;background:#0b1526;border:1px solid #22345c;border-radius:8px;padding:6px;display:none;white-space:pre-wrap}
#tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px}
#tabs button{flex:1;padding:6px 4px;font-size:11.5px;border-radius:8px}
#tabs button.on{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent;color:#fff}
.pane{display:none;flex:1;min-height:0;overflow-y:auto}
.pane.on{display:block}
.fld{margin:6px 0}
.fld span{display:block;color:#93a6c9;font-size:11.5px;margin-bottom:3px}
.fld input,.fld select,.fld textarea{width:100%;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:7px 9px;font-size:13px}
.fld input:focus,.fld select:focus,.fld textarea:focus{outline:2px solid rgba(76,195,255,.4);border-color:#4cc3ff}
.flowRow{border:1px solid #22345c;border-radius:10px;padding:7px;margin:5px 0;background:#132038}
.flowRow .h{display:flex;align-items:center;gap:6px}
.flowRow .h b{flex:1;font-size:12.5px}
.flowRow .g{display:flex;gap:4px;margin-top:5px}
.flowRow select,.flowRow input{background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:7px;padding:4px 6px;font-size:11.5px;min-width:0;flex:1}
table.mini{width:100%;border-collapse:collapse;font:11.5px Consolas,monospace}
table.mini th{color:#7f93b8;text-align:left;padding:4px 6px;border-bottom:1px solid #22345c;font-weight:600}
table.mini td{padding:4px 6px;border-bottom:1px solid #16233c;color:#dfe9ff}
table.mini tr:hover td{background:#16233c}
.chkRow{border:1px solid #22345c;border-left:4px solid #f59e0b;border-radius:9px;padding:7px;margin:5px 0;background:#132038;font-size:12.5px}
.chkRow.ok{border-left-color:#3ddc97}
.chkRow .fx{margin-top:5px}
#planOut{background:#060b16;border:1px solid #1c2a44;border-radius:10px;color:#7dd3fc;font:11.5px/1.5 Consolas,monospace;padding:8px;white-space:pre-wrap;max-height:300px;overflow-y:auto}
#log{background:#060b16;border:1px solid #1c2a44;border-radius:10px;color:#6fd3ff;font:11.5px/1.5 Consolas,monospace;height:260px;overflow-y:auto;padding:8px;white-space:pre-wrap}
#log .ok{color:#3ddc97}#log .bad{color:#ff6b6b}#log .warn{color:#ffc857}#log .info{color:#8fa2c4}
#status{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:6px 14px;background:#0e1a2e;border-top:1px solid #22345c;color:#93a6c9;font-size:12px;position:relative;z-index:5}
#status b{color:#4cc3ff;font-variant-numeric:tabular-nums}
#status b.bad{color:#ff6b6b}#status b.ok{color:#3ddc97}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;background:#16233c;border:1px solid #2c3f6b;color:#dfe9ff}
#modal{display:none;position:fixed;inset:0;z-index:40;background:rgba(3,6,14,.75);align-items:center;justify-content:center}
#modal.open{display:flex}
#modalBox{width:min(600px,94vw);max-height:82vh;overflow-y:auto;background:#0e1a2e;border:1px solid #2c3f6b;border-radius:16px;padding:16px}
#modalBox h3{margin:0 0 10px;color:#4cc3ff}
.mRow{display:flex;align-items:center;gap:8px;padding:8px;border:1px solid #22345c;border-radius:10px;margin:6px 0;background:#132038}
.mRow .t{flex:1;font-size:13px}
.mRow .d{color:#7f93b8;font-size:11.5px}
#toast{position:fixed;left:50%;bottom:52px;transform:translateX(-50%) translateY(20px);opacity:0;pointer-events:none;display:flex;gap:10px;align-items:center;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;font-weight:700;padding:10px 16px;border-radius:12px;box-shadow:0 10px 30px rgba(14,165,233,.4);transition:all .25s;z-index:60}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0);pointer-events:auto}
#toastAct{background:rgba(255,255,255,.22);border:1px solid rgba(255,255,255,.5);color:#fff;padding:5px 10px;border-radius:8px}
#left,#side,.pane,#log,#planOut,#modalBox{scrollbar-width:thin;scrollbar-color:#2c3f6b #0b1526}
#left::-webkit-scrollbar,#side::-webkit-scrollbar,.pane::-webkit-scrollbar,#log::-webkit-scrollbar,#planOut::-webkit-scrollbar,#modalBox::-webkit-scrollbar{width:10px}
#left::-webkit-scrollbar-track,#side::-webkit-scrollbar-track,.pane::-webkit-scrollbar-track,#log::-webkit-scrollbar-track,#planOut::-webkit-scrollbar-track,#modalBox::-webkit-scrollbar-track{background:#0b1526;border-radius:8px}
#left::-webkit-scrollbar-thumb,#side::-webkit-scrollbar-thumb,.pane::-webkit-scrollbar-thumb,#log::-webkit-scrollbar-thumb,#planOut::-webkit-scrollbar-thumb,#modalBox::-webkit-scrollbar-thumb{background:#2c3f6b;border-radius:8px;border:2px solid #0b1526}
#left::-webkit-scrollbar-thumb:hover,#side::-webkit-scrollbar-thumb:hover,.pane::-webkit-scrollbar-thumb:hover,#log::-webkit-scrollbar-thumb:hover,#planOut::-webkit-scrollbar-thumb:hover,#modalBox::-webkit-scrollbar-thumb:hover{background:#4cc3ff}
@media (max-width:1080px){
 body{overflow:auto}
 #wrap{flex-direction:column;height:auto}
 #left{width:100%;order:2;max-height:360px}
 #stage{order:1;height:56vh;min-height:380px}
 #side{width:100%;order:3;max-height:none}
 #hint{display:none}
}
@media print{
 #top,#ctrl,#left,#side,#status,#toast,#modal,#errbar,#storm{display:none!important}
 body{overflow:visible;background:#fff}
 #wrap{height:auto;padding:0}
 #stage{border:none;height:92vh;background:#fff!important}
}
</style></head>
<body>
<div id="errbar"></div>
<div id="top">
<span class="brand">🧪 <em>NetLab</em> PRO<small>схемы · планы · симуляция</small></span>
<button id="bSound" class="on">🔊 Звук</button>
<button class="g" id="bSave">💾 Сохранить</button>
<button class="p" id="bOpen">📂 Схемы</button>
<button id="bSvg">⬇ SVG</button>
<button id="bPng">⬇ PNG</button>
<button id="bPrint">🖨</button>
<button class="w" id="bLink">🔗 Линия</button>
<button id="bSel" class="on">🖱 Выбор</button>
<button class="m" id="bMarquee">⬚ Рамка</button>
<button id="bUndo">↩</button>
<button id="bRedo">↪</button>
<button id="bDup">⧉ Дубль</button>
<button class="d" id="bDelSel">✕ Выделенное</button>
<button class="d" id="bClearAll">🧹 Очистить всё</button>
<button id="bClearSel">⬚ Снять</button>
<span id="hint">рамка = массовое выделение · shift+клик = добавить · Ctrl+A всё · Del удалить · Ctrl+Z/Y отмена/повтор · 2×клик холст = добавить</span>
</div>
<div id="ctrl">
<label>Зум <input type="range" id="cZoom" min="30" max="260" value="100"><span class="val" id="vZoom">100%</span></label>
<label>Сетка <input type="checkbox" id="cGrid" checked></label>
<label>Привязка <input type="checkbox" id="cSnap" checked></label>
<label>Скорость <input type="range" id="cSpeed" min="20" max="400" value="100"><span class="val" id="vSpeed">1.0x</span></label>
<label>Hop мс <input type="range" id="cHop" min="60" max="1200" value="380"><span class="val" id="vHop">380</span></label>
<label>Пакет px <input type="range" id="cPkt" min="3" max="12" value="6"><span class="val" id="vPkt">6</span></label>
<label>Свечение <input type="range" id="cGlow" min="0" max="12" value="6"><span class="val" id="vGlow">6</span></label>
<label>Шлейф <input type="range" id="cTrail" min="0" max="40" value="18"><span class="val" id="vTrail">18</span></label>
<label>Подписи <input type="range" id="cLabel" min="8" max="18" value="11"><span class="val" id="vLabel">11</span></label>
<label>Изгиб <input type="range" id="cCurve" min="0" max="60" value="22"><span class="val" id="vCurve">22</span></label>
<label>Нагрузка <input type="checkbox" id="cHeat" checked></label>
<label>Цвет VLAN <input type="checkbox" id="cVcol" checked></label>
<label>Loopdetect <input type="checkbox" id="cLoop" checked></label>
<label>Тема <select id="cTheme"><option value="dark">тёмная</option><option value="light">светлая</option><option value="blue">blueprint</option></select></label>
<button id="bFit">🎯 Вписать</button>
<button id="bRand">🧹 Раскладка</button>
<button id="bFault">⚡ Авария</button>
<button id="bHeal">🩹 Починить</button>
<button id="bCfg">♻ Настройки</button>
</div>
<div id="wrap">
<div id="left">
<h4>Устройства · клик / тяни</h4><div id="palDev"></div>
<h4>Шаблоны</h4><div id="palTpl"></div>
<h4>Реестр · поиск / фильтр / сортировка</h4>
<input id="regSearch" placeholder="🔍 имя, IP, VLAN, MAC, модель">
<select id="regType"><option value="">все типы</option></select>
<select id="regSort"><option value="name">сортировка: имя</option><option value="ip">IP</option><option value="vlan">VLAN</option><option value="type">тип</option><option value="order">порядок отрисовки</option></select>
<div id="regCount"></div>
<div id="regList"></div>
<div class="fld"><span>Массово: VLAN выделенным</span><input id="bulkVlan" list="vlanList" placeholder="напр. 135"></div>
<button class="p" id="bBulkVlan" style="width:100%">Применить VLAN к выделенным</button>
<button class="d" id="bBulkDel" style="width:100%;margin-top:5px">✕ Удалить выделенные</button>
<h4>Сохранённые виды</h4>
<input id="viewName" placeholder="название вида (камера+зум)">
<button class="g" id="bViewSave" style="width:100%">📌 Сохранить вид</button>
<div id="viewList"></div>
<h4>Схема</h4>
<button id="bDemo" style="width:100%;margin:4px 0">📦 Пример: абонент + PON</button>
<button id="bRandTopo" style="width:100%;margin:4px 0">🎲 Случайный подъезд</button>
</div>
<div id="stage" class="grid">
<div id="storm">⚠️ BROADCAST-ШТОРМ: петля в сети!</div>
<svg id="cv" xmlns="http://www.w3.org/2000/svg">
<defs><filter id="glow" x="-90%" y="-90%" width="280%" height="280%"><feGaussianBlur id="glowBlur" stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs>
<g id="world"><g id="geo"></g><g id="pk"></g></g>
<rect id="marquee" x="0" y="0" width="0" height="0" fill="rgba(217,70,239,.14)" stroke="#d946ef" stroke-width="1.5" stroke-dasharray="5 4" style="display:none"/>
</svg>
</div>
<div id="side">
<div id="simBox">
<h3>📡 Симуляция трафика</h3>
<div class="row"><select id="simMode">
<option value="flows">Потоки (непрерывно)</option>
<option value="ping">Ping A → B (RTT)</option>
<option value="multicast">Multicast + IGMP snooping</option>
<option value="broadcast">Broadcast / flood</option>
<option value="pon">PON downstream</option>
</select></div>
<div class="row"><select id="simSrc"></select><select id="simDst"></select></div>
<div class="row"><input id="simVlan" value="135" list="vlanList" placeholder="VLAN"><label>pps <input type="range" id="simRate" min="1" max="20" value="4" style="width:70px"><span class="val" id="vSimRate">4</span></label></div>
<div class="row"><button class="g" id="bRun" style="flex:2">▶ Пуск</button><button id="bPause" style="flex:1">⏸</button><button id="bStep" style="flex:1">⏭</button><button class="d" id="bStop" style="flex:1">⏹</button></div>
<div id="pingResult"></div>
</div>
<div id="tabs">
<button data-tab="props" class="on">🔧 Свойства</button>
<button data-tab="flows">🌊 Потоки</button>
<button data-tab="fdb">📚 FDB</button>
<button data-tab="check">🔎 Проверка</button>
<button data-tab="plan">📋 План</button>
<button data-tab="events">📜 События</button>
</div>
<div class="pane on" id="paneProps"><div id="props"><span style="color:#93a6c9">Выберите устройство или линию. Рамка (⬚) выделяет группу для массовых операций.</span></div></div>
<div class="pane" id="paneFlows"><div id="flowList"></div><button class="g" id="bAddFlow" style="width:100%;margin-top:6px">➕ Добавить поток</button></div>
<div class="pane" id="paneFdb">
<div class="fld"><span>Коммутатор</span><select id="fdbDev"></select></div>
<table class="mini"><thead><tr><th>MAC</th><th>Порт</th><th>VLAN</th><th>возраст</th></tr></thead><tbody id="fdbBody"></tbody></table>
<button id="bFdbClear" style="width:100%;margin-top:6px">🧽 Очистить FDB</button>
</div>
<div class="pane" id="paneCheck">
<button class="p" id="bCheck" style="width:100%">🔎 Проверить VLAN-план и доступность</button>
<div id="checkList" style="margin-top:6px"></div>
</div>
<div class="pane" id="panePlan">
<div class="fld"><span>Синтаксис</span><select id="planSyn"><option value="des">D-Link DES (vlanid)</option><option value="dgs">D-Link DGS-1210/ME</option></select></div>
<button class="g" id="bPlanCopy" style="width:100%">📋 Копировать план работ</button>
<div id="planOut" style="margin-top:6px"></div>
</div>
<div class="pane" id="paneEvents">
<div class="fld"><span>Фильтр</span><select id="evFilter"><option value="">все</option><option value="ok">доставлено</option><option value="bad">потери</option><option value="warn">предупреждения</option><option value="info">инфо</option></select></div>
<div id="log"></div>
<button id="bLogClear" style="width:100%;margin-top:6px">🧽 Очистить журнал</button>
</div>
</div>
</div>
<div id="status">
<span>Устройств: <b id="stDev">0</b></span>
<span>Линий: <b id="stLink">0</b></span>
<span>Выделено: <b id="stSel">0</b></span>
<span>Зум: <b id="stZoom">100%</b></span>
<span>Пакетов: <b id="stPkts" class="ok">0</b></span>
<span>Потерь: <b id="stDrops" class="bad">0</b></span>
<span>MAC выучено: <b id="stMac">0</b></span>
<span id="stSim" class="chip">симуляция: стоп</span>
<span style="margin-left:auto"><span class="chip" style="color:#ff9f43">135 камеры</span> <span class="chip" style="color:#ffc857">1151 IPTV</span> <span class="chip" style="color:#3ddc97">2201 абоненты</span></span>
</div>
<div id="modal"><div id="modalBox"><h3>📂 Сохранённые схемы</h3><div id="modalList"></div><button id="modalClose" style="margin-top:10px">Закрыть</button></div></div>
<div id="toast"><span id="toastMsg"></span><button id="toastAct" style="display:none">Отменить</button></div>
<datalist id="vlanList"></datalist>
<script>
(function(){
'use strict';
window.onerror=function(m){var e=document.getElementById('errbar');e.style.display='block';e.textContent='JS: '+m;};
var TYPES={
 router:{i:'📶',n:'Роутер абонента',c:'#f472b6',sw:1},
 switch:{i:'🖧',n:'Коммутатор',c:'#4cc3ff',sw:1},
 agg:{i:'🔀',n:'Агрегация',c:'#8b9dff',sw:1},
 core:{i:'🌐',n:'Ядро провайдера',c:'#ff6b6b',sw:1},
 olt:{i:'🏢',n:'OLT',c:'#c084fc',sw:1},
 split:{i:'🌳',n:'Сплиттер PON',c:'#2dd4bf',sw:0},
 onu:{i:'📡',n:'ONU / ONT',c:'#3ddc97',sw:1},
 camera:{i:'📹',n:'IP-камера',c:'#ff9f43',sw:0},
 pc:{i:'🖥️',n:'ПК / терминал',c:'#9fb2d4',sw:0},
 tv:{i:'📺',n:'TV / приставка',c:'#ffd166',sw:0},
 nvr:{i:'🗄️',n:'NVR / сервер',c:'#ff6bb5',sw:0},
 ap:{i:'📡',n:'Wi-Fi точка',c:'#60a5fa',sw:0},
 printer:{i:'🖨️',n:'Принтер',c:'#b8c2d9',sw:0}
};
var VLANS=[['135','Камеры ОТТ'],['1151','IPTV multicast'],['2101','Тура · красный'],['2103','Тура · жёлтый'],['2117','Тура · ЖК Клевер к1'],['2201','Михеенко · красный'],['2208','Михеенко · Лихачева 6'],['2301','Королёва · красный'],['2402','Черняховка · оранжевый'],['2601','Жучки · красный'],['2603','Жучки · PON 1'],['2604','Жучки · PON 2'],['2704','Горбуновка · PON'],['2803','ГОП · PON 1'],['2020','Сегмент 02 · МКД'],['2021','Сегмент 02 · PON'],['2050','Сегмент 05 · МКД'],['2054','Сегмент 05 · PON'],['2080','Сегмент 08 · PON запад'],['2081','Сегмент 08 · PON восток'],['2110','Сегмент 11 · МКД'],['2114','Сегмент 11 · PON'],['2122','Сегмент 12 · PON Кировка'],['2123','Сегмент 12 · PON Дружба'],['2150','Сегмент 15 · PON'],['2160','Сегмент 16 · PON'],['2171','Сегмент 17 · PON']];
var cfg={grid:true,snap:true,speed:1,hop:380,pkt:6,glow:6,trail:18,label:11,curve:0.22,heat:true,vcol:true,loop:true,theme:'dark',sound:true};
var S=null,view={x:70,y:50,k:1};
var selD={},selL={},selN=0,tool='select',linkFrom=null,lastType='pc';
var drag=null,pan=null,marq=null,undoStack=[],redoStack=[],dirty=true;
var sim={running:false,paused:false,packets:[],pid:1,stats:{pk:0,dr:0},fdb:{},ev:[],flowAcc:{},last:0,blocked:{},storm:false,deliverCount:0};
var audio=null;
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function dev(id){for(var i=0;i<S.devices.length;i++){if(S.devices[i].id===id)return S.devices[i];}return null;}
function lnk(id){for(var i=0;i<S.links.length;i++){if(S.links[i].id===id)return S.links[i];}return null;}
function hue(v){var h=((parseInt(v,10)||0)*47)%360;return 'hsl('+h+',85%,62%)';}
function macOf(d){if(d.mac)return d.mac;var p=(d.type==='camera')?'00:1A:79':'02:4C:AB';var h=('0'+(d.id*7%256).toString(16)).slice(-2);var h2=('0'+(d.id*13%256).toString(16)).slice(-2);var h3=('0'+(d.id*29%256).toString(16)).slice(-2);return p+':'+h+':'+h2+':'+h3;}
function isSw(d){return d&&TYPES[d.type]&&TYPES[d.type].sw;}
function snap(v){return cfg.snap?Math.round(v/12)*12:v;}
function mark(){dirty=true;}
function pushUndo(){undoStack.push(JSON.stringify(S));if(undoStack.length>80)undoStack.shift();redoStack=[];}
function autosave(){try{localStorage.setItem('netlab_auto',JSON.stringify(S));}catch(e){}}
function toast(msg,act){var t=$('toast');$('toastMsg').textContent=msg;var a=$('toastAct');
 if(act){a.style.display='';a.onclick=function(){act();t.className='';};}else{a.style.display='none';a.onclick=null;}
 t.className='show';clearTimeout(t._t);t._t=setTimeout(function(){t.className='';},act?6000:2200);}
function ev(type,msg){sim.ev.push({t:new Date().toLocaleTimeString('ru'),type:type,msg:msg});if(sim.ev.length>400)sim.ev.shift();renderLog();}
function renderLog(){var f=$('evFilter').value;var l=$('log');var rows=sim.ev.filter(function(e){return !f||e.type===f;});
 l.innerHTML=rows.slice(-160).map(function(e){return '<div class="'+e.type+'">['+e.t+'] '+esc(e.msg)+'</div>';}).join('');l.scrollTop=l.scrollHeight;}
function blip(freq,dur,kind){if(!cfg.sound)return;try{if(!audio)audio=new (window.AudioContext||window.webkitAudioContext)();
 var o=audio.createOscillator(),g=audio.createGain();o.type=kind==='bad'?'sawtooth':'sine';o.frequency.value=freq;
 g.gain.value=kind==='bad'?0.05:0.035;o.connect(g);g.connect(audio.destination);o.start();
 g.gain.exponentialRampToValueAtTime(0.0001,audio.currentTime+dur);o.stop(audio.currentTime+dur);}catch(e){}}
function demo(){
 var d={nid:13,lid:12,devices:[
  {id:1,type:'core',x:430,y:40,name:'Ядро S6330',ip:'10.163.100.8',vlan:'',model:'S6330',notes:'',down:false},
  {id:2,type:'nvr',x:680,y:40,name:'NVR провайдера',ip:'10.135.0.10',vlan:'135',model:'NVR-64',notes:'',down:false},
  {id:3,type:'olt',x:430,y:170,name:'OLT Михеенко',ip:'10.163.202.13',vlan:'',model:'PON OLT',notes:'',down:false},
  {id:4,type:'split',x:430,y:290,name:'Сплиттер 1:8',ip:'',vlan:'',model:'1x8',notes:'',down:false},
  {id:5,type:'onu',x:430,y:410,name:'ONU абонент кв.12',ip:'',vlan:'2201',model:'ONT-1G',notes:'bridge',down:false},
  {id:6,type:'router',x:430,y:530,name:'Роутер абонента',ip:'192.168.1.1',vlan:'',model:'Keenetic',notes:'',down:false},
  {id:7,type:'switch',x:430,y:650,name:'Свитч квартиры',ip:'192.168.1.2',vlan:'',model:'DES-1008',notes:'',down:false},
  {id:8,type:'pc',x:170,y:790,name:'ПК кабинет',ip:'192.168.1.10',vlan:'2201',model:'PC',notes:'',down:false},
  {id:9,type:'camera',x:350,y:790,name:'Камера прихожая',ip:'192.168.1.20',vlan:'135',model:'BEWARD B2710',notes:'',down:false},
  {id:10,type:'tv',x:530,y:790,name:'TV приставка',ip:'192.168.1.30',vlan:'1151',model:'IPTV STB',notes:'',down:false},
  {id:11,type:'printer',x:700,y:790,name:'Принтер',ip:'192.168.1.40',vlan:'2201',model:'HP',notes:'',down:false},
  {id:12,type:'ap',x:860,y:790,name:'Wi-Fi точка',ip:'192.168.1.3',vlan:'2201',model:'AP',notes:'',down:false}
 ],links:[
  {id:1,a:1,b:3,pa:'4',pb:'uplink',mode:'trunk',vlans:'135,1151,2201',media:'fiber',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:2,a:1,b:2,pa:'6',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:3,a:3,b:4,pa:'pon1',pb:'in',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:3,down:false,pk:0,by:0,er:0,load:0},
  {id:4,a:4,b:5,pa:'3',pb:'pon',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:5,a:5,b:6,pa:'lan1',pb:'wan',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:6,a:6,b:7,pa:'lan1',pb:'1',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:7,a:7,b:8,pa:'2',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:8,a:7,b:9,pa:'3',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:9,a:7,b:10,pa:'4',pb:'1',mode:'access',vlans:'1151',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:10,a:7,b:11,pa:'5',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0},
  {id:11,a:7,b:12,pa:'6',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0}
 ],flows:[
  {id:1,name:'Камера → NVR',src:9,dst:2,vlan:'135',mode:'unicast',rate:3,on:true},
  {id:2,name:'IPTV → приставки',src:1,dst:0,vlan:'1151',mode:'multicast',rate:2,on:true},
  {id:3,name:'Абонент → ядро',src:8,dst:1,vlan:'2201',mode:'unicast',rate:2,on:true}
 ],fid:4};
 return d;
}
function norm(){if(!S.flows){S.flows=[];S.fid=1;}if(!S.fid)S.fid=1;
 S.devices.forEach(function(d){if(d.down==null)d.down=false;});
 S.links.forEach(function(L){if(L.down==null)L.down=false;if(L.pk==null){L.pk=0;L.by=0;L.er=0;L.load=0;}});}
function selCount(){var n=0,k;for(k in selD)n++;for(k in selL)n++;return n;}
function clearSel(){selD={};selL={};selN=0;mark();fillReg();props();}
function selectDev(id,add){if(!add){selD={};selL={};}selD[id]=1;selN=selCount();mark();fillReg();props();}
function selectLink(id,add){if(!add){selD={};selL={};}selL[id]=1;selN=selCount();mark();fillReg();props();}
function render(){
 dirty=false;
 var light=cfg.theme==='light';
 var ink=light?'#12203a':'#eaf2ff',mut=light?'#5a6b8c':'#9fb2d4';
 var h='';
 S.links.forEach(function(L){
  var a=dev(L.a),b=dev(L.b);if(!a||!b)return;
  var mx=(a.x+b.x)/2,my=(a.y+b.y)/2,dx=b.x-a.x,dy=b.y-a.y,len=Math.sqrt(dx*dx+dy*dy)||1;
  var cx=mx-dy/len*cfg.curve*len*0.5,cy=my+dx/len*cfg.curve*len*0.5;
  var on=!!selL[L.id],blocked=!!sim.blocked[L.id];
  var col=L.down?'#ff6b6b':(blocked?'#f59e0b':(on?'#ff6bb5':(cfg.vcol?hue(String(L.vlans).split(',')[0]):(L.media==='fiber'?'#ffc857':(L.media==='pon'?'#2dd4bf':'#7c93b8')))));
  var w=2.4+(cfg.heat?Math.min(4,L.load*0.5):0)+(on?1.6:0);
  h+='<path data-l="'+L.id+'" d="M'+a.x+' '+a.y+' Q'+cx+' '+cy+' '+b.x+' '+b.y+'" fill="none" stroke="'+col+'" stroke-width="'+w.toFixed(1)+'" stroke-dasharray="'+(L.down?'3 5':(blocked?'8 4':(L.media==='pon'?'7 4':'none')))+'" style="cursor:pointer" opacity="'+(L.down?0.6:(on?1:0.88))+'"/>';
  var lbl=esc(L.pa||'?')+'→'+esc(L.pb||'?')+' · '+(L.mode==='trunk'?'trunk['+esc(L.vlans)+']':'acc'+esc(L.vlans));
  if(cfg.heat&&L.load>0.2)lbl+=' · '+Math.min(99,Math.round(L.load*8))+'%';
  if(L.down)lbl+=' · DOWN';
  if(blocked)lbl+=' · BLOCKED';
  h+='<text x="'+cx+'" y="'+(cy-6)+'" text-anchor="middle" font-size="'+cfg.label+'" fill="'+(L.down?'#ff6b6b':mut)+'" style="pointer-events:none">'+lbl+'</text>';
 });
 S.devices.forEach(function(d){
  var t=TYPES[d.type]||TYPES.switch,on=!!selD[d.id];
  h+='<g data-d="'+d.id+'" style="cursor:move">';
  if(on)h+='<rect x="'+(d.x-58)+'" y="'+(d.y-38)+'" width="116" height="76" rx="16" fill="none" stroke="#d946ef" stroke-opacity="0.45" stroke-width="6"/>';
  h+='<rect x="'+(d.x-52)+'" y="'+(d.y-32)+'" width="104" height="64" rx="12" fill="'+(d.down?'#3a1220':t.c)+'" fill-opacity="'+(light?0.9:0.2)+'" stroke="'+(d.down?'#ff6b6b':(on?'#d946ef':t.c))+'" stroke-width="'+(on?3:1.6)+'"/>';
  h+='<text x="'+d.x+'" y="'+(d.y-8)+'" text-anchor="middle" font-size="19">'+(d.down?'⛔':t.i)+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+9)+'" text-anchor="middle" font-size="'+cfg.label+'" font-weight="700" fill="'+(light?'#0d1728':ink)+'">'+esc((d.name||t.n).slice(0,18))+'</text>';
  h+='<text x="'+d.x+'" y="'+(d.y+24)+'" text-anchor="middle" font-size="'+(cfg.label-1)+'" fill="'+(light?'#41537a':mut)+'">'+esc(d.ip||'')+(d.vlan?' · v'+esc(d.vlan):'')+'</text>';
  h+='</g>';
 });
 $('geo').innerHTML=h;
 $('world').setAttribute('transform','translate('+view.x+','+view.y+') scale('+view.k+')');
 $('glowBlur').setAttribute('stdDeviation',cfg.glow);
 $('stDev').textContent=S.devices.length;
 $('stLink').textContent=S.links.length;
 $('stSel').textContent=selCount();
 $('stZoom').textContent=Math.round(view.k*100)+'%';
 $('vZoom').textContent=Math.round(view.k*100)+'%';
 $('cZoom').value=Math.round(view.k*100);
 $('bDelSel').disabled=selCount()===0;
 $('bDup').disabled=selCount()===0;
 fillSim();fillReg();fillFdbDev();
}
function fillSim(){
 var o=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('');
 var a=$('simSrc'),b=$('simDst'),av=a.value,bv=b.value;
 a.innerHTML=o;b.innerHTML='<option value="0">— (по режиму)</option>'+o;
 if(av&&dev(+av))a.value=av;else{var c=null;S.devices.forEach(function(d){if(d.type==='camera')c=d.id;});a.value=c||(S.devices[0]?S.devices[0].id:'');}
 if(bv&&dev(+bv))b.value=bv;else{var n=null;S.devices.forEach(function(d){if(d.type==='nvr')n=d.id;});b.value=n||'0';}
}
function fillReg(){
 var q=($('regSearch').value||'').toLowerCase(),ft=$('regType').value,sort=$('regSort').value;
 var rows=S.devices.filter(function(d){
  if(ft&&d.type!==ft)return false;
  if(!q)return true;
  return ((d.name||'')+' '+(d.ip||'')+' '+(d.vlan||'')+' '+(d.model||'')+' '+macOf(d)+' '+TYPES[d.type].n).toLowerCase().indexOf(q)>=0;
 });
 if(sort==='ip')rows.sort(function(a,b){return (a.ip||'').localeCompare(b.ip||'','ru',{numeric:true});});
 else if(sort==='vlan')rows.sort(function(a,b){return (parseInt(a.vlan,10)||0)-(parseInt(b.vlan,10)||0);});
 else if(sort==='type')rows.sort(function(a,b){return (a.type||'').localeCompare(b.type||'');});
 else if(sort==='name')rows.sort(function(a,b){return (a.name||'').localeCompare(b.name||'','ru');});
 $('regCount').textContent='показано '+rows.length+' из '+S.devices.length+' · выделено '+selCount();
 $('regList').innerHTML=rows.map(function(d){
  return '<div class="regRow'+(selD[d.id]?' sel':'')+'" draggable="true" data-reg="'+d.id+'"><input type="checkbox" data-chk="'+d.id+'"'+(selD[d.id]?' checked':'')+'><i style="font-style:normal">'+TYPES[d.type].i+'</i><span class="nm">'+esc(d.name||TYPES[d.type].n)+'</span>'+(d.down?'<span class="dn">DOWN</span>':'')+'<span class="vl">'+(d.vlan?'v'+esc(d.vlan):'—')+'</span></div>';
 }).join('')||'<div style="color:#7f93b8;font-size:12px">ничего не найдено</div>';
}
function fillFdbDev(){
 var s=$('fdbDev'),v=s.value;
 s.innerHTML=S.devices.filter(isSw).map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('')||'<option value="">нет коммутаторов</option>';
 if(v&&dev(+v))s.value=v;
 renderFdb();
}
function renderFdb(){
 var id=+$('fdbDev').value,t=sim.fdb[id]||{},now=Date.now(),rows=[];
 for(var m in t)rows.push({mac:m,p:t[m].port,v:t[m].vlan,age:Math.round((now-t[m].t)/1000)});
 rows.sort(function(a,b){return a.age-b.age;});
 $('fdbBody').innerHTML=rows.map(function(r){return '<tr><td>'+r.mac+'</td><td>'+esc(r.p)+'</td><td>'+esc(r.v)+'</td><td>'+r.age+'с</td></tr>';}).join('')||'<tr><td colspan="4" style="color:#7f93b8">пусто — запустите симуляцию</td></tr>';
 var total=0;for(var k in sim.fdb){for(var m2 in sim.fdb[k])total++;}
 $('stMac').textContent=total;
}
function palette(){
 $('palDev').innerHTML=Object.keys(TYPES).map(function(k){return '<button draggable="true" data-add="'+k+'"><i>'+TYPES[k].i+'</i>'+TYPES[k].n+'</button>';}).join('');
 $('palTpl').innerHTML='<button data-tpl="sub"><i>🏠</i>Абонентская локалка</button><button data-tpl="pod"><i>🏢</i>Подъезд: DES + камеры</button><button data-tpl="pon"><i>🌳</i>PON: OLT+сплиттер+ONU</button><button data-tpl="core"><i>🌐</i>Ядро+агрегация+OLT</button>';
 $('regType').innerHTML='<option value="">все типы</option>'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'">'+TYPES[k].n+'</option>';}).join('');
 $('vlanList').innerHTML=VLANS.map(function(v){return '<option value="'+v[0]+'">'+v[0]+' · '+v[1]+'</option>';}).join('');
}
function center(){var r=$('cv').getBoundingClientRect();return {x:(r.width/2-view.x)/view.k,y:(r.height/2-view.y)/view.k};}
function addDevice(k,x,y){
 pushUndo();lastType=k;var c=center();
 var d={id:S.nid++,type:k,x:snap(x==null?c.x+(Math.random()*120-60):x),y:snap(y==null?c.y+(Math.random()*90-45):y),name:'',ip:'',vlan:(k==='camera'?'135':(k==='tv'?'1151':(k==='pc'||k==='onu'||k==='printer'||k==='ap')?'2201':'')),model:'',notes:'',down:false};
 S.devices.push(d);clearSel();selD[d.id]=1;selN=1;autosave();mark();props();toast('Добавлено: '+TYPES[k].n);
}
function addTpl(k){
 pushUndo();var c=center();
 function mk(t,dx,dy,name,ip,vlan){var id=S.nid++;S.devices.push({id:id,type:t,x:snap(c.x+dx),y:snap(c.y+dy),name:name,ip:ip,vlan:vlan||'',model:'',notes:'',down:false});return id;}
 function L(a,b,pa,pb,mode,vlans,media){S.links.push({id:S.lid++,a:a,b:b,pa:pa,pb:pb,mode:mode,vlans:vlans,media:media||'copper',cost:1,down:false,pk:0,by:0,er:0,load:0});}
 if(k==='sub'){var r=mk('router',0,-140,'Роутер абонента','192.168.1.1',''),sw=mk('switch',0,-20,'Свитч квартиры','192.168.1.2','');
  var pc=mk('pc',-220,120,'ПК','192.168.1.10','2201'),cam=mk('camera',-70,120,'Камера','192.168.1.20','135'),tv=mk('tv',80,120,'TV','192.168.1.30','1151'),pr=mk('printer',230,120,'Принтер','192.168.1.40','2201');
  L(r,sw,'lan1','1','trunk','135,1151,2201');L(sw,pc,'2','1','access','2201');L(sw,cam,'3','1','access','135');L(sw,tv,'4','1','access','1151');L(sw,pr,'5','1','access','2201');}
 if(k==='pod'){var s1=mk('switch',0,-120,'DES-3200 подъезд','10.163.202.88',''),c1=mk('camera',-160,20,'Камера БР-1','10.135.1.21','135'),c2=mk('camera',0,20,'Камера БР-2','10.135.1.22','135'),p1=mk('pc',160,20,'Абонент кв.1','10.163.202.11','2201');
  L(s1,c1,'21','1','access','135');L(s1,c2,'22','1','access','135');L(s1,p1,'12','1','access','2201');}
 if(k==='pon'){var ol=mk('olt',0,-140,'OLT','10.163.206.8',''),sp=mk('split',0,-30,'Сплиттер 1:8','',''),o1=mk('onu',-120,90,'ONU-1','','2603'),o2=mk('onu',120,90,'ONU-2','','2601');
  var cc=mk('camera',-120,200,'Камера PON','10.135.2.10','2603'),pp=mk('pc',120,200,'Абонент PON','10.163.206.21','2601');
  L(ol,sp,'pon1','in','trunk','2601,2603','pon');L(sp,o1,'3','pon','trunk','2601,2603','pon');L(sp,o2,'5','pon','trunk','2601,2603','pon');L(o1,cc,'lan1','1','access','2603');L(o2,pp,'lan1','1','access','2601');}
 if(k==='core'){var co=mk('core',0,-160,'Ядро','10.163.100.8',''),ag=mk('agg',0,-40,'Агрегация','10.163.100.2',''),ol2=mk('olt',-160,80,'OLT','10.163.206.8',''),s2=mk('switch',160,80,'DES доступ','10.163.202.13','');
  L(co,ag,'1','1','trunk','135,1151,2201,2601','fiber');L(ag,ol2,'2','uplink','trunk','135,1151,2601','fiber');L(ag,s2,'3','28','trunk','135,1151,2201','fiber');}
 autosave();mark();props();toast('Шаблон добавлен');
}
function randTopo(){
 pushUndo();S={nid:1,lid:1,devices:[],links:[],flows:[],fid:1};
 var c=center(),n=3+Math.floor(Math.random()*3);
 var sw=S.nid++;S.devices.push({id:sw,type:'switch',x:snap(c.x),y:snap(c.y-140),name:'DES-3200 подъезд '+(1+Math.floor(Math.random()*9)),ip:'10.163.202.'+(10+Math.floor(Math.random()*80)),vlan:'',model:'DES-3200-28',notes:'',down:false});
 var vl=VLANS[5+Math.floor(Math.random()*8)][0];
 for(var i=0;i<n;i++){var cam=S.nid++;S.devices.push({id:cam,type:'camera',x:snap(c.x-180+i*120),y:snap(c.y+40),name:'Камера БР-'+(i+1),ip:'10.135.1.'+(20+i),vlan:'135',model:'BEWARD',notes:'',down:false});
  S.links.push({id:S.lid++,a:sw,b:cam,pa:String(21+i),pb:'1',mode:'access',vlans:'135',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0});}
 for(var j=0;j<2;j++){var pc=S.nid++;S.devices.push({id:pc,type:'pc',x:snap(c.x-60+j*160),y:snap(c.y+180),name:'Абонент кв.'+(j+1),ip:'10.163.202.'+(100+j),vlan:vl,model:'PC',notes:'',down:false});
  S.links.push({id:S.lid++,a:sw,b:pc,pa:String(12+j),pb:'1',mode:'access',vlans:vl,media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0});}
 S.flows.push({id:S.fid++,name:'Камеры → NVR',src:S.devices[1].id,dst:0,vlan:'135',mode:'unicast',rate:3,on:true});
 clearSel();autosave();mark();fit();toast('Случайный подъезд создан');
}
function pt(e){var r=$('cv').getBoundingClientRect();return {x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k,sx:e.clientX-r.left,sy:e.clientY-r.top};}
function setTool(t){tool=t;linkFrom=null;
 $('bLink').className=(t==='link')?'w on':'w';
 $('bSel').className=(t==='select')?'on':'';
 $('bMarquee').className=(t==='marquee')?'m on':'m';
 $('cv').style.cursor=t==='marquee'?'crosshair':(t==='link'?'cell':'grab');}
function props(){
 var p=$('props');
 var nd=0,nl=0,k;for(k in selD)nd++;for(k in selL)nl++;
 if(nd+nl>1){
  p.innerHTML='<div class="fld"><span>Выделено: устройств '+nd+', линий '+nl+'</span></div>'
  +'<div class="fld"><span>Массово VLAN устройствам</span><input id="pBulkVlan" list="vlanList" placeholder="135"></div>'
  +'<button class="p" id="pBulkApply" style="width:100%">Применить VLAN</button>'
  +'<button class="g" id="pBulkUp" style="width:100%;margin-top:5px">⬆ Поднять выделенные</button>'
  +'<button class="d" id="pDel" style="width:100%;margin-top:5px">✕ Удалить выделенное ('+(nd+nl)+')</button>';
  $('pBulkApply').addEventListener('click',function(){bulkVlan($('pBulkVlan').value);});
  $('pBulkUp').addEventListener('click',function(){pushUndo();for(var id in selD){var d=dev(+id);if(d)d.down=false;}autosave();mark();toast('Выделенные подняты');});
  $('pDel').addEventListener('click',delSel);
  return;
 }
 if(nl===1){
  var lid=+Object.keys(selL)[0],L=lnk(lid);if(!L){clearSel();return;}
  p.innerHTML='<div class="fld"><span>Линия #'+L.id+' · '+esc((dev(L.a)||{}).name||'')+' ↔ '+esc((dev(L.b)||{}).name||'')+'</span></div>'
  +'<div class="fld"><span>Порт A</span><input data-lf="pa" value="'+esc(L.pa)+'"></div>'
  +'<div class="fld"><span>Порт B</span><input data-lf="pb" value="'+esc(L.pb)+'"></div>'
  +'<div class="fld"><span>Режим</span><select data-lf="mode"><option value="trunk"'+(L.mode==='trunk'?' selected':'')+'>trunk</option><option value="access"'+(L.mode==='access'?' selected':'')+'>access</option></select></div>'
  +'<div class="fld"><span>VLAN-ы через запятую</span><input data-lf="vlans" list="vlanList" value="'+esc(L.vlans)+'"></div>'
  +'<div class="fld"><span>Среда</span><select data-lf="media"><option value="copper"'+(L.media==='copper'?' selected':'')+'>медь 100M</option><option value="fiber"'+(L.media==='fiber'?' selected':'')+'>оптика 1G</option><option value="pon"'+(L.media==='pon'?' selected':'')+'>PON 2.5G</option></select></div>'
  +'<div class="fld"><span>Задержка, мс</span><input type="number" data-lf="cost" value="'+(L.cost||1)+'"></div>'
  +'<div class="fld"><span>Состояние</span><select data-lf="down"><option value="0"'+(!L.down?' selected':'')+'>работает</option><option value="1"'+(L.down?' selected':'')+'>АВАРИЯ (обрыв)</option></select></div>'
  +'<table class="mini"><tr><th>пакетов</th><th>байт</th><th>ошибок</th><th>нагрузка</th></tr><tr><td>'+L.pk+'</td><td>'+L.by+'</td><td>'+L.er+'</td><td>'+Math.min(99,Math.round(L.load*8))+'%</td></tr></table>'
  +'<button class="d" id="pDel" style="width:100%;margin-top:6px">✕ Удалить линию</button>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-lf]'),function(inp){inp.addEventListener('input',function(){pushUndo();var f=inp.getAttribute('data-lf');L[f]=(f==='down')?(inp.value==='1'):inp.value;autosave();mark();});});
  $('pDel').addEventListener('click',delSel);
  return;
 }
 if(nd===1){
  var id=+Object.keys(selD)[0],d=dev(id);if(!d){clearSel();return;}
  var conns=S.links.filter(function(L){return L.a===id||L.b===id;}).map(function(L){
   var o=dev(L.a===id?L.b:L.a);return '<div style="color:#93a6c9;font-size:12px">↔ '+esc(o?o.name:'?')+' · '+(L.a===id?esc(L.pa):esc(L.pb))+'→'+(L.a===id?esc(L.pb):esc(L.pa))+' · '+L.mode+'['+esc(L.vlans)+']'+(L.down?' · DOWN':'')+'</div>';
  }).join('');
  p.innerHTML='<div class="fld"><span>Тип</span><select data-df="type">'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'"'+(d.type===k?' selected':'')+'>'+TYPES[k].i+' '+TYPES[k].n+'</option>';}).join('')+'</select></div>'
  +'<div class="fld"><span>Имя</span><input data-df="name" value="'+esc(d.name)+'"></div>'
  +'<div class="fld"><span>IP</span><input data-df="ip" value="'+esc(d.ip)+'"></div>'
  +'<div class="fld"><span>MAC</span><input data-df="mac" value="'+esc(macOf(d))+'"></div>'
  +'<div class="fld"><span>Access-VLAN</span><input data-df="vlan" list="vlanList" value="'+esc(d.vlan)+'"></div>'
  +'<div class="fld"><span>Модель</span><input data-df="model" value="'+esc(d.model)+'"></div>'
  +'<div class="fld"><span>Состояние</span><select data-df="down"><option value="0"'+(!d.down?' selected':'')+'>работает</option><option value="1"'+(d.down?' selected':'')+'>выключено / авария</option></select></div>'
  +'<div class="fld"><span>Заметки</span><textarea data-df="notes" rows="2">'+esc(d.notes)+'</textarea></div>'
  +'<div class="fld"><span>Подключения</span>'+(conns||'<div style="color:#7f93b8;font-size:12px">нет линий</div>')+'</div>'
  +'<button class="d" id="pDel" style="width:100%">✕ Удалить устройство</button>';
  Array.prototype.forEach.call(p.querySelectorAll('[data-df]'),function(inp){inp.addEventListener('input',function(){pushUndo();var f=inp.getAttribute('data-df');d[f]=(f==='down')?(inp.value==='1'):inp.value;autosave();mark();});});
  $('pDel').addEventListener('click',delSel);
  return;
 }
 p.innerHTML='<span style="color:#93a6c9">Выберите устройство или линию. Рамка (⬚) выделяет группу для массовых операций.</span>';
}
function bulkVlan(v){
 v=String(v||'').trim();if(!v){toast('Введите VLAN');return;}
 pushUndo();var n=0;for(var id in selD){var d=dev(+id);if(d){d.vlan=v;n++;}}
 autosave();mark();props();toast('VLAN '+v+' применён к '+n+' устройствам',function(){undo();});
}
function delSel(){
 var n=selCount();if(!n){toast('Нечего удалять');return;}
 pushUndo();stopSim();
 S.links=S.links.filter(function(L){return !selL[L.id]&&!selD[L.a]&&!selD[L.b];});
 S.devices=S.devices.filter(function(d){return !selD[d.id];});
 S.flows=(S.flows||[]).filter(function(f){return dev(f.src)&&(!f.dst||dev(f.dst));});
 clearSel();autosave();mark();props();renderFlows();
 toast('Удалено объектов: '+n,function(){undo();});
}
function clearAll(){
 pushUndo();stopSim();
 S={nid:1,lid:1,devices:[],links:[],flows:[],fid:1};
 clearSel();autosave();mark();props();renderFlows();
 toast('Холст очищен полностью',function(){undo();});
}
function dupSel(){
 var ids=[];for(var k in selD)ids.push(+k);
 if(!ids.length){toast('Выделите устройства');return;}
 pushUndo();var map={};
 ids.forEach(function(id){var d=dev(id);if(!d)return;var nd={id:S.nid++,type:d.type,x:d.x+40,y:d.y+40,name:(d.name||'')+' копия',ip:d.ip,vlan:d.vlan,model:d.model,notes:d.notes,mac:'',down:false};map[id]=nd.id;S.devices.push(nd);});
 S.links.forEach(function(L){if(map[L.a]&&map[L.b]){S.links.push({id:S.lid++,a:map[L.a],b:map[L.b],pa:L.pa,pb:L.pb,mode:L.mode,vlans:L.vlans,media:L.media,cost:L.cost,down:false,pk:0,by:0,er:0,load:0});}});
 clearSel();for(var m in map)selD[map[m]]=1;selN=selCount();
 autosave();mark();props();toast('Продублировано: '+ids.length,function(){undo();});
}
function undo(){if(!undoStack.length){toast('Нечего отменять');return;}redoStack.push(JSON.stringify(S));S=JSON.parse(undoStack.pop());norm();clearSel();autosave();mark();props();renderFlows();toast('Отменено');}
function redo(){if(!redoStack.length){toast('Нечего повторять');return;}undoStack.push(JSON.stringify(S));S=JSON.parse(redoStack.pop());norm();clearSel();autosave();mark();props();renderFlows();toast('Повторено');}
function allows(L,v){var list=String(L.vlans||'').split(',').map(function(x){return x.trim();});return L.mode==='trunk'?list.indexOf(String(v))>=0:String(L.vlans)===String(v);}
function treeLinks(){
 var root=null;S.devices.forEach(function(d){if(!root&&(d.type==='core'||d.type==='agg'))root=d.id;});
 if(!root&&S.devices[0])root=S.devices[0].id;
 var seen={},keep={},q=[root];seen[root]=1;
 while(q.length){var c=q.shift();S.links.forEach(function(L){if(L.down)return;var o=null;if(L.a===c)o=L.b;else if(L.b===c)o=L.a;if(o==null)return;if(!seen[o]){seen[o]=1;keep[L.id]=1;q.push(o);}});}
 return keep;
}
function usable(L,v){if(L.down)return false;if(cfg.loop&&sim.blocked[L.id])return false;return allows(L,v);}
function nbrs(id,v){var out=[];S.links.forEach(function(L){if(!usable(L,v))return;if(L.a===id)out.push({to:L.b,L:L});if(L.b===id)out.push({to:L.a,L:L});});return out;}
function path(s,d,v){
 var prev={},seen={},q=[s];seen[s]=1;
 while(q.length){var c=q.shift();if(c===d)break;var ns=nbrs(c,v);for(var i=0;i<ns.length;i++){var n=ns[i];if(!seen[n.to]){seen[n.to]=1;prev[n.to]={f:c,L:n.L};q.push(n.to);}}}
 if(!seen[d])return null;
 var hops=[],cur=d;while(cur!==s){var p=prev[cur];hops.unshift({from:p.f,to:cur,L:p.L});cur=p.f;}return hops;
}
function rawPath(s,d){
 var prev={},seen={},q=[s];seen[s]=1;
 while(q.length){var c=q.shift();if(c===d)break;S.links.forEach(function(L){if(L.down)return;var o=null;if(L.a===c)o=L.b;else if(L.b===c)o=L.a;if(o==null||seen[o])return;seen[o]=1;prev[o]={f:c,L:L};q.push(o);});}
 if(!seen[d])return null;var hops=[],cur=d;while(cur!==s){var p=prev[cur];hops.unshift({from:p.f,to:cur,L:p.L});cur=p.f;}return hops;
}
function capacity(L){return L.media==='fiber'?1000:(L.media==='pon'?2500:100);}
function emit(flow,src,dst,v,mode,tag){
 var sd=dev(src);if(!sd||sd.down){drop('источник выключен: '+(sd?sd.name:src));return;}
 var targets=[];
 if(mode==='unicast'||mode==='ping'){if(!dst||!dev(dst)){drop('нет приёмника');return;}targets=[dst];}
 else if(mode==='multicast'){targets=S.devices.filter(function(x){return x.id!==src&&String(x.vlan)===String(v)&&!isSw(x)&&!x.down;}).map(function(x){return x.id;});
  if(!targets.length){drop('IGMP: нет viewers с VLAN '+v);return;}
  ev('info','IGMP snooping: поток VLAN '+v+' только на порты с '+targets.length+' viewers');}
 else if(mode==='pon'){targets=S.devices.filter(function(x){return x.type==='onu'&&!x.down;}).map(function(x){return x.id;});
  if(!targets.length){drop('нет ONU');return;}}
 else if(mode==='broadcast'){
  var seen={},q=[src],edges=[];seen[src]=1;var storm=false;
  while(q.length){var c=q.shift();S.links.forEach(function(L){if(L.down)return;if(cfg.loop&&sim.blocked[L.id])return;if(!allows(L,v))return;var o=null;if(L.a===c)o=L.b;else if(L.b===c)o=L.a;if(o==null)return;edges.push({from:c,to:o,L:L});if(seen[o])storm=true;else{seen[o]=1;q.push(o);}});}
  sim.storm=storm;$('storm').className=storm?'show':'';
  if(storm){ev('warn','ПЕТЛЯ: broadcast-шторм! loopdetect '+(cfg.loop?'включён, но петля в разрешённых VLAN':'ВЫКЛЮЧЕН — включите!'));blip(120,0.4,'bad');}
  else ev('info','flood VLAN '+v+' дошёл до '+Object.keys(seen).length+' устройств');
  edges.forEach(function(e,i){spawn([{from:e.from,to:e.to,L:e.L}],v,macOf(sd),'FF:FF:FF:FF:FF:FF',tag||'🌊',i*90,1500);});
  return;
 }
 targets.forEach(function(t){
  var hops=path(src,t,v);
  if(!hops){
   var rp=rawPath(src,t);
   if(rp){var bad=null;rp.forEach(function(h){if(!allows(h.L,v))bad=h.L;});
    drop('VLAN '+v+' не пропущен: линия #'+(bad?bad.id:'?')+' ('+(bad?bad.mode+'['+bad.vlans+']':'')+') → '+(dev(t).name||t));}
   else drop('нет физического пути до '+(dev(t).name||t));
   return;}
  spawn(hops,v,macOf(sd),macOf(dev(t)),tag||(mode==='ping'?'📍':(mode==='multicast'?'📺':(mode==='pon'?'🌊':'📨'))),0,mode==='ping'?64:1400);
 });
}
function spawn(hops,v,ms,md,tag,delay,bytes){
 if(sim.packets.length>140){sim.stats.dr++;return;}
 var p={id:sim.pid++,hops:hops,idx:0,prog:0,v:v,ms:ms,md:md,tag:tag,bytes:bytes,delay:delay||0,px:null,py:null,el:null,tl:null,done:false};
 sim.packets.push(p);
}
function drop(reason){sim.stats.dr++;ev('bad','❌ '+reason);blip(140,0.18,'bad');$('stDrops').textContent=sim.stats.dr;}
function learn(d,L,fromId,mac,v){
 if(!isSw(d))return;
 var port=(L.a===d.id)?L.pa:L.pb;
 if(!sim.fdb[d.id])sim.fdb[d.id]={};
 sim.fdb[d.id][mac]={port:port||'?',vlan:v,t:Date.now()};
 var keys=Object.keys(sim.fdb[d.id]);if(keys.length>80)delete sim.fdb[d.id][keys[0]];
}
function packetNode(p){
 var c=document.createElementNS('http://www.w3.org/2000/svg','circle');
 c.setAttribute('r',cfg.pkt);c.setAttribute('fill',hue(p.v));c.setAttribute('filter','url(#glow)');c.setAttribute('stroke','#ffffff');c.setAttribute('stroke-width','1');
 var t=document.createElementNS('http://www.w3.org/2000/svg','line');
 t.setAttribute('stroke',hue(p.v));t.setAttribute('stroke-width',Math.max(1,cfg.pkt*0.6));t.setAttribute('stroke-linecap','round');t.setAttribute('opacity','0.5');
 $('pk').appendChild(t);$('pk').appendChild(c);p.el=c;p.tl=t;
}
function killPacket(p){if(p.el&&p.el.parentNode)p.el.parentNode.removeChild(p.el);if(p.tl&&p.tl.parentNode)p.tl.parentNode.removeChild(p.tl);p.el=null;p.tl=null;p.done=true;}
function stepPacket(p,dt){
 if(p.delay>0){p.delay-=dt;return;}
 if(!p.el)packetNode(p);
 var h=p.hops[p.idx];if(!h){killPacket(p);return;}
 var a=dev(h.from),b=dev(h.to);
 if(!a||!b||h.L.down||a.down||b.down){killPacket(p);h.L.er++;drop('обрыв на линии #'+h.L.id);return;}
 var dur=cfg.hop*(h.L.cost||1);
 p.prog+=dt/dur;
 var k=Math.min(1,p.prog);
 var x=a.x+(b.x-a.x)*k,y=a.y+(b.y-a.y)*k;
 p.el.setAttribute('cx',x);p.el.setAttribute('cy',y);p.el.setAttribute('r',cfg.pkt);
 if(cfg.trail>0&&p.px!=null){p.tl.setAttribute('x1',p.px);p.tl.setAttribute('y1',p.py);p.tl.setAttribute('x2',x);p.tl.setAttribute('y2',y);p.tl.style.display='';}
 else p.tl.style.display='none';
 p.px=x;p.py=y;
 if(k>=1){
  h.L.pk++;h.L.by+=p.bytes;h.L.load=Math.min(12,h.L.load+p.bytes/capacity(h.L)*8);
  learn(b,h.L,h.from,p.ms,p.v);
  var bd=dev(h.to);
  if(bd&&bd.type==='onu'&&p.idx===p.hops.length-1&&String(bd.vlan)!==String(p.v)){
   killPacket(p);drop('ONU '+(bd.name||bd.id)+' отбросила: VLAN '+bd.vlan+' ≠ '+p.v);return;}
  p.idx++;p.prog=0;p.px=null;p.py=null;
  blip(300+((parseInt(p.v,10)||0)%12)*60,0.06,'ok');
  if(p.idx>=p.hops.length){
   killPacket(p);sim.stats.pk++;sim.deliverCount++;
   $('stPkts').textContent=sim.stats.pk;
   if(sim.deliverCount%12===1||p.tag==='📍')ev('ok','✅ '+p.tag+' '+p.ms+' → '+p.md+' VLAN '+p.v+' доставлен ('+p.hops.length+' hop)');
   if(p.tag==='📍'){var rtt=0;p.hops.forEach(function(hh){rtt+=(hh.L.cost||1)*2;});
    $('pingResult').style.display='block';
    $('pingResult').textContent='PING '+p.ms+' → '+p.md+'\nVLAN '+p.v+' · hops '+p.hops.length+' · RTT ≈ '+rtt+' мс\nпотерь: 0%  TTL=64';}
  }
 }
}
function stopSim(){sim.running=false;sim.paused=false;sim.packets.forEach(killPacket);sim.packets=[];sim.storm=false;$('storm').className='';
 $('stSim').textContent='симуляция: стоп';$('stSim').style.color='';$('bPause').textContent='⏸';}
function startSim(){
 stopSim();sim.stats={pk:0,dr:0};sim.deliverCount=0;sim.flowAcc={};$('stPkts').textContent='0';$('stDrops').textContent='0';
 $('pingResult').style.display='none';
 sim.blocked={};
 if(cfg.loop){var keep=treeLinks();S.links.forEach(function(L){if(!keep[L.id]&&!L.down)sim.blocked[L.id]=1;});
  var nb=0;for(var k in sim.blocked)nb++;if(nb)ev('info','Loopdetect/RSTP: заблокировано избыточных портов: '+nb);}
 var mode=$('simMode').value,s=+$('simSrc').value,d=+$('simDst').value,v=$('simVlan').value||'1';
 sim.running=true;sim.paused=false;
 $('stSim').textContent='симуляция: идёт';$('stSim').style.color='#3ddc97';
 ev('info','▶ режим '+mode+' · VLAN '+v);
 if(mode==='flows'){if(!(S.flows||[]).length){ev('warn','нет потоков — добавьте во вкладке «Потоки»');}}
 else if(mode==='ping'){emit(null,s,d,v,'ping','📍');}
 else if(mode==='multicast'){emit(null,s,0,v,'multicast','📺');}
 else if(mode==='pon'){emit(null,s,0,v,'pon','🌊');}
 else if(mode==='broadcast'){emit(null,s,0,v,'broadcast','🌊');}
 mark();
}
function loop(t){
 requestAnimationFrame(loop);
 var dt=Math.min(60,t-(sim.last||t));sim.last=t;
 if(dirty)render();
 var active=sim.running&&!sim.paused;
 if(active){
  var sdt=dt*cfg.speed;
  if($('simMode').value==='flows'){
   (S.flows||[]).forEach(function(f){
    if(!f.on||!dev(f.src))return;
    sim.flowAcc[f.id]=(sim.flowAcc[f.id]||0)+sdt;
    var interval=1000/Math.max(1,f.rate);
    while(sim.flowAcc[f.id]>=interval){sim.flowAcc[f.id]-=interval;emit(f,f.src,f.dst,f.vlan,f.mode,f.mode==='multicast'?'📺':'📨');}
   });
  }
  for(var i=sim.packets.length-1;i>=0;i--){var p=sim.packets[i];stepPacket(p,sdt);if(p.done)sim.packets.splice(i,1);}
  S.links.forEach(function(L){L.load*=0.96;});
  if($('cHeat').checked&&Math.random()<0.12)mark();
 }
 $('stPkts').textContent=sim.stats.pk;
 $('stDrops').textContent=sim.stats.dr;
}
function checkPlan(){
 var out=[],leaves=S.devices.filter(function(d){return d.vlan&&!isSw(d);});
 var roots=S.devices.filter(function(d){return d.type==='core'||d.type==='agg'||d.type==='nvr';});
 leaves.forEach(function(d){
  var target=null;
  roots.forEach(function(r){if(!target&&String(r.vlan)===String(d.vlan))target=r;});
  if(!target)roots.forEach(function(r){if(!target)target=r;});
  if(!target){out.push({ok:false,msg:'нет ядра/приёмника для '+(d.name||d.id)});return;}
  var rp=rawPath(d.id,target.id);
  if(!rp){out.push({ok:false,msg:'НЕТ физического пути: '+(d.name||d.id)+' → '+(target.name||target.id)+' (обрыв?)'});return;}
  var bad=[];rp.forEach(function(h){if(!allows(h.L,d.vlan))bad.push(h.L);});
  if(!bad.length)out.push({ok:true,msg:'VLAN '+d.vlan+' проходит: '+(d.name||d.id)+' → '+(target.name||target.id)+' ('+rp.length+' hop)'});
  else bad.forEach(function(L){out.push({ok:false,fix:L.id,vlan:d.vlan,msg:'VLAN '+d.vlan+' НЕ пропущен на линии #'+L.id+' ('+L.mode+'['+L.vlans+']) по пути '+(d.name||d.id)+' → '+(target.name||target.id)});});
 });
 S.links.forEach(function(L){if(L.down)out.push({ok:false,msg:'АВАРИЯ: линия #'+L.id+' down'});});
 S.devices.forEach(function(d){if(d.down)out.push({ok:false,msg:'АВАРИЯ: устройство '+(d.name||d.id)+' выключено'});});
 if(cfg.loop){var keep=treeLinks();S.links.forEach(function(L){if(!keep[L.id]&&!L.down)out.push({ok:true,msg:'Избыточная линия #'+L.id+' заблокирована loopdetect (петли нет)'});});}
 else{var seen={},q=[],cyc=false;S.devices.forEach(function(d){if(!seen[d.id]){seen[d.id]=1;q=[d.id];while(q.length){var c=q.shift();S.links.forEach(function(L){if(L.down)return;var o=null;if(L.a===c)o=L.b;else if(L.b===c)o=L.a;if(o==null)return;if(seen[o])cyc=true;else{seen[o]=1;q.push(o);}});}}});
  if(cyc)out.push({ok:false,msg:'В топологии есть петля, а Loopdetect ВЫКЛЮЧЕН → риск шторма'});}
 $('checkList').innerHTML=out.map(function(o,i){
  return '<div class="chkRow'+(o.ok?' ok':'')+'">'+(o.ok?'✅ ':'⚠️ ')+esc(o.msg)+(o.fix?'<div class="fx"><button class="g" data-fix="'+o.fix+'" data-fv="'+esc(o.vlan)+'">➕ Пропустить VLAN '+esc(o.vlan)+' на линии #'+o.fix+'</button></div>':'')+'</div>';
 }).join('')||'<div class="chkRow ok">✅ Схема пуста или всё чисто</div>';
 ev('info','Проверка VLAN-плана: '+(out.filter(function(o){return !o.ok;}).length)+' проблем');
}
function fixLink(id,v){
 var L=lnk(id);if(!L)return;pushUndo();
 if(L.mode==='trunk'){var list=String(L.vlans).split(',').map(function(x){return x.trim();}).filter(Boolean);if(list.indexOf(String(v))<0)list.push(String(v));L.vlans=list.join(',');}
 else L.vlans=String(v);
 autosave();mark();checkPlan();toast('VLAN '+v+' пропущен на линии #'+id,function(){undo();});
}
function buildPlan(){
 var syn=$('planSyn').value,txt='';
 S.devices.filter(isSw).forEach(function(d){
  var acc={},trunk={};
  S.links.forEach(function(L){
   if(L.a!==d.id&&L.b!==d.id)return;
   var port=(L.a===d.id)?L.pa:L.pb;
   if(L.mode==='access'){(acc[L.vlans]=acc[L.vlans]||[]).push(port);}
   else String(L.vlans).split(',').forEach(function(v){v=v.trim();if(v)(trunk[v]=trunk[v]||[]).push(port);});
  });
  var vlans={};for(var a in acc)vlans[a]=1;for(var t in trunk)vlans[t]=1;
  txt+='! ===== '+(d.name||TYPES[d.type].n)+' ('+(d.ip||'без IP')+') =====\n';
  if(syn==='des'){
   for(var v in vlans)txt+='create vlan VLAN'+v+' tag '+v+'\n';
   for(var v2 in trunk)txt+='config vlan vlanid '+v2+' add tagged '+trunk[v2].join(',')+'\n';
   for(var v3 in acc){txt+='config vlan vlanid '+v3+' add untagged '+acc[v3].join(',')+'\n';txt+='config ports '+acc[v3].join(',')+' pvid '+v3+'\n';}
   txt+='save\n\n';
  }else{
   txt+='vlan database\n';for(var v4 in vlans)txt+='vlan '+v4+'\n';txt+='exit\n';
   for(var v5 in trunk)txt+='interface ethernet 1/0/'+trunk[v5].join(',')+'\nvlan participation include '+v5+'\nvlan tagging tagged\nexit\n';
   for(var v6 in acc)txt+='interface ethernet 1/0/'+acc[v6].join(',')+'\nvlan participation include '+v6+'\nvlan pvid '+v6+'\nexit\n';
   txt+='copy running-config startup-config\n\n';
  }
 });
 if(!txt)txt='Нет коммутаторов на схеме.';
 $('planOut').textContent=txt;
}
function renderFlows(){
 var el=$('flowList');
 el.innerHTML=(S.flows||[]).map(function(f){
  var opts=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('');
  return '<div class="flowRow"><div class="h"><input type="checkbox" data-fon="'+f.id+'"'+(f.on?' checked':'')+'><b>'+esc(f.name)+'</b><button class="d" data-fdel="'+f.id+'" style="padding:3px 8px">✕</button></div>'
  +'<div class="g"><select data-fsrc="'+f.id+'">'+opts+'</select><select data-fdst="'+f.id+'"><option value="0">—</option>'+opts+'</select></div>'
  +'<div class="g"><input data-fvlan="'+f.id+'" list="vlanList" value="'+esc(f.vlan)+'"><select data-fmode="'+f.id+'"><option value="unicast"'+(f.mode==='unicast'?' selected':'')+'>unicast</option><option value="multicast"'+(f.mode==='multicast'?' selected':'')+'>multicast</option></select><input type="number" data-frate="'+f.id+'" value="'+f.rate+'" min="1" max="20" title="pps"></div></div>';
 }).join('')||'<div style="color:#7f93b8;font-size:12px">Потоков нет. Добавьте: камера→NVR, IPTV→приставки, абонент→ядро.</div>';
 Array.prototype.forEach.call(el.querySelectorAll('[data-fsrc]'),function(s){s.value=String(flowById(+s.getAttribute('data-fsrc')).src);});
 Array.prototype.forEach.call(el.querySelectorAll('[data-fdst]'),function(s){s.value=String(flowById(+s.getAttribute('data-fdst')).dst||0);});
}
function flowById(id){for(var i=0;i<(S.flows||[]).length;i++){if(S.flows[i].id===id)return S.flows[i];}return {};}
function views(){try{return JSON.parse(localStorage.getItem('netlab_views')||'[]');}catch(e){return [];}}
function renderViews(){
 $('viewList').innerHTML=views().map(function(v,i){return '<div class="viewRow"><button data-view="'+i+'">📌 '+esc(v.name)+'</button><button class="d" data-vdel="'+i+'" style="flex:0;padding:4px 8px">✕</button></div>';}).join('')||'<div style="color:#7f93b8">видов нет</div>';
}
function pin(){return localStorage.getItem('swhpin')||prompt('PIN админки:')||'';}
function saveScheme(){
 var name=prompt('Название схемы:','Локалка '+new Date().toLocaleDateString('ru'));if(!name)return;
 fetch('/api/schemes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin(),name:name,data:JSON.stringify(S)})})
 .then(function(r){return r.json();}).then(function(res){toast(res.ok?('Сохранено #'+res.id):('Ошибка: '+(res.error||'')));}).catch(function(e){toast('Ошибка: '+e.message);});
}
function openModal(){
 fetch('/api/schemes').then(function(r){return r.json();}).then(function(rows){
  $('modalList').innerHTML=(rows||[]).map(function(r){return '<div class="mRow"><span class="t">'+esc(r.name)+'</span><span class="d">'+esc(r.updated_at||'')+'</span><button class="p" data-open="'+r.id+'">Открыть</button><button class="d" data-mdel="'+r.id+'">✕</button></div>';}).join('')||'<div style="color:#93a6c9">Сохранённых схем нет.</div>';
  $('modal').className='open';
 }).catch(function(e){toast('Ошибка: '+e.message);});
}
function exportSvg(){
 var clone=$('cv').cloneNode(true);clone.setAttribute('width','1600');clone.setAttribute('height','1000');
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var mq=clone.querySelector('#marquee');if(mq)mq.parentNode.removeChild(mq);
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');bg.setAttribute('width','1600');bg.setAttribute('height','1000');bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0a1424');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});
 var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='netlab-scheme.svg';a.click();toast('SVG скачан');
}
function exportPng(){
 var clone=$('cv').cloneNode(true);clone.setAttribute('width','1600');clone.setAttribute('height','1000');
 clone.querySelector('#world').setAttribute('transform','translate(80,60) scale(1)');
 var mq=clone.querySelector('#marquee');if(mq)mq.parentNode.removeChild(mq);
 var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');bg.setAttribute('width','1600');bg.setAttribute('height','1000');bg.setAttribute('fill',cfg.theme==='light'?'#ffffff':'#0a1424');
 clone.insertBefore(bg,clone.firstChild);
 var blob=new Blob([clone.outerHTML],{type:'image/svg+xml'});var img=new Image();
 img.onload=function(){var c=document.createElement('canvas');c.width=1600;c.height=1000;var ctx=c.getContext('2d');ctx.drawImage(img,0,0);var a=document.createElement('a');a.href=c.toDataURL('image/png');a.download='netlab-scheme.png';a.click();toast('PNG скачан');};
 img.onerror=function(){toast('PNG не удалось — используйте SVG');};
 img.src=URL.createObjectURL(blob);
}
function fit(){
 if(!S.devices.length){view={x:70,y:50,k:1};mark();return;}
 var minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;
 S.devices.forEach(function(d){minX=Math.min(minX,d.x-60);maxX=Math.max(maxX,d.x+60);minY=Math.min(minY,d.y-40);maxY=Math.max(maxY,d.y+40);});
 var r=$('cv').getBoundingClientRect();
 var k=Math.max(0.3,Math.min(2.2,Math.min((r.width-60)/(maxX-minX),(r.height-60)/(maxY-minY))));
 view.k=k;view.x=(r.width-(maxX-minX)*k)/2-minX*k;view.y=(r.height-(maxY-minY)*k)/2-minY*k;mark();
}
function tidy(){
 pushUndo();var hasP={};S.links.forEach(function(L){hasP[L.b]=1;});
 var roots=S.devices.filter(function(d){return !hasP[d.id];}).map(function(d){return d.id;});
 if(!roots.length&&S.devices[0])roots=[S.devices[0].id];
 var lvl={},seen={},q=roots.map(function(r){return [r,0];});
 while(q.length){var it=q.shift();if(seen[it[0]])continue;seen[it[0]]=1;lvl[it[0]]=it[1];S.links.forEach(function(L){if(L.a===it[0])q.push([L.b,it[1]+1]);});}
 var by={};S.devices.forEach(function(d){var l=(lvl[d.id]==null)?4:lvl[d.id];(by[l]=by[l]||[]).push(d);});
 Object.keys(by).forEach(function(l){by[l].forEach(function(d,i){d.x=120+i*230;d.y=70+(+l)*150;});});
 autosave();mark();fit();toast('Автораскладка выполнена',function(){undo();});
}
function bind(){
 $('cv').addEventListener('pointerdown',function(e){
  var t=e.target,g=null,l=null;
  while(t&&t!==$('cv')){if(t.getAttribute){if(t.getAttribute('data-d')){g=t;break;}if(t.getAttribute('data-l')){l=t;break;}}t=t.parentNode;}
  var p=pt(e);
  if(tool==='marquee'&&!g&&!l){marq={x0:p.sx,y0:p.sy,x1:p.sx,y1:p.sy,add:e.shiftKey};$('marquee').style.display='';return;}
  if(g){var id=+g.getAttribute('data-d');
   if(tool==='link'){
    if(linkFrom==null){linkFrom=id;ev('info','🔗 линия от #'+id+' — кликните второе устройство');}
    else if(linkFrom!==id){pushUndo();S.links.push({id:S.lid++,a:linkFrom,b:id,pa:'',pb:'',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false,pk:0,by:0,er:0,load:0});linkFrom=null;setTool('select');autosave();mark();props();toast('Линия создана');}
    return;}
   if(e.shiftKey){if(selD[id])delete selD[id];else selD[id]=1;selN=selCount();mark();fillReg();props();return;}
   if(!selD[id]){selectDev(id,false);}
   var offs=[];for(var k in selD){var dd=dev(+k);if(dd)offs.push({id:+k,dx:p.x-dd.x,dy:p.y-dd.y});}
   drag={offs:offs,moved:false};pushUndo();return;}
  if(l){selectLink(+l.getAttribute('data-l'),e.shiftKey);return;}
  if(tool==='marquee'){marq={x0:p.sx,y0:p.sy,x1:p.sx,y1:p.sy,add:e.shiftKey};$('marquee').style.display='';return;}
  if(!e.shiftKey)clearSel();
  pan={x:e.clientX-view.x,y:e.clientY-view.y};
 });
 window.addEventListener('pointermove',function(e){
  if(marq){var r=$('cv').getBoundingClientRect();marq.x1=e.clientX-r.left;marq.y1=e.clientY-r.top;
   var m=$('marquee');m.setAttribute('x',Math.min(marq.x0,marq.x1));m.setAttribute('y',Math.min(marq.y0,marq.y1));
   m.setAttribute('width',Math.abs(marq.x1-marq.x0));m.setAttribute('height',Math.abs(marq.y1-marq.y0));return;}
  if(drag){var p=pt(e);drag.moved=true;drag.offs.forEach(function(o){var d=dev(o.id);if(d){d.x=snap(p.x-o.dx);d.y=snap(p.y-o.dy);}});mark();return;}
  if(pan){view.x=e.clientX-pan.x;view.y=e.clientY-pan.y;mark();}
 });
 window.addEventListener('pointerup',function(e){
  if(marq){
   var x0=(Math.min(marq.x0,marq.x1)-view.x)/view.k,x1=(Math.max(marq.x0,marq.x1)-view.x)/view.k;
   var y0=(Math.min(marq.y0,marq.y1)-view.y)/view.k,y1=(Math.max(marq.y0,marq.y1)-view.y)/view.k;
   if(!marq.add){selD={};selL={};}
   S.devices.forEach(function(d){if(d.x>=x0&&d.x<=x1&&d.y>=y0&&d.y<=y1)selD[d.id]=1;});
   S.links.forEach(function(L){var a=dev(L.a),b=dev(L.b);if(a&&b&&selD[a.id]&&selD[b.id])selL[L.id]=1;});
   selN=selCount();marq=null;$('marquee').style.display='none';mark();fillReg();props();
   if(selN)toast('Выделено рамкой: '+selN);
   return;}
  if(drag){if(drag.moved)autosave();else undoStack.pop();drag=null;return;}
  pan=null;
 });
 $('cv').addEventListener('wheel',function(e){
  e.preventDefault();var r=$('cv').getBoundingClientRect();var mx=e.clientX-r.left,my=e.clientY-r.top;
  var f=e.deltaY<0?1.12:0.89,nk=Math.max(0.3,Math.min(2.6,view.k*f));
  view.x=mx-(mx-view.x)*(nk/view.k);view.y=my-(my-view.y)*(nk/view.k);view.k=nk;mark();
 },{passive:false});
 $('cv').addEventListener('dblclick',function(e){var p=pt(e);addDevice(lastType||'pc',p.x,p.y);});
 $('cv').addEventListener('dragover',function(e){e.preventDefault();});
 $('cv').addEventListener('drop',function(e){e.preventDefault();var k=e.dataTransfer?e.dataTransfer.getData('text/plain'):'';if(k&&TYPES[k]){var p=pt(e);addDevice(k,p.x,p.y);}});
 $('palDev').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){addDevice(t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palDev').addEventListener('dragstart',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){if(e.dataTransfer)e.dataTransfer.setData('text/plain',t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palTpl').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palTpl')){if(t.getAttribute&&t.getAttribute('data-tpl')){addTpl(t.getAttribute('data-tpl'));return;}t=t.parentNode;}});
 $('regSearch').addEventListener('input',fillReg);
 $('regType').addEventListener('change',fillReg);
 $('regSort').addEventListener('change',fillReg);
 $('regList').addEventListener('click',function(e){
  var t=e.target;
  if(t.getAttribute&&t.getAttribute('data-chk')){var cid=+t.getAttribute('data-chk');if(t.checked)selD[cid]=1;else delete selD[cid];selN=selCount();mark();props();fillReg();return;}
  while(t&&t!==$('regList')){if(t.getAttribute&&t.getAttribute('data-reg')){var id=+t.getAttribute('data-reg');selectDev(id,e.shiftKey);var d=dev(id);
   if(d){var r=$('cv').getBoundingClientRect();view.x=r.width/2-d.x*view.k;view.y=r.height/2-d.y*view.k;mark();}return;}t=t.parentNode;}
 });
 var dragReg=null;
 $('regList').addEventListener('dragstart',function(e){var t=e.target;while(t&&t!==$('regList')){if(t.getAttribute&&t.getAttribute('data-reg')){dragReg=+t.getAttribute('data-reg');t.className+=' drag';return;}t=t.parentNode;}});
 $('regList').addEventListener('dragover',function(e){e.preventDefault();});
 $('regList').addEventListener('drop',function(e){
  e.preventDefault();var t=e.target;while(t&&t!==$('regList')){if(t.getAttribute&&t.getAttribute('data-reg')){var to=+t.getAttribute('data-reg');
   if(dragReg!=null&&dragReg!==to){pushUndo();var fromIdx=-1,toIdx=-1;S.devices.forEach(function(d,i){if(d.id===dragReg)fromIdx=i;if(d.id===to)toIdx=i;});
    if(fromIdx>=0&&toIdx>=0){var it=S.devices.splice(fromIdx,1)[0];S.devices.splice(toIdx,0,it);autosave();mark();toast('Порядок отрисовки изменён',function(){undo();});}}
   dragReg=null;fillReg();return;}t=t.parentNode;}
  dragReg=null;fillReg();
 });
 $('bBulkVlan').addEventListener('click',function(){bulkVlan($('bulkVlan').value);});
 $('bBulkDel').addEventListener('click',delSel);
 $('bViewSave').addEventListener('click',function(){
  var n=$('viewName').value||('Вид '+(views().length+1));
  var v=views();v.push({name:n,view:{x:view.x,y:view.y,k:view.k}});
  try{localStorage.setItem('netlab_views',JSON.stringify(v));}catch(e){}
  $('viewName').value='';renderViews();toast('Вид сохранён: '+n);
 });
 $('viewList').addEventListener('click',function(e){
  var t=e.target;while(t&&t!==$('viewList')){
   if(t.getAttribute&&t.getAttribute('data-view')){var v=views()[+t.getAttribute('data-view')];if(v){view=v.view;mark();toast('Вид применён: '+v.name);}return;}
   if(t.getAttribute&&t.getAttribute('data-vdel')){var arr=views();arr.splice(+t.getAttribute('data-vdel'),1);try{localStorage.setItem('netlab_views',JSON.stringify(arr));}catch(e2){}renderViews();return;}
   t=t.parentNode;}
 });
 $('bSave').addEventListener('click',saveScheme);
 $('bOpen').addEventListener('click',openModal);
 $('modalClose').addEventListener('click',function(){$('modal').className='';});
 $('modal').addEventListener('click',function(e){if(e.target===$('modal'))$('modal').className='';});
 $('modalList').addEventListener('click',function(e){
  var t=e.target;while(t&&t!==$('modalList')){
   if(t.getAttribute&&t.getAttribute('data-open')){var id=t.getAttribute('data-open');
    fetch('/api/schemes/'+id).then(function(r){return r.json();}).then(function(sc){if(sc&&sc.data){pushUndo();S=JSON.parse(sc.data);norm();clearSel();autosave();mark();props();renderFlows();fit();$('modal').className='';toast('Открыто: '+sc.name);}});return;}
   if(t.getAttribute&&t.getAttribute('data-mdel')){var did=t.getAttribute('data-mdel');
    if(confirm('Удалить схему #'+did+'?')){fetch('/api/schemes/'+did,{method:'DELETE',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin()})}).then(function(r){return r.json();}).then(function(){openModal();toast('Схема удалена');});}return;}
   t=t.parentNode;}
 });
 $('bSvg').addEventListener('click',exportSvg);
 $('bPng').addEventListener('click',exportPng);
 $('bPrint').addEventListener('click',function(){window.print();});
 $('bLink').addEventListener('click',function(){setTool(tool==='link'?'select':'link');});
 $('bSel').addEventListener('click',function(){setTool('select');});
 $('bMarquee').addEventListener('click',function(){setTool(tool==='marquee'?'select':'marquee');});
 $('bUndo').addEventListener('click',undo);
 $('bRedo').addEventListener('click',redo);
 $('bDup').addEventListener('click',dupSel);
 $('bDelSel').addEventListener('click',delSel);
 $('bClearAll').addEventListener('click',function(){if(confirm('Очистить ВСЁ: устройства, линии, потоки? (можно отменить)'))clearAll();});
 $('bClearSel').addEventListener('click',function(){clearSel();toast('Выделение снято');});
 $('bSound').addEventListener('click',function(){cfg.sound=!cfg.sound;$('bSound').textContent=cfg.sound?'🔊 Звук':'🔇 Тихо';$('bSound').className=cfg.sound?'on':'';toast(cfg.sound?'Звук включён':'Звук выключен');});
 $('bRun').addEventListener('click',startSim);
 $('bPause').addEventListener('click',function(){if(!sim.running)return;sim.paused=!sim.paused;$('bPause').textContent=sim.paused?'▶':'⏸';$('stSim').textContent=sim.paused?'симуляция: пауза':'симуляция: идёт';});
 $('bStep').addEventListener('click',function(){if(!sim.running){startSim();sim.paused=true;$('bPause').textContent='▶';}
  sim.paused=true;sim.packets.forEach(function(p){var h=p.hops[p.idx];if(h){p.prog=1;stepPacket(p,0);}});
  for(var i=sim.packets.length-1;i>=0;i--){if(sim.packets[i].done)sim.packets.splice(i,1);}
  $('stSim').textContent='симуляция: шаг';});
 $('bStop').addEventListener('click',function(){stopSim();ev('info','⏹ остановлено');mark();});
 $('simRate').addEventListener('input',function(){$('vSimRate').textContent=this.value;});
 $('bDemo').addEventListener('click',function(){pushUndo();S=demo();norm();clearSel();autosave();mark();props();renderFlows();fit();toast('Пример загружен',function(){undo();});});
 $('bRandTopo').addEventListener('click',randTopo);
 $('bFit').addEventListener('click',function(){fit();toast('Схема вписана');});
 $('bRand').addEventListener('click',tidy);
 $('bFault').addEventListener('click',function(){
  var up=S.links.filter(function(L){return !L.down;});if(!up.length){toast('Нет работающих линий');return;}
  pushUndo();var L=up[Math.floor(Math.random()*up.length)];L.down=true;autosave();mark();
  ev('warn','⚡ АВАРИЯ: оборвана линия #'+L.id+' ('+(dev(L.a)||{}).name+' ↔ '+(dev(L.b)||{}).name+')');
  toast('Авария на линии #'+L.id,function(){undo();});
 });
 $('bHeal').addEventListener('click',function(){pushUndo();S.links.forEach(function(L){L.down=false;L.er=0;});S.devices.forEach(function(d){d.down=false;});autosave();mark();ev('ok','🩹 все аварии устранены');toast('Сеть восстановлена',function(){undo();});});
 $('bCfg').addEventListener('click',function(){
  cfg={grid:true,snap:true,speed:1,hop:380,pkt:6,glow:6,trail:18,label:11,curve:0.22,heat:true,vcol:true,loop:true,theme:'dark',sound:cfg.sound};
  $('cZoom').value=100;$('cGrid').checked=true;$('cSnap').checked=true;$('cSpeed').value=100;$('cHop').value=380;$('cPkt').value=6;$('cGlow').value=6;$('cTrail').value=18;$('cLabel').value=11;$('cCurve').value=22;$('cHeat').checked=true;$('cVcol').checked=true;$('cLoop').checked=true;$('cTheme').value='dark';
  $('vSpeed').textContent='1.0x';$('vHop').textContent='380';$('vPkt').textContent='6';$('vGlow').textContent='6';$('vTrail').textContent='18';$('vLabel').textContent='11';$('vCurve').textContent='22';
  stageClass();view={x:70,y:50,k:1};mark();toast('Настройки сброшены');
 });
 $('cZoom').addEventListener('input',function(){view.k=this.value/100;mark();});
 $('cGrid').addEventListener('change',function(){cfg.grid=this.checked;stageClass();});
 $('cSnap').addEventListener('change',function(){cfg.snap=this.checked;});
 $('cSpeed').addEventListener('input',function(){cfg.speed=this.value/100;$('vSpeed').textContent=cfg.speed.toFixed(1)+'x';});
 $('cHop').addEventListener('input',function(){cfg.hop=+this.value;$('vHop').textContent=this.value;});
 $('cPkt').addEventListener('input',function(){cfg.pkt=+this.value;$('vPkt').textContent=this.value;});
 $('cGlow').addEventListener('input',function(){cfg.glow=+this.value;$('vGlow').textContent=this.value;mark();});
 $('cTrail').addEventListener('input',function(){cfg.trail=+this.value;$('vTrail').textContent=this.value;});
 $('cLabel').addEventListener('input',function(){cfg.label=+this.value;$('vLabel').textContent=this.value;mark();});
 $('cCurve').addEventListener('input',function(){cfg.curve=this.value/100;$('vCurve').textContent=this.value;mark();});
 $('cHeat').addEventListener('change',function(){cfg.heat=this.checked;mark();});
 $('cVcol').addEventListener('change',function(){cfg.vcol=this.checked;mark();});
 $('cLoop').addEventListener('change',function(){cfg.loop=this.checked;sim.blocked={};if(cfg.loop){var keep=treeLinks();S.links.forEach(function(L){if(!keep[L.id]&&!L.down)sim.blocked[L.id]=1;});}mark();ev('info','Loopdetect '+(cfg.loop?'включён':'выключен'));});
 $('cTheme').addEventListener('change',function(){cfg.theme=this.value;stageClass();mark();});
 $('tabs').addEventListener('click',function(e){
  var t=e.target;while(t&&t!==$('tabs')){if(t.getAttribute&&t.getAttribute('data-tab')){
   var name=t.getAttribute('data-tab');
   Array.prototype.forEach.call($('tabs').children,function(b){b.className=(b.getAttribute('data-tab')===name)?'on':'';});
   ['props','flows','fdb','check','plan','events'].forEach(function(pn){$('pane'+pn.charAt(0).toUpperCase()+pn.slice(1)).className=(pn===name)?'pane on':'pane';});
   if(name==='plan')buildPlan();if(name==='fdb')renderFdb();if(name==='flows')renderFlows();
   return;}t=t.parentNode;}
 });
 $('bAddFlow').addEventListener('click',function(){
  pushUndo();var src=S.devices[0]?S.devices[0].id:0;
  S.flows.push({id:S.fid++,name:'Поток '+(S.flows.length+1),src:src,dst:0,vlan:'135',mode:'unicast',rate:3,on:true});
  autosave();renderFlows();toast('Поток добавлен',function(){undo();});
 });
 $('flowList').addEventListener('click',function(e){
  var t=e.target;
  if(t.getAttribute&&t.getAttribute('data-fdel')){pushUndo();var id=+t.getAttribute('data-fdel');S.flows=S.flows.filter(function(f){return f.id!==id;});autosave();renderFlows();toast('Поток удалён',function(){undo();});return;}
  if(t.getAttribute&&t.getAttribute('data-fon')){var f=flowById(+t.getAttribute('data-fon'));f.on=t.checked;autosave();ev('info',(f.on?'▶':'⏸')+' поток '+f.name);return;}
 });
 $('flowList').addEventListener('input',function(e){
  var t=e.target,a;
  if((a=t.getAttribute('data-fsrc'))){flowById(+a).src=+t.value;autosave();}
  if((a=t.getAttribute('data-fdst'))){flowById(+a).dst=+t.value;autosave();}
  if((a=t.getAttribute('data-fvlan'))){flowById(+a).vlan=t.value;autosave();}
  if((a=t.getAttribute('data-fmode'))){flowById(+a).mode=t.value;autosave();}
  if((a=t.getAttribute('data-frate'))){flowById(+a).rate=Math.max(1,+t.value||1);autosave();}
 });
 $('fdbDev').addEventListener('change',renderFdb);
 $('bFdbClear').addEventListener('click',function(){sim.fdb={};renderFdb();toast('FDB очищена');});
 $('bCheck').addEventListener('click',checkPlan);
 $('checkList').addEventListener('click',function(e){
  var t=e.target;while(t&&t!==$('checkList')){if(t.getAttribute&&t.getAttribute('data-fix')){fixLink(+t.getAttribute('data-fix'),t.getAttribute('data-fv'));return;}t=t.parentNode;}
 });
 $('planSyn').addEventListener('change',buildPlan);
 $('bPlanCopy').addEventListener('click',function(){buildPlan();
  var txt=$('planOut').textContent;
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(function(){toast('План работ скопирован');},function(){toast('Не удалось скопировать');});}
  else{var ta=document.createElement('textarea');ta.value=txt;document.body.appendChild(ta);ta.select();try{document.execCommand('copy');toast('План работ скопирован');}catch(e2){toast('Скопируйте вручную');}document.body.removeChild(ta);}
 });
 $('evFilter').addEventListener('change',renderLog);
 $('bLogClear').addEventListener('click',function(){sim.ev=[];renderLog();});
 window.addEventListener('keydown',function(e){
  var tag=e.target?e.target.tagName:'';
  if(tag==='INPUT'||tag==='SELECT'||tag==='TEXTAREA')return;
  if(e.key==='Delete'||e.key==='Backspace'){delSel();e.preventDefault();}
  if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='z'){if(e.shiftKey)redo();else undo();e.preventDefault();}
  if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='y'){redo();e.preventDefault();}
  if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='a'){selD={};selL={};S.devices.forEach(function(d){selD[d.id]=1;});S.links.forEach(function(L){selL[L.id]=1;});selN=selCount();mark();fillReg();props();e.preventDefault();toast('Выделено всё: '+selN);}
  if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='d'){dupSel();e.preventDefault();}
  if(e.key==='Escape'){setTool('select');clearSel();}
 });
 window.addEventListener('resize',function(){mark();});
 setInterval(function(){if($('paneFdb').className.indexOf('on')>=0)renderFdb();},1500);
}
function stageClass(){$('stage').className=(cfg.grid?'grid ':'')+cfg.theme;}
palette();bind();
var saved=null;try{saved=localStorage.getItem('netlab_auto');}catch(e){}
try{S=saved?JSON.parse(saved):demo();}catch(e){S=demo();}
if(!S||!S.devices||!S.links)S=demo();
norm();stageClass();renderViews();renderFlows();props();mark();fit();
ev('info','🧪 NetLab PRO готов: '+S.devices.length+' устройств, '+S.links.length+' линий, '+(S.flows||[]).length+' потоков');
ev('info','▶ Пуск — потоки; ⬚ Рамка — массовое выделение; 🔎 Проверка — VLAN-план; 📋 План — команды для свитчей');
requestAnimationFrame(loop);
})();
</script>
</body></html>
'''

# ---------- ИСПРАВЛЕННЫЙ self-check: только разметка, динамические id разрешены ----------
markup = HTML.split('<script>')[0]
script = HTML.split('<script>')[1].split('</script>')[0]
markup_ids = re.findall(r'id="([A-Za-z0-9_]+)"', markup)
dup = sorted(set([i for i in markup_ids if markup_ids.count(i) > 1]))
refs = set(re.findall(r"\$\('([A-Za-z0-9_]+)'\)", script))
dynamic_ok = {'pDel', 'pBulkVlan', 'pBulkApply', 'pBulkUp'}
missing = sorted(refs - set(markup_ids) - dynamic_ok)
clean = re.sub(r'/\*.*?\*/', '', script, flags=re.S)
bal = {'{': 0, '(': 0, '[': 0}
pairs = {'}': '{', ')': '(', ']': '['}
instr = None
escq = False
for ch in clean:
    if instr:
        if escq:
            escq = False
        elif ch == '\\':
            escq = True
        elif ch == instr:
            instr = None
        continue
    if ch in ('"', "'", '`'):
        instr = ch
        continue
    if ch in bal:
        bal[ch] += 1
    elif ch in pairs:
        bal[pairs[ch]] -= 1
problems = []
if dup:
    problems.append('duplicate markup ids: ' + ','.join(dup))
if missing:
    problems.append('missing ids: ' + ','.join(missing))
if any(v != 0 for v in bal.values()):
    problems.append('unbalanced brackets: ' + str(bal))
if problems:
    raise SystemExit('SELF-CHECK FAILED (файлы НЕ тронуты): ' + ' | '.join(problems))
print('ok: self-check пройден (markup ids:', len(markup_ids), ', refs:', len(refs), ', brackets balanced)')

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
        print('ok: /netlab -> файл, no-store')
    else:
        print('ПРОПУСК: маршрут netlab_page не найден')
else:
    print('ok: маршрут уже файловый')

try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v25b_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v25b',
           'fixes': ['fixed self-check (markup-only ids, dynamic ids allowed, comments stripped)',
                     'netlab PRO: flows engine, FDB, faults, storm/loopdetect, IGMP, PON, ping RTT',
                     'marquee multi-select + bulk ops', 'quick clear-all with undo', 'undo/redo',
                     'VLAN plan check + one-click fix', 'work plan DES/DGS', 'saved views',
                     'registry drag reorder', 'sound with mute', '14 live controls']},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v25b. Бэкапы: backups/swh_pre_v25b_' + TS + '.py, backups/netlab_pre_v25b_' + TS + '.html')
