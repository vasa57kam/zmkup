import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Убрать недоделанный генератор из /tools
i = src.find('<b>🧬 Генератор команд (VLAN / порты / MAC)</b>')
if i >= 0:
    j = src.find('<div class="card"><pre id="out"', i)
    if j > i:
        k = src.rfind('<div class="card">', 0, i)
        src = src[:k] + src[j:]
        print('ok: карточка-генератор убрана из tools')
i = src.find('function genCmd(){')
if i >= 0:
    j = src.find('</script>', i)
    if j > i:
        src = src[:i] + src[j:]
        print('ok: JS генератора убран из tools')

# 2) Тулза принимает команду со страницы генератора
if 'gen2tools' not in src:
    rep('function pin(){',
"""var _g=sessionStorage.getItem('gen2tools');
if(_g){
  sessionStorage.removeItem('gen2tools');
  window.addEventListener('DOMContentLoaded', function(){
    document.getElementById('cmd').value=_g;
    document.getElementById('tool').value='ssh';
  });
}
function pin(){""", 'tools: приём из генератора')

# 3) Отдельная страница /gen
if "'/gen'" not in src:
    GEN = '''GEN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 Генератор команд</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}</style></head>
<body>
<div class="card big">🧬 Генератор команд — D-Link L2</div>
<div class="card">
Семейство: <select id="fam" onchange="setFam()"><option value="dlink">D-Link xStack L2 (DES-3200 / DGS-1210)</option><option value="custom">Свой шаблон</option></select>
Операция: <select id="op" onchange="fillTpl()"></select><br>
VLAN: <input id="v" value="135" style="width:70px;">
Порт(ы): <input id="p" placeholder="21 или 26-28" style="width:120px;">
MAC: <input id="m" placeholder="00:1A:79:.." style="width:150px;">
IP: <input id="ip" style="width:130px;">
Текст: <input id="txt" style="width:140px;"><br>
Шаблон (редактируемый): <textarea id="tpl" style="width:100%;height:80px;font-family:monospace;"></textarea>
<button class="btn" style="background:#8e44ad;" onclick="gen()">🧬 Сгенерировать</button>
<button class="btn" style="background:#3498db;" onclick="cpy()">📋 Копировать</button>
<button class="btn" style="background:#27ae60;" onclick="toTools()">🔗 В Тулзу (SSH)</button>
<button class="btn" style="background:#7f8c8d;" onclick="sav()">💾 В справочник</button>
<textarea id="outg" style="width:100%;height:120px;font-family:monospace;margin-top:6px;"></textarea>
</div>
<div class="card"><b>Подсказка:</b> плейсхолдеры {vlan} {ports} {mac} {ip} {text}. Комбо-операции дают несколько строк сразу. «🔗 В Тулзу» передаёт команды в SSH-поле выполнения на свитче.</div>
<script>
var TPL={ dlink:{
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
var NAMES={create:'Создать VLAN',del_vlan:'Удалить VLAN',add_untag:'Добавить порт (untagged)',add_tag:'Добавить порт (tagged/транк)',del_port:'Убрать порт из VLAN',show_vlan:'Показать VLAN',show_ports:'Показать VLAN на портах',pvid:'PVID порту',find_mac:'Найти MAC в FDB',show_fdb:'Показать FDB (всю)',port_off:'Выключить порт',port_on:'Включить порт',save:'Сохранить конфигурацию',reboot:'Перезагрузить свитч',cam:'КОМБО: камера на VLAN',trunk:'КОМБО: транк на ядро'};
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
function cpy(){ navigator.clipboard.writeText(document.getElementById('outg').value); alert('Скопировано'); }
function toTools(){ sessionStorage.setItem('gen2tools', document.getElementById('outg').value); location.href='/tools'; }
function sav(){
  var t=prompt('Название:','Команда: '+(NAMES[document.getElementById('op').value]||document.getElementById('op').value));
  if(!t) return;
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:t, category:'генератор', body:document.getElementById('outg').value, notes:''})})
  .then(function(){ alert('Сохранено в справочник'); });
}
setFam();
</script>
</body></html>"""

@app.route('/gen')
def gen_page():
    return render_template_string(GEN_HTML)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + GEN + src[idx:]
    print('ok: страница /gen')

GEN_LINK = '<a href="/gen" class="nav-link">🧬 Команды</a>'
if GEN_LINK not in src:
    rep('<a href="/tools" class="nav-link">🖥️ Тулза</a>',
        '<a href="/tools" class="nav-link">🖥️ Тулза</a>\n            ' + GEN_LINK,
        'ссылка Генератор в меню')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')