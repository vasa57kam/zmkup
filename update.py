import ast, os, sqlite3
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Таблица журнала изменений
conn = sqlite3.connect('switch_replacements.db')
conn.execute('''CREATE TABLE IF NOT EXISTS change_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT, author TEXT, text TEXT)''')
conn.commit()
conn.close()
print('ok: таблица change_log')

# 2) Хелпер журнала + чтение для промптов
if 'def changelog_text' not in src:
    helper = '''
def log_change(author, text):
    conn = get_db()
    conn.execute('INSERT INTO change_log (ts, author, text) VALUES (?,?,?)',
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), author, text))
    conn.commit()
    conn.close()

def changelog_text(n=15):
    conn = get_db()
    rows = conn.execute('SELECT ts, author, text FROM change_log ORDER BY id DESC LIMIT ?', (n,)).fetchall()
    conn.close()
    return '\\n'.join('%s [%s] %s' % (r['ts'], r['author'], r['text']) for r in reversed(rows)) or '(журнал пуст)'

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('ok: log_change/changelog_text')

# 3) Автозапись в журнал при каждом применении патча
rep("    log_update(source, rc, out, code)\n    return rc, out",
"""    log_update(source, rc, out, code)
    log_change(source, 'патч rc=%s: %s' % (rc, (out or '')[:200].replace('\\n', ' ')))
    return rc, out""", 'журнал при применении патчей')

# 4) Нейронка читает журнал перед анализом
rep("    job_log('[ai] нейронка думает...')",
"""    prompt = prompt + '\\n\\nЖУРНАЛ ИЗМЕНЕНИЙ (последние записи):\\n' + changelog_text()
    job_log('[ai] нейронка думает...')""", 'журнал в ai-промпт')
rep("    job_log('[selfheal] нейронка думает (минуты)...')",
"""    prompt = prompt + '\\n\\nЖУРНАЛ ИЗМЕНЕНИЙ (последние записи):\\n' + changelog_text()
    job_log('[selfheal] нейронка думает (минуты)...')""", 'журнал в selfheal-промпт')

# 5) «Прикрепить ВСЁ» + большой контекст
rep("    elif attach in SECTS:",
"""    elif attach == 'all':
        ctx = routes_list() + '\\n\\nПОЛНЫЙ КОД swh.py (первые 100000 символов):\\n' + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swh.py')).read()[:100000]
    elif attach in SECTS:""", 'attach=all')
rep('def _ollama_gen(prompt):', 'def _ollama_gen(prompt, ctx=16384):', 'ctx-параметр')
rep("'stream': False, 'num_ctx': 16384}).encode()", "'stream': False, 'num_ctx': ctx}).encode()", 'num_ctx из параметра')
rep("    job_log('[ai] нейронка думает...')\n    text = _ollama_gen(prompt)",
    "    job_log('[ai] нейронка думает...')\n    text = _ollama_gen(prompt, 32768 if attach == 'all' else 16384)", 'большой контекст для ВСЁ')
rep('<option value="routes">Прикрепить: список маршрутов (кратко)</option>',
    '<option value="all">📦 Прикрепить: ВСЁ (весь код + диагностика)</option>\n<option value="routes">Прикрепить: список маршрутов (кратко)</option>',
    'опция ВСЁ в селекте')

# 6) Кнопки по умолчанию шлют ВСЁ
rep("function auditCode(){",
"""function auditCode(){
  var s=document.getElementById('aiAttach');
  if(s){ s.value='all'; }""", 'аудит = весь код')
ajs_path = os.path.join('static', 'admin.js')
if os.path.exists(ajs_path):
    ajs = open(ajs_path).read()
    old_aj = "startJob('ai',{prompt:p, with_diag:withDiag});"
    if old_aj in ajs:
        ajs = ajs.replace(old_aj, "startJob('ai',{prompt:p, with_diag:withDiag, attach:'all'});", 1)
        open(ajs_path, 'w').write(ajs)
        print('ok: Спросить Qwen теперь прикрепляет ВСЁ')
    else:
        print('admin.js: уже с attach')
else:
    print('admin.js не найден')

# 7) UI журнала изменений в админке
if 'id="clList"' not in src:
    rep('<div id="histBox"',
"""<div style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>📝 Журнал изменений (связь вы ↔ нейронка ↔ мастер)</h3>
<p style="color:#7f8c8d;font-size:.9rem;">Опишите проблему своими словами — нейронка читает журнал при каждом анализе, все применённые патчи пишутся сюда сами. Мастеру достаточно показать журнал.</p>
<textarea id="clText" style="width:100%;height:70px;" placeholder="Напр.: после сохранения наряда исчезает uplink-устройство..."></textarea>
<button class="btn btn-primary" onclick="addCL()">➕ Добавить в журнал</button>
<div id="clList" style="margin-top:.5rem;max-height:220px;overflow:auto;"></div>
</div>
<div id="histBox\"""", 'UI журнала')
    rep('function askAiCode(){',
"""function loadCL(){
  fetch('/api/changelog?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(rows){
    var h='';
    rows.forEach(function(x){
      h+='<div style="background:#f8f9fa;padding:.4rem;margin:.2rem 0;border-radius:4px;"><small>'+x.ts+' ['+x.author+']</small> '+x.text+'</div>';
    });
    document.getElementById('clList').innerHTML=h||'<small>Журнал пуст</small>';
  });
}
function addCL(){
  var t=document.getElementById('clText').value;
  if(!t.trim()) return;
  fetch('/api/changelog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:getPin(),author:'user',text:t})}).then(function(){
    document.getElementById('clText').value='';
    loadCL();
  });
}
function askAiCode(){""", 'JS журнала')
    rep("  logLine('Страница загружена, JS жив.');",
"""  logLine('Страница загружена, JS жив.');
  if(document.getElementById('clList')){ loadCL(); }""", 'журнал грузится при входе')

# 8) Эндпоинты журнала
if "'/api/changelog'" not in src:
    ep = '''
@app.route('/api/changelog', methods=['GET', 'POST'])
def changelog_api():
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        conn = get_db()
        rows = conn.execute('SELECT ts, author, text FROM change_log ORDER BY id DESC LIMIT 50').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    log_change(d.get('author', 'user'), d.get('text', ''))
    return jsonify({'success': True})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: эндпоинты журнала')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')