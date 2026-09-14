import ast, os
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Весь JS генератора — в статический файл (неубиваемый)
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
var NAMES={create:'Create VLAN',del_vlan:'Delete VLAN',add_untag:'Add port (untagged)',add_tag:'Add port (tagged/trunk)',del_port:'Remove port from VLAN',show_vlan:'Show VLAN',show_ports:'Show VLAN on ports',pvid:'PVID to port',find_mac:'Find MAC in FDB',show_fdb:'Show FDB (all)',port_off:'Disable port',port_on:'Enable port',save:'Save config',reboot:'Reboot switch',cam:'COMBO: camera to VLAN',trunk:'COMBO: trunk to core'};
function setFam(){
  var f=document.getElementById('fam').value;
  var o=document.getElementById('op');
  if(f==='custom'){ o.innerHTML='<option value="custom">Custom template</option>'; }
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
function cpy(){ navigator.clipboard.writeText(document.getElementById('outg').value); alert('Copied'); }
function toTools(){ sessionStorage.setItem('gen2tools', document.getElementById('outg').value); location.href='/tools'; }
function sav(){
  var t=prompt('Name:','Command: '+(NAMES[document.getElementById('op').value]||document.getElementById('op').value));
  if(!t) return;
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({title:t, category:'generator', body:document.getElementById('outg').value, notes:''})})
  .then(function(){ alert('Saved'); });
}
if(document.readyState!=='loading'){ setFam(); }
else { document.addEventListener('DOMContentLoaded', setFam); }
'''
os.makedirs('static', exist_ok=True)
open('static/gen.js', 'w').write(GENJS)
print('ok: static/gen.js')

# 2) Страница /gen: убираем inline-скрипт, подключаем gen.js
i = src.find('GEN_HTML = """')
if i >= 0:
    j = src.find('"""', i + 20)
    if j > 0:
        NEW_GEN = '''GEN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 Command generator</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}</style></head>
<body>
<div class="card big">🧬 Command generator — D-Link L2</div>
<div class="card">
Family: <select id="fam" onchange="setFam()"><option value="dlink">D-Link xStack L2 (DES-3200 / DGS-1210)</option><option value="custom">Custom template</option></select>
Operation: <select id="op" onchange="fillTpl()"></select><br>
VLAN: <input id="v" value="135" style="width:70px;">
Port(s): <input id="p" placeholder="21 or 26-28" style="width:120px;">
MAC: <input id="m" placeholder="00:1A:79:.." style="width:150px;">
IP: <input id="ip" style="width:130px;">
Text: <input id="txt" style="width:140px;"><br>
Template (editable): <textarea id="tpl" style="width:100%;height:80px;font-family:monospace;"></textarea>
<button class="btn" style="background:#8e44ad;" onclick="gen()">🧬 Generate</button>
<button class="btn" style="background:#3498db;" onclick="cpy()">📋 Copy</button>
<button class="btn" style="background:#27ae60;" onclick="toTools()">🔗 To Tools (SSH)</button>
<button class="btn" style="background:#7f8c8d;" onclick="sav()">💾 To reference</button>
<textarea id="outg" style="width:100%;height:120px;font-family:monospace;margin-top:6px;"></textarea>
</div>
<div class="card"><b>Hint:</b> placeholders {vlan} {ports} {mac} {ip} {text}. Combos give multiple lines at once. «🔗 To Tools» sends commands to the SSH execution field.</div>
<script src="/static/gen.js?v=2"></script>
</body></html>"""'''
        src = src[:i] + NEW_GEN + src[j+3:]
        print('ok: /gen на внешнем JS')
else:
    print('ПРОПУСК: GEN_HTML')

# 3) Диагностика: UI-самопроверка страниц и JS-файлов
if "'ui':" not in src:
    rep("'routes_missing': [e for e in ('/', '/map', '/commands', '/admin', '/stock',",
"""'ui': (lambda: {
                **{u: (lambda t: ('ok' if m in t else 'BAD:' + m))(
                    __import__('urllib.request', fromlist=['urlopen']).urlopen('http://localhost:9500' + u, timeout=5).read().decode())
                   for u, m in (('/gen', 'gen.js'), ('/tools', 'runTool'), ('/field', 'Field mode'), ('/', 'orderSearch'), ('/admin', 'admin.js'))},
                **{s: (lambda t: ('ok' if m in t else 'BAD:' + m))(
                    __import__('urllib.request', fromlist=['urlopen']).urlopen('http://localhost:9500' + s, timeout=5).read().decode())
                   for s, m in (('/static/common.js', 'devLocSync'), ('/static/gen.js', 'setFam'), ('/static/admin.js', 'startJob'))}
            })(),
            'routes_missing': [e for e in ('/', '/map', '/commands', '/admin', '/stock',""", 'диагностика: ui-проверка')

# 4) Показ ui в админке
rep("    L.push('Endpoints:');",
"""    L.push('UI:');
    Object.keys(res.ui||{}).forEach(function(k){
      L.push((res.ui[k]==='ok'?'  OK  ':'  BAD ')+k+' -> '+res.ui[k]);
    });
    L.push('Endpoints:');""", 'показ ui в диагностике')

# 5) Аудит нейронки: смотреть пункт ui
rep('ПЕРВЫМ делом проверь пункт routes_missing в диагностике — отсутствующие маршруты wajib восстановить.',
    'ПЕРВЫМ делом проверь пункты routes_missing и ui в диагностике: отсутствующие маршруты восстанови, а для строк BAD:<маркер> найди, почему маркер не найден на странице/в JS-файле, и исправь.',
    'аудит: ui-пункт')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')