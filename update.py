import ast
src = open('swh.py').read()

GEN_CARD = '''<div class="card">
<b>🧬 Генератор команд (VLAN / порты / MAC)</b><br>
Семейство: <select id="genFam"><option value="dlink">D-Link xStack (DES-3200 / DGS-1210)</option></select>
Операция: <select id="genOp">
<option value="create">Создать VLAN</option>
<option value="add_untag">Добавить порт в VLAN (untagged)</option>
<option value="add_tag">Добавить порт (tagged / транк)</option>
<option value="del_port">Убрать порт из VLAN</option>
<option value="del_vlan">Удалить VLAN</option>
<option value="show_vlan">Показать VLAN</option>
<option value="show_ports">Показать VLAN на портах</option>
<option value="pvid">PVID порту</option>
<option value="find_mac">Найти MAC в FDB</option>
</select><br>
VLAN: <input id="genVlan" value="135" style="width:70px;">
Порт(ы): <input id="genPorts" placeholder="21 или 26-28" style="width:120px;">
MAC: <input id="genMac" placeholder="00:1A:79:.." style="width:150px;"><br>
Свой образец-шаблон (необязательно; {vlan} {ports} {mac} {ip}): <input id="genTpl" style="width:70%;" placeholder="напр.: config vlan {vlan} add untagged {ports}"><br>
<button class="btn" style="background:#8e44ad;" onclick="genCmd()">🧬 Сгенерировать</button>
<button class="btn" style="background:#3498db;" onclick="copyGen()">📋 Копировать</button>
<button class="btn" style="background:#27ae60;" onclick="runGenSsh()">▶ В SSH-поле</button>
<button class="btn" style="background:#7f8c8d;" onclick="saveGen()">💾 В справочник</button>
<textarea id="genOut" style="width:100%;height:80px;font-family:monospace;margin-top:6px;"></textarea>
</div>
<div class="card"><pre id="out"'''

if 'id="genOut"' not in src:
    old = '<div class="card"><pre id="out"'
    if old in src:
        src = src.replace(old, GEN_CARD, 1)
        print('ok: карточка генератора')
    else:
        print('ПРОПУСК: якорь карточки out')

    GEN_JS = '''
function genCmd(){
  var op=document.getElementById('genOp').value;
  var v=document.getElementById('genVlan').value.trim();
  var p=document.getElementById('genPorts').value.trim();
  var m=document.getElementById('genMac').value.trim();
  var ip=document.getElementById('tgt').value.trim();
  var tpl=document.getElementById('genTpl').value;
  var L=[];
  if(tpl.trim()){
    L.push(tpl.replace(/{vlan}/g,v).replace(/{ports}/g,p).replace(/{mac}/g,m).replace(/{ip}/g,ip));
  } else {
    if(op==='create'){ L.push('create vlan '+v); }
    if(op==='add_untag'){ L.push('config vlan '+v+' add untagged '+p); }
    if(op==='add_tag'){ L.push('config vlan '+v+' add tagged '+p); }
    if(op==='del_port'){ L.push('config vlan '+v+' delete '+p); }
    if(op==='del_vlan'){ L.push('delete vlan '+v); }
    if(op==='show_vlan'){ L.push('show vlan '+v); }
    if(op==='show_ports'){ L.push('show vlan ports '+p); }
    if(op==='pvid'){ L.push('config ports '+p+' pvid '+v); }
    if(op==='find_mac'){ L.push('show fdb '+m); }
  }
  document.getElementById('genOut').value=L.join('\\n');
}
function copyGen(){ navigator.clipboard.writeText(document.getElementById('genOut').value); alert('Скопировано'); }
function runGenSsh(){
  var c=document.getElementById('cmd');
  c.value=(c.value? c.value+'\\n':'')+document.getElementById('genOut').value;
  document.getElementById('tool').value='ssh';
  alert('Команды вставлены в поле SSH — выберите устройство и жмите ▶ Выполнить');
}
function saveGen(){
  var t=prompt('Название в справочнике:','VLAN '+document.getElementById('genVlan').value+': '+document.getElementById('genOp').value);
  if(!t) return;
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:t, category:'генератор', body:document.getElementById('genOut').value, notes:''})})
  .then(function(){ alert('Сохранено в справочник команд'); });
}
</script>'''
    # вставляем JS перед закрывающим </script> страницы tools
    i = src.find('function copyCmd(){ navigator.clipboard.writeText(document.getElementById(\'cmd\').value); alert(\'Команда скопирована\'); }')
    if i >= 0:
        j = src.find('</script>', i)
        src = src[:j] + GEN_JS.replace('</script>', '') + src[j:]
        print('ok: JS генератора')
    else:
        print('ПРОПУСК: якорь copyCmd')
else:
    print('генератор уже есть')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')