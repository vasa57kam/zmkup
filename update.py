import ast
src = open('swh.py').read()
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) Кнопки редактирования на карточке наряда и в шапке наряда
rep('<button class="btn btn-danger" style="padding:2px 8px;font-size:12px;float:right;" onclick="event.stopPropagation();delOrder(${order.id})">🗑</button>',
    """<button class="btn btn-secondary" style="padding:2px 8px;font-size:12px;float:right;margin-left:4px;" onclick="event.stopPropagation();editOrder(${order.id})">✏️</button>
                    <button class="btn btn-danger" style="padding:2px 8px;font-size:12px;float:right;" onclick="event.stopPropagation();delOrder(${order.id})">🗑</button>""",
    'кнопка ✏️ на карточке наряда')

rep('<a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>',
    """<a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>
        <button class="btn btn-primary" onclick="editOrder({{ order_id }})">✏️ Редактировать</button>""",
    'кнопка ✏️ в шапке наряда')

# 2) Модалка редактирования (переиспользуем ту же форму, но с другим заголовком и PUT)
rep("""<div id="createOrderModal" class="modal">
    <div class="modal-content">
        <h2>📝 Новый наряд</h2>
        <form id="createOrderForm">""",
"""<div id="createOrderModal" class="modal">
    <div class="modal-content">
        <h2 id="orderModalTitle">📝 Новый наряд</h2>
        <form id="createOrderForm">
        <input type="hidden" id="editingOrderId" value="">""",
    'модалка: заголовок + скрытое id')

rep("function showCreateOrderModal() {",
"""var editingId=null;
function showCreateOrderModal() {
    editingId=null;
    document.getElementById('orderModalTitle').textContent='📝 Новый наряд';
    document.getElementById('editingOrderId').value='';""",
    'showCreateOrderModal: сброс режима')

rep("function closeModal() {",
"""function editOrder(id){
  editingId=id;
  fetch('/api/orders/'+id).then(function(r){return r.json();}).then(function(o){
    document.getElementById('orderModalTitle').textContent='✏️ Редактировать наряд №'+(o.order_number||id);
    document.getElementById('editingOrderId').value=id;
    document.getElementById('orderNumber').value=o.order_number||'';
    document.getElementById('orderType').value=o.order_type||'replace';
    document.getElementById('oldSwitchIp').value=o.old_switch_ip||'';
    document.getElementById('oldSwitchModel').value=o.old_switch_model||'';
    document.getElementById('oldSwitchPorts').value=o.old_switch_ports||28;
    document.getElementById('oldSwitchLocation').value=o.old_switch_location||'';
    document.getElementById('newSwitchIp').value=o.new_switch_ip||'';
    document.getElementById('newSwitchModel').value=o.new_switch_model||'';
    document.getElementById('newSwitchPorts').value=o.new_switch_ports||28;
    document.getElementById('newSwitchLocation').value=o.new_switch_location||'';
    document.getElementById('uplinksContainer').innerHTML='';
    document.getElementById('downlinksContainer').innerHTML='';
    uplinkCount=0;
    document.getElementById('createOrderModal').style.display='block';
    return fetch('/api/links/'+id).then(function(r){return r.json();});
  }).then(function(links){
    (links||[]).forEach(function(l){
      if(l.link_type==='uplink'){
        addUplinkField();
        var u=document.querySelectorAll('#uplinksContainer .uplink-field');
        var last=u[u.length-1];
        last.querySelector('.uplink-port').value=l.old_port||'';
        last.querySelector('.uplink-upstream-port').value=l.upstream_port||'';
        fillDevSelect(last.querySelector('.uplink-device'), l.upstream_device||'');
        last.dataset.linkId=l.id;
      } else {
        addDownlinkField();
        var dd=document.querySelectorAll('#downlinksContainer .uplink-field');
        var last2=dd[dd.length-1];
        last2.querySelector('.dl-port').value=l.old_port||'';
        last2.querySelector('.dl-new-port').value=l.new_port||'';
        last2.querySelector('.dl-upstream-port').value=l.upstream_port||'';
        fillDevSelect(last2.querySelector('.dl-device'), l.upstream_device||'');
        last2.dataset.linkId=l.id;
      }
    });
  });
}
function closeModal() {""",
    'editOrder: загрузка данных наряда')

# 3) Submit формы: POST или PUT + обновление линий
rep("""        const response = await fetch('/api/orders-upsert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(orderData)
        });
        
        const result = await response.json();
        if (result.success) {""",
"""        var targetId = editingId;
        var response;
        if(editingId){
          response = await fetch('/api/orders/'+editingId, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(orderData)
          });
        } else {
          response = await fetch('/api/orders-upsert', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(orderData)
          });
        }
        
        const result = await response.json();
        if (result.success || response.ok) {
          if(!targetId){ targetId = result.order_id; }""",
    'submit: ветка PUT для редактирования')

rep("""            for (let i = 0; i < uplinkPorts.length; i++) {
                if (uplinkPorts[i].value) {
                    await fetch(`/api/links/${result.order_id}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            old_port: uplinkPorts[i].value,
                            upstream_device: uplinkDevices[i].value,
                            upstream_port: uplinkUpstreamPorts[i].value
                        })
                    });
                }
            }
            
            const dlPorts = document.querySelectorAll('.dl-port');""",
"""            var upFields=document.querySelectorAll('#uplinksContainer .uplink-field');
            for (let i = 0; i < upFields.length; i++) {
              var port=upFields[i].querySelector('.uplink-port').value;
              var dev=upFields[i].querySelector('.uplink-device').value;
              var up=upFields[i].querySelector('.uplink-upstream-port').value;
              if(!port) continue;
              var lid=upFields[i].dataset.linkId;
              if(lid && editingId){
                await fetch('/api/links/'+lid,{method:'PUT',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up})});
              } else {
                await fetch('/api/links/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,link_type:'uplink'})});
              }
            }
            const dlPorts = document.querySelectorAll('.dl-port');""",
    'uplink: PUT существующих или POST новых')

rep("""            for (let i = 0; i < dlPorts.length; i++) {
                if (dlPorts[i].value) {
                    await fetch(`/api/downlinks/${result.order_id}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            old_port: dlPorts[i].value,
                            upstream_device: dlDevices[i].value,
                            upstream_port: dlUp[i].value,
                            new_port: dlNew[i].value
                        })
                    });
                }
            }
            closeModal();
            loadOrders();""",
"""            var dlFields=document.querySelectorAll('#downlinksContainer .uplink-field');
            for (let i = 0; i < dlFields.length; i++) {
              var port=dlFields[i].querySelector('.dl-port').value;
              var dev=dlFields[i].querySelector('.dl-device').value;
              var up=dlFields[i].querySelector('.dl-upstream-port').value;
              var np=dlFields[i].querySelector('.dl-new-port').value;
              if(!port && !dev) continue;
              var lid=dlFields[i].dataset.linkId;
              if(lid && editingId){
                await fetch('/api/links/'+lid,{method:'PUT',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,new_port:np})});
              } else {
                await fetch('/api/downlinks/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,new_port:np})});
              }
            }
            closeModal();
            loadOrders();
            if(editingId && typeof loadOrder==='function'){ loadOrder(); }
            if(editingId && typeof loadLinks==='function'){ loadLinks(); }
            if(editingId){ location.reload(); }""",
    'downlink: PUT или POST + reload наряда')

# 4) Линии на странице наряда: input-поля + удаление
rep("""<table class="data-table">
                    <thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th></tr></thead>
                    <tbody>
                        ${links.map(link => `
                            <tr>
                                <td>${link.old_port}</td>
                                <td>${link.upstream_device || '-'}</td>
                                <td>${link.upstream_port || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>""",
"""<table class="data-table">
                    <thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th><th></th></tr></thead>
                    <tbody>
                        ${links.map(link => `
                            <tr data-lid="${link.id}">
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><input type="text" class="port-input" style="width:160px;" value="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>
                                <td><button class="btn btn-danger" style="padding:2px 8px;" onclick="delLink(${link.id})">🗑</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <button class="btn btn-secondary" onclick="addLinkToOrder('uplink')">+ uplink</button>""",
    'uplink таблица: редактируемая')

rep("""<table class="data-table">
                    <thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th></tr></thead>
                    <tbody>
                        ${links.map(link => `
                            <tr>
                                <td>${link.old_port}</td>
                                <td>${link.upstream_device || '-'}</td>
                                <td>${link.upstream_port || '-'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;""",
"""<table class="data-table">
                    <thead><tr><th>Порт</th><th>Устройство</th><th>Порт устройства</th><th>Новый порт</th><th></th></tr></thead>
                    <tbody>
                        ${links.map(link => `
                            <tr>
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><input type="text" class="port-input" style="width:160px;" value="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>
                                <td><input type="number" class="port-input" value="${link.new_port||''}" onchange="updLink(${link.id}, 'new_port', this.value)"></td>
                                <td><button class="btn btn-danger" style="padding:2px 8px;" onclick="delLink(${link.id})">🗑</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <button class="btn btn-secondary" onclick="addLinkToOrder('downlink')">+ downlink</button>
            `;""",
    'downlink таблица: редактируемая')

if 'function updLink' not in src:
    rep('loadOrder();',
"""function updLink(id, field, val){
  var body={}; body[field]=(field==='upstream_device')? val : (parseInt(val)||0);
  fetch('/api/links/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
}
function delLink(id){
  if(!confirm('Удалить линию?')) return;
  fetch('/api/links/'+id,{method:'DELETE'}).then(function(){location.reload();});
}
function addLinkToOrder(type){
  var body = (type==='uplink')
    ? {old_port:1, upstream_device:'', upstream_port:1, link_type:'uplink'}
    : {old_port:1, new_port:1, upstream_device:'', upstream_port:1, link_type:'downlink'};
  fetch('/api/links/'+orderId,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(){location.reload();});
}
loadOrder();""",
    'JS: updLink / delLink / addLinkToOrder')

# 5) Эндпоинты: DELETE линии + PUT принимает все поля наряда
if "conn.execute('DELETE FROM links WHERE id = ?'" not in src:
    rep("""@app.route('/api/links/<int:link_id>', methods=['PUT'])
def api_link_update(link_id):
    data = request.json or {}
    if 'new_port' in data:
        conn = get_db()
        conn.execute('UPDATE links SET new_port = ? WHERE id = ?', (data['new_port'], link_id))
        conn.commit()
        conn.close()
    return jsonify({'success': True})""",
"""@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
def api_link_update(link_id):
    if request.method == 'DELETE':
        conn = get_db()
        conn.execute('DELETE FROM links WHERE id = ?', (link_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    data = request.json or {}
    conn = get_db()
    sets=[]
    vals=[]
    for f in ('old_port','new_port','upstream_port'):
        if f in data:
            sets.append(f+'=?'); vals.append(int(data[f]) if data[f] not in ('',None) else 0)
    for f in ('upstream_device','link_type'):
        if f in data:
            sets.append(f+'=?'); vals.append(data[f])
    if sets:
        vals.append(link_id)
        conn.execute('UPDATE links SET '+','.join(sets)+' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})""",
    'эндарт: PUT всех полей линии + DELETE')

# 6) PUT наряда принимает все поля (если список неполный)
rep("for f in ('status','old_switch_ip','new_switch_ip','old_switch_location','commands_used','vehicle_needed','order_type','new_switch_location'):",
"""for f in ('status','old_switch_ip','new_switch_ip','old_switch_location','commands_used','vehicle_needed','order_type','new_switch_location','old_switch_model','new_switch_model','old_switch_ports','new_switch_ports','order_number'):""",
    'PUT наряда: все поля')

open('swh.py', 'w').write(src)
ast.parse(open('swh.py').read())
print('update.py отработал, синтаксис ОК')