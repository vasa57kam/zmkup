import ast
GENJS = '''var TPL={ dlink:{
 create:'create vlan {text} tag {vlan}',
 del_vlan:'delete vlan {vlan}',
 add_untag:'config vlan vlanid {vlan} add untagged {ports}',
 add_tag:'config vlan vlanid {vlan} add tagged {ports}',
 del_port:'config vlan vlanid {vlan} delete {ports}',
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
 cam:'create vlan {text} tag {vlan}\\nconfig vlan vlanid {vlan} add untagged {ports}\\nconfig ports {ports} pvid {vlan}',
 trunk:'config vlan vlanid {vlan} add tagged {ports}'
}};
var NAMES={create:'Создать VLAN (имя + tag)',del_vlan:'Удалить VLAN',add_untag:'Добавить порт в VLAN (untagged / абонентский)',add_tag:'Добавить порт в VLAN (tagged / магистраль)',del_port:'Убрать порт из VLAN',show_vlan:'Показать информацию о VLAN',show_ports:'Показать VLAN на порту(ах)',pvid:'Назначить PVID порту (абонентский)',find_mac:'Найти MAC в FDB',show_fdb:'Показать всю FDB-таблицу',port_info:'Информация о портах (состояние/скорость/duplex)',port_util:'Загрузка портов (%) — узкие места и штормы',port_err:'Ошибки портов (счётчики CRC и др.)',clear_cnt:'Сбросить счётчики ошибок портов',port_speed:'Изменить скорость/duplex порта',port_off:'Выключить порт',port_on:'Включить порт',save:'Сохранить конфигурацию (save)',reboot:'Перезагрузить свитч (осторожно!)',cam:'КОМБО: камера на VLAN (create+untagged+PVID)',trunk:'КОМБО: магистраль на ядро (tagged)'};
var HINTS={create:'VLAN — номер (tag, напр. 135); Текст — ИМЯ VLAN (напр. OTS.INTERCOM.UFA.PRV). Имя не нужно — поправьте шаблон руками.',
del_vlan:'VLAN — номер удаляемого VLAN (сначала уберите из него все порты!).',
add_untag:'VLAN — номер VLAN; Порт(ы) — абонентский порт или порт камеры (напр. 21 или 19-24). Команда: config vlan vlanid … add untagged.',
add_tag:'VLAN — номер VLAN; Порт(ы) — МАГИСТРАЛЬНЫЙ порт / uplink (напр. 26-28 или 28). Команда: config vlan vlanid … add tagged.',
del_port:'VLAN — номер ЛИШНЕГО VLAN; Порт(ы) — порты, которые убрать (как в инструкции: config vlan vlanid 2402 delete 14).',
show_vlan:'VLAN — номер VLAN, который показать.',
show_ports:'Порт(ы) — порты, по которым показать VLAN-конфиг.',
pvid:'VLAN — номер VLAN; Порт(ы) — абонентские порты, где PVID = этот VLAN.',
find_mac:'MAC — адрес вида 00:1A:79:xx:xx:xx (камеры/абонента).',
show_fdb:'Ничего вводить не надо — покажет всю таблицу MAC.',
port_info:'Порт(ы) — порты для просмотра (напр. 21 или 1-28). Покажет состояние, скорость, duplex.',
port_util:'Порт(ы) — порты для замера. >80% на uplink = узкое место, 100% при пустых = шторм/петля.',
port_err:'Порт(ы) — порты для просмотра счётчиков ошибок (CRC/Align). Нет команды на прошивке — поправьте шаблон.',
clear_cnt:'Порт(ы) — порты, на которых сбросить счётчики ошибок.',
port_speed:'Порт(ы) — порты; Скорость и Duplex выбираются из списков (auto / 10 / 100 / 1000).',
port_off:'Порт(ы) — порты, которые выключить.',
port_on:'Порт(ы) — порты, которые включить.',
save:'Ничего вводить не надо — сохранит конфиг в память свитча.',
reboot:'ВНИМАНИЕ: свитч перезагрузится! Вводить ничего не надо.',
cam:'Текст — ИМЯ VLAN; VLAN — номер (напр. 135); Порт(ы) — порт, куда воткнута камера. Даёт 3 команды сразу.',
trunk:'VLAN — номер VLAN, который пропускаем; Порт(ы) — магистральный порт на ядро/uplink.'};
var MEMO={cam:'1) создать VLAN (имя + tag)\\n2) добавить порт камеры untagged (vlanid)\\n3) PVID порту\\n4) save\\n5) в биллинге вписать VLAN (абон. и реал.)\\n6) проверить поток камеры',
trunk:'1) добавить магистральный порт tagged (vlanid)\\n2) save\\n3) проверить, что uplink поднялся',
create:'1) create vlan ИМЯ tag N\\n2) save',
add_untag:'1) добавить порт untagged (vlanid)\\n2) save\\n3) проверить состояние порта',
del_port:'1) убрать порт: config vlan vlanid N delete P\\n2) save',
del_vlan:'1) убрать все порты из VLAN\\n2) delete vlan\\n3) save',
save:'1) save\\n2) убедиться, что конфиг сохранился',
reboot:'1) предупредить абонентов\\n2) reboot\\n3) проверить доступность',
port_speed:'1) выставить скорость/duplex\\n2) save\\n3) проверить скорость порта (show ports)',
port_err:'1) посмотреть счётчики\\n2) ошибки растут — проверить кабель/коннектор/SFP\\n3) после устранения — сбросить счётчики',
port_info:'1) посмотреть состояние/скорость\\n2) порт down или не та скорость — проверить кабель и настройки'};
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
print('ok: gen.js v6 — синтаксис vlanid')

src = open('swh.py').read()
for old_v in ('?v=5', '?v=4', '?v=3', '?v=2'):
    if ('/static/gen.js' + old_v) in src:
        src = src.replace('/static/gen.js' + old_v, '/static/gen.js?v=6', 1)
        print('ok: версия gen.js -> v6')
        break
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')