import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v30_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []

# 1) Гость НЕ пускается на /admin (серверный редирект)
if 'GUEST_ADMIN_REDIRECT_V30' not in src:
    i = src.find('def _global_auth():')
    if i >= 0:
        ends = [x for x in (src.find('\n@app.', i), src.find('\ndef ', i + 20)) if x > 0]
        end = min(ends) if ends else len(src)
        block = src[i:end]
        k = block.rfind('    return None')
        if k >= 0:
            ins = ("    # GUEST_ADMIN_REDIRECT_V30\n"
                   "    if session.get('role') == 'guest' and (request.path == '/admin' or request.path.startswith('/admin/') or request.path.startswith('/api/admin/')):\n"
                   "        if request.path.startswith('/api/'):\n"
                   "            return jsonify({'error': 'admin only'}), 403\n"
                   "        return redirect('/?denied=admin')\n")
            src = src[:i] + block[:k] + ins + block[k:] + src[end:]
            FIXES.append('guest /admin redirect'); print('  ok: гость редиректится с /admin')
    else:
        print('  ПРОПУСК: def _global_auth не найден')

# 2) Жёсткое скрытие опасных кнопок у гостя (MutationObserver, работает для JS-карточек)
if 'guest_hard_js_v30' not in src:
    ep = '''
@app.after_request
def _guest_hard_js_v30(resp):
    try:
        if session.get('role') != 'guest':
            return resp
        if 'text/html' not in (resp.content_type or ''):
            return resp
        t = resp.get_data(as_text=True)
        if 'guest_hard_js_v30' in t:
            return resp
        js = ("<script id='guest_hard_js_v30'>window.__ROLE__='guest';"
              "function _gh30(){document.querySelectorAll('.btn-danger,[onclick*=\"delOrder\"],[onclick*=\"editOrder\"],"
              "[onclick*=\"rmRow\"],[onclick*=\"clearAll\"],[onclick*=\"delSel\"],[onclick*=\"delArticle\"],[onclick*=\"delKbImg\"]')"
              ".forEach(function(e){e.style.display='none';e.disabled=true;});}"
              "document.addEventListener('DOMContentLoaded',_gh30);"
              "new MutationObserver(_gh30).observe(document.documentElement,{childList:true,subtree:true});"
              "</script>")
        t = t.replace('</body>', js + '</body>', 1)
        resp.set_data(t)
    except Exception:
        pass
    return resp


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    FIXES.append('guest hard-hide JS'); print('  ok: MutationObserver-скрытие для гостя')

# 3) Умные подсказки при неверной роли на логине
if 'LOGIN_HINT_V30' not in src:
    src = src.replace("    if ah and _pcheck(ah, p):\n        session['role'] = 'admin'",
                      "    if ah and _pcheck(ah, p) and want == 'admin':\n        session['role'] = 'admin'", 1)
    new_tail = ("    # LOGIN_HINT_V30\n"
                "    if gh and _pcheck(gh, p):\n"
                "        return jsonify({'ok': False, 'error': 'это ГОСТЕВОЙ пароль — нажмите кнопку «Гостевой вход»'}), 401\n"
                "    if ah and _pcheck(ah, p):\n"
                "        return jsonify({'ok': False, 'error': 'это АДМИН-пароль — нажмите «Войти как админ»'}), 401\n"
                "    return jsonify({'ok': False, 'error': 'неверный пароль для выбранной роли'}), 401")
    src2, n = re.subn(r"    # если пароль совпал с гостевым[^\n]*\n    return jsonify\(\{'ok': False, 'error': 'неверный пароль для выбранной роли'\}\), 401",
                      new_tail, src, count=1)
    if n:
        src = src2; FIXES.append('login hints'); print('  ok: подсказки ролей на логине')
    else:
        print('  ПРОПУСК: хвост auth_login не найден')

# 4) Топология: нечёткий поиск устройства для uplink/downlink
if '_resolve_dev_v30' not in src:
    helper = '''
def _resolve_dev_v30(s, by_name, by_ip, devs):
    if not s:
        return None
    s = s.strip()
    if s in by_name:
        return by_name[s]
    ip = _ip_of(s)
    if ip and ip in by_ip:
        return by_ip[ip]
    for d in devs:
        nm = d['name'] or ''
        if nm and (nm in s or s in nm):
            return d
    for d in devs:
        nip = (d['ip_address'] or '').strip()
        if nip and nip in s:
            return d
    return None

'''
    i = src.find('def _topo_data(')
    if i >= 0:
        src = src[:i] + helper + src[i:]
        src2, n = re.subn(r"up = by_name\.get\(l\['upstream_device'\]\)[^\n]*",
                          "up = by_name.get(l['upstream_device']) or by_ip.get(_ip_of(l['upstream_device'])) or _resolve_dev_v30(l['upstream_device'], by_name, by_ip, devs)",
                          src, count=1)
        if n:
            src = src2; FIXES.append('topology fuzzy resolve'); print('  ok: топология — нечёткий поиск устройств')
        else:
            print('  ПРОПУСК: строка up = by_name.get(...) не найдена')
    else:
        print('  ПРОПУСК: def _topo_data не найден')

# 5) Проверка + запись
try:
    ast.parse(src)
    print('  ok: ast.parse swh.py')
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v30_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v30', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v30. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v30_' + TS + '.py')
