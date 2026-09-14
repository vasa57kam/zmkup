import ast
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
 port_info:'show ports {ports}',
 port_util:'show utilization ports {ports}',
 port_err:'show counters ports {ports}',
 clear_cnt:'clear counters ports {ports}',
 port_speed:'config ports {ports} speed {speed}{duplex}',
 port_off:'config ports {ports} state disabled',
 port_on:'config ports {ports} state enabled',
 save:'save',
 reboot:'reboot',
 cam:'create vlan {vlan}\\nconfig vlan {vlan} add untagged {ports}\\nconfig ports {ports} pvid {vlan}',
 trunk:'config vlan {vlan} add tagged {ports}'
}};
var NAMES={create:'Создать VLAN',del_vlan:'Удалить VLAN',add_untag:'Добавить порт в VLAN (untagged / абонентский)',add_tag:'Добавить порт в VLAN (tagged / магистраль)',del_port:'Убрать порт из VLAN',show_vlan:'Показать информацию о VLAN',show_ports:'Показать VLAN на порту(ах)',pvid:'Назначить PVID порту (абонентский)',find_mac:'Найти MAC в FDB',show_fdb:'Показать всю FDB-таблицу',port_info:'Информация о портах (состояние/скорость/duplex)',port_util:'Загрузка портов (%) — узкие места и штормы',port_err:'Ошибки портов (счётчики CRC и др.)',clear_cnt:'Сбросить счётчики ошибок портов',port_speed:'Изменить скорость/duplex порта',port_off:'Выключить порт',port_on:'Включить порт',save:'Сохранить конфигурацию (save)',reboot:'Перезагрузить свитч (осторожно!)',cam:'КОМБО: камера на VLAN (создать+порт+PVID)',trunk:'КОМБО: магистраль на ядро (tagged)'};
var HINTS={create:'VLAN — номер нового VLAN (напр. 135). Порты не нужны.',
add_untag:'VLAN — номер VLAN; Порт(ы) — абонентский порт или порт камеры (напр. 21 или 19-24).',
add_tag:'VLAN — номер VLAN; Порт(ы) — МАГИСТРАЛЬНЫЙ порт / uplink (напр. 26-28 или 28).',
del_port:'VLAN — номер VLAN; Порт(ы) — порты, которые убрать из этого VLAN.',
del_vlan:'VLAN — номер удаляемого VLAN (сначала уберите из него все порты!).',
show_vlan:'VLAN — номер VLAN, который показать.',
show_ports:'Порт(ы) — порты, по которым показать VLAN-конфиг.',
pvid:'VLAN — номер VLAN; Порт(ы) — абонентские порты, где PVID = этот VLAN.',
find_mac:'MAC — адрес вида 00:1A:79:xx:xx:xx (камеры/абонента).',
show_fdb:'Ничего вводить не надо — покажет всю таблицу MAC.',
port_info:'Порт(ы) — порты для просмотра (напр. 21 или 1-28). Покажет состояние, скорость, duplex.',
port_util:'Порт(ы) — порты для замера. Показывает % загрузки полосы: >80% на uplink = узкое место, 100% при пустых абонентах = шторм/петля.',
port_err:'Порт(ы) — порты для просмотра счётчиков ошибок (CRC/Align). Если на прошивке команды нет — поправьте шаблон.',
clear_cnt:'Порт(ы) — порты, на которых сбросить счётчики ошибок.',
port_speed:'Порт(ы) — порты; Скорость и Duplex выбираются из списков ниже (auto / 10 / 100 / 1000).',
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
reboot:'1) предупредить абонентов\\n2) reboot\\n3) проверить доступность',
port_speed:'1) выставить скорость/duplex\\n2) save\\n3) проверить, что порт поднялся на нужной скорости (show ports)',
port_err:'1) посмотреть счётчики\\n2) если ошибки растут — проверить кабель/коннектор/SFP\\n3) после устранения — сбросить счётчики',
port_info:'1) посмотреть состояние/скорость\\n2) если порт down или не та скорость — проверить кабель и настройки порта',
port_util:'1) замерить загрузку\\n2) >80% на магистрали — планировать апгрейд/разгрузку\\n3) 100% без абонентов — искать петлю/шторм'};
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
  var sr=document.getElementById('spdRow');
  if(sr){ sr.style.display=(k==='port_speed')? 'inline':'none'; }
}
function gen(){
  var t=document.getElementById('tpl').value;
  var spd=(document.getElementById('spd')||{}).value||'auto';
  var dpx=(document.getElementById('dpx')||{}).value||'';
  var r=t.replace(/{vlan}/g,document.getElementById('v').value)
         .replace(/{ports}/g,document.getElementById('p').value)
         .replace(/{mac}/g,document.getElementById('m').value)
         .replace(/{ip}/g,document.getElementById('ip').value)
         .replace(/{text}/g,document.getElementById('txt').value)
         .replace(/{speed}/g,spd)
         .replace(/{duplex}/g,dpx? ' duplex '+dpx : '');
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
print('ok: gen.js v5')

src = open('swh.py').read()
if 'id="spdRow"' not in src:
    old = 'Текст: <input id="txt" style="width:140px;">'
    if old in src:
        src = src.replace(old,
"""<span id="spdRow" style="display:none;">Скорость: <select id="spd"><option value="auto">auto</option><option value="10">10</option><option value="100">100</option><option value="1000">1000</option></select>
Duplex: <select id="dpx"><option value="">—</option><option value="half">half</option><option value="full">full</option></select></span>
Текст: <input id="txt" style="width:140px;">""", 1)
        print('ok: списки скорости/duplex')
    else:
        print('ПРОПУСК: якорь Текст')
if 'gen.js?v=5' not in src:
    src = src.replace('/static/gen.js?v=4', '/static/gen.js?v=5', 1)
    print('ok: версия gen.js v5')
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')