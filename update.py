# update.py v27: аутентификация (admin + guest), смена паролей, защита маршрутов
import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v27_' + TS + '.py')

src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# --- 1. Импорты: session + werkzeug.security + wraps ---
if 'from flask import' in src and 'session' not in src.split('from flask import')[1].split('\n')[0]:
    src = re.sub(
        r'(from flask import [^\n]+)',
        r'\1, session',
        src, count=1)
    FIXES.append('import session'); print('  ok: import session')

if 'from functools import wraps' not in src:
    rep('import json\n', 'import json\nfrom functools import wraps\n', 'import wraps')

if 'from werkzeug.security' not in src:
    rep('import json\n', 'import json\nfrom werkzeug.security import generate_password_hash, check_password_hash\n', 'import werkzeug.security')

# --- 2. SECRET_KEY из БД (стабильный между перезапусками) ---
if "app.config['SECRET_KEY']" not in src:
    sk_block = '''
# --- АВТОРИЗАЦИЯ: секрет сессий (сохранён в БД) ---
def _get_or_make_secret():
    import secrets as _secrets
    conn = sqlite3.connect('switch_replacements.db')
    r = conn.execute("SELECT content FROM app_notes WHERE note_key='session_secret'").fetchone()
    if r and r[0]:
        s = r[0]
    else:
        s = _secrets.token_hex(32)
        conn.execute("INSERT OR REPLACE INTO app_notes (note_key, content) VALUES ('session_secret', ?)", (s,))
    conn.commit(); conn.close()
    return s
try:
    app.config['SECRET_KEY'] = _get_or_make_secret()
except Exception:
    app.config['SECRET_KEY'] = 'fallback-key-change-me'


def _phash(p):
    return generate_password_hash(p or '', method='pbkdf2:sha256', salt_length=12)

def _pcheck(h, p):
    try: return check_password_hash(h or '', p or '')
    except Exception: return False

def _pw(key):
    try:
        conn = sqlite3.connect('switch_replacements.db')
        r = conn.execute("SELECT content FROM app_notes WHERE note_key=?", (key,)).fetchone()
        conn.close()
        return r[0] if r else None
    except Exception: return None

def _pw_set(key, plaintext):
    conn = sqlite3.connect('switch_replacements.db')
    conn.execute("INSERT OR REPLACE INTO app_notes (note_key, content) VALUES (?, ?)",
                 (key, _phash(plaintext)))
    conn.commit(); conn.close()

# первичная инициализация: если админ-пароль не задан — 'admin'
if not _pw('admin_hash'):
    _pw_set('admin_hash', 'admin')
# гостевой по умолчанию — 'guest'
if not _pw('guest_hash'):
    _pw_set('guest_hash', 'guest')

PUBLIC_PREFIXES = ('/login', '/api/auth/', '/static/', '/uploads/', '/favicon.ico')

def login_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if any(request.path.startswith(p) for p in PUBLIC_PREFIXES):
            return f(*a, **kw)
        if 'role' not in session:
            if request.path.startswith('/api/') or request.method == 'POST':
                return jsonify({'error': 'not logged in'}), 401
            return redirect('/login?next=' + request.path)
        return f(*a, **kw)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*a, **kw):
        if session.get('role') != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'error': 'admin only'}), 403
            return redirect('/login?next=' + request.path)
        return f(*a, **kw)
    return wrapper

@app.before_request
def _global_auth():
    if any(request.path.startswith(p) for p in PUBLIC_PREFIXES):
        return None
    if 'role' not in session:
        if request.path.startswith('/api/') or request.method in ('POST','PUT','DELETE'):
            return jsonify({'error': 'not logged in'}), 401
        if request.path != '/login':
            return redirect('/login?next=' + request.path)
    # админские POST — только админу
    if request.method in ('POST','PUT','DELETE') and request.path.startswith('/api/admin/'):
        if session.get('role') != 'admin':
            return jsonify({'error': 'admin only'}), 403
    return None


LOGIN_HTML = """<!DOCTYPE html>
<html lang=\"ru\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">
<title>Вход — Замена коммутаторов</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:radial-gradient(1200px 700px at 80% -10%,#1a2742 0%,#070d18 60%);font-family:'Segoe UI',system-ui,Arial,sans-serif;color:#eaf2ff;display:flex;align-items:center;justify-content:center}
.card{width:min(420px,94vw);background:#101b30;border:1px solid #2c3f6b;border-radius:18px;padding:28px;box-shadow:0 14px 40px rgba(0,0,0,.45)}
.card h1{margin:0 0 6px;font-size:20px;letter-spacing:.4px}
.card p{color:#93a6c9;font-size:13px;margin:0 0 18px}
input{width:100%;background:#0b1526;border:1px solid #2c3f6b;color:#eaf2ff;border-radius:10px;padding:12px 14px;font-size:15px;margin-bottom:10px}
input:focus{outline:2px solid rgba(76,195,255,.4);border-color:#4cc3ff}
.row{display:flex;gap:8px;margin-top:8px}
button{flex:1;border:none;border-radius:10px;padding:12px;font-weight:700;font-size:14px;cursor:pointer;transition:transform .12s,filter .12s}
button:hover{transform:translateY(-1px);filter:brightness(1.15)}
.b-admin{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff}
.b-guest{background:#1f2d4a;color:#eaf2ff;border:1px solid #2c3f6b}
.b-guest:hover{background:#2a3e62}
.msg{margin-top:10px;padding:10px;border-radius:8px;font-size:13px;display:none}
.msg.err{background:#3a1220;color:#ff9ea8;border:1px solid #7a2535;display:block}
.msg.ok{background:#0f2d20;color:#7ed8a0;border:1px solid #1e6a45;display:block}
.hint{margin-top:14px;color:#7f93b8;font-size:11.5px;text-align:center}
</style></head>
<body>
<form class=\"card\" id=\"f\" onsubmit=\"return doLogin()\">
<h1>🔐 Вход в панель</h1>
<p>Админ-пароль — полный доступ, гостевой — только просмотр.</p>
<input id=\"pwd\" type=\"password\" placeholder=\"Пароль\" autofocus autocomplete=\"current-password\">
<div class=\"row\">
<button type=\"button\" class=\"b-admin\" onclick=\"doLogin('admin')\">👑 Войти как админ</button>
<button type=\"button\" class=\"b-guest\" onclick=\"doLogin('guest')\">👁 Гостевой вход</button>
</div>
<div class=\"msg\" id=\"msg\"></div>
<div class=\"hint\">По умолчанию: admin / guest (смените в админке после входа)</div>
</form>
<script>
function doLogin(role){
  var p=document.getElementById('pwd').value;
  var m=document.getElementById('msg');
  m.className='msg';m.textContent='';
  fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({password:p, role:role})})
  .then(function(r){return r.json();}).then(function(res){
    if(res.ok){
      m.className='msg ok';m.textContent='Вход выполнен: '+res.role;
      var next=new URLSearchParams(location.search).get('next');
      setTimeout(function(){location.href=next||'/';},350);
    } else { m.className='msg err';m.textContent='Ошибка: '+(res.error||'неверный пароль'); }
  }).catch(function(e){ m.className='msg err';m.textContent='Ошибка: '+e.message; });
  return false;
}
document.getElementById('pwd').addEventListener('keydown',function(e){
  if(e.key==='Enter'){e.preventDefault();doLogin('admin');}
});
</script>
</body></html>"""

@app.route('/login')
def login_page():
    return Response(LOGIN_HTML, mimetype='text/html')

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    d = request.json or {}
    p = d.get('password', '')
    want = d.get('role', 'admin')
    ah = _pw('admin_hash')
    gh = _pw('guest_hash')
    if ah and _pcheck(ah, p):
        session['role'] = 'admin'
        session['uid'] = 'admin'
        session.permanent = True
        return jsonify({'ok': True, 'role': 'admin'})
    if gh and _pcheck(gh, p) and want == 'guest':
        session['role'] = 'guest'
        session['uid'] = 'guest'
        session.permanent = True
        return jsonify({'ok': True, 'role': 'guest'})
    # если пароль совпал с гостевым, но нажали админ — отказ
    return jsonify({'ok': False, 'error': 'неверный пароль для выбранной роли'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def auth_logout():
    session.clear()
    return jsonify({'ok': True})

@app.route('/api/auth/whoami')
def auth_whoami():
    return jsonify({'role': session.get('role'), 'ok': bool(session.get('role'))})

@app.route('/api/auth/set_password', methods=['POST'])
def auth_set_password():
    if session.get('role') != 'admin':
        return jsonify({'error': 'admin only'}), 403
    d = request.json or {}
    which = d.get('which')        # 'admin' or 'guest'
    cur   = d.get('current', '')
    new   = d.get('new', '')
    conf  = d.get('confirm', '')
    if which not in ('admin','guest'):
        return jsonify({'error': 'which=admin|guest'}), 400
    if not new or len(new) < 3:
        return jsonify({'error': 'новый пароль слишком короткий (мин. 3)'}), 400
    if new != conf:
        return jsonify({'error': 'пароли не совпадают'}), 400
    if which == 'admin':
        h = _pw('admin_hash')
        if h and not _pcheck(h, cur):
            return jsonify({'error': 'неверный текущий админ-пароль'}), 403
        _pw_set('admin_hash', new)
        return jsonify({'ok': True, 'msg': 'Админ-пароль изменён'})
    else:
        _pw_set('guest_hash', new)
        return jsonify({'ok': True, 'msg': 'Гостевой пароль изменён'})


@app.route('/logout')
def logout_page():
    session.clear()
    return redirect('/login')


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + sk_block + src[idx:]
    FIXES.append('auth endpoints + decorators'); print('  ok: /login, /api/auth/*, декораторы')

# --- 3. Кнопка выхода + блок смены паролей в админке ---
# Добавим ссылку «Выйти» в навбар
if 'id="navLogout"' not in src:
    rep('<a href="/kb" class="nav-link">📖 База знаний</a>',
        '<a href="/kb" class="nav-link">📖 База знаний</a>\n            <a href="/logout" id="navLogout" class="nav-link" style="background:rgba(220,38,38,.25)">🚪 Выйти</a>',
        'nav logout')

# Блок смены паролей — перед закрывающим </div> админского контейнера
if 'id="pwAdminBlock"' not in src:
    pw_block = '''<div class="card" id="pwAdminBlock" style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>🔐 Пароли доступа</h3>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
<div>
<b>Админ-пароль</b> (полный доступ)<br>
Текущий: <input id="pwCurAdmin" type="password" style="width:160px;"><br>
Новый: <input id="pwNewAdmin" type="password" style="width:160px;"><br>
Ещё раз: <input id="pwConfAdmin" type="password" style="width:160px;"><br>
<button class="btn btn-primary" onclick="setPw('admin')">Сменить админ-пароль</button>
</div>
<div>
<b>Гостевой пароль</b> (только просмотр)<br>
Новый: <input id="pwNewGuest" type="password" style="width:160px;"><br>
Ещё раз: <input id="pwConfGuest" type="password" style="width:160px;"><br>
<button class="btn btn-secondary" onclick="setPw('guest')">Сменить гостевой пароль</button>
</div>
</div>
<div id="pwMsg" style="margin-top:8px;color:#7f8c8d;font-size:13px;"></div>
<small style="color:#7f8c8d;">Админ может всё; гость — только смотреть (без записи в БД, без админки, без удаления).</small>
</div>
'''
    rep('<h3>🔄 Автозапуск после ребута и обновлений</h3>',
        pw_block + '<h3>🔄 Автозапуск после ребута и обновлений</h3>',
        'блок смены паролей в админке')

# JS для смены паролей — добавим в admin.js если есть, иначе в inject
ajs_path = 'static/admin.js'
if os.path.exists(ajs_path):
    ajs = open(ajs_path, encoding='utf-8').read()
    if 'function setPw(' not in ajs:
        ajs += '''
function setPw(which){
  var b={which:which};
  if(which==='admin'){
    b.current=document.getElementById('pwCurAdmin').value;
    b.new=document.getElementById('pwNewAdmin').value;
    b.confirm=document.getElementById('pwConfAdmin').value;
  } else {
    b.new=document.getElementById('pwNewGuest').value;
    b.confirm=document.getElementById('pwConfGuest').value;
  }
  var m=document.getElementById('pwMsg');
  fetch('/api/auth/set_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)})
  .then(function(r){return r.json();}).then(function(res){
    m.style.color=res.ok?'#27ae60':'#e74c3c';
    m.textContent=res.ok?res.msg:('Ошибка: '+(res.error||''));
    if(res.ok){
      if(which==='admin'){document.getElementById('pwCurAdmin').value='';document.getElementById('pwNewAdmin').value='';document.getElementById('pwConfAdmin').value='';}
      else{document.getElementById('pwNewGuest').value='';document.getElementById('pwConfGuest').value='';}
    }
  }).catch(function(e){ m.style.color='#e74c3c'; m.textContent='Ошибка: '+e.message; });
}
'''
        open(ajs_path, 'w', encoding='utf-8').write(ajs)
        FIXES.append('admin.js setPw'); print('  ok: admin.js setPw')
else:
    # инжектим прямо в base.html через after_request
    if 'window.setPw' not in src:
        ep = '''
@app.after_request
def _inject_setpw(resp):
    try:
        if 'text/html' in (resp.content_type or '') and 'window.setPw' not in resp.get_data(as_text=True):
            if request.path == '/admin' and 'pwAdminBlock' in resp.get_data(as_text=True):
                t = resp.get_data(as_text=True)
                js = "<script>function setPw(which){var b={which:which};if(which==='admin'){b.current=document.getElementById('pwCurAdmin').value;b.new=document.getElementById('pwNewAdmin').value;b.confirm=document.getElementById('pwConfAdmin').value;}else{b.new=document.getElementById('pwNewGuest').value;b.confirm=document.getElementById('pwConfGuest').value;}var m=document.getElementById('pwMsg');fetch('/api/auth/set_password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(function(r){return r.json();}).then(function(res){m.style.color=res.ok?'#27ae60':'#e74c3c';m.textContent=res.ok?res.msg:('Ошибка: '+(res.error||''));});}</script>"
                t = t.replace('</body>', js + '</body>', 1)
                resp.set_data(t)
    except Exception:
        pass
    return resp


'''
        idx = src.rfind("if __name__ == '__main__':")
        src = src[:idx] + ep + src[idx:]
        FIXES.append('inject setPw'); print('  ok: inject setPw в /admin')

# --- 4. Версия + штамп ---
try:
    ast.parse(src)
    print('  ok: ast.parse swh.py')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v27_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))

open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v27', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v27. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v27_' + TS + '.py')
