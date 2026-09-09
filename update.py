import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Песочница + автономный режим
if 'def sandbox_check' not in src:
    infra = '''
def sandbox_check(patch_code):
    import subprocess
    import shutil
    base = os.path.dirname(os.path.abspath(__file__))
    sd = os.path.join(base, 'sandbox')
    if os.path.isdir(sd):
        shutil.rmtree(sd)
    os.makedirs(sd)
    shutil.copy(os.path.join(base, 'swh.py'), os.path.join(sd, 'swh.py'))
    try:
        shutil.copy(os.path.join(base, 'switch_replacements.db'), os.path.join(sd, 'switch_replacements.db'))
    except Exception:
        pass
    if os.path.isdir(os.path.join(base, 'static')):
        shutil.copytree(os.path.join(base, 'static'), os.path.join(sd, 'static'))
    open(os.path.join(sd, 'patch.py'), 'w').write(patch_code)
    checker = """
import ast, sys
src = open('swh.py').read()
ast.parse(src)
import importlib.util
spec = importlib.util.spec_from_file_location('swh_test', 'swh.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
c = m.app.test_client()
urls = ['/', '/map', '/commands', '/admin', '/api/orders', '/api/inventory', '/api/network-map', '/api/commands']
bad = []
for u in urls:
    try:
        r = c.get(u)
        if r.status_code != 200:
            bad.append(u + ':' + str(r.status_code))
    except Exception:
        bad.append(u + ':ERR')
if bad:
    print('SMOKE FAIL ' + str(bad))
    sys.exit(2)
print('SMOKE OK')
"""
    open(os.path.join(sd, 'check.py'), 'w').write(checker)
    try:
        p1 = subprocess.run(['python3', 'patch.py'], cwd=sd, capture_output=True, text=True, timeout=180)
    except Exception as e:
        return False, 'патч завис: ' + str(e)[:200]
    if p1.returncode != 0:
        return False, 'ошибка патча: ' + (p1.stderr or p1.stdout)[-500:]
    try:
        p2 = subprocess.run(['python3', 'check.py'], cwd=sd, capture_output=True, text=True, timeout=180)
    except Exception as e:
        return False, 'проверка зависла: ' + str(e)[:200]
    out2 = (p2.stdout or '') + (p2.stderr or '')
    if p2.returncode != 0 or 'SMOKE OK' not in out2:
        return False, 'sandbox: ' + out2[-600:]
    return True, 'sandbox: SMOKE OK'

def _extract_patch(text):
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    return code

def do_autonomous(payload):
    wish = (payload or {}).get('prompt', '') or ''
    job_log('[auto] желание: ' + wish[:200])
    base = os.path.dirname(os.path.abspath(__file__))
    full = open(os.path.join(base, 'swh.py')).read()
    prompt = ('Ты автономный разработчик панели swh.py (Flask+SQLite, JS внутри шаблонов). '
              'Правила: правь ТОЛЬКО через replace с точными якорями из приложенного кода; '
              'НЕ выдумывай библиотеки (никакой SQLAlchemy); не трогай то, что не просили; '
              'в конце ast.parse; между ===PATCH=== и ===END=== — ТОЛЬКО код патча. '
              'Если желание непонятно или невыполнимо — НЕ выдумывай, ответь текстом.\\n'
              'ЖЕЛАНИЕ/БАГ: ' + wish +
              '\\n\\nЖУРНАЛ ИЗМЕНЕНИЙ:\\n' + changelog_text() +
              '\\n\\nДИАГНОСТИКА:\\n' + _diag_text()[:4000] +
              '\\n\\nПОЛНЫЙ КОД swh.py:\\n' + full[:100000])
    job_log('[auto] нейронка думает...')
    text = _ollama_gen(prompt, 32768)
    code = _extract_patch(text)
    if not code.strip():
        JOB['result'] = {'ok': True, 'rc': 0, 'out': 'Нейронка ответила без патча (см. ответ).', 'ai': text[:6000]}
        log_change('ai', 'ответ без патча: ' + text[:150].replace('\\n', ' '))
        return
    ok, gate = sandbox_check(code)
    job_log('[auto] sandbox: ' + gate[:200])
    if not ok:
        job_log('[auto] авто-повтор с фидбеком ошибки...')
        prompt2 = prompt + '\\n\\nТвой прошлый патч НЕ прошёл sandbox: ' + gate[:1500] + '\\nИсправь и дай исправленный патч.'
        text2 = _ollama_gen(prompt2, 32768)
        code2 = _extract_patch(text2)
        if code2.strip():
            ok2, gate2 = sandbox_check(code2)
            if ok2:
                code, text, ok, gate = code2, text2, ok2, gate2
            else:
                gate = gate + ' | повтор: ' + gate2
    if ok:
        job_log('[auto] применяю к боевому файлу...')
        rc, out = _run_patch_code(code, 'ai-auto')
        JOB['result'] = {'ok': rc == 0, 'rc': rc,
            'out': 'Sandbox OK. Боевой: rc=' + str(rc) + '\\n' + out[-2000:], 'ai': text[:2000]}
        log_change('ai-auto', 'патч применён (sandbox OK), rc=' + str(rc) + ' | ' + wish[:100])
        if rc == 0:
            _restart_later()
    else:
        open(os.path.join(base, 'pending_patch.py'), 'w').write(code)
        JOB['result'] = {'ok': False, 'rc': -7,
            'out': 'Sandbox НЕ пройден, патч НЕ применён. Сохранён в pending_patch.py. НУЖЕН МАСТЕР.\\n' + gate[:1500],
            'ai': text[:3000]}
        log_change('ai', 'НУЖЕН МАСТЕР: sandbox: ' + gate[:200].replace('\\n', ' ') + ' | желание: ' + wish[:100])

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + infra + src[idx:]
    print('ok: песочница + автономный режим')
else:
    print('автономка уже есть')

# 2) Вид задачи в job-воркере
rep("        elif kind == 'ai':",
"""        elif kind == 'auto':
            do_autonomous(payload)
        elif kind == 'ai':""", 'job kind auto')

# 3) Кнопка автономки
rep('<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>',
"""<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>
<button class="btn btn-success" onclick="autoWish()">🤖 Автономка: воплотить желание</button>""", 'кнопка автономки')

rep('function auditCode(){',
"""function autoWish(){
  var p=document.getElementById('aiPrompt').value;
  if(!p || !p.trim()){ p='Выполни последнее желание из журнала изменений (строка, начинающаяся с ХОЧУ:). Если такого нет - ответь текстом, что желаний нет.'; }
  startJob('auto',{prompt:p});
}
function auditCode(){""", 'JS autoWish')

# 4) Подсказка про ХОЧУ: в журнале
rep('placeholder="Напр.: после сохранения наряда исчезает uplink-устройство..."',
    'placeholder="Напр.: ХОЧУ: чтобы кнопка Закрыть наряд работала... или описание бага"', 'подсказка ХОЧУ')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')