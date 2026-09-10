import ast, sqlite3
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# ========== 1) МАСТЕР: поле «Подъезд» у наряда ==========
conn = sqlite3.connect('switch_replacements.db')
for col in ('old_podyezd', 'new_podyezd'):
    try:
        conn.execute('ALTER TABLE work_orders ADD COLUMN ' + col + ' TEXT')
        print('  ok: колонка', col)
    except Exception:
        print('  колонка уже есть:', col)
conn.commit()
conn.close()

rep('''<label>Местоположение:</label>
                <input type="text" id="oldSwitchLocation">''',
'''<label>Местоположение:</label>
                <input type="text" id="oldSwitchLocation">
            </div>
            <div class="form-group">
                <label>Подъезд (старый):</label>
                <input type="text" id="oldPodyezd" placeholder="Напр.: 2">''', 'поле подъезд (старый)')

rep('''<input type="text" id="newSwitchLocation" placeholder="Где стоит / будет стоять">''',
'''<input type="text" id="newSwitchLocation" placeholder="Где стоит / будет стоять">
            </div>
            <div class="form-group">
                <label>Подъезд (новый):</label>
                <input type="text" id="newPodyezd" placeholder="Напр.: 2">''', 'поле подъезд (новый)')

rep("new_switch_location: document.getElementById('newSwitchLocation').value",
"""new_switch_location: document.getElementById('newSwitchLocation').value,
        old_podyezd: document.getElementById('oldPodyezd').value,
        new_podyezd: document.getElementById('newPodyezd').value""", 'подъезды в orderData')

rep("""    cur.execute('UPDATE work_orders SET order_type=?, new_switch_location=? WHERE id=?',
        (data.get('order_type', 'replace'), data.get('new_switch_location', ''), order_id))""",
"""    cur.execute('UPDATE work_orders SET order_type=?, new_switch_location=?, old_podyezd=?, new_podyezd=? WHERE id=?',
        (data.get('order_type', 'replace'), data.get('new_switch_location', ''),
         data.get('old_podyezd', ''), data.get('new_podyezd', ''), order_id))""", 'upsert сохраняет подъезды')

rep("'order_type','new_switch_location','old_switch_model'",
    "'order_type','new_switch_location','old_podyezd','new_podyezd','old_switch_model'", 'PUT: подъезды')

rep("document.getElementById('newSwitchLocation').value=o.new_switch_location||'';",
"""document.getElementById('newSwitchLocation').value=o.new_switch_location||'';
    document.getElementById('oldPodyezd').value=o.old_podyezd||'';
    document.getElementById('newPodyezd').value=o.new_podyezd||'';""", 'editOrder: подъезды')

rep("<p><strong>Адрес:</strong> ${order.old_switch_location || 'Не указан'}</p>",
"""<p><strong>Адрес:</strong> ${order.old_switch_location || 'Не указан'}${order.old_podyezd? ', подъезд '+order.old_podyezd : ''}</p>""", 'наряд: подъезд старого')

rep("<p><strong>Адрес:</strong> ${order.new_switch_location || '—'}</p>",
"""<p><strong>Адрес:</strong> ${order.new_switch_location || '—'}${order.new_podyezd? ', подъезд '+order.new_podyezd : ''}</p>""", 'наряд: подъезд нового')

rep("L.append('Адрес нового: %s' % (o['new_switch_location'] or '—'))",
"""L.append('Адрес нового: %s' % (o['new_switch_location'] or '—'))
    L.append('Подъезды: старый %s / новый %s' % (o['old_podyezd'] or '—', o['new_podyezd'] or '—'))""", 'отчёт: подъезды')

# ========== 2) ЗАКАЛКА КОНВЕЙЕРА ==========
rep("""def _extract_patch(text):
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    return code""",
"""def _extract_patch(text):
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    c = code.strip()
    if c.startswith('diff ') or c.startswith('--- ') or c.startswith('index ') or 'diff --git' in c[:200]:
        return ''
    return code""", 'отсев git-diff формата')

rep('ОБЯЗАН выдать готовый python-патч между ===PATCH=== и ===END===.',
    'ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-скрипт между ===PATCH=== и ===END=== (read/replace/write/ast.parse). Форматы git diff и patch ЗАПРЕЩЕНЫ.',
    'формат только python', all_=True)

rep("_ollama_gen(prompt + extra, 16384, 1200)", "_ollama_gen(prompt + extra, 16384, 900)", 'таймаут попытки 900')
rep("return '\\n\\n'.join(p for p in parts if p)[:40000]",
    "return '\\n\\n'.join(p for p in parts if p)[:30000]", 'умная нарезка 30K')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')