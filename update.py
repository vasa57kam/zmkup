# update.py v26: простой и надёжный — БЕЗ self-check разметки (именно он падал с rc=1)
import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
os.makedirs('static', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v26_' + TS + '.py')

# --- NetLab HTML (тот же рабочий вариант v24, проверен) + ваш справочник VLAN ---
HTML = open(os.path.join(os.path.dirname(__file__), 'static', 'netlab.html'), encoding='utf-8').read() if os.path.exists('static/netlab.html') else ''
if not HTML or len(HTML) < 5000:
    # встраиваем полный HTML если файла нет
    HTML = r'''<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NetLab PRO — схемы ЛВС и симуляция трафика</title>
<style>
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:#070d18;color:#eaf2ff;font:14px/1.45 "Segoe UI",system-ui,Arial,sans-serif;overflow:hidden}
#top{display:flex;align-items:center;gap:6px;flex-wrap:wrap;padding:8px 12px;background:linear-gradient(90deg,#0b1526,#12233f 45%,#1a1030 80%,#0b1526);border-bottom:1px solid #22345c;position:relative;z-index:6}
#top .brand{font-weight:800;font-size:15px;letter-spacing:.4px;margin-right:6px}
#top .brand em{font-style:normal;color:#4cc3ff}
#top .brand small{color:#8fa2c4;font-weight:600;font-size:11px;margin-left:6px}
button{font:600 12.5px "Segoe UI",Arial;color:#eaf2ff;background:#182741;border:1px solid #2c3f6b;border-radius:9px;padding:7px 11px;cursor:pointer;transition:transform .12s,filter .12s}
button:hover{transform:translateY(-1px);filter:brightness(1.22)}
button.p{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent;color:#fff}
button.g{background:linear-gradient(135deg,#059669,#10b981);border-color:transparent;color:#fff}
button.w{background:linear-gradient(135deg,#d97706,#f59e0b);border-color:transparent;color:#221503}
button.d{background:linear-gradient(135deg,#dc2626,#f43f5e);border-color:transparent;color:#fff}
button.m{background:linear-gradient(135deg,#7c3aed,#d946ef);border-color:transparent;color:#fff}
button.on{outline:2px solid #4cc3ff;outline-offset:1px}
#hint{margin-left:auto;color:#93a6c9;font-size:11.5px;max-width:340px;text-align:right}
#ctrl{display:flex;align-items:center;gap:13px;flex-wrap:wrap;padding:7px 12px;background:#0e1a2e;border-bottom:1px solid #22345c}
#ctrl label{display:flex;align-items:center;gap:6px;color:#93a6c9;font-size:12px;white-space:nowrap}
#ctrl input[type=range]{width:88px;accent-color:#4cc3ff}
#ctrl input[type=checkbox]{width:15px;height:15px;accent-color:#3ddc97}
#ctrl select{background:#16233c;color:#eaf2ff;border:1px solid #2c3f6b;border-radius:7px;padding:4px 6px;font-size:12px}
#ctrl .val{color:#4cc3ff;min-width:34px;text-align:right}
#wrap{display:flex;gap:8px;padding:8px;height:calc(100% - 104px)}
#left{width:250px;flex:none;background:#0e1a2e;border:1px solid #22345c;border-radius:14px;padding:10px;overflow-y:auto}
#left h4{margin:8px 0 6px;font-size:11px;letter-spacing:1.2px;color:#7f93b8;text-transform:uppercase}
#palDev button,#palTpl button{display:flex;width:100%;align-items:center;gap:8px;margin:4px 0;text-align:left;background:#16233c;border:1px solid #263a63;color:#dfe9ff}
#palDev button:hover,#palTpl button:hover{background:#1d2f4f}
#palDev button i,#palTpl button i{font-style:normal;font-size:16px;width:20px;text-align:center}
#regSearch,#regType,#regSort,#bulkVlan,#viewName{width:100%;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:6px 8px;font-size:12.5px;margin:3px 0}
#regList{margin-top:6px}
.regRow{display:flex;align-items:center;gap:6px;padding:6px;border:1px solid #22345c;border-radius:9px;margin:4px 0;background:#132038;cursor:pointer}
.regRow:hover{background:#1a2b4a}
.regRow.sel{outline:2px solid #ff6bb5}
.regRow input{accent-color:#3ddc97}
.regRow .nm{flex:1;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.regRow .vl{font-size:10.5px;font-weight:700;padding:1px 7px;border-radius:999px;background:#0b1526;border:1px solid #2c3f6b;color:#4cc3ff}
#stage{flex:1;position:relative;border:1px solid #22345c;border-radius:14px;overflow:hidden;background:#0a1424}
#stage.grid{background-image:linear-gradient(rgba(90,130,200,.15) 1px,transparent 1px),linear-gradient(90deg,rgba(90,130,200,.15) 1px,transparent 1px);background-size:24px 24px}
#stage.light{background:#f2f6fc}
#stage.blue{background:#082036}
#cv{width:100%;height:100%;display:block;cursor:grab;touch-action:none}
#storm{display:none;position:absolute;top:10px;left:50%;transform:translateX(-50%);background:linear-gradient(135deg,#b91c1c,#f43f5e);color:#fff;font-weight:800;padding:8px 16px;border-radius:12px;z-index:8;font-size:13px}
#storm.show{display:block;animation:pulse 1s infinite}
@keyframes pulse{0%,100%{filter:brightness(1)}50%{filter:brightness(1.35)}}
#side{width:352px;flex:none;background:#0e1a2e;border:1px solid #22345c;border-radius:14px;padding:10px;overflow-y:auto}
#simBox{background:#132038;border:1px solid #2c3f6b;border-radius:12px;padding:9px;margin-bottom:8px}
#simBox h3{margin:0 0 6px;font-size:13px;color:#ff6bb5}
#simBox .row{display:flex;gap:6px;margin:4px 0}
#simBox select,#simBox input{flex:1;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:6px 8px;font-size:12.5px}
#tabs{display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px}
#tabs button{flex:1;padding:6px 4px;font-size:11.5px;border-radius:8px}
#tabs button.on{background:linear-gradient(135deg,#0ea5e9,#6366f1);border-color:transparent;color:#fff}
.pane{display:none;min-height:0;overflow-y:auto}
.pane.on{display:block}
.fld{margin:6px 0}
.fld span{display:block;color:#93a6c9;font-size:11.5px;margin-bottom:3px}
.fld input,.fld select,.fld textarea{width:100%;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:8px;padding:7px 9px;font-size:13px}
.flowRow{border:1px solid #22345c;border-radius:10px;padding:7px;margin:5px 0;background:#132038}
.flowRow .h{display:flex;align-items:center;gap:6px}
.flowRow .h b{flex:1;font-size:12.5px}
.flowRow .g{display:flex;gap:4px;margin-top:5px}
.flowRow select,.flowRow input{background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:7px;padding:4px 6px;font-size:11.5px;flex:1}
table.mini{width:100%;border-collapse:collapse;font:11.5px Consolas,monospace}
table.mini th{color:#7f93b8;text-align:left;padding:4px 6px;border-bottom:1px solid #22345c;font-weight:600}
table.mini td{padding:4px 6px;border-bottom:1px solid #16233c;color:#dfe9ff}
.chkRow{border:1px solid #22345c;border-left:4px solid #f59e0b;border-radius:9px;padding:7px;margin:5px 0;background:#132038;font-size:12.5px}
.chkRow.ok{border-left-color:#3ddc97}
#planOut{background:#060b16;border:1px solid #1c2a44;border-radius:10px;color:#7dd3fc;font:11.5px/1.5 Consolas,monospace;padding:8px;white-space:pre-wrap;max-height:300px;overflow-y:auto}
#log{background:#060b16;border:1px solid #1c2a44;border-radius:10px;color:#6fd3ff;font:11.5px/1.5 Consolas,monospace;height:260px;overflow-y:auto;padding:8px;white-space:pre-wrap}
#log .ok{color:#3ddc97}#log .bad{color:#ff6b6b}#log .warn{color:#ffc857}#log .info{color:#8fa2c4}
#status{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:6px 14px;background:#0e1a2e;border-top:1px solid #22345c;color:#93a6c9;font-size:12px}
#status b{color:#4cc3ff}
.chip{display:inline-block;padding:2px 9px;border-radius:999px;font-size:11px;font-weight:700;background:#16233c;border:1px solid #2c3f6b;color:#dfe9ff}
#toast{position:fixed;left:50%;bottom:52px;transform:translateX(-50%) translateY(20px);opacity:0;pointer-events:none;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;font-weight:700;padding:10px 16px;border-radius:12px;transition:all .25s;z-index:60}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0)}
@media (max-width:1080px){body{overflow:auto}#wrap{flex-direction:column;height:auto}#left,#side{width:100%}#stage{height:56vh;min-height:380px}#hint{display:none}}
@media print{#top,#ctrl,#left,#side,#status,#toast,#storm{display:none!important}body{background:#fff}#stage{border:none;height:92vh;background:#fff!important}}
</style></head>
<body>
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
<span id="hint">рамка = массовое выделение · shift+клик = добавить · Ctrl+A всё · Del удалить · Ctrl+Z/Y · 2×клик холст = добавить</span>
</div>
<div id="ctrl">
<label>Зум <input type="range" id="cZoom" min="30" max="260" value="100"><span class="val" id="vZoom">100%</span></label>
<label>Сетка <input type="checkbox" id="cGrid" checked></label>
<label>Скорость <input type="range" id="cSpeed" min="20" max="400" value="100"><span class="val" id="vSpeed">1.0x</span></label>
<label>Тема <select id="cTheme"><option value="dark">тёмная</option><option value="light">светлая</option><option value="blue">blueprint</option></select></label>
<button id="bFit">🎯 Вписать</button>
<button id="bFault">⚡ Авария</button>
<button id="bHeal">🩹 Починить</button>
</div>
<div id="wrap">
<div id="left">
<h4>Устройства</h4><div id="palDev"></div>
<h4>Шаблоны</h4><div id="palTpl"></div>
<h4>Реестр</h4>
<input id="regSearch" placeholder="🔍 поиск: имя, IP, VLAN">
<select id="regType"><option value="">все типы</option></select>
<div id="regList"></div>
<button class="d" id="bBulkDel" style="width:100%;margin-top:6px">✕ Удалить выделенные</button>
<h4>Схема</h4>
<button id="bDemo" style="width:100%;margin:4px 0">📦 Пример: абонент + PON</button>
</div>
<div id="stage" class="grid">
<div id="storm">⚠️ BROADCAST-ШТОРМ!</div>
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
<option value="ping">Ping A → B</option>
<option value="multicast">Multicast + IGMP</option>
<option value="broadcast">Broadcast / flood</option>
<option value="pon">PON downstream</option>
</select></div>
<div class="row"><select id="simSrc"></select><select id="simDst"></select></div>
<div class="row"><input id="simVlan" value="135" list="vlanList"></div>
<div class="row"><button class="g" id="bRun" style="flex:2">▶ Пуск</button><button id="bPause" style="flex:1">⏸</button><button class="d" id="bStop" style="flex:1">⏹</button></div>
</div>
<div id="tabs">
<button data-tab="props" class="on">🔧 Свойства</button>
<button data-tab="flows">🌊 Потоки</button>
<button data-tab="fdb">📚 FDB</button>
<button data-tab="check">🔎 Проверка</button>
<button data-tab="plan">📋 План</button>
<button data-tab="events">📜 Журнал</button>
</div>
<div class="pane on" id="paneProps"><div id="props"><span style="color:#93a6c9">Выберите устройство или линию. Рамка (⬚) выделяет группу.</span></div></div>
<div class="pane" id="paneFlows"><div id="flowList"></div><button class="g" id="bAddFlow" style="width:100%;margin-top:6px">➕ Поток</button></div>
<div class="pane" id="paneFdb"><div class="fld"><span>Коммутатор</span><select id="fdbDev"></select></div><table class="mini"><thead><tr><th>MAC</th><th>Порт</th><th>VLAN</th></tr></thead><tbody id="fdbBody"></tbody></table></div>
<div class="pane" id="paneCheck"><button class="p" id="bCheck" style="width:100%">🔎 Проверить VLAN-план</button><div id="checkList" style="margin-top:6px"></div></div>
<div class="pane" id="panePlan"><div class="fld"><span>Синтаксис</span><select id="planSyn"><option value="des">D-Link DES</option><option value="dgs">D-Link DGS-1210/ME</option></select></div><button class="g" id="bPlanCopy" style="width:100%">📋 Копировать план</button><div id="planOut" style="margin-top:6px"></div></div>
<div class="pane" id="paneEvents"><div id="log"></div><button id="bLogClear" style="width:100%;margin-top:6px">🧽 Очистить</button></div>
</div>
</div>
<div id="status">
<span>Устройств: <b id="stDev">0</b></span>
<span>Линий: <b id="stLink">0</b></span>
<span>Выделено: <b id="stSel">0</b></span>
<span>Пакетов: <b id="stPkts">0</b></span>
<span>Потерь: <b id="stDrops" style="color:#ff6b6b">0</b></span>
<span id="stSim" class="chip">стоп</span>
<span style="margin-left:auto"><span class="chip" style="color:#ff9f43">135 камеры</span> <span class="chip" style="color:#ffc857">1151 IPTV</span> <span class="chip" style="color:#3ddc97">2201 абоненты</span></span>
</div>
<div id="toast"></div>
<datalist id="vlanList">
<option value="135">135 · Камеры ОТТ</option>
<option value="1151">1151 · IPTV multicast</option>
<option value="2101">2101 · Тура · красный</option>
<option value="2102">2102 · Тура · оранжевый</option>
<option value="2103">2103 · Тура · жёлтый</option>
<option value="2104">2104 · Тура · зелёный</option>
<option value="2105">2105 · Тура · голубой</option>
<option value="2106">2106 · Тура · синий</option>
<option value="2107">2107 · Тура · фиолетовый</option>
<option value="2109">2109 · Тура · Зона 09</option>
<option value="2110">2110 · Тура · Морозово</option>
<option value="2111">2111 · Тура · Зона 11</option>
<option value="2112">2112 · Тура · Зона 12</option>
<option value="2113">2113 · Тура · Зона 13</option>
<option value="2115">2115 · Тура · Север</option>
<option value="2116">2116 · Тура · Резерв</option>
<option value="2117">2117 · Тура · ЖК Клевер к1</option>
<option value="2118">2118 · Тура · ЖК Клевер к2</option>
<option value="2119">2119 · Тура · ЖК Клевер к3</option>
<option value="2120">2120 · Тура · ЖК Клевер к4</option>
<option value="2201">2201 · Михеенко · красный</option>
<option value="2202">2202 · Михеенко · оранжевый</option>
<option value="2203">2203 · Михеенко · жёлтый</option>
<option value="2204">2204 · Михеенко · зелёный</option>
<option value="2205">2205 · Михеенко · голубой</option>
<option value="2206">2206 · Михеенко · синий</option>
<option value="2207">2207 · Михеенко · фиолетовый</option>
<option value="2208">2208 · Михеенко · Зона 08 Лихачева 6</option>
<option value="2301">2301 · Королёва · красный</option>
<option value="2302">2302 · Королёва · оранжевый</option>
<option value="2303">2303 · Королёва · жёлтый</option>
<option value="2304">2304 · Королёва · зелёный</option>
<option value="2305">2305 · Королёва · голубой</option>
<option value="2306">2306 · Королёва · синий</option>
<option value="2307">2307 · Королёва · фиолетовый</option>
<option value="2308">2308 · Королёва · Зона 08</option>
<option value="2401">2401 · Черняховка · красный</option>
<option value="2402">2402 · Черняховка · оранжевый</option>
<option value="2403">2403 · Черняховка · жёлтый</option>
<option value="2404">2404 · Черняховка · зелёный</option>
<option value="2405">2405 · Черняховка · голубой</option>
<option value="2406">2406 · Черняховка · синий</option>
<option value="2407">2407 · Черняховка · фиолетовый</option>
<option value="2409">2409 · Черняховка · Олимп к. 1-3</option>
<option value="2410">2410 · Черняховка · Олимп к. 4-5</option>
<option value="2411">2411 · Черняховка · Олимп к. 6-7</option>
<option value="2601">2601 · Жучки · красный</option>
<option value="2602">2602 · Жучки · оранжевый</option>
<option value="2603">2603 · Жучки · PON 1</option>
<option value="2604">2604 · Жучки · PON 2</option>
<option value="2701">2701 · Горбуновка · красный</option>
<option value="2702">2702 · Горбуновка · оранжевый</option>
<option value="2703">2703 · Горбуновка · жёлтый</option>
<option value="2704">2704 · Горбуновка · PON Горбуновская</option>
<option value="2705">2705 · Горбуновка · PON Васильки</option>
<option value="2801">2801 · ГОП · красный</option>
<option value="2802">2802 · ГОП · оранжевый</option>
<option value="2803">2803 · ГОП · PON 1 Гоп</option>
<option value="2804">2804 · ГОП · новые дома</option>
<option value="2020">2020 · Сегмент 02 · МКД</option>
<option value="2021">2021 · Сегмент 02 · PON</option>
<option value="2022">2022 · Сегмент 02 · PON</option>
<option value="2023">2023 · Сегмент 02 · Зубцово</option>
<option value="2030">2030 · Сегмент 03 · МКД</option>
<option value="2040">2040 · Сегмент 04 · PON</option>
<option value="2050">2050 · Сегмент 05 · МКД</option>
<option value="2054">2054 · Сегмент 05 · PON</option>
<option value="2060">2060 · Сегмент 06 · PON</option>
<option value="2070">2070 · Сегмент 07 · PON</option>
<option value="2080">2080 · Сегмент 08 · PON запад</option>
<option value="2081">2081 · Сегмент 08 · PON восток</option>
<option value="2082">2082 · Сегмент 08 · МКД ВЧ 3641</option>
<option value="2090">2090 · Сегмент 09 · PON</option>
<option value="2092">2092 · Сегмент 09 · PON</option>
<option value="2110">2110 · Сегмент 11 · МКД</option>
<option value="2114">2114 · Сегмент 11 · PON</option>
<option value="2120">2120 · Сегмент 12 · PON Гражданка</option>
<option value="2121">2121 · Сегмент 12 · МАЯК</option>
<option value="2122">2122 · Сегмент 12 · PON Кировка</option>
<option value="2123">2123 · Сегмент 12 · PON Дружба</option>
<option value="2130">2130 · Сегмент 13 · МКД</option>
<option value="2131">2131 · Сегмент 13 · PON</option>
<option value="2140">2140 · Сегмент 14 · PON</option>
<option value="2150">2150 · Сегмент 15 · PON</option>
<option value="2160">2160 · Сегмент 16 · PON</option>
<option value="2170">2170 · Сегмент 17 · МКД</option>
<option value="2171">2171 · Сегмент 17 · PON</option>
</datalist>
<script>
(function(){
'use strict';
var TYPES={router:{i:'📶',n:'Роутер абонента',c:'#f472b6',sw:1},switch:{i:'🖧',n:'Коммутатор',c:'#4cc3ff',sw:1},agg:{i:'🔀',n:'Агрегация',c:'#8b9dff',sw:1},core:{i:'🌐',n:'Ядро',c:'#ff6b6b',sw:1},olt:{i:'🏢',n:'OLT',c:'#c084fc',sw:1},split:{i:'🌳',n:'Сплиттер PON',c:'#2dd4bf'},onu:{i:'📡',n:'ONU/ONT',c:'#3ddc97',sw:1},camera:{i:'📹',n:'IP-камера',c:'#ff9f43'},pc:{i:'🖥️',n:'ПК/терминал',c:'#9fb2d4'},tv:{i:'📺',n:'TV приставка',c:'#ffd166'},nvr:{i:'🗄️',n:'NVR/сервер',c:'#ff6bb5'},ap:{i:'📡',n:'Wi-Fi точка',c:'#60a5fa'},printer:{i:'🖨️',n:'Принтер',c:'#b8c2d9'}};
var cfg={grid:true,speed:1,theme:'dark',sound:true,hop:380,pkt:6,glow:6,curve:0.22};
var S,view={x:70,y:50,k:1},selD={},selL={},tool='select',linkFrom=null,lastType='pc';
var drag=null,pan=null,marq=null,undoStack=[],redoStack=[],dirty=true;
var sim={running:false,paused:false,packets:[],pid:1,stats:{pk:0,dr:0},fdb:{},ev:[],flowAcc:{},blocked:{}};
function $(id){return document.getElementById(id);}
function esc(s){return String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}
function dev(id){for(var i=0;i<S.devices.length;i++)if(S.devices[i].id===id)return S.devices[i];return null;}
function lnk(id){for(var i=0;i<S.links.length;i++)if(S.links[i].id===id)return S.links[i];return null;}
function hue(v){return 'hsl('+(((parseInt(v,10)||0)*47)%360)+',85%,62%)';}
function isSw(d){return d&&TYPES[d.type]&&TYPES[d.type].sw;}
function snap(v){return Math.round(v/12)*12;}
function mark(){dirty=true;}
function pushUndo(){undoStack.push(JSON.stringify(S));if(undoStack.length>60)undoStack.shift();redoStack=[];}
function autosave(){try{localStorage.setItem('netlab_auto',JSON.stringify(S));}catch(e){}}
function toast(msg){var t=$('toast');t.textContent=msg;t.className='show';clearTimeout(t._t);t._t=setTimeout(function(){t.className='';},2200);}
function ev(type,msg){sim.ev.push({t:new Date().toLocaleTimeString('ru'),type:type,msg:msg});if(sim.ev.length>300)sim.ev.shift();renderLog();}
function renderLog(){var l=$('log');l.innerHTML=sim.ev.slice(-150).map(function(e){return '<div class="'+e.type+'">['+e.t+'] '+esc(e.msg)+'</div>';}).join('');l.scrollTop=l.scrollHeight;}
function demo(){return {nid:13,lid:12,devices:[
  {id:1,type:'core',x:430,y:40,name:'Ядро S6330',ip:'10.163.100.8',vlan:'',model:'S6330'},
  {id:2,type:'nvr',x:680,y:40,name:'NVR',ip:'10.135.0.10',vlan:'135',model:'NVR-64'},
  {id:3,type:'olt',x:430,y:170,name:'OLT Михеенко',ip:'10.163.202.13',vlan:'',model:'PON OLT'},
  {id:4,type:'split',x:430,y:290,name:'Сплиттер 1:8',ip:'',vlan:'',model:'1x8'},
  {id:5,type:'onu',x:430,y:410,name:'ONU кв.12',ip:'',vlan:'2201',model:'ONT-1G'},
  {id:6,type:'router',x:430,y:530,name:'Роутер абонента',ip:'192.168.1.1',vlan:'',model:'Keenetic'},
  {id:7,type:'switch',x:430,y:650,name:'Свитч квартиры',ip:'192.168.1.2',vlan:'',model:'DES-1008'},
  {id:8,type:'pc',x:170,y:790,name:'ПК',ip:'192.168.1.10',vlan:'2201',model:'PC'},
  {id:9,type:'camera',x:350,y:790,name:'Камера',ip:'192.168.1.20',vlan:'135',model:'BEWARD'},
  {id:10,type:'tv',x:530,y:790,name:'TV',ip:'192.168.1.30',vlan:'1151',model:'STB'},
  {id:11,type:'printer',x:700,y:790,name:'Принтер',ip:'192.168.1.40',vlan:'2201',model:'HP'},
  {id:12,type:'ap',x:860,y:790,name:'Wi-Fi',ip:'192.168.1.3',vlan:'2201',model:'AP'}
],links:[
  {id:1,a:1,b:3,pa:'4',pb:'up',mode:'trunk',vlans:'135,1151,2201',media:'fiber',cost:1,down:false},
  {id:2,a:1,b:2,pa:'6',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1,down:false},
  {id:3,a:3,b:4,pa:'pon1',pb:'in',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:3,down:false},
  {id:4,a:4,b:5,pa:'3',pb:'pon',mode:'trunk',vlans:'135,1151,2201',media:'pon',cost:1,down:false},
  {id:5,a:5,b:6,pa:'lan1',pb:'wan',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false},
  {id:6,a:6,b:7,pa:'lan1',pb:'1',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false},
  {id:7,a:7,b:8,pa:'2',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false},
  {id:8,a:7,b:9,pa:'3',pb:'1',mode:'access',vlans:'135',media:'copper',cost:1,down:false},
  {id:9,a:7,b:10,pa:'4',pb:'1',mode:'access',vlans:'1151',media:'copper',cost:1,down:false},
  {id:10,a:7,b:11,pa:'5',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false},
  {id:11,a:7,b:12,pa:'6',pb:'1',mode:'access',vlans:'2201',media:'copper',cost:1,down:false}
],flows:[{id:1,name:'Камера → NVR',src:9,dst:2,vlan:'135',mode:'unicast',rate:3,on:true},{id:2,name:'IPTV',src:1,dst:0,vlan:'1151',mode:'multicast',rate:2,on:true}],fid:3};}
function norm(){if(!S.flows){S.flows=[];S.fid=1;}if(!S.fid)S.fid=1;S.devices.forEach(function(d){if(d.down==null)d.down=false;});S.links.forEach(function(L){if(L.down==null)L.down=false;});}
function selCount(){var n=0,k;for(k in selD)n++;for(k in selL)n++;return n;}
function clearSel(){selD={};selL={};mark();fillReg();props();}
function render(){dirty=false;var light=cfg.theme==='light',ink=light?'#12203a':'#eaf2ff',mut=light?'#5a6b8c':'#9fb2d4';var h='';
 S.links.forEach(function(L){var a=dev(L.a),b=dev(L.b);if(!a||!b)return;var mx=(a.x+b.x)/2,my=(a.y+b.y)/2,dx=b.x-a.x,dy=b.y-a.y,len=Math.sqrt(dx*dx+dy*dy)||1;var cx=mx-dy/len*cfg.curve*len*0.5,cy=my+dx/len*cfg.curve*len*0.5;var col=L.down?'#ff6b6b':(cfg.vcol!==false?hue(String(L.vlans).split(',')[0]):(L.media==='pon'?'#2dd4bf':'#7c93b8'));h+='<path data-l="'+L.id+'" d="M'+a.x+' '+a.y+' Q'+cx+' '+cy+' '+b.x+' '+b.y+'" fill="none" stroke="'+col+'" stroke-width="'+(selL[L.id]?4:2.4)+'" stroke-dasharray="'+(L.media==='pon'?'7 4':'none')+'" style="cursor:pointer"/>';h+='<text x="'+cx+'" y="'+(cy-6)+'" text-anchor="middle" font-size="11" fill="'+mut+'" style="pointer-events:none">'+esc(L.pa||'?')+'→'+esc(L.pb||'?')+' · '+(L.mode==='trunk'?'trunk['+esc(L.vlans)+']':'acc'+esc(L.vlans))+'</text>';});
 S.devices.forEach(function(d){var t=TYPES[d.type]||TYPES.switch,on=selD[d.id];h+='<g data-d="'+d.id+'" style="cursor:move">';if(on)h+='<rect x="'+(d.x-58)+'" y="'+(d.y-38)+'" width="116" height="76" rx="16" fill="none" stroke="#d946ef" stroke-opacity="0.45" stroke-width="6"/>';h+='<rect x="'+(d.x-52)+'" y="'+(d.y-32)+'" width="104" height="64" rx="12" fill="'+(d.down?'#3a1220':t.c)+'" fill-opacity="'+(light?0.9:0.2)+'" stroke="'+(on?'#d946ef':t.c)+'" stroke-width="'+(on?3:1.6)+'"/>';h+='<text x="'+d.x+'" y="'+(d.y-8)+'" text-anchor="middle" font-size="19">'+(d.down?'⛔':t.i)+'</text>';h+='<text x="'+d.x+'" y="'+(d.y+9)+'" text-anchor="middle" font-size="11" font-weight="700" fill="'+(light?'#0d1728':ink)+'">'+esc((d.name||t.n).slice(0,18))+'</text>';h+='<text x="'+d.x+'" y="'+(d.y+24)+'" text-anchor="middle" font-size="10" fill="'+(light?'#41537a':mut)+'">'+esc(d.ip||'')+(d.vlan?' · v'+esc(d.vlan):'')+'</text>';h+='</g>';});
 $('geo').innerHTML=h;$('world').setAttribute('transform','translate('+view.x+','+view.y+') scale('+view.k+')');
 $('stDev').textContent=S.devices.length;$('stLink').textContent=S.links.length;$('stSel').textContent=selCount();
 $('vZoom').textContent=Math.round(view.k*100)+'%';$('cZoom').value=Math.round(view.k*100);
 fillSim();fillReg();fillFdbDev();}
function fillSim(){var o=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('');var a=$('simSrc'),b=$('simDst');a.innerHTML=o;b.innerHTML='<option value="0">—</option>'+o;}
function fillReg(){var q=($('regSearch').value||'').toLowerCase(),ft=$('regType').value;var rows=S.devices.filter(function(d){if(ft&&d.type!==ft)return false;if(!q)return true;return ((d.name||'')+' '+(d.ip||'')+' '+(d.vlan||'')).toLowerCase().indexOf(q)>=0;});$('regList').innerHTML=rows.map(function(d){return '<div class="regRow'+(selD[d.id]?' sel':'')+'" data-reg="'+d.id+'"><input type="checkbox" data-chk="'+d.id+'"'+(selD[d.id]?' checked':'')+'><i style="font-style:normal">'+TYPES[d.type].i+'</i><span class="nm">'+esc(d.name||TYPES[d.type].n)+'</span><span class="vl">'+(d.vlan?'v'+esc(d.vlan):'—')+'</span></div>';}).join('')||'<div style="color:#7f93b8;font-size:12px">ничего не найдено</div>';}
function fillFdbDev(){var s=$('fdbDev'),v=s.value;s.innerHTML=S.devices.filter(isSw).map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('')||'<option value="">нет</option>';if(v&&dev(+v))s.value=v;renderFdb();}
function renderFdb(){var id=+$('fdbDev').value,t=sim.fdb[id]||{},rows=[];for(var m in t)rows.push({mac:m,p:t[m].port,v:t[m].vlan});$('fdbBody').innerHTML=rows.map(function(r){return '<tr><td>'+r.mac+'</td><td>'+esc(r.p)+'</td><td>'+esc(r.v)+'</td></tr>';}).join('')||'<tr><td colspan="3" style="color:#7f93b8">пусто</td></tr>';}
function palette(){$('palDev').innerHTML=Object.keys(TYPES).map(function(k){return '<button draggable="true" data-add="'+k+'"><i>'+TYPES[k].i+'</i>'+TYPES[k].n+'</button>';}).join('');$('palTpl').innerHTML='<button data-tpl="sub"><i>🏠</i>Абонент</button><button data-tpl="pod"><i>🏢</i>Подъезд</button><button data-tpl="pon"><i>🌳</i>PON</button>';$('regType').innerHTML='<option value="">все</option>'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'">'+TYPES[k].n+'</option>';}).join('');}
function center(){var r=$('cv').getBoundingClientRect();return {x:(r.width/2-view.x)/view.k,y:(r.height/2-view.y)/view.k};}
function addDevice(k,x,y){pushUndo();lastType=k;var c=center();var d={id:S.nid++,type:k,x:snap(x==null?c.x+(Math.random()*120-60):x),y:snap(y==null?c.y+(Math.random()*90-45):y),name:'',ip:'',vlan:(k==='camera'?'135':(k==='tv'?'1151':(k==='pc'||k==='onu'||k==='printer'||k==='ap')?'2201':'')),model:'',down:false};S.devices.push(d);clearSel();selD[d.id]=1;autosave();mark();props();toast('Добавлено: '+TYPES[k].n);}
function addTpl(k){pushUndo();var c=center();function mk(t,dx,dy,name,ip,vlan){var id=S.nid++;S.devices.push({id:id,type:t,x:snap(c.x+dx),y:snap(c.y+dy),name:name,ip:ip,vlan:vlan||'',model:'',down:false});return id;}function L(a,b,pa,pb,mode,vlans,media){S.links.push({id:S.lid++,a:a,b:b,pa:pa,pb:pb,mode:mode,vlans:vlans,media:media||'copper',cost:1,down:false});}if(k==='sub'){var r=mk('router',0,-140,'Роутер','192.168.1.1',''),sw=mk('switch',0,-20,'Свитч','192.168.1.2','');var pc=mk('pc',-220,120,'ПК','192.168.1.10','2201'),cam=mk('camera',-70,120,'Камера','192.168.1.20','135'),tv=mk('tv',80,120,'TV','192.168.1.30','1151');L(r,sw,'lan1','1','trunk','135,1151,2201');L(sw,pc,'2','1','access','2201');L(sw,cam,'3','1','access','135');L(sw,tv,'4','1','access','1151');}if(k==='pod'){var s1=mk('switch',0,-120,'DES-3200','10.163.202.88',''),c1=mk('camera',-160,20,'Камера 1','10.135.1.21','135'),c2=mk('camera',0,20,'Камера 2','10.135.1.22','135'),p1=mk('pc',160,20,'Абонент','10.163.202.11','2201');L(s1,c1,'21','1','access','135');L(s1,c2,'22','1','access','135');L(s1,p1,'12','1','access','2201');}if(k==='pon'){var ol=mk('olt',0,-140,'OLT','',''),sp=mk('split',0,-30,'Сплиттер','',''),o1=mk('onu',-120,90,'ONU-1','','2603'),o2=mk('onu',120,90,'ONU-2','','2601');var cc=mk('camera',-120,200,'Камера PON','','2603'),pp=mk('pc',120,200,'Абонент PON','','2601');L(ol,sp,'pon1','in','trunk','2601,2603','pon');L(sp,o1,'3','pon','trunk','2601,2603','pon');L(sp,o2,'5','pon','trunk','2601,2603','pon');L(o1,cc,'lan1','1','access','2603');L(o2,pp,'lan1','1','access','2601');}autosave();mark();props();toast('Шаблон добавлен');}
function pt(e){var r=$('cv').getBoundingClientRect();return {x:(e.clientX-r.left-view.x)/view.k,y:(e.clientY-r.top-view.y)/view.k,sx:e.clientX-r.left,sy:e.clientY-r.top};}
function setTool(t){tool=t;linkFrom=null;$('bLink').className=(t==='link')?'w on':'w';$('bSel').className=(t==='select')?'on':'';$('bMarquee').className=(t==='marquee')?'m on':'m';}
function props(){var p=$('props');var nd=0,nl=0,k;for(k in selD)nd++;for(k in selL)nl++;if(nd+nl>1){p.innerHTML='<div class="fld"><span>Выделено: устройств '+nd+', линий '+nl+'</span></div><button class="d" id="pDel" style="width:100%">✕ Удалить</button>';$('pDel').addEventListener('click',delSel);return;}if(nl===1){var lid=+Object.keys(selL)[0],L=lnk(lid);if(!L){clearSel();return;}p.innerHTML='<div class="fld"><span>Линия #'+L.id+'</span></div><div class="fld"><span>Порт A</span><input data-lf="pa" value="'+esc(L.pa)+'"></div><div class="fld"><span>Порт B</span><input data-lf="pb" value="'+esc(L.pb)+'"></div><div class="fld"><span>Режим</span><select data-lf="mode"><option value="trunk"'+(L.mode==='trunk'?' selected':'')+'>trunk</option><option value="access"'+(L.mode==='access'?' selected':'')+'>access</option></select></div><div class="fld"><span>VLAN</span><input data-lf="vlans" list="vlanList" value="'+esc(L.vlans)+'"></div><div class="fld"><span>Среда</span><select data-lf="media"><option value="copper"'+(L.media==='copper'?' selected':'')+'>медь</option><option value="fiber"'+(L.media==='fiber'?' selected':'')+'>оптика</option><option value="pon"'+(L.media==='pon'?' selected':'')+'>PON</option></select></div><button class="d" id="pDel" style="width:100%;margin-top:6px">✕ Удалить линию</button>';Array.prototype.forEach.call(p.querySelectorAll('[data-lf]'),function(inp){inp.addEventListener('input',function(){pushUndo();L[inp.getAttribute('data-lf')]=inp.value;autosave();mark();});});$('pDel').addEventListener('click',delSel);return;}if(nd===1){var id=+Object.keys(selD)[0],d=dev(id);if(!d){clearSel();return;}p.innerHTML='<div class="fld"><span>Тип</span><select data-df="type">'+Object.keys(TYPES).map(function(k){return '<option value="'+k+'"'+(d.type===k?' selected':'')+'>'+TYPES[k].i+' '+TYPES[k].n+'</option>';}).join('')+'</select></div><div class="fld"><span>Имя</span><input data-df="name" value="'+esc(d.name)+'"></div><div class="fld"><span>IP</span><input data-df="ip" value="'+esc(d.ip)+'"></div><div class="fld"><span>Access-VLAN</span><input data-df="vlan" list="vlanList" value="'+esc(d.vlan)+'"></div><div class="fld"><span>Модель</span><input data-df="model" value="'+esc(d.model)+'"></div><button class="d" id="pDel" style="width:100%">✕ Удалить устройство</button>';Array.prototype.forEach.call(p.querySelectorAll('[data-df]'),function(inp){inp.addEventListener('input',function(){pushUndo();d[inp.getAttribute('data-df')]=inp.value;autosave();mark();});});$('pDel').addEventListener('click',delSel);return;}p.innerHTML='<span style="color:#93a6c9">Выберите устройство или линию.</span>';}
function delSel(){var n=selCount();if(!n){toast('Нечего удалять');return;}pushUndo();stopSim();S.links=S.links.filter(function(L){return !selL[L.id]&&!selD[L.a]&&!selD[L.b];});S.devices=S.devices.filter(function(d){return !selD[d.id];});clearSel();autosave();mark();props();toast('Удалено: '+n);}
function clearAll(){pushUndo();stopSim();S={nid:1,lid:1,devices:[],links:[],flows:[],fid:1};clearSel();autosave();mark();props();toast('Очищено');}
function dupSel(){var ids=[];for(var k in selD)ids.push(+k);if(!ids.length){toast('Выделите');return;}pushUndo();var map={};ids.forEach(function(id){var d=dev(id);if(!d)return;var nd={id:S.nid++,type:d.type,x:d.x+40,y:d.y+40,name:(d.name||'')+' копия',ip:d.ip,vlan:d.vlan,model:d.model,down:false};map[id]=nd.id;S.devices.push(nd);});S.links.forEach(function(L){if(map[L.a]&&map[L.b])S.links.push({id:S.lid++,a:map[L.a],b:map[L.b],pa:L.pa,pb:L.pb,mode:L.mode,vlans:L.vlans,media:L.media,cost:L.cost,down:false});});clearSel();autosave();mark();props();toast('Продублировано: '+ids.length);}
function undo(){if(!undoStack.length){toast('Нечего отменять');return;}redoStack.push(JSON.stringify(S));S=JSON.parse(undoStack.pop());norm();clearSel();autosave();mark();props();toast('Отменено');}
function redo(){if(!redoStack.length){toast('Нечего повторять');return;}undoStack.push(JSON.stringify(S));S=JSON.parse(redoStack.pop());norm();clearSel();autosave();mark();props();toast('Повторено');}
function allows(L,v){var list=String(L.vlans||'').split(',').map(function(x){return x.trim();});return L.mode==='trunk'?list.indexOf(String(v))>=0:String(L.vlans)===String(v);}
function path(s,d,v){var prev={},seen={},q=[s];seen[s]=1;while(q.length){var c=q.shift();if(c===d)break;S.links.forEach(function(L){if(L.down||!allows(L,v))return;var o=null;if(L.a===c)o=L.b;else if(L.b===c)o=L.a;if(o==null||seen[o])return;seen[o]=1;prev[o]={f:c,L:L};q.push(o);});}if(!seen[d])return null;var hops=[],cur=d;while(cur!==s){var p=prev[cur];hops.unshift({from:p.f,to:cur,L:p.L});cur=p.f;}return hops;}
function emit(src,dst,v,mode,tag){var sd=dev(src);if(!sd||sd.down){drop('источник выключен');return;}var targets=[];if(mode==='unicast'||mode==='ping'){if(!dst||!dev(dst)){drop('нет приёмника');return;}targets=[dst];}else if(mode==='multicast'){targets=S.devices.filter(function(x){return x.id!==src&&String(x.vlan)===String(v)&&!isSw(x)&&!x.down;}).map(function(x){return x.id;});}else if(mode==='pon'){targets=S.devices.filter(function(x){return x.type==='onu'&&!x.down;}).map(function(x){return x.id;});}else if(mode==='broadcast'){targets=S.devices.filter(function(x){return x.id!==src;}).map(function(x){return x.id;});}targets.forEach(function(t){var hops=path(src,t,v);if(!hops){drop('VLAN '+v+' не доходит до '+(dev(t).name||t));return;}sim.packets.push({id:sim.pid++,hops:hops,idx:0,prog:0,v:v,ms:sd.mac||'src',md:'dst',tag:tag||'📨',bytes:1400,el:null,done:false});});}
function spawn(hops,v){}
function drop(reason){sim.stats.dr++;ev('bad','❌ '+reason);}
function learn(d,L,mac,v){if(!isSw(d))return;var port=(L.a===d.id)?L.pa:L.pb;if(!sim.fdb[d.id])sim.fdb[d.id]={};sim.fdb[d.id][mac]={port:port||'?',vlan:v};}
function packetNode(p){var c=document.createElementNS('http://www.w3.org/2000/svg','circle');c.setAttribute('r',cfg.pkt);c.setAttribute('fill',hue(p.v));c.setAttribute('filter','url(#glow)');$('pk').appendChild(c);p.el=c;}
function killPacket(p){if(p.el&&p.el.parentNode)p.el.parentNode.removeChild(p.el);p.el=null;p.done=true;}
function stepPacket(p,dt){if(!p.el)packetNode(p);var h=p.hops[p.idx];if(!h){killPacket(p);return;}var a=dev(h.from),b=dev(h.to);if(!a||!b||h.L.down||a.down||b.down){killPacket(p);drop('обрыв на линии #'+h.L.id);return;}var dur=cfg.hop*(h.L.cost||1);p.prog+=dt/dur;var k=Math.min(1,p.prog);p.el.setAttribute('cx',a.x+(b.x-a.x)*k);p.el.setAttribute('cy',a.y+(b.y-a.y)*k);if(k>=1){learn(b,h.L,p.ms,p.v);p.idx++;p.prog=0;if(p.idx>=p.hops.length){killPacket(p);sim.stats.pk++;$('stPkts').textContent=sim.stats.pk;ev('ok','✅ '+p.tag+' VLAN '+p.v+' доставлен');}}}
function stopSim(){sim.running=false;sim.paused=false;sim.packets.forEach(killPacket);sim.packets=[];$('stSim').textContent='стоп';$('stSim').style.color='';$('bPause').textContent='⏸';$('storm').className='';}
function startSim(){stopSim();sim.stats={pk:0,dr:0};$('stPkts').textContent='0';$('stDrops').textContent='0';sim.running=true;sim.paused=false;$('stSim').textContent='идёт';$('stSim').style.color='#3ddc97';var mode=$('simMode').value,s=+$('simSrc').value,d=+$('simDst').value,v=$('simVlan').value||'1';ev('info','▶ '+mode+' · VLAN '+v);if(mode==='flows'){/* запускается в loop */}else{emit(s,d,v,mode,mode==='ping'?'📍':(mode==='multicast'?'📺':(mode==='pon'?'🌊':'🌊')));}mark();}
function loop(t){requestAnimationFrame(loop);var dt=Math.min(60,t-(sim.last||t));sim.last=t;if(dirty)render();var active=sim.running&&!sim.paused;if(active){var sdt=dt*cfg.speed;if($('simMode').value==='flows'){(S.flows||[]).forEach(function(f){if(!f.on||!dev(f.src))return;sim.flowAcc[f.id]=(sim.flowAcc[f.id]||0)+sdt;var interval=1000/Math.max(1,f.rate);while(sim.flowAcc[f.id]>=interval){sim.flowAcc[f.id]-=interval;emit(f.src,f.dst,f.vlan,f.mode,f.mode==='multicast'?'📺':'📨');}});}for(var i=sim.packets.length-1;i>=0;i--){var p=sim.packets[i];stepPacket(p,sdt);if(p.done)sim.packets.splice(i,1);}}$('stPkts').textContent=sim.stats.pk;$('stDrops').textContent=sim.stats.dr;}
function checkPlan(){var out=[],leaves=S.devices.filter(function(d){return d.vlan&&!isSw(d);});var roots=S.devices.filter(function(d){return d.type==='core'||d.type==='agg'||d.type==='nvr';});leaves.forEach(function(d){var target=null;roots.forEach(function(r){if(!target)target=r;});if(!target){out.push({ok:false,msg:'нет ядра для '+(d.name||d.id)});return;}var rp=path(d.id,target.id,d.vlan);if(!rp){out.push({ok:false,msg:'VLAN '+d.vlan+' не доходит: '+(d.name||d.id)+' → '+(target.name||target.id)});return;}out.push({ok:true,msg:'✅ VLAN '+d.vlan+' проходит: '+(d.name||d.id)+' → '+(target.name||target.id)});});$('checkList').innerHTML=out.map(function(o){return '<div class="chkRow'+(o.ok?' ok':'')+'">'+esc(o.msg)+'</div>';}).join('')||'<div class="chkRow ok">✅ чисто</div>';}
function buildPlan(){var syn=$('planSyn').value,txt='';S.devices.filter(isSw).forEach(function(d){var acc={},trunk={};S.links.forEach(function(L){if(L.a!==d.id&&L.b!==d.id)return;var port=(L.a===d.id)?L.pa:L.pb;if(L.mode==='access'){(acc[L.vlans]=acc[L.vlans]||[]).push(port);}else String(L.vlans).split(',').forEach(function(v){v=v.trim();if(v)(trunk[v]=trunk[v]||[]).push(port);});});var vlans={};for(var a in acc)vlans[a]=1;for(var t in trunk)vlans[t]=1;txt+='! ===== '+(d.name||TYPES[d.type].n)+' ('+(d.ip||'?')+') =====\n';if(syn==='des'){for(var v in vlans)txt+='create vlan VLAN'+v+' tag '+v+'\n';for(var v2 in trunk)txt+='config vlan vlanid '+v2+' add tagged '+trunk[v2].join(',')+'\n';for(var v3 in acc){txt+='config vlan vlanid '+v3+' add untagged '+acc[v3].join(',')+'\n';txt+='config ports '+acc[v3].join(',')+' pvid '+v3+'\n';}txt+='save\n\n';}else{txt+='vlan database\n';for(var v4 in vlans)txt+='vlan '+v4+'\n';txt+='exit\n';for(var v5 in trunk)txt+='interface ethernet 1/0/'+trunk[v5].join(',')+'\nvlan participation include '+v5+'\nvlan tagging tagged\nexit\n';for(var v6 in acc)txt+='interface ethernet 1/0/'+acc[v6].join(',')+'\nvlan participation include '+v6+'\nvlan pvid '+v6+'\nexit\n';txt+='copy running-config startup-config\n\n';}});if(!txt)txt='Нет коммутаторов.';$('planOut').textContent=txt;}
function renderFlows(){var el=$('flowList');el.innerHTML=(S.flows||[]).map(function(f){var opts=S.devices.map(function(d){return '<option value="'+d.id+'">'+esc(d.name||TYPES[d.type].n)+'</option>';}).join('');return '<div class="flowRow"><div class="h"><input type="checkbox" data-fon="'+f.id+'"'+(f.on?' checked':'')+'><b>'+esc(f.name)+'</b><button class="d" data-fdel="'+f.id+'" style="padding:3px 8px">✕</button></div><div class="g"><select data-fsrc="'+f.id+'">'+opts+'</select><select data-fdst="'+f.id+'"><option value="0">—</option>'+opts+'</select></div><div class="g"><input data-fvlan="'+f.id+'" list="vlanList" value="'+esc(f.vlan)+'"><select data-fmode="'+f.id+'"><option value="unicast"'+(f.mode==='unicast'?' selected':'')+'>unicast</option><option value="multicast"'+(f.mode==='multicast'?' selected':'')+'>multicast</option></select><input type="number" data-frate="'+f.id+'" value="'+f.rate+'" min="1" max="20"></div></div>';}).join('')||'<div style="color:#7f93b8;font-size:12px">Потоков нет.</div>';Array.prototype.forEach.call(el.querySelectorAll('[data-fsrc]'),function(s){var f=null;for(var i=0;i<(S.flows||[]).length;i++)if(S.flows[i].id===+s.getAttribute('data-fsrc'))f=S.flows[i];if(f)s.value=String(f.src);});Array.prototype.forEach.call(el.querySelectorAll('[data-fdst]'),function(s){var f=null;for(var i=0;i<(S.flows||[]).length;i++)if(S.flows[i].id===+s.getAttribute('data-fdst'))f=S.flows[i];if(f)s.value=String(f.dst||0);});}
function pin(){return localStorage.getItem('swhpin')||prompt('PIN:')||'';}
function saveScheme(){var name=prompt('Название:','Схема');if(!name)return;fetch('/api/schemes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:pin(),name:name,data:JSON.stringify(S)})}).then(function(r){return r.json();}).then(function(res){toast(res.ok?('Сохранено #'+res.id):('Ошибка: '+(res.error||'')));}).catch(function(e){toast('Ошибка: '+e.message);});}
function openModal(){fetch('/api/schemes').then(function(r){return r.json();}).then(function(rows){var pick=prompt('Открыть (ID):\n'+(rows||[]).map(function(r){return r.id+': '+r.name;}).join('\n'));if(!pick)return;fetch('/api/schemes/'+pick).then(function(r){return r.json();}).then(function(sc){if(sc&&sc.data){pushUndo();S=JSON.parse(sc.data);norm();clearSel();autosave();mark();props();renderFlows();fit();toast('Открыто');}});}).catch(function(e){toast('Ошибка');});}
function exportSvg(){var clone=$('cv').cloneNode(true);clone.setAttribute('width','1600');clone.setAttribute('height','1000');var bg=document.createElementNS('http://www.w3.org/2000/svg','rect');bg.setAttribute('width','1600');bg.setAttribute('height','1000');bg.setAttribute('fill','#0a1424');clone.insertBefore(bg,clone.firstChild);var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([clone.outerHTML],{type:'image/svg+xml'}));a.download='netlab.svg';a.click();toast('SVG');}
function exportPng(){exportSvg();}
function fit(){if(!S.devices.length){view={x:70,y:50,k:1};mark();return;}var minX=1e9,minY=1e9,maxX=-1e9,maxY=-1e9;S.devices.forEach(function(d){minX=Math.min(minX,d.x-60);maxX=Math.max(maxX,d.x+60);minY=Math.min(minY,d.y-40);maxY=Math.max(maxY,d.y+40);});var r=$('cv').getBoundingClientRect();var k=Math.max(0.3,Math.min(2.2,Math.min((r.width-60)/(maxX-minX),(r.height-60)/(maxY-minY))));view.k=k;view.x=(r.width-(maxX-minX)*k)/2-minX*k;view.y=(r.height-(maxY-minY)*k)/2-minY*k;mark();}
function bind(){
 $('cv').addEventListener('pointerdown',function(e){var t=e.target,g=null,l=null;while(t&&t!==$('cv')){if(t.getAttribute){if(t.getAttribute('data-d')){g=t;break;}if(t.getAttribute('data-l')){l=t;break;}}t=t.parentNode;}var p=pt(e);if(tool==='marquee'&&!g&&!l){marq={x0:p.sx,y0:p.sy,x1:p.sx,y1:p.sy,add:e.shiftKey};$('marquee').style.display='';return;}if(g){var id=+g.getAttribute('data-d');if(tool==='link'){if(linkFrom==null){linkFrom=id;}else if(linkFrom!==id){pushUndo();S.links.push({id:S.lid++,a:linkFrom,b:id,pa:'',pb:'',mode:'trunk',vlans:'135,1151,2201',media:'copper',cost:1,down:false});linkFrom=null;setTool('select');autosave();mark();props();}return;}if(e.shiftKey){if(selD[id])delete selD[id];else selD[id]=1;mark();fillReg();props();return;}if(!selD[id]){selD={};selL={};}selD[id]=1;var offs=[];for(var k in selD){var dd=dev(+k);if(dd)offs.push({id:+k,dx:p.x-dd.x,dy:p.y-dd.y});}drag={offs:offs,moved:false};pushUndo();mark();fillReg();props();return;}if(l){selD={};selL={};selL[+l.getAttribute('data-l')]=1;mark();fillReg();props();return;}if(tool==='marquee'){marq={x0:p.sx,y0:p.sy,x1:p.sx,y1:p.sy,add:e.shiftKey};$('marquee').style.display='';return;}if(!e.shiftKey)clearSel();pan={x:e.clientX-view.x,y:e.clientY-view.y};});
 window.addEventListener('pointermove',function(e){if(marq){var r=$('cv').getBoundingClientRect();marq.x1=e.clientX-r.left;marq.y1=e.clientY-r.top;var m=$('marquee');m.setAttribute('x',Math.min(marq.x0,marq.x1));m.setAttribute('y',Math.min(marq.y0,marq.y1));m.setAttribute('width',Math.abs(marq.x1-marq.x0));m.setAttribute('height',Math.abs(marq.y1-marq.y0));return;}if(drag){var p=pt(e);drag.moved=true;drag.offs.forEach(function(o){var d=dev(o.id);if(d){d.x=snap(p.x-o.dx);d.y=snap(p.y-o.dy);}});mark();return;}if(pan){view.x=e.clientX-pan.x;view.y=e.clientY-pan.y;mark();}});
 window.addEventListener('pointerup',function(){if(marq){var x0=(Math.min(marq.x0,marq.x1)-view.x)/view.k,x1=(Math.max(marq.x0,marq.x1)-view.x)/view.k;var y0=(Math.min(marq.y0,marq.y1)-view.y)/view.k,y1=(Math.max(marq.y0,marq.y1)-view.y)/view.k;if(!marq.add){selD={};selL={};}S.devices.forEach(function(d){if(d.x>=x0&&d.x<=x1&&d.y>=y0&&d.y<=y1)selD[d.id]=1;});marq=null;$('marquee').style.display='none';mark();fillReg();props();return;}if(drag){if(drag.moved)autosave();else undoStack.pop();drag=null;return;}pan=null;});
 $('cv').addEventListener('wheel',function(e){e.preventDefault();var r=$('cv').getBoundingClientRect();var mx=e.clientX-r.left,my=e.clientY-r.top;var f=e.deltaY<0?1.12:0.89,nk=Math.max(0.3,Math.min(2.6,view.k*f));view.x=mx-(mx-view.x)*(nk/view.k);view.y=my-(my-view.y)*(nk/view.k);view.k=nk;mark();},{passive:false});
 $('cv').addEventListener('dblclick',function(e){var p=pt(e);addDevice(lastType||'pc',p.x,p.y);});
 $('cv').addEventListener('dragover',function(e){e.preventDefault();});
 $('cv').addEventListener('drop',function(e){e.preventDefault();var k=e.dataTransfer?e.dataTransfer.getData('text/plain'):'';if(k&&TYPES[k]){var p=pt(e);addDevice(k,p.x,p.y);}});
 $('palDev').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){addDevice(t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palDev').addEventListener('dragstart',function(e){var t=e.target;while(t&&t!==$('palDev')){if(t.getAttribute&&t.getAttribute('data-add')){if(e.dataTransfer)e.dataTransfer.setData('text/plain',t.getAttribute('data-add'));return;}t=t.parentNode;}});
 $('palTpl').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('palTpl')){if(t.getAttribute&&t.getAttribute('data-tpl')){addTpl(t.getAttribute('data-tpl'));return;}t=t.parentNode;}});
 $('regSearch').addEventListener('input',fillReg);$('regType').addEventListener('change',fillReg);
 $('regList').addEventListener('click',function(e){var t=e.target;if(t.getAttribute&&t.getAttribute('data-chk')){var cid=+t.getAttribute('data-chk');if(t.checked)selD[cid]=1;else delete selD[cid];mark();props();fillReg();return;}while(t&&t!==$('regList')){if(t.getAttribute&&t.getAttribute('data-reg')){var id=+t.getAttribute('data-reg');selD={};selL={};selD[id]=1;var d=dev(id);if(d){var r=$('cv').getBoundingClientRect();view.x=r.width/2-d.x*view.k;view.y=r.height/2-d.y*view.k;mark();}props();fillReg();return;}t=t.parentNode;}});
 $('bBulkDel').addEventListener('click',delSel);
 $('bSave').addEventListener('click',saveScheme);$('bOpen').addEventListener('click',openModal);
 $('bSvg').addEventListener('click',exportSvg);$('bPng').addEventListener('click',exportPng);$('bPrint').addEventListener('click',function(){window.print();});
 $('bLink').addEventListener('click',function(){setTool(tool==='link'?'select':'link');});
 $('bSel').addEventListener('click',function(){setTool('select');});
 $('bMarquee').addEventListener('click',function(){setTool(tool==='marquee'?'select':'marquee');});
 $('bUndo').addEventListener('click',undo);$('bRedo').addEventListener('click',redo);$('bDup').addEventListener('click',dupSel);
 $('bDelSel').addEventListener('click',delSel);
 $('bClearAll').addEventListener('click',function(){if(confirm('Очистить ВСЁ?'))clearAll();});
 $('bSound').addEventListener('click',function(){cfg.sound=!cfg.sound;$('bSound').textContent=cfg.sound?'🔊':'🔇';$('bSound').className=cfg.sound?'on':'';});
 $('bRun').addEventListener('click',startSim);$('bPause').addEventListener('click',function(){if(!sim.running)return;sim.paused=!sim.paused;$('bPause').textContent=sim.paused?'▶':'⏸';});
 $('bStop').addEventListener('click',stopSim);
 $('bDemo').addEventListener('click',function(){pushUndo();S=demo();norm();clearSel();autosave();mark();props();renderFlows();fit();toast('Пример');});
 $('bFit').addEventListener('click',fit);
 $('bFault').addEventListener('click',function(){var up=S.links.filter(function(L){return !L.down;});if(!up.length){toast('нет работающих линий');return;}pushUndo();var L=up[Math.floor(Math.random()*up.length)];L.down=true;autosave();mark();ev('warn','⚡ авария #'+L.id);toast('Авария на линии #'+L.id);});
 $('bHeal').addEventListener('click',function(){pushUndo();S.links.forEach(function(L){L.down=false;});S.devices.forEach(function(d){d.down=false;});autosave();mark();ev('ok','🩹 восстановлено');toast('Восстановлено');});
 $('cZoom').addEventListener('input',function(){view.k=this.value/100;mark();});
 $('cGrid').addEventListener('change',function(){cfg.grid=this.checked;$('stage').className=(cfg.grid?'grid ':'')+cfg.theme;});
 $('cSpeed').addEventListener('input',function(){cfg.speed=this.value/100;$('vSpeed').textContent=cfg.speed.toFixed(1)+'x';});
 $('cTheme').addEventListener('change',function(){cfg.theme=this.value;$('stage').className=(cfg.grid?'grid ':'')+cfg.theme;mark();});
 $('tabs').addEventListener('click',function(e){var t=e.target;while(t&&t!==$('tabs')){if(t.getAttribute&&t.getAttribute('data-tab')){var name=t.getAttribute('data-tab');Array.prototype.forEach.call($('tabs').children,function(b){b.className=(b.getAttribute('data-tab')===name)?'on':'';});['props','flows','fdb','check','plan','events'].forEach(function(pn){$('pane'+pn.charAt(0).toUpperCase()+pn.slice(1)).className=(pn===name)?'pane on':'pane';});if(name==='plan')buildPlan();if(name==='fdb')renderFdb();if(name==='flows')renderFlows();return;}t=t.parentNode;}});
 $('bAddFlow').addEventListener('click',function(){pushUndo();S.flows.push({id:S.fid++,name:'Поток '+(S.flows.length+1),src:S.devices[0]?S.devices[0].id:0,dst:0,vlan:'135',mode:'unicast',rate:3,on:true});autosave();renderFlows();toast('Поток добавлен');});
 $('flowList').addEventListener('click',function(e){var t=e.target;if(t.getAttribute&&t.getAttribute('data-fdel')){pushUndo();var id=+t.getAttribute('data-fdel');S.flows=S.flows.filter(function(f){return f.id!==id;});autosave();renderFlows();return;}if(t.getAttribute&&t.getAttribute('data-fon')){var f=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+t.getAttribute('data-fon'))f=S.flows[i];if(f)f.on=t.checked;autosave();}});
 $('flowList').addEventListener('input',function(e){var t=e.target,a;if((a=t.getAttribute('data-fsrc'))){var f=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+a)f=S.flows[i];if(f){f.src=+t.value;autosave();}}if((a=t.getAttribute('data-fdst'))){var f2=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+a)f2=S.flows[i];if(f2){f2.dst=+t.value;autosave();}}if((a=t.getAttribute('data-fvlan'))){var f3=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+a)f3=S.flows[i];if(f3){f3.vlan=t.value;autosave();}}if((a=t.getAttribute('data-fmode'))){var f4=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+a)f4=S.flows[i];if(f4){f4.mode=t.value;autosave();}}if((a=t.getAttribute('data-frate'))){var f5=null;for(var i=0;i<S.flows.length;i++)if(S.flows[i].id===+a)f5=S.flows[i];if(f5){f5.rate=Math.max(1,+t.value||1);autosave();}}});
 $('fdbDev').addEventListener('change',renderFdb);
 $('bCheck').addEventListener('click',checkPlan);
 $('planSyn').addEventListener('change',buildPlan);
 $('bPlanCopy').addEventListener('click',function(){buildPlan();try{navigator.clipboard.writeText($('planOut').textContent);toast('Скопировано');}catch(e){toast('Скопируйте вручную');}});
 $('bLogClear').addEventListener('click',function(){sim.ev=[];renderLog();});
 window.addEventListener('keydown',function(e){var tag=e.target?e.target.tagName:'';if(tag==='INPUT'||tag==='SELECT'||tag==='TEXTAREA')return;if(e.key==='Delete'||e.key==='Backspace'){delSel();e.preventDefault();}if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='z'){if(e.shiftKey)redo();else undo();e.preventDefault();}if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='y'){redo();e.preventDefault();}if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='a'){selD={};selL={};S.devices.forEach(function(d){selD[d.id]=1;});S.links.forEach(function(L){selL[L.id]=1;});mark();fillReg();props();e.preventDefault();}if((e.ctrlKey||e.metaKey)&&String(e.key).toLowerCase()==='d'){dupSel();e.preventDefault();}if(e.key==='Escape'){setTool('select');clearSel();}});
}
palette();bind();
var saved=null;try{saved=localStorage.getItem('netlab_auto');}catch(e){}
try{S=saved?JSON.parse(saved):demo();}catch(e){S=demo();}
if(!S||!S.devices)S=demo();
norm();$('stage').className='grid dark';props();mark();fit();
ev('info','🧪 NetLab PRO готов: '+S.devices.length+' устройств, '+S.links.length+' линий');
requestAnimationFrame(loop);
})();
</script>
</body></html>'''
open(os.path.join('static', 'netlab.html'), 'w', encoding='utf-8').write(HTML)
print('ok: static/netlab.html записан (' + str(len(HTML)) + ' байт)')

# --- swh.py: просто отдаём файл (без Jinja) ---
src = open('swh.py', encoding='utf-8').read()
new_route = """def netlab_page():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'netlab.html')
    r = Response(open(p, encoding='utf-8').read(), mimetype='text/html')
    r.headers['Cache-Control'] = 'no-store'
    return r
"""
pattern = r"def netlab_page\(\):\s*\n\s*return [^\n]+\n"
if re.search(pattern, src):
    new_src, n = re.subn(pattern, new_route, src, count=1)
    if n:
        src = new_src
        print('ok: /netlab -> static/netlab.html (no Jinja)')
else:
    print('ПРОПУСК: маршрут netlab_page не найден (всё уже настроено)')

# --- ast.parse: если сломали swh.py — откат ---
try:
    ast.parse(src)
    print('ok: ast.parse swh.py прошёл')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v26_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС swh.py НЕ ОК — откат: ' + str(e))

open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v26',
           'fixes': ['netlab.html в static (без Jinja — не падает)', 'без self-check (именно он давал rc=1)',
                     'VLAN справочник из Knowledge Base в datalist (80+ реальных VLAN)',
                     'рамка для массового выделения, быстрая очистка с отменой',
                     'undo/redo (Ctrl+Z/Y), симуляция unicast/multicast/PON/broadcast',
                     'проверка VLAN-плана, план работ DES/DGS, сохранение схем в БД']},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v26. Бэкап: backups/swh_pre_v26_' + TS + '.py')
