import ast, re
GENJS = r'''var TPL={
des:{
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
 cam:'create vlan {text} tag {vlan}\nconfig vlan vlanid {vlan} add tagged {trunk}\nconfig vlan vlanid {vlan} add untagged {ports}\nconfig ports {ports} pvid {vlan}\nsave',
 trunk:'config vlan vlanid {vlan} add tagged {trunk}',
 ddm:'show ddm ports {ports}',
 ddm_all:'show ddm',
 ism_show:'show igmp_snooping multicast_vlan vlan{vlan}',
 ism_del_tag:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}',
 ism_del_mem:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {ports}',
 ism_add_mem:'config igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}',
 ism_add_src:'config igmp_snooping multicast_vlan vlan{vlan} add source_port {ports}',
 ism_swap:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} delete source_port {ports}\nconfig igmp_snooping multicast_vlan vlan{vlan} add source_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\nshow igmp_snooping multicast_vlan\nsave',
 t2a:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\nconfig vlan vlanid {trunk} delete {ports}\nconfig vlan vlanid {text} add untagged {ports}\nconfig ports {ports} pvid {text}'
},
dgs:{
 create:'vlan database\nvlan {vlan}\nexit',
 del_vlan:'vlan database\nno vlan {vlan}\nexit',
 add_untag:'interface ethernet 1/0/{ports}\nvlan participation include {vlan}\nvlan pvid {vlan}\nexit',
 add_tag:'interface ethernet 1/0/{ports}\nvlan participation include {vlan}\nvlan tagging tagged\nexit',
 del_port:'interface ethernet 1/0/{ports}\nvlan participation exclude {vlan}\nexit',
 show_vlan:'show vlan {vlan}',
 show_ports:'show vlan interface ethernet 1/0/{ports}',
 pvid:'interface ethernet 1/0/{ports}\nvlan pvid {vlan}\nexit',
 find_mac:'show bridge mac-address-table | include {mac}',
 show_fdb:'show bridge mac-address-table',
 port_info:'show interface ethernet 1/0/{ports}',
 port_util:'show interface ethernet 1/0/{ports} utilization',
 port_err:'show interface ethernet 1/0/{ports} counters',
 clear_cnt:'clear counters interface ethernet 1/0/{ports}',
 port_speed:'interface ethernet 1/0/{ports}\nspeed {speed}\nexit',
 port_off:'interface ethernet 1/0/{ports}\nshutdown\nexit',
 port_on:'interface ethernet 1/0/{ports}\nno shutdown\nexit',
 save:'copy running-config startup-config',
 reboot:'reload',
 cam:'vlan database\nvlan {vlan}\nexit\ninterface ethernet 1/0/{trunk}\nvlan participation include {vlan}\nvlan tagging tagged\nexit\ninterface ethernet 1/0/{ports}\nvlan participation include {vlan}\nvlan pvid {vlan}\nexit\ncopy running-config startup-config',
 trunk:'interface ethernet 1/0/{trunk}\nvlan participation include {vlan}\nvlan tagging tagged\nexit',
 ddm:'show ddm interface ethernet 1/0/{ports}',
 ddm_all:'show ddm',
 ism_show:'show igmp_snooping multicast_vlan vlan{vlan}',
 ism_del_tag:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}',
 ism_del_mem:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {ports}',
 ism_add_mem:'config igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}',
 ism_add_src:'config igmp_snooping multicast_vlan vlan{vlan} add source_port {ports}',
 ism_swap:'config igmp_snooping multicast_vlan vlan{vlan} delete member_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} delete source_port {ports}\nconfig igmp_snooping multicast_vlan vlan{vlan} add source_port {trunk}\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\nshow igmp_snooping multicast_vlan\nsave',
 t2a:'config igmp_snooping multicast_vlan vlan{vlan} delete tag_member_port {ports}\nconfig igmp_snooping multicast_vlan vlan{vlan} add member_port {ports}\ninterface ethernet 1/0/{ports}\nvlan participation exclude {trunk}\nvlan participation include {text}\nvlan pvid {text}\nexit'
}};
var NAMES={create:'Создать VLAN',del_vlan:'Удалить VLAN',add_untag:'Добавить порт в VLAN (untagged / абонентский)',add_tag:'Добавить порт в VLAN (tagged / магистраль)',del_port:'Убрать порт из VLAN',show_vlan:'Показать информацию о VLAN',show_ports:'Показать VLAN на порту(ах)',pvid:'Назначить PVID порту (абонентский)',find_mac:'Найти MAC в FDB',show_fdb:'Показать всю FDB-таблицу',port_info:'Информация о портах (состояние/скорость)',port_util:'Загрузка портов (%) — узкие места и штормы',port_err:'Ошибки портов (счётчики CRC и др.)',clear_cnt:'Сбросить счётчики ошибок портов',port_speed:'Изменить скорость/duplex порта',port_off:'Выключить порт',port_on:'Включить порт',save:'Сохранить конфигурацию',reboot:'Перезагрузить свитч (осторожно!)',cam:'КОМБО: камера на VLAN',trunk:'КОМБО: транзит VLAN на магистрали (tagged)',ddm:'DDM оптики на порту',ddm_all:'DDM всех портов (SFP)',ism_show:'ISM: показать конфиг multicast_vlan (IPTV)',ism_del_tag:'ISM: убрать порт из tag_member (магистрали)',ism_del_mem:'ISM: убрать порт из member',ism_add_mem:'ISM: добавить порт в member (абонентский)',ism_add_src:'ISM: добавить source_port (куда заходит поток)',ism_swap:'КОМБО: смена source-порта ISM (безопасный порядок)',t2a:'КОМБО: магистраль→абонент без ошибок ISM'};
var HINTS={create:'DES: VLAN — номер (tag), Текст — ИМЯ VLAN (напр. OTS.INTERCOM.UFA.PRV). DGS: только номер.',
del_vlan:'VLAN — номер удаляемого VLAN (сначала уберите порты!).',
add_untag:'VLAN — номер; Порт(ы) — абонентский порт или порт камеры (21 или 19-24).',
add_tag:'VLAN — номер; Порт(ы) магистрали — транк/uplink (26-28 или 28).',
del_port:'VLAN — номер ЛИШНЕГО VLAN; Порт(ы) — порты, которые убрать.',
show_vlan:'VLAN — номер VLAN, который показать.',
show_ports:'Порт(ы) — порты, по которым показать VLAN-конфиг.',
pvid:'VLAN — номер; Порт(ы) — абонентские порты, где PVID = этот VLAN.',
find_mac:'MAC — адрес вида 00:1A:79:xx:xx:xx.',
show_fdb:'Ничего вводить не надо — покажет всю таблицу MAC.',
port_info:'Порт(ы) — порты для просмотра (21 или 1-28).',
port_util:'Порт(ы) — порты для замера. >80% на uplink = узкое место, 100% при пустых = шторм.',
port_err:'Порт(ы) — порты для счётчиков ошибок (CRC/Align).',
clear_cnt:'Порт(ы) — порты, на которых сбросить счётчики.',
port_speed:'Порт(ы) — порты; Скорость/Duplex из списков (auto/10/100/1000).',
port_off:'Порт(ы) — порты, которые выключить.',
port_on:'Порт(ы) — порты, которые включить.',
save:'Ничего вводить не надо — сохранит конфиг.',
reboot:'ВНИМАНИЕ: свитч перезагрузится!',
cam:'Текст (DES) — ИМЯ VLAN; VLAN — номер; Порт(ы) магистрали — транк-порты (tagged); Порт(ы) — порт камеры.',
trunk:'VLAN — номер; Порт(ы) магистрали — ВСЕ транк-порты, куда прокидываем VLAN тегом.',
ddm:'Порт(ы) — порт с SFP. Tx/Rx мощность, температура.',
ddm_all:'Ничего вводить не надо.',
ism_show:'VLAN — МУЛЬТИКАСТ-VLAN вашего свитча (часто 1151, но бывает другой — смотрите show igmp_snooping multicast_vlan). Покажет source_port / tag_member_port / member_port.',
ism_del_tag:'VLAN — мультикаст-VLAN; Порт(ы) — магистральный порт, который переводим в абонентский.',
ism_del_mem:'VLAN — мультикаст-VLAN; Порт(ы) — убираемые из member.',
ism_add_mem:'VLAN — мультикаст-VLAN; Порт(ы) — ставшие абонентскими.',
ism_add_src:'VLAN — мультикаст-VLAN; Порт(ы) — порт, куда заходит IPTV-поток (напр. 27). БЕЗ source будет ошибка «wrong ISM config / Source is absent».',
ism_swap:'VLAN — мультикаст-VLAN; Порт(ы) — СТАРЫЙ source-порт; Порт(ы) магистрали — НОВЫЙ source-порт. Source в ISM VLAN всегда ОДИН! Патч-корд переставить физически после назначения нового source.',
t2a:'VLAN — мультикаст-VLAN (1151 или ваш); Порт(ы) — переводимый порт; Порт(ы) магистрали — его СТАРЫЙ магистральный VLAN; Текст — НОВЫЙ абонентский VLAN. Команды в безопасном порядке.'};
var HINTS_DGS={create:'VLAN — номер. Команды режима vlan database (Cisco-подобный CLI DGS-1210 ME).',
add_untag:'Порт(ы) — номер БЕЗ префикса (подставится 1/0/N).',
add_tag:'Порт(ы) — магистральный порт; VLAN получит тег.',
del_port:'exclude убирает порт из VLAN.',
port_speed:'Скорость из списка (auto/10/100/1000).',
save:'Сохранение: copy running-config startup-config.',
reboot:'Перезагрузка: reload. Осторожно!',
find_mac:'Если фильтр | include не сработал — уберите его из шаблона.',
ism_show:'ISM-команды на DGS ME могут отличаться по ревизии — шаблон редактируемый.',
t2a:'Порт(ы) магистрали здесь — СТАРЫЙ магистральный VLAN (exclude), Текст — НОВЫЙ абонентский.'};
var MEMO={cam:'1) создать VLAN\n2) протранзить на магистрали tagged\n3) добавить порт камеры untagged\n4) PVID порту\n5) save\n6) в биллинге вписать VLAN (абон. и реал.)\n7) проверить поток камеры',
trunk:'1) добавить магистральный порт tagged\n2) save\n3) проверить, что uplink поднялся',
create:'1) создать VLAN\n2) save',
add_untag:'1) добавить порт untagged\n2) save\n3) проверить состояние порта',
del_port:'1) убрать порт из VLAN\n2) save',
del_vlan:'1) убрать все порты из VLAN\n2) удалить VLAN\n3) save',
save:'1) save\n2) убедиться, что конфиг лёг',
reboot:'1) предупредить абонентов\n2) reboot/reload\n3) проверить доступность',
port_speed:'1) выставить скорость\n2) save\n3) проверить скорость порта',
port_err:'1) посмотреть счётчики\n2) ошибки растут — кабель/коннектор/SFP\n3) после устранения — сбросить счётчики',
port_info:'1) посмотреть состояние/скорость\n2) порт down или не та скорость — кабель и настройки',
port_util:'1) замерить загрузку\n2) >80% на магистрали — планировать апгрейд\n3) 100% без абонентов — петля/шторм',
ddm:'1) Tx/Rx мощность\n2) Rx ниже -25 dBm — деградация оптики/грязный коннектор\n3) почистить/заменить патч-корд или SFP\n4) снова show ddm и сравнить',
ddm_all:'1) найти порты с аномальной Rx\n2) запланировать чистку/замену оптики',
ism_swap:'1) вычистить новый порт из member/tag_member\n2) delete source_port старого\n3) add source_port нового\n4) ФИЗИЧЕСКИ переставить патч-корд\n5) старый порт add member_port\n6) show igmp_snooping multicast_vlan + group vlan\n7) save\n8) два source нельзя: петля мультикаста и дубли каналов; резерв — только LACP/RSTP/ERPS',
t2a:'1) show igmp_snooping multicast_vlan vlan<ваш> — посмотреть роли\n2) если порт был source_port — СНАЧАЛА add source_port новому порту\n3) delete tag_member_port, add member_port\n4) убрать порт из магистрального VLAN\n5) add untagged в абонентский + pvid\n6) save\n7) проверить IPTV и show log'};
function setFam(){
  var f=document.getElementById('fam').value;
  var o=document.getElementById('op');
  if(f==='custom'){ o.innerHTML='<option value="custom">Свой шаблон</option>'; }
  else { o.innerHTML=Object.keys(TPL[f]||{}).map(function(k){ return '<option value="'+k+'">'+NAMES[k]+'</option>'; }).join(''); }
  fillTpl();
}
function fillTpl(){
  var f=document.getElementById('fam').value;
  var k=document.getElementById('op').value;
  if(f!=='custom'){ document.getElementById('tpl').value=((TPL[f]||{})[k]||''); }
  var h=document.getElementById('hint');
  if(h){ h.textContent='💡 '+((f==='dgs'&&HINTS_DGS[k])||HINTS[k]||'Заполните поля и нажмите «Сгенерировать».'); }
  var m=document.getElementById('memo');
  if(m){ m.value=MEMO[k]||''; }
  if(k.indexOf('ism')===0||k==='t2a'){
    var vv=document.getElementById('v');
    if(!vv.value||vv.value==='135'){ vv.value='1151'; }
  }
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
         .replace(/{trunk}/g,(document.getElementById('tr')||{}).value||'')
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
print('ok: gen.js перезаписан ЦЕЛИКОМ (финальная версия)')

src = open('swh.py').read()
new_src, n = re.subn(r'/static/gen\.js\?v=\d+', '/static/gen.js?v=13', src)
if n:
    print('ok: версия gen.js -> v13')
src = new_src
open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')