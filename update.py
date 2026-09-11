import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Эндпоинт выполнения инструментов (белый список бинарников, без shell)
if "'/api/tools/run'" not in src:
    ep = '''
@app.route('/api/tools/run', methods=['POST'])
def tools_run():
    import subprocess
    import socket as _sock
    import shutil
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    tool = d.get('tool', '')
    tgt = (d.get('target') or '').strip()
    cmd = d.get('cmd') or ''
    if not tgt and tool != 'ssh':
        return jsonify({'error': 'нет цели'}), 400
    ok_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-_:')
    if tgt and not set(tgt.lower()) <= ok_chars:
        return jsonify({'error': 'цель содержит запрещённые символы'}), 400
    try:
        if tool == 'ping':
            p = subprocess.run(['ping', '-c', '4', tgt], capture_output=True, text=True, timeout=20)
        elif tool == 'nslookup':
            p = subprocess.run(['nslookup', tgt], capture_output=True, text=True, timeout=20)
        elif tool == 'traceroute':
            if not shutil.which('traceroute'):
                return jsonify({'error': 'на сервере нет traceroute: apt-get install -y traceroute'}), 503
            p = subprocess.run(['traceroute', '-n', '-m', '15', tgt], capture_output=True, text=True, timeout=60)
        elif tool == 'tcp':
            port = int(d.get('port') or 23)
            s = _sock.socket(); s.settimeout(5)
            r = s.connect_ex((tgt, port)); s.close()
            return jsonify({'out': ('Порт %d ОТКРЫТ' % port) if r == 0 else ('Порт %d закрыт/недоступен (код %d)' % (port, r))})
        elif tool == 'snmpfdb':
            if not shutil.which('snmpwalk'):
                return jsonify({'error': 'нет snmpwalk: apt-get install -y snmp'}), 503
            p = subprocess.run(['snmpwalk', '-v2c', '-c', d.get('community') or 'public', tgt,
                                '1.3.6.1.2.1.17.7.1.2.2.1.2'], capture_output=True, text=True, timeout=60)
        elif tool == 'ssh':
            if not cmd.strip():
                return jsonify({'error': 'для SSH нужна команда в поле'}), 400
            if not shutil.which('sshpass'):
                return jsonify({'error': 'нет sshpass: apt-get install -y sshpass (или используйте кнопку копирования подключения)'}), 503
            p = subprocess.run(['sshpass', '-p', d.get('pass') or '', 'ssh',
                                '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
                                (d.get('user') or 'admin') + '@' + tgt, cmd],
                               capture_output=True, text=True, timeout=60)
        elif tool == 'curl':
            p = subprocess.run(['curl', '-s', '-m', '10', '-o', '-', tgt if tgt.startswith('http') or tgt.startswith('rtsp') else ('http://' + tgt)],
                               capture_output=True, text=True, timeout=20)
        else:
            return jsonify({'error': 'неизвестный инструмент'}), 400
        out = (p.stdout or '') + (p.stderr or '')
        return jsonify({'out': out[:8000] or '(пусто)', 'rc': p.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'таймаут выполнения'}), 504
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 500


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: /api/tools/run')

# 2) Страница /tools
if "'/tools'" not in src:
    TOOLS = '''TOOLS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🖥️ Тулза</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
button.q{margin:3px;padding:8px 12px;border:1px solid #bbb;border-radius:6px;background:#eef3f7;cursor:pointer;font-size:14px;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}</style></head>
<body>
<div class="card big">🖥️ Тулза — сетевой ящик инструментов</div>
<div class="card">
Устройство: <select id="devSel" onchange="pickDev()"></select>
Цель (IP/имя): <input id="tgt" style="width:150px;">
Инструмент: <select id="tool">
<option value="ping">ping</option>
<option value="nslookup">nslookup (DNS)</option>
<option value="traceroute">traceroute</option>
<option value="tcp">проверка порта (TCP)</option>
<option value="snmpfdb">SNMP: FDB свитча</option>
<option value="ssh">SSH: команда</option>
<option value="curl">HTTP/RTSP проверка (curl)</option>
</select>
Порт: <input id="port" value="23" style="width:60px;">
SSH user: <input id="sshUser" value="admin" style="width:90px;">
SSH pass: <input id="sshPass" type="password" style="width:90px;">
community: <input id="com" value="public" style="width:90px;">
</div>
<div class="card">
<b>⌨️ Команда (для SSH; кнопки вставляют):</b>
<textarea id="cmd" style="width:100%;height:90px;font-family:monospace;"></textarea>
<div id="quickBtns"></div><br>
<button class="btn" style="background:#27ae60;" onclick="runTool()">▶ Выполнить</button>
<button class="btn" style="background:#3498db;" onclick="copyConn()">📋 Скопировать подключение</button>
<button class="btn" style="background:#7f8c8d;" onclick="copyCmd()">📋 Команду</button>
<span id="msg"></span>
</div>
<div class="card"><pre id="out" style="background:#111;color:#0f0;padding:10px;min-height:140px;white-space:pre-wrap;font-size:13px;"></pre></div>
<script>
function pin(){ if(sessionStorage.pinp){ return sessionStorage.pinp; } var p=prompt('PIN:'); sessionStorage.pinp=p; return p; }
function pickDev(){
  var s=document.getElementById('devSel');
  var v=s.value;
  if(v){ document.getElementById('tgt').value=v; }
}
fetch('/api/network-map').then(function(r){return r.json();}).then(function(ds){
  var s=document.getElementById('devSel');
  s.innerHTML='<option value="">— устройство —</option>'+ds.map(function(d){
    return '<option value="'+(d.ip_address||'')+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
  }).join('');
});
var QUICK=['apt install ','apt update','show fdb','show ports','save','reboot','ping ','snmpwalk -v2c -c public ','telnet ','ssh '];
function renderQuick(extra){
  var b=document.getElementById('quickBtns');
  b.innerHTML=QUICK.concat(extra).map(function(t){
    return '<button class="q" onclick="insCmd(this.dataset.c)" data-c="'+t.replace(/"/g,'&quot;')+'">'+t.trim()+'</button>';
  }).join('');
}
fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){
  renderQuick((rows||[]).map(function(c){ return c.title; }).slice(0,12));
  window.cmdDict=rows||[];
}).catch(function(){ renderQuick([]); });
function insCmd(t){
  var c=document.getElementById('cmd');
  var dict=(window.cmdDict||[]).find(function(x){ return x.title===t; });
  c.value += (dict? dict.body : t);
  c.focus();
}
function runTool(){
  document.getElementById('msg').textContent='Выполняю...';
  var body={pin:pin(), tool:document.getElementById('tool').value,
    target:document.getElementById('tgt').value, cmd:document.getElementById('cmd').value,
    port:document.getElementById('port').value, user:document.getElementById('sshUser').value,
    pass:document.getElementById('sshPass').value, community:document.getElementById('com').value};
  fetch('/api/tools/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json();}).then(function(res){
    document.getElementById('msg').textContent='';
    document.getElementById('out').textContent=res.out||res.error||'(пусто)';
  }).catch(function(e){ document.getElementById('msg').textContent=''; document.getElementById('out').textContent='Ошибка: '+e.message; });
}
function copyConn(){
  var t=document.getElementById('tool').value;
  var ip=document.getElementById('tgt').value;
  var u=document.getElementById('sshUser').value;
  var s=(t==='ssh')? ('ssh '+u+'@'+ip) : (t==='tcp'? ('telnet '+ip+' '+document.getElementById('port').value) : ('telnet '+ip));
  navigator.clipboard.writeText(s);
  alert('Скопировано: '+s);
}
function copyCmd(){ navigator.clipboard.writeText(document.getElementById('cmd').value); alert('Команда скопирована'); }
</script>
</body></html>"""

@app.route('/tools')
def tools_page():
    return render_template_string(TOOLS_HTML)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + TOOLS + src[idx:]
    print('ok: страница /tools')

FIELD_LINK = '<a href="/tools" class="nav-link">🖥️ Тулза</a>'
if FIELD_LINK not in src:
    rep('<a href="/field" class="nav-link">📱 Полевой</a>',
        '<a href="/field" class="nav-link">📱 Полевой</a>\n            ' + FIELD_LINK,
        'ссылка Тулза в меню')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')