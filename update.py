import ast
src = open('swh.py').read()

# 1) gen.js полностью на русском + подсказки + памятки
GENJS = '''var TPL={ dlink:{
 create:'create vlan {vlan}',
 del_vlan:'delete vlan {vlan}',
 add_untag:'config vlan {vlan} add untagged {ports}',
 add_tag:'config vlan {vlan} add tagged {ports}',
 del_port:'config vlan {vlan} delete {ports}',
 show_vlan:'show vlan {vlan}',
 show_ports:'show vlan ports {ports}',
 pvid:'config ports {ports} pvid {vlan}',
 find_mac:'show fdb {mac}',
 show_fdb:'show fdb',
 port_off:'config ports {ports} state disabled',
 port_on:'config ports {ports} state enabled',
 save:'save',
 reboot:'reboot',
 cam:'create vlan {vlan}\\nconfig vlan {vlan} add untagged {ports}\\nconfig ports {ports} pvid {vlan}',
 trunk:'config vlan {vlan} add tagged {ports}'
}};
var NAMES={create:'Создать VLAN',del_vlan:'Удалить VLAN',add_untag:'Добавить порт в VLAN (untagged / абонентский)',add_tag:'Добавить порт в VLAN (tagged / магистраль)',del_port:'Убрать порт из VLAN',show_vlan:'Показать информацию о VLAN',show_ports:'Показать VLAN на порту(ах)',pvid:'Назначить PVID порту (абонентский)',find_mac:'Найти MAC в FDB',show_fdb:'Показать всю FDB-таблицу',port_off:'Выключить порт',port_on:'Включить порт',save:'Сохранить конфигурацию (save)',reboot:'Перезагрузить свитч (осторожно!)',cam:'КОМБО: камера на VLAN (создать+порт+PVID)',trunk:'КОМБО: магистраль на ядро (tagged)'};
var HINTS={create:'VLAN — номер нового VLAN (напр. 135). Порты не нужны.',
add_untag:'VLAN — номер VLAN; Порт(ы) — абонентский порт или порт камеры (напр. 21 или 19-24). Порт станет доступовым.',
add_tag:'VLAN — номер VLAN; Порт(ы) — МАГИСТРАЛЬНЫЙ порт / uplink (напр. 26-28 или 28).',
del_port:'VLAN — номер VLAN; Порт(ы) — порты, которые убрать из этого VLAN.',
del_vlan:'VLAN — номер удаляемого VLAN (сначала уберите из него все порты!).',
show_vlan:'VLAN — номер VLAN, который показать.',
show_ports:'Порт(ы) — порты, по которым показать VLAN-конфиг.',
pvid:'VLAN — номер VLAN; Порт(ы) — абонентские порты, где PVID = этот VLAN.',
find_mac:'MAC — адрес вида 00:1A:79:xx:xx:xx (камеры/абонента).',
show_fdb:'Ничего вводить не надо — покажет всю таблицу MAC.',
port_off:'Порт(ы) — порты, которые выключить.',
port_on:'Порт(ы) — порты, которые включить.',
save:'Ничего вводить не надо — сохранит конфиг в память свитча.',
reboot:'ВНИМАНИЕ: свитч перезагрузится! Вводить ничего не надо.',
cam:'VLAN — VLAN камеры (напр. 135); Порт(ы) — порт, куда воткнута камера.',
trunk:'VLAN — VLAN, который пропускаем; Порт(ы) — магистральный порт на ядро/uplink.'};
var MEMO={cam:'1) создать VLAN\\n2) добавить порт камеры untagged\\n3) PVID порту\\n4) save\\n5) в биллинге вписать VLAN 135 (абон. и реал.)\\n6) проверить поток камеры',
trunk:'1) добавить магистральный порт tagged\\n2) save\\n3) проверить, что uplink поднялся',
create:'1) create vlan\\n2) save',
add_untag:'1) добавить порт untagged\\n2) save\\n3) проверить состояние порта',
del_port:'1) убрать порт из VLAN\\n2) save',
del_vlan:'1) убрать все порты из VLAN\\n2) delete vlan\\n3) save',
save:'1) save\\n2) убедиться, что конфиг сохранился',
reboot:'1) предупредить абонентов\\n2) reboot\\n3) проверить доступность'};
function setFam(){
  var f=document.getElementById('fam').value;
  var o=document.getElementById('op');
  if(f==='custom'){ o.innerHTML='<option value="custom">Свой шаблон</option>'; }
  else { o.innerHTML=Object.keys(TPL.dlink).map(function(k){ return '<option value="'+k+'">'+NAMES[k]+'</option>'; }).join(''); }
  fillTpl();
}
function fillTpl(){
  var f=document.getElementById('fam').value;
  var k=document.getElementById('op').value;
  if(f!=='custom'){ document.getElementById('tpl').value=(TPL.dlink[k]||''); }
  var h=document.getElementById('hint');
  if(h){ h.textContent='💡 '+(HINTS[k]||'Заполните поля и нажмите «Сгенерировать».'); }
  var m=document.getElementById('memo');
  if(m){ m.value=MEMO[k]||''; }
}
function gen(){
  var t=document.getElementById('tpl').value;
  var r=t.replace(/{vlan}/g,document.getElementById('v').value)
         .replace(/{ports}/g,document.getElementById('p').value)
         .replace(/{mac}/g,document.getElementById('m').value)
         .replace(/{ip}/g,document.getElementById('ip').value)
         .replace(/{text}/g,document.getElementById('txt').value);
  document.getElementById('outg').value=r;
}
function cpy(){ navigator.clipboard.writeText(document.getElementById('outg').value); alert('Команды скопированы'); }
function toTools(){ sessionStorage.setItem('gen2tools', document.getElementById('outg').value); location.href='/tools'; }
function sav(){
  var t=prompt('Название в справочнике:','Команда: '+(NAMES[document.getElementById('op').value]||document.getElementById('op').value));
  if(!t) return;
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:t, category:'генератор', body:document.getElementById('outg').value, notes:document.getElementById('memo').value})})
  .then(function(){ alert('Сохранено в справочник команд'); });
}
if(document.readyState!=='loading'){ setFam(); }
else { document.addEventListener('DOMContentLoaded', setFam); }
'''
open('static/gen.js', 'w').write(GENJS)
print('ok: gen.js на русском')

# 2) Страница /gen на русском
i = src.find('GEN_HTML = """')
if i >= 0:
    j = src.find('"""', i + 20)
    if j > 0:
        NEW_GEN = '''GEN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 Генератор команд</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}
#hint{background:#fff8e1;border:1px solid #f1c40f;border-radius:8px;padding:10px;margin:8px 0;}</style></head>
<body>
<div class="card big">🧬 Генератор команд — D-Link L2</div>
<div class="card">
Семейство: <select id="fam" onchange="setFam()"><option value="dlink">D-Link xStack L2 (DES-3200 / DGS-1210)</option><option value="custom">Свой шаблон</option></select>
Операция: <select id="op" onchange="fillTpl()" style="max-width:420px;"></select><br>
VLAN: <input id="v" value="135" style="width:70px;">
Порт(ы): <input id="p" placeholder="21 или 26-28" style="width:120px;">
MAC: <input id="m" placeholder="00:1A:79:.." style="width:150px;">
IP: <input id="ip" placeholder="10.163.x.x" style="width:130px;">
Текст: <input id="txt" style="width:140px;">
<div id="hint">💡 Выберите операцию — здесь появится пояснение, что вводить.</div>
Шаблон (можно править руками): <textarea id="tpl" style="width:100%;height:80px;font-family:monospace;"></textarea>
<button class="btn" style="background:#8e44ad;" onclick="gen()">🧬 Сгенерировать</button>
<button class="btn" style="background:#3498db;" onclick="cpy()">📋 Копировать команды</button>
<button class="btn" style="background:#27ae60;" onclick="toTools()">🔗 В Тулзу (выполнить по SSH)</button>
<button class="btn" style="background:#7f8c8d;" onclick="sav()">💾 В справочник</button>
<textarea id="outg" style="width:100%;height:120px;font-family:monospace;margin-top:6px;" placeholder="Здесь появятся готовые команды"></textarea>
</div>
<div class="card"><b>📝 Памятка (шаги для этой операции):</b><textarea id="memo" style="width:100%;height:110px;margin-top:6px;"></textarea>
<div style="color:#7f8c8d;font-size:14px;margin-top:6px;">Плейсхолдеры шаблона: {vlan} {ports} {mac} {ip} {text}. Комбо-операции дают несколько команд сразу. Памятка сохраняется вместе с командой в справочник.</div></div>
<script src="/static/gen.js?v=3"></script>
</body></html>"""'''
        src = src[:i] + NEW_GEN + src[j+3:]
        print('ok: /gen на русском')
else:
    print('ПРОПУСК: GEN_HTML')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')