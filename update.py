import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# ========== 1) ПЕЧАТНЫЙ ПАСПОРТ НАРЯДА ==========
if "'/passport/" not in src:
    PASS = '''PASS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Паспорт наряда {{ o.order_number }}</title>
<style>
body{font-family:Arial,sans-serif;font-size:12px;color:#000;margin:15mm 15mm;}
h1{font-size:18px;margin:0 0 6px;} h2{font-size:14px;margin:14px 0 6px;}
table{width:100%;border-collapse:collapse;margin:6px 0;}
td,th{border:1px solid #000;padding:4px 6px;font-size:11px;text-align:left;vertical-align:top;}
.noprint{margin:0 0 12px;} @media print{.noprint{display:none;}}
</style></head><body>
<div class="noprint">
<button onclick="window.print()" style="padding:8px 16px;font-size:14px;cursor:pointer;">🖨️ Печать</button>
<a href="/order/{{ o.id }}">← К наряду</a>
</div>
<h1>ПАСПОРТ НАРЯДА № {{ o.order_number }}</h1>
<p>Дата: {{ o.created_at }} | Тип: {{ 'новая установка' if o.order_type=='new' else 'сервис' if o.order_type=='service' else 'замена коммутатора' }} | Статус: {{ o.status }}</p>
<h2>1. Оборудование</h2>
<table>
<tr><th></th><th>IP</th><th>Модель</th><th>Портов</th><th>Адрес</th></tr>
<tr><td>Старый</td><td>{{ o.old_switch_ip or '—' }}</td><td>{{ o.old_switch_model or '—' }}</td><td>{{ o.old_switch_ports }}</td><td>{{ o.old_switch_location or '—' }}</td></tr>
<tr><td>Новый</td><td>{{ o.new_switch_ip or '—' }}</td><td>{{ o.new_switch_model or '—' }}</td><td>{{ o.new_switch_ports }}</td><td>{{ o.new_switch_location or '—' }}</td></tr>
</table>
<h2>2. Подключения</h2>
<table><tr><th>Тип</th><th>Порт (стар)</th><th>Порт (нов)</th><th>Устройство</th><th>Адрес устройства</th><th>Порт там</th></tr>
{% for l in links %}<tr><td>{{ 'UPLINK' if l.link_type=='uplink' else 'downlink' }}</td><td>{{ l.old_port }}</td><td>{{ l.new_port or '—' }}</td><td>{{ l.upstream_device }}</td><td>{{ dev_loc(l.upstream_device) or '—' }}</td><td>{{ l.upstream_port }}</td></tr>{% endfor %}
</table>
<h2>3. Абоненты ({{ subs|length }})</h2>
{% if subs %}<table><tr><th>Порт (стар)</th><th>Порт (нов)</th><th>Абонент</th><th>Адрес</th><th>VLAN</th><th>MAC</th></tr>
{% for s in subs %}<tr><td>{{ s.old_port }}</td><td>{{ s.new_port or '—' }}</td><td>{{ s.subscriber_name or '' }}</td><td>{{ s.address or '' }}</td><td>{{ s.vlan or '' }}</td><td>{{ s.mac_address or '' }}</td></tr>{% endfor %}
</table>{% else %}<p>Абонентов нет.</p>{% endif %}
<h2>4. Контроль FDB</h2>
<p>Записей ДО: {{ oldn }} | ПОСЛЕ: {{ newn }} | Потеряно MAC: {{ lost|length }}</p>
{% if lost %}<table><tr><th>MAC</th><th>Порт</th><th>Абонент</th></tr>{% for m in lost %}<tr><td>{{ m[0] }}</td><td>{{ m[1] }}</td><td>{{ m[2] }}</td></tr>{% endfor %}</table>{% endif %}
<h2>5. Чек-лист работ</h2>
<table>{% for s in steps %}<tr><td style="width:10px;text-align:center;">{{ '☑' if (s.done or fl.get(loop.index0)) else '☐' }}</td><td>{{ s.step_text }}</td></tr>{% endfor %}</table>
{% if o.commands_used %}<h2>6. Использованные команды</h2><p>{{ o.commands_used }}</p><p>Нужна была машина: {{ 'ДА' if o.vehicle_needed else 'нет' }}</p>{% endif %}
<h2>Подписи</h2>
<table><tr><td style="height:60px;">Работу выполнил: ____________________</td><td style="height:60px;">Принял: ____________________</td></tr></table>
</body></html>"""

@app.route('/passport/<int:order_id>')
def passport(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    if not o:
        conn.close()
        return 'Наряд не найден', 404
    links = conn.execute('SELECT * FROM links WHERE order_id=? ORDER BY link_type, old_port', (order_id,)).fetchall()
    subs = conn.execute('SELECT * FROM subscribers WHERE order_id=? ORDER BY old_port', (order_id,)).fetchall()
    steps = conn.execute('SELECT * FROM order_steps WHERE order_id=? ORDER BY pos', (order_id,)).fetchall()
    oldf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchall()
    newf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchall()
    conn.close()
    fl = auto_flags(order_id)
    om = {r['mac_address'].upper(): r for r in oldf if r['mac_address']}
    nm = {r['mac_address'].upper(): r for r in newf if r['mac_address']}
    lost = [(m, om[m]['port'], om[m]['subscriber'] or '') for m in sorted(set(om) - set(nm))]
    return render_template_string(PASS_HTML, o=o, links=links, subs=subs,
        steps=steps, fl=fl, oldn=len(oldf), newn=len(newf), lost=lost, dev_loc=dev_loc)


'''
    idx = src.rfind("if __name__ == '__main__':")
    src = src[:idx] + PASS + src[idx:]
    print('ok: паспорт наряда')

rep('<a class="btn btn-secondary" href="/api/report/{{ order_id }}" target="_blank">📄 Отчёт</a>',
    '<a class="btn btn-secondary" href="/api/report/{{ order_id }}" target="_blank">📄 Отчёт</a>\n        <a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>',
    'кнопка паспорта на наряде')

rep('<button class="btn btn-success" onclick="exportReport()">📄 Экспорт отчета</button>',
    '<button class="btn btn-success" onclick="exportReport()">📄 Экспорт отчета</button>\n        <a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>',
    'кнопка паспорта в планировщике')

# ========== 2) АВТО-ПОДТЯГИВАНИЕ ЛИНКОВ ИЗ КАРТЫ ==========
rep('<h3>Старый коммутатор</h3>',
    '<h3>Старый коммутатор <select id="oldFromMap" onchange="fillFromMap(this.value)" style="margin-left:1rem;padding:.4rem;max-width:340px;"><option value="">— взять с карты —</option></select></h3>',
    'селект старого свитча из карты')

rep('function showCreateOrderModal() {',
"""function showCreateOrderModal() {
    devList().then(function(ds){
      var s=document.getElementById('oldFromMap');
      if(s){
        s.innerHTML='<option value="">— взять с карты —</option>'+ds.map(function(d){
          return '<option value="'+d.id+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
        }).join('');
      }
    });""", 'наполнение селекта карты')

rep('function fillDevSelect(sel){',
"""function fillFromMap(devId){
  if(!devId) return;
  Promise.all([devList(), fetch('/api/map-connections').then(function(r){return r.json();})]).then(function(res){
    var ds=res[0], cs=res[1];
    var dev=ds.find(function(d){ return String(d.id)===String(devId); });
    if(!dev) return;
    if(!confirm('Подставить старый свитч из карты: '+dev.name+' (IP, модель, адрес, порты)?')) return;
    document.getElementById('oldSwitchIp').value=dev.ip_address||'';
    document.getElementById('oldSwitchModel').value=dev.model||'';
    document.getElementById('oldSwitchPorts').value=dev.total_ports||28;
    document.getElementById('oldSwitchLocation').value=dev.location||'';
    document.getElementById('uplinksContainer').innerHTML='';
    document.getElementById('downlinksContainer').innerHTML='';
    var n=0;
    cs.forEach(function(c){
      var other=null, portOld=null, portOther=null;
      if(String(c.from_device_id)===String(devId)){
        other=ds.find(function(d){ return d.id===c.to_device_id; });
        portOld=c.from_port; portOther=c.to_port;
      } else if(String(c.to_device_id)===String(devId)){
        other=ds.find(function(d){ return d.id===c.from_device_id; });
        portOld=c.to_port; portOther=c.from_port;
      }
      if(!other) return;
      n++;
      if(other.device_type==='core'){
        addUplinkField();
        var u=document.querySelectorAll('#uplinksContainer .uplink-field');
        var last=u[u.length-1];
        last.querySelector('.uplink-port').value=portOld;
        last.querySelector('.uplink-upstream-port').value=portOther;
        fillDevSelect(last.querySelector('.uplink-device'), other.name);
      } else {
        addDownlinkField();
        var dd=document.querySelectorAll('#downlinksContainer .uplink-field');
        var last2=dd[dd.length-1];
        last2.querySelector('.dl-port').value=portOld;
        last2.querySelector('.dl-upstream-port').value=portOther;
        fillDevSelect(last2.querySelector('.dl-device'), other.name);
      }
    });
    alert('Готово: линий подтянуто с карты: '+n);
  });
}
function fillDevSelect(sel, pre){""", 'fillFromMap + preselect в fillDevSelect')

rep("""    sel.innerHTML='<option value="">— выберите устройство —</option><option value="__manual">✏️ Вписать вручную…</option>'+ds.map(function(d){
      return '<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
    }).join('');
  });""",
"""    sel.innerHTML='<option value="">— выберите устройство —</option><option value="__manual">✏️ Вписать вручную…</option>'+ds.map(function(d){
      return '<option value="'+d.name+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
    }).join('');
    if(pre){
      var ex=false;
      for(var i=0;i<sel.options.length;i++){ if(sel.options[i].value===pre){ ex=true; break; } }
      if(!ex){ var o=document.createElement('option'); o.value=pre; o.textContent=pre; sel.appendChild(o); }
      sel.value=pre;
    }
  });""", 'preselect в fillDevSelect')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')