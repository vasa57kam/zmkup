import os, ast
src = open('swh.py').read()

old = "body = _json.dumps({'model': model, 'prompt': prompt, 'stream': False}).encode()"
new = "body = _json.dumps({'model': model, 'prompt': prompt, 'stream': False, 'num_ctx': 16384}).encode()"
if old in src:
    src = src.replace(old, new, 1)
    print('ok: num_ctx 16384 (больше контекст)')

if 'def code_slice' not in src:
    helper = '''
def code_slice(a, b):
    base = os.path.dirname(os.path.abspath(__file__))
    t = open(os.path.join(base, 'swh.py')).read()
    i = t.find(a)
    if i < 0:
        return ''
    j = t.find(b, i + 10)
    if j < 0 or j <= i:
        j = i + 20000
    return t[i:j]

def routes_list():
    base = os.path.dirname(os.path.abspath(__file__))
    t = open(os.path.join(base, 'swh.py')).read()
    out = []
    for line in t.split('\\n'):
        s = line.strip()
        if s.startswith('@app.route') or s.startswith('def '):
            out.append(s)
    return '\\n'.join(out)

SECTS = {
    'orders': ('INDEX_HTML = ', 'ORDER_HTML = '),
    'order': ('ORDER_HTML = ', 'PLANNER_HTML = '),
    'planner': ('PLANNER_HTML = ', 'FDB_HTML = '),
    'fdb': ('FDB_HTML = ', 'STOCK_HTML = '),
    'stock': ('STOCK_HTML = ', 'MAP_HTML = '),
    'map': ('MAP_HTML = ', 'ADMIN_HTML = '),
    'admin': ('ADMIN_HTML = ', 'def get_order_number'),
}

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('ok: helpers для вырезки кода')

old_sig = "def do_ai(prompt, with_diag):"
new_sig = "def do_ai(prompt, with_diag, payload=None):"
if old_sig in src:
    src = src.replace(old_sig, new_sig, 1)
    print('ok: сигнатура do_ai')

old_call = "            do_ai(payload.get('prompt', ''), payload.get('with_diag'))"
new_call = "            do_ai(payload.get('prompt', ''), payload.get('with_diag'), payload)"
if old_call in src:
    src = src.replace(old_call, new_call, 1)
    print('ok: вызов do_ai с payload')

k = src.find("    job_log('[ai] нейронка думает...')")
if k > 0 and 'attach' not in src[k-800:k]:
    ins = """    attach = (payload or {}).get('attach', '')
    ctx = ''
    if attach == 'routes':
        ctx = routes_list()
    elif attach in SECTS:
        ctx = routes_list() + '\\n\\n' + code_slice(*SECTS[attach])
    if ctx:
        job_log('[ai] прикрепляю код: ' + attach + ' (' + str(len(ctx)) + ' симв)')
        prompt = prompt + '\\n\\nРЕЛЕВАНТНЫЙ КОД:\\n' + ctx[:40000]
    prompt = ('Ты разрабатываешь и проверяешь панель замены коммутаторов swh.py. '
              'Если нужна правка или новый функционал — дай ГОТОВЫЙ python-патч для swh.py '
              'между ===PATCH=== и ===END=== (читает swh.py, правит через replace с точными '
              'якорями, пишет обратно, в конце ast.parse). Пояснения кратко по-русски. ') + prompt
"""
    src = src[:k] + ins + src[k:]
    print('ok: attach кода в do_ai')

old_inp = '<input type="text" id="aiPrompt" placeholder="Напр.: почему не работает кнопка...">'
if old_inp in src and 'aiAttach' not in src:
    add = old_inp + '''
<select id="aiAttach" style="margin-top:.5rem;padding:.5rem;max-width:420px;">
<option value="routes">Прикрепить: список маршрутов (кратко)</option>
<option value="orders">Прикрепить: код главной (наряды)</option>
<option value="order">Прикрепить: код страницы наряда</option>
<option value="planner">Прикрепить: код планировщика</option>
<option value="fdb">Прикрепить: код FDB-страницы</option>
<option value="stock">Прикрепить: код склада</option>
<option value="map">Прикрепить: код карты сети</option>
<option value="admin">Прикрепить: код админ-центра</option>
</select>
<button class="btn btn-primary" onclick="askAiCode()">🧩 С кодом: разработать / проверить</button>'''
    src = src.replace(old_inp, add, 1)
    print('ok: селект и кнопка')

i = src.find('<script src="/static/admin.js')
if i >= 0 and 'askAiCode' not in src[i:i+500]:
    j = src.find('</script>', i) + len('</script>')
    inline = '''
<script>
function askAiCode(){
  var p=document.getElementById('aiPrompt').value||'Разработай новый функционал для панели';
  var a=document.getElementById('aiAttach').value;
  startJob('ai',{prompt:p, with_diag:true, attach:a});
}
</script>'''
    src = src[:j] + inline + src[j:]
    print('ok: askAiCode')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал')