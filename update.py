import ast
src = open('swh.py').read()

def slice_replace(start_marker, end_marker, new_body, label, include_end=False):
    global src
    i = src.find(start_marker)
    if i < 0:
        print('  ПРОПУСК (старт):', label); return False
    j = src.find(end_marker, i + len(start_marker))
    if j < 0:
        print('  ПРОПУСК (конец):', label); return False
    if include_end:
        j += len(end_marker)
    src = src[:i] + new_body + src[j:]
    print('  ok:', label)
    return True

# 1) Эндпоинт линии: PUT всех полей + DELETE (замена по границам маршрутов)
i = src.find("@app.route('/api/links/<int:link_id>'")
if i >= 0 and 'methods=[\'PUT\', \'DELETE\']' not in src[i:i+400]:
    j = src.find('@app.route', i + 10)
    if j > 0:
        new_ep = '''@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def api_link_update(link_id):
    if request.method == 'DELETE':
        conn = get_db()
        conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    data = request.json or {}
    conn = get_db()
    sets = []
    vals = []
    for f in ('old_port', 'new_port', 'upstream_port'):
        if f in data:
            sets.append(f + '=?')
            vals.append(int(data[f]) if data[f] not in ('', None) else 0)
    for f in ('upstream_device', 'link_type'):
        if f in data:
            sets.append(f + '=?')
            vals.append(data[f])
    if sets:
        vals.append(link_id)
        conn.execute('UPDATE links SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})


'''
        src = src[:i] + new_ep + src[j:]
        print('  ok: PUT/DELETE линии заменён целиком')
else:
    print('  эндпоинт линии уже правильный')

# 2) Циклы сохранения линий в форме (замена от старого начала до closeModal)
if 'upFields' not in src:
    s = src.find("const uplinkPorts = document.querySelectorAll('.uplink-port');")
    e = src.find('closeModal();', s) if s >= 0 else -1
    if s >= 0 and e > s:
        new_block = """var upFields=document.querySelectorAll('#uplinksContainer .uplink-field');
            for (let i = 0; i < upFields.length; i++) {
              var port=upFields[i].querySelector('.uplink-port').value;
              var dev=upFields[i].querySelector('.uplink-device').value;
              var up=upFields[i].querySelector('.uplink-upstream-port').value;
              if(!port && !dev) continue;
              var lid=upFields[i].dataset.linkId;
              if(lid && editingId){
                await fetch('/api/links/'+lid,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_port:parseInt(port)||0,upstream_device:dev,upstream_port:parseInt(up)||0})});
              } else {
                await fetch('/api/links/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_port:parseInt(port)||0,upstream_device:dev,upstream_port:parseInt(up)||0,link_type:'uplink'})});
              }
            }
            var dlFields=document.querySelectorAll('#downlinksContainer .uplink-field');
            for (let i = 0; i < dlFields.length; i++) {
              var port2=dlFields[i].querySelector('.dl-port').value;
              var dev2=dlFields[i].querySelector('.dl-device').value;
              var up2=dlFields[i].querySelector('.dl-upstream-port').value;
              var np2=dlFields[i].querySelector('.dl-new-port').value;
              if(!port2 && !dev2) continue;
              var lid2=dlFields[i].dataset.linkId;
              if(lid2 && editingId){
                await fetch('/api/links/'+lid2,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_port:parseInt(port2)||0,upstream_device:dev2,upstream_port:parseInt(up2)||0,new_port:parseInt(np2)||0})});
              } else {
                await fetch('/api/downlinks/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_port:parseInt(port2)||0,upstream_device:dev2,upstream_port:parseInt(up2)||0,new_port:parseInt(np2)||0})});
              }
            }
            if(window.linkDeletes && window.linkDeletes.length){
              for(const did of window.linkDeletes){ await fetch('/api/links/'+did,{method:'DELETE'}); }
              window.linkDeletes=[];
            }
            """
        src = src[:s] + new_block + src[e:]
        print('  ok: циклы сохранения линий заменены')
    else:
        print('  ПРОПУСК: циклы сохранения')
else:
    print('  циклы уже новые')

# 3) rmRow (красная кнопка) — гарантированно
if 'function rmRow' not in src:
    a = src.find('function fillDevSelect(')
    if a >= 0:
        src = src[:a] + """function rmRow(btn){
  var row=btn.closest('.uplink-field');
  if(!row) return;
  if(row.dataset.linkId){
    window.linkDeletes=window.linkDeletes||[];
    window.linkDeletes.push(row.dataset.linkId);
  }
  row.remove();
}
""" + src[a:]
        print('  ok: rmRow добавлена')
    else:
        print('  ПРОПУСК: rmRow')
else:
    print('  rmRow уже есть')

# 4) fillDevSelect с предвыбором — замена целиком по границам функции
i = src.find('function fillDevSelect(')
if i >= 0 and 'if(pre){ sel.value=pre; }' not in src[i:i+1200]:
    j = src.find('\n}\n', i)
    if j > 0:
        new_fd = """function fillDevSelect(sel, pre){
  if(!sel) return;
  devList().then(function(ds){
    var html='<option value="">— выберите устройство —</option><option value="__manual">✏️ Вписать вручную…</option>';
    ds.forEach(function(d){
      html+='<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
    });
    if(pre){
      var ex=false;
      ds.forEach(function(d){ if(d.name===pre){ ex=true; } });
      if(!ex){ html+='<option value="'+pre+'">'+pre+' (текущее)</option>'; }
    }
    sel.innerHTML=html;
    if(pre){ sel.value=pre; }
  });
}
"""
        src = src[:i] + new_fd + src[j+3:]
        print('  ok: fillDevSelect заменён целиком')
    else:
        print('  ПРОПУСК: конец fillDevSelect')
else:
    print('  fillDevSelect уже правильный')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')