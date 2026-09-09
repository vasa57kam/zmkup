import ast, os, glob, shutil
src = open('swh.py').read()

# 0) САМОРЕМОНТ: если файл бит — откат на последний хороший бэкап
try:
    ast.parse(src)
    print('текущий swh.py цел')
except Exception as e:
    print('swh.py бит:', str(e)[:120], '— откатываюсь на бэкап')
    done = False
    for c in sorted(glob.glob('backups/swh_*.py'), reverse=True):
        t = open(c).read()
        try:
            ast.parse(t)
        except Exception:
            continue
        if 'def admin_apply' in t and 'ADMIN_PIN' in t:
            shutil.copy(c, 'swh.py')
            src = t
            print('ВОССТАНОВЛЕНО из', c)
            done = True
            break
    if not done:
        raise SystemExit('нет хорошего бэкапа!')

def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

def slice_replace(start_marker, end_marker, new_body, label):
    global src
    i = src.find(start_marker)
    if i < 0:
        print('  ПРОПУСК (старт):', label); return
    j = src.find(end_marker, i + len(start_marker))
    if j < 0:
        print('  ПРОПУСК (конец):', label); return
    src = src[:i] + new_body + src[j:]
    print('  ok:', label)

# 1) Нормализатор голосового ввода + умная нарезка
if 'def clarify_wish' not in src:
    helper = '''
def clarify_wish(wish):
    p = ('Ты нормализатор голосового ввода: задачи диктуются голосом для разработчика панели swh.py '
         '(замена коммутаторов: наряды, планировщик портов, FDB-таблицы, карта сети, склад, отчёты, паспорт наряда, админ-центр). '
         'Перепиши диктовку в чёткое техническое задание 1-3 предложения, исправь ошибки распознавания по смыслу '
         '(напр. "паспорт не найден" -> "кнопка Паспорт отдаёт 404", "аплинк" -> "uplink"). '
         'Ответь ТОЛЬКО текстом задания.\\nДиктовка: ' + wish[:1000])
    try:
        r = _ollama_gen(p, 4096, 300).strip()
        return (r or wish)[:1000]
    except Exception:
        return wish

def smart_ctx(wish):
    w = (wish or '').lower()
    keys = []
    if 'паспорт' in w or 'печать' in w or 'отчёт' in w or 'отчет' in w: keys += ['order', 'planner']
    if 'наряд' in w or 'закрыть' in w or 'редакт' in w or 'создать' in w: keys += ['orders', 'order']
    if 'план' in w or 'uplink' in w or 'аплинк' in w or 'downlink' in w or 'даунлинк' in w or 'порт' in w: keys += ['planner']
    if 'fdb' in w or 'фдб' in w or 'мак' in w or 'mac' in w: keys += ['fdb']
    if 'склад' in w or 'статус' in w or 'сбро' in w: keys += ['stock']
    if 'карт' in w or 'адрес' in w or 'устройств' in w or 'свитч' in w: keys += ['map']
    if 'команд' in w or 'справочник' in w: keys += ['admin']
    if 'админ' in w or 'обновлен' in w or 'патч' in w or 'нейрон' in w: keys += ['admin']
    if not keys: keys = ['orders', 'order', 'planner']
    seen = set()
    parts = [routes_list()]
    for k in keys:
        if k in seen or k not in SECTS: continue
        seen.add(k)
        parts.append(code_slice(*SECTS[k]))
    return '\\n\\n'.join(p for p in parts if p)[:40000]

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('ok: clarify_wish + smart_ctx')

# 2) Таймауты ollama
rep('def _ollama_gen(prompt, ctx=16384):', 'def _ollama_gen(prompt, ctx=16384, timeout=900):', 'таймаут-параметр')
rep('r = urllib.request.urlopen(rq, timeout=1800)', 'r = urllib.request.urlopen(rq, timeout=timeout)', 'urlopen с timeout')

# 3) do_ai: умный контекст + фолбэк при таймауте (без ошибок отступов!)
slice_replace("    attach = (payload or {}).get('attach', '')",
"    job_log('[ai] нейронка думает...')",
"""    wish0 = (payload or {}).get('prompt', '')
    clear = clarify_wish(wish0)
    job_log('[ai] задача после нормализации: ' + clear[:150])
    attach = (payload or {}).get('attach', 'smart')
    if attach == 'all':
        ctx = routes_list() + '\\n\\nПОЛНЫЙ КОД (первые 60000 символов):\\n' + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swh.py')).read()[:60000]
        ctxsize = 32768
    elif attach == 'routes':
        ctx = routes_list()
        ctxsize = 8192
    elif attach in SECTS:
        ctx = routes_list() + '\\n\\n' + code_slice(*SECTS[attach])
        ctxsize = 16384
    else:
        ctx = smart_ctx(clear)
        ctxsize = 16384
    job_log('[ai] прикрепляю код: ' + attach + ' (' + str(len(ctx)) + ' симв)')
    prompt = ('Ты разработчик и аудитор панели swh.py (Flask+SQLite, JS внутри шаблонов). '
              'Если нужна правка или функция — дай ГОТОВЫЙ python-патч между ===PATCH=== и ===END=== '
              '(читает swh.py, правит через replace с точными якорями, пишет обратно, в конце ast.parse). '
              'Пояснения кратко по-русски.\\nЗАДАЧА: ' + clear +
              '\\n\\nЖУРНАЛ ИЗМЕНЕНИЙ:\\n' + changelog_text() +
              '\\n\\nРЕЛЕВАНТНЫЙ КОД:\\n' + ctx)
    try:
        text = _ollama_gen(prompt, ctxsize)
    except Exception:
        job_log('[ai] таймаут на большом контексте — переход на умную нарезку')
        ctx = smart_ctx(clear)
        prompt = prompt + '\\n\\nКОД (умная нарезка):\\n' + ctx
        text = _ollama_gen(prompt, 12000, 1200)
""", 'do_ai: умный контекст')

rep("    text = _ollama_gen(prompt, 32768 if attach == 'all' else 16384)",
    "    # text уже получен выше", 'убрать двойной вызов')

# 4) Автономка до 3 попыток
i = src.find('def do_autonomous(payload):')
j = src.find('def passport(', i) if i >= 0 else -1
if i >= 0 and j > i and 'попытка ' not in src[i:j]:
    new_auto = '''def do_autonomous(payload):
    wish = (payload or {}).get('prompt', '') or ''
    job_log('[auto] желание: ' + wish[:200])
    clear = clarify_wish(wish)
    job_log('[auto] после нормализации: ' + clear[:200])
    log_change('user', 'желание: ' + wish[:150])
    base = os.path.dirname(os.path.abspath(__file__))
    ctx = smart_ctx(clear)
    prompt = ('Ты автономный разработчик панели swh.py (Flask+SQLite, JS внутри шаблонов). '
              'Правила: правь ТОЛЬКО через replace с точными якорями из приложенного кода; '
              'НЕ выдумывай библиотеки (никакой SQLAlchemy); не трогай то, что не просили; '
              'в конце ast.parse; между ===PATCH=== и ===END=== — ТОЛЬКО код патча. '
              'Если явно невыполнимо — ответь текстом.\\n'
              'ЗАДАЧА: ' + clear +
              '\\n\\nЖУРНАЛ ИЗМЕНЕНИЙ:\\n' + changelog_text() +
              '\\n\\nДИАГНОСТИКА:\\n' + _diag_text()[:3000] +
              '\\n\\nРЕЛЕВАНТНЫЙ КОД:\\n' + ctx)
    last_gate = ''
    code = ''
    text = ''
    for attempt in (1, 2, 3):
        job_log('[auto] попытка ' + str(attempt) + ': нейронка думает...')
        extra = ('\\n\\nТвой прошлый патч НЕ прошёл sandbox: ' + last_gate[:1200] + '\\nИсправь и дай исправленный патч.') if last_gate else ''
        text = _ollama_gen(prompt + extra, 16384, 1200)
        code = _extract_patch(text)
        if not code.strip():
            job_log('[auto] патча нет — строгий повтор...')
            text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый python-патч между ===PATCH=== и ===END===. Объяснения вместо кода ЗАПРЕЩЕНЫ.', 16384, 1200)
            code = _extract_patch(text)
        if not code.strip():
            JOB['result'] = {'ok': True, 'rc': 0, 'out': 'Нейронка не дала патч (см. ответ).', 'ai': text[:6000]}
            log_change('ai', 'без патча: ' + text[:150].replace('\\n', ' '))
            return
        ok, gate = sandbox_check(code)
        job_log('[auto] sandbox: ' + gate[:150])
        if ok:
            job_log('[auto] применяю к боевому файлу...')
            rc, out = _run_patch_code(code, 'ai-auto')
            JOB['result'] = {'ok': rc == 0, 'rc': rc,
                'out': 'Sandbox OK (попытка ' + str(attempt) + '). Боевой: rc=' + str(rc) + '\\n' + out[-2000:],
                'ai': text[:1500]}
            log_change('ai-auto', 'патч применён (попытка ' + str(attempt) + '), rc=' + str(rc) + ' | ' + wish[:100])
            if rc == 0:
                _restart_later()
            return
        last_gate = gate
    open(os.path.join(base, 'pending_patch.py'), 'w').write(code)
    JOB['result'] = {'ok': False, 'rc': -7,
        'out': '3 попытки, sandbox не пройден. Патч в pending_patch.py. НУЖЕН МАСТЕР.\\n' + last_gate[:1500],
        'ai': text[:3000]}
    log_change('ai', 'НУЖЕН МАСТЕР: ' + last_gate[:200].replace('\\n', ' ') + ' | ' + wish[:100])

'''
    src = src[:i] + new_auto + src[j:]
    print('ok: автономка до 3 попыток')
else:
    print('автономка уже обновлена или не найдена')

# 5) UI: умный режим по умолчанию
rep('<option value="all">📦 Прикрепить: ВСЁ (весь код + диагностика)</option>',
    '<option value="smart" selected>🧠 Прикрепить: умное (релевантное задаче)</option>\n<option value="all">📦 Прикрепить: ВСЁ (долго думает, возможен таймаут)</option>',
    'умный режим по умолчанию')
ajs_path = os.path.join('static', 'admin.js')
if os.path.exists(ajs_path):
    ajs = open(ajs_path).read()
    if "attach:'all'" in ajs:
        ajs = ajs.replace("startJob('ai',{prompt:p, with_diag:withDiag, attach:'all'});",
                          "startJob('ai',{prompt:p, with_diag:withDiag, attach:(document.getElementById('aiAttach')||{value:'smart'}).value});", 1)
        open(ajs_path, 'w').write(ajs)
        print('ok: admin.js берёт режим из селекта')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')