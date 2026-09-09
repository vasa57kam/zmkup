import ast
src = open('swh.py').read()
def rep(old, new, label, all_=False):
    global src
    if old in src:
        src = src.replace(old, new) if all_ else src.replace(old, new, 1)
        print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Глобальные хелперы устройств с адресами (все страницы)
if 'function devLocSync' not in src:
    rep("    </script>\n    </body>",
"""    window.devArr=[];
    function devList(){
      if(!window.devCache){
        window.devCache=fetch('/api/network-map').then(function(r){return r.json();}).then(function(ds){ window.devArr=ds; return ds; });
      }
      return window.devCache;
    }
    function devLocSync(s){
      if(!s||!window.devArr){ return ''; }
      for(var i=0;i<window.devArr.length;i++){
        var d=window.devArr[i];
        if(d.name && s.indexOf(d.name)>=0){ return d.location||''; }
        if(d.ip_address && s.indexOf(d.ip_address)>=0){ return d.location||''; }
      }
      return '';
    }
    devList();
    </script>
    </body>""", 'хелперы адресов устройств')

# 2) Форма наряда: устройства выбираются из справочника
rep('        <input type="text" placeholder="Устройство" class="uplink-device">',
    '        <select class="uplink-device" onchange="devSelect(this)"></select>', 'uplink: select')
rep('        <input type="text" placeholder="Куда: свитч / IP" class="dl-device">',
    '        <select class="dl-device" onchange="devSelect(this)"></select>', 'downlink: select')
rep('    container.appendChild(div);',
"""    container.appendChild(div);
    fillDevSelect(div.querySelector('.uplink-device'));""", 'fill uplink select')
rep('    container.appendChild(div);',
"""    container.appendChild(div);
    fillDevSelect(div.querySelector('.dl-device'));""", 'fill downlink select')
if 'function fillDevSelect' not in src:
    rep('function addDownlinkField() {',
"""function fillDevSelect(sel){
  if(!sel) return;
  devList().then(function(ds){
    sel.innerHTML='<option value="">— выберите устройство —</option><option value="__manual">✏️ Вписать вручную…</option>'+ds.map(function(d){
      return '<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
    }).join('');
  });
}
function devSelect(sel){
  if(sel.value==='__manual'){
    var v=prompt('Устройство вручную (имя / IP):');
    if(v){
      var o=document.createElement('option');
      o.value=v; o.textContent=v;
      sel.appendChild(o); sel.value=v;
    } else { sel.value=''; }
  }
}
function addDownlinkField() {""", 'fillDevSelect + devSelect')

# 3) Адреса в таблицах планировщика
rep("<td>${l.upstream_device||'-'}</td><td>${l.upstream_port||'-'}</td>",
    "<td>${l.upstream_device||'-'}${devLocSync(l.upstream_device)?' 📍 '+devLocSync(l.upstream_device):''}</td><td>${l.upstream_port||'-'}</td>",
    'адреса в таблицах планировщика', all_=True)

# 4) Адреса в напоминаниях (замена и установка)
rep("+' → станет с <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b></li>';",
    "+' → станет с <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b> (адрес: '+ (devLocSync(l.upstream_device)||'—') +')</li>';",
    'адрес в uplink-напоминании')
rep("+' → станет на <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b> (в базе: имя «2-й подъезд (снять)» → новое имя/IP)</li>';",
    "+' → станет на <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b> (адрес: '+ (devLocSync(l.upstream_device)||'—') +')</li>';",
    'адрес в downlink-напоминании')
rep("': настроить uplink на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||l.old_port||'??')+'</b></li>';",
    "': настроить uplink на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||l.old_port||'??')+'</b> (адрес: '+(devLocSync(l.upstream_device)||'—')+')</li>';",
    'адрес в напоминании установки uplink')
rep("': настроить линк на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||'?? — назначьте выше!')+'</b></li>';",
    "': настроить линк на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||'?? — назначьте выше!')+'</b> (адрес: '+(devLocSync(l.upstream_device)||'—')+')</li>';",
    'адрес в напоминании установки downlink')

# 5) Адреса на схеме наряда
rep("port там: '+(c.dport||'?')+'</text>'",
    "port там: '+(c.dport||'?')+' 📍 '+(devLocSync(c.dev)||'')+'</text>'",
    'адреса на схеме наряда', all_=True)

# 6) Серверный поиск адреса + адреса в отчёте
if 'def dev_loc' not in src:
    helper = '''
def dev_loc(s):
    if not s:
        return ''
    conn = get_db()
    rows = conn.execute('SELECT name, ip_address, location FROM network_devices').fetchall()
    conn.close()
    for r in rows:
        if r['name'] and r['name'] in s:
            return r['location'] or ''
        if r['ip_address'] and r['ip_address'] in s:
            return r['location'] or ''
    return ''

'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + helper + src[idx:]
    print('  ok: серверный dev_loc')
rep("        L.append('  порт %s (стар) -> порт %s (нов) | %s : порт %s' % (l['old_port'], np, l['upstream_device'], l['upstream_port']))",
"""        loc = dev_loc(l['upstream_device'])
        L.append('  порт %s (стар) -> порт %s (нов) | %s%s : порт %s' % (l['old_port'], np, l['upstream_device'], (' 📍 '+loc) if loc else '', l['upstream_port']))""",
    'адреса в отчёте', all_=True)

# 7) Дашборд «Незакрытые дела» на главной
if 'id="todoBox"' not in src:
    rep('<div style="margin-bottom:1rem;">\n    <input id="orderSearch"',
"""<div id="todoBox" style="background:#fff8e1;border:1px solid #f1c40f;border-radius:8px;padding:1rem;margin-bottom:1rem;"></div>
<div style="margin-bottom:1rem;">
    <input id="orderSearch\"""", 'блок незакрытых дел')
    rep("`).join('');\n        });",
"""`).join('');
            renderTodo(orders);
        });""", 'вызов renderTodo')
    rep('function filterOrders(){ loadOrders(); }',
"""function renderTodo(orders){
  var box=document.getElementById('todoBox');
  if(!box) return;
  var open=orders.filter(function(o){ return o.status!=='closed'; });
  Promise.all(open.map(function(o){
    return fetch('/api/links/'+o.id).then(function(r){return r.json();}).then(function(ls){ return {o:o, ls:ls}; });
  })).then(function(rs){
    var h='<b>⏰ Незакрытые дела:</b><br>';
    rs.forEach(function(x){
      var bu=x.ls.filter(function(l){ return l.link_type==='uplink' && !l.new_port; }).length;
      var bd=x.ls.filter(function(l){ return l.link_type==='downlink' && !l.new_port; }).length;
      if(bu+bd>0){
        h+='<div>🔧 Наряд #'+x.o.order_number+': аплинков без порта: '+bu+', даунлинков: '+bd+' — <a href="/planner/'+x.o.id+'">открыть планировщик</a></div>';
      }
    });
    fetch('/api/inventory').then(function(r){return r.json();}).then(function(inv){
      inv.forEach(function(i){
        if(i.status==='removed'||i.status==='to_reset'){
          h+='<div>📦 '+(i.model||'')+' ('+(i.last_ip||'')+'): '+(i.status==='removed'?'снят, ждёт решения':'НУЖНО СБРОСИТЬ')+' — <a href="/stock">склад</a></div>';
        }
      });
      box.innerHTML=h;
      if(h.indexOf('<div>')<0){ box.innerHTML='<b>👍 Незакрытых дел нет</b>'; }
    });
  }).catch(function(){ box.style.display='none'; });
}
function filterOrders(){ loadOrders(); }""", 'функция renderTodo')

# 8) Копирование команд в один клик
rep("h+='<button class=\"btn btn-danger\" style=\"padding:2px 8px;\" data-id=\"'+c.id+'\" onclick=\"delCmd(this.dataset.id)\">🗑</button>';",
"""h+='<button class="btn btn-danger" style="padding:2px 8px;" data-id="'+c.id+'" onclick="delCmd(this.dataset.id)">🗑</button> ';
      h+='<button class="btn btn-secondary" style="padding:2px 8px;" data-id="'+c.id+'" onclick="copyCmd(this.dataset.id)">📋 копировать</button>';""", 'кнопка копирования команды')
if 'function copyCmd' not in src:
    rep('function loadCmds(){',
"""function copyCmd(id){
  var c=(window.cmdRows||[]).find(function(x){ return String(x.id)===String(id); });
  if(c && navigator.clipboard){
    navigator.clipboard.writeText(c.body||'');
    alert('Команда скопирована в буфер');
  }
}
function loadCmds(){""", 'copyCmd')
    rep("    document.getElementById('cmdList').innerHTML=h||'<p>Справочник пуст</p>';",
"""    window.cmdRows=rows;
    document.getElementById('cmdList').innerHTML=h||'<p>Справочник пуст</p>';""", 'cmdRows для копирования')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')