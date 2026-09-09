import ast
src = open('swh.py').read()

def slice_replace(start_marker, end_marker, new_body, label):
    global src
    i = src.find(start_marker)
    if i < 0:
        print('  ПРОПУСК:', label); return
    j = src.find(end_marker, i)
    if j < 0:
        print('  ПРОПУСК:', label); return
    src = src[:i] + new_body + src[j+len(end_marker):]
    print('  ok:', label)

def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Правильный fillDevSelect с предвыбором (чинит «саморедактирование»)
slice_replace('function fillDevSelect(sel, pre){', '\n}\n',
"""function fillDevSelect(sel, pre){
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
""", 'fillDevSelect с предвыбором')

# 2) Ручной ввод: сразу адрес + предложение добавить на карту
slice_replace('function devSelect(sel){', '\n}\n',
"""function devSelect(sel){
  if(sel.value==='__manual'){
    var v=prompt('Устройство вручную (имя / IP):');
    if(v){
      var loc=prompt('Адрес этого устройства (или оставьте пустым):','');
      var o=document.createElement('option');
      o.value=v; o.textContent=v+(loc?' · 📍 '+loc:'');
      sel.appendChild(o); sel.value=v;
      if(loc){
        if(confirm('Добавить устройство "'+v+'" на карту сети с этим адресом?')){
          var ipm=v.match(/(\\d{1,3}\\.){3}\\d{1,3}/);
          fetch('/api/network-map',{method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({name:v, ip_address:ipm?ipm[0]:'', location:loc,
              device_type:'switch', total_ports:28,
              position_x:100+Math.random()*400, position_y:100+Math.random()*300})});
        }
        window.devCache=null; window.devArr=[];
      }
    } else { sel.value=''; }
  }
}
""", 'devSelect с адресом и добавлением на карту')

# 3) Кнопка аудита багов нейронкой
rep('<button class="btn btn-primary" onclick="askAiCode()">🧩 С кодом: разработать / проверить</button>',
"""<button class="btn btn-primary" onclick="askAiCode()">🧩 С кодом: разработать / проверить</button>
<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>""", 'кнопка аудита багов')

rep('function askAiCode(){',
"""function auditCode(){
  document.getElementById('aiPrompt').value='Проанализируй прикреплённый код и диагностику: перечисли ВСЕ найденные баги и несоответствия по пунктам, затем дай один исправляющий патч для swh.py между ===PATCH=== и ===END===';
  askAiCode();
}
function askAiCode(){""", 'функция auditCode')

# 4) В режиме редактирования не затираем линию, если устройство пустое
rep("""              var lid=upFields[i].dataset.linkId;
              if(lid && editingId){""",
"""              var lid=upFields[i].dataset.linkId;
              if(!dev && lid){ continue; }
              if(lid && editingId){""", 'защита от затирания устройства uplink')

rep("""              var lid=dlFields[i].dataset.linkId;
              if(lid && editingId){""",
"""              var lid=dlFields[i].dataset.linkId;
              if(!dev && lid){ continue; }
              if(lid && editingId){""", 'защита от затирания устройства downlink')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')