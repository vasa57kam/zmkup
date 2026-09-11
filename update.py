import ast, os
src = open('swh.py').read()
def rep(old, new, label, target=None):
    global src
    t = target if target is not None else src
    if old in t:
        t = t.replace(old, new, 1)
        if target is not None:
            pass
        else:
            src = t
        print('  ok:', label)
        return t
    print('  ПРОПУСК:', label)
    return t

# 1) _ollama_gen принимает модель извне
rep('def _ollama_gen(prompt, ctx=16384, timeout=900):',
    'def _ollama_gen(prompt, ctx=16384, timeout=900, model=None):', 'сигнатура с model')
rep("""    model = 'qwen3-coder:30b'
    if model not in tags:
        model = next((t for t in tags if 'qwen' in t.lower()), tags[0])""",
"""    if not model:
        model = 'qwen3-coder:30b'
        if model not in tags:
            model = next((t for t in tags if 'qwen' in t.lower()), tags[0])""", 'model по умолчанию')

# 2) Задачи передают выбранную модель
rep("        text = _ollama_gen(prompt, ctxsize)",
    "        text = _ollama_gen(prompt, ctxsize, 900, (payload or {}).get('model'))", 'ai: модель из payload')
rep("        text = _ollama_gen(prompt, 12000, 1200)",
    "        text = _ollama_gen(prompt, 12000, 1200, (payload or {}).get('model'))", 'ai фолбэк: модель')
rep("        text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-патч между ===PATCH=== и ===END=== (read/replace/write/ast.parse). Форматы git diff и patch ЗАПРЕЩЕНЫ. Пояснения — после патча, кратко.', 16384, 900)",
    "        text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-патч между ===PATCH=== и ===END=== (read/replace/write/ast.parse). Форматы git diff и patch ЗАПРЕЩЕНЫ. Пояснения — после патча, кратко.', 16384, 900, (payload or {}).get('model'))",
    'ai строгий повтор: модель')
rep("        text = _ollama_gen(prompt + extra, 16384, 900)",
    "        text = _ollama_gen(prompt + extra, 16384, 900, (payload or {}).get('model'))", 'автономка: модель')
rep("            text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый python-патч между ===PATCH=== и ===END===. Объяснения вместо кода ЗАПРЕЩЕНЫ.', 16384, 900)",
    "            text = _ollama_gen(prompt + '\\n\\nВАЖНО: ты ОБЯЗАН выдать готовый python-патч между ===PATCH=== и ===END===. Объяснения вместо кода ЗАПРЕЩЕНЫ.', 16384, 900, (payload or {}).get('model'))",
    'автономка строгий: модель')

# 3) Эндпоинт списка моделей
if "'/api/admin/models'" not in src:
    ep = '''
@app.route('/api/admin/models')
def admin_models():
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    return jsonify(_ollama_tags())


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + ep + src[idx:]
    print('ok: /api/admin/models')

# 4) Селект модели в админке
rep('<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>',
    '<select id="aiModel" style="margin-top:.5rem;padding:.5rem;max-width:340px;" title="Модель для задач ИИ"></select>\n<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>',
    'селект модели в HTML')

# 5) admin.js: наполнение селекта + передача модели в payload
ajs_path = os.path.join('static', 'admin.js')
ajs = open(ajs_path).read() if os.path.exists(ajs_path) else ''
if 'aiModel' not in ajs:
    ajs = ajs.replace("function startJob(kind,payload,confirmText){",
"""function startJob(kind,payload,confirmText){
  payload=payload||{};
  payload.model=payload.model||((document.getElementById('aiModel')||{}).value||'');""", 1)
    ajs = ajs.replace("  if(document.getElementById('clList')){ loadCL(); }",
"""  if(document.getElementById('clList')){ loadCL(); }
  var ms=document.getElementById('aiModel');
  if(ms){
    fetch('/api/admin/models?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(tags){
      ms.innerHTML=(tags||[]).map(function(t){
        var fast=(t.indexOf('q4')>=0||t.indexOf('24b')>=0||t.indexOf('20b')>=0||t.indexOf('14b')>=0)?' ⚡быстрее':'';
        return '<option value="'+t+'">'+t+fast+'</option>';
      }).join('');
      if((tags||[]).indexOf('qwen3-coder:30b')>=0){ ms.value='qwen3-coder:30b'; }
    }).catch(function(){});
  }""", 1)
    open(ajs_path, 'w').write(ajs)
    print('ok: admin.js селект модели')
else:
    print('admin.js уже с моделью')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')