import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Серверный разбор xlsx/csv + эндпоинт импорта
if "'/api/vlans/import'" not in src:
    IMP = '''VL_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

def _parse_xlsx_bytes(b):
    import zipfile
    import io
    import xml.etree.ElementTree as ET
    z = zipfile.ZipFile(io.BytesIO(b))
    shared = []
    if 'xl/sharedStrings.xml' in z.namelist():
        r = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for si in r.findall(VL_NS + 'si'):
            shared.append(''.join(t.text or '' for t in si.iter(VL_NS + 't')))
    sheet = None
    for n in z.namelist():
        if n.startswith('xl/worksheets/sheet'):
            sheet = n
            break
    if not sheet:
        return []
    r = ET.fromstring(z.read(sheet))
    rows = []
    for row in r.iter(VL_NS + 'row'):
        vals = []
        for c in row.findall(VL_NS + 'c'):
            t = c.get('t')
            v = c.find(VL_NS + 'v')
            isv = c.find(VL_NS + 'is')
            if t == 's' and v is not None:
                vals.append(shared[int(v.text)])
            elif t == 'inlineStr' and isv is not None:
                vals.append(''.join(x.text or '' for x in isv.iter(VL_NS + 't')))
            elif v is not None:
                vals.append(v.text or '')
            else:
                vals.append('')
        rows.append(vals)
    return rows

def _parse_csv_bytes(b):
    t = None
    for enc in ('utf-8-sig', 'cp1251', 'utf-8'):
        try:
            t = b.decode(enc)
            break
        except Exception:
            continue
    if t is None:
        t = b.decode('utf-8', 'ignore')
    rows = []
    for line in t.splitlines():
        if not line.strip():
            continue
        sep = '\\t' if '\\t' in line else (';' if line.count(';') >= line.count(',') else ',')
        rows.append([x.strip().strip('"') for x in line.split(sep)])
    return rows

@app.route('/api/vlans/import', methods=['POST'])
def vlans_import():
    import json as _json
    if request.form.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'нет файла'}), 400
    b = f.read()
    fn = (f.filename or '').lower()
    try:
        if fn.endswith('.xlsx'):
            rows = _parse_xlsx_bytes(b)
        elif fn.endswith('.csv') or fn.endswith('.txt'):
            rows = _parse_csv_bytes(b)
        else:
            return jsonify({'error': 'нужен .xlsx или .csv'}), 400
    except Exception as e:
        return jsonify({'error': 'разбор файла: ' + str(e)[:200]}), 400
    conn = get_db()
    n = 0
    for r in rows:
        if len(r) < 4:
            continue
        region = (r[0] or '').strip()
        ip = (r[1] or '').strip()
        seg = (r[2] or '').strip()
        vl = (r[3] or '').strip()
        if not vl.isdigit():
            continue
        if region.lower().startswith('район'):
            continue
        conn.execute('INSERT OR REPLACE INTO region_vlans (region, switch_ip, segment, vlan) VALUES (?,?,?,?)',
                     (region, ip, seg, int(vl)))
        n += 1
    conn.commit()
    allr = conn.execute('SELECT region, switch_ip, segment, vlan FROM region_vlans ORDER BY region, vlan').fetchall()
    conn.close()
    try:
        import os as _os
        _os.makedirs('static', exist_ok=True)
        open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'static', 'vlans.js'), 'w').write(
            'var VLAN_DATA=' + _json.dumps([[x['region'], x['switch_ip'], x['segment'], x['vlan']] for x in allr], ensure_ascii=False) + ';')
    except Exception:
        pass
    return jsonify({'ok': True, 'added': n, 'total': len(allr)})


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + IMP + src[idx:]
    print('ok: эндпоинт импорта xlsx/csv')

# 2) Карточка импорта на странице /vlans
if 'id="impFile"' not in src:
    rep('<div class="card"><b>➕ Добавить строку</b>',
"""<div class="card"><b>📥 Импорт файла (xlsx / csv)</b><br>
<input type="file" id="impFile" accept=".xlsx,.csv,.txt">
<button class="btn" style="background:#8e44ad;" onclick="impVlans()">Загрузить и импортировать</button>
<span id="impMsg"></span>
<div style="color:#7f8c8d;font-size:13px;margin-top:4px;">Колонки: Район | IP свитча | Сегмент | Номер VLAN (как в вашем файле). Повторный импорт обновляет строки без дублей.</div></div>
<div class="card"><b>➕ Добавить строку</b>""", 'карточка импорта')

    rep('function addRow(){',
"""function impVlans(){
  var inp=document.getElementById('impFile');
  var f=inp.files[0];
  if(!f){ alert('Выберите файл xlsx или csv'); return; }
  var fd=new FormData();
  fd.append('file', f);
  fd.append('pin', localStorage.getItem('swhpin')||prompt('PIN:')||'');
  document.getElementById('impMsg').textContent='Импортирую...';
  fetch('/api/vlans/import',{method:'POST', body:fd}).then(function(r){return r.json();}).then(function(res){
    document.getElementById('impMsg').textContent=res.ok? ('Готово: добавлено '+res.added+', всего '+res.total) : ('Ошибка: '+(res.error||''));
    if(res.ok){ load(); }
  }).catch(function(e){ document.getElementById('impMsg').textContent='Ошибка: '+e.message; });
}
function addRow(){""", 'JS impVlans')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')