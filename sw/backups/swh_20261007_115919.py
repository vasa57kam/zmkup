from jinja2 import DictLoader
import os, uuid, csv, io
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, Response, send_from_directory
import sqlite3
import json
from datetime import datetime
from flask_cors import CORS
import passport_mod

app = Flask(__name__)
CORS(app)

DATABASE = 'switch_replacements.db'
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA busy_timeout=30000')
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS work_orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_number TEXT UNIQUE, created_at TEXT,
        old_switch_ip TEXT, old_switch_model TEXT, old_switch_ports INTEGER DEFAULT 28,
        old_switch_location TEXT,
        new_switch_ip TEXT, new_switch_model TEXT, new_switch_ports INTEGER DEFAULT 28,
        status TEXT DEFAULT 'created'
    );
    CREATE TABLE IF NOT EXISTS subscribers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER, old_port INTEGER, new_port INTEGER,
        login TEXT, ip_address TEXT, subscriber_name TEXT, address TEXT,
        vlan INTEGER, mac_address TEXT,
        is_broken INTEGER DEFAULT 0, is_camera INTEGER DEFAULT 0, notes TEXT
    );
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER, link_type TEXT, old_port INTEGER, new_port INTEGER,
        upstream_device TEXT, upstream_port INTEGER, is_broken INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS fdb_tables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER, switch_type TEXT, port INTEGER, vlan TEXT,
        mac_address TEXT, subscriber TEXT
    );
    CREATE TABLE IF NOT EXISTS network_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_type TEXT, name TEXT, ip_address TEXT, model TEXT, location TEXT,
        total_ports INTEGER, position_x INTEGER, position_y INTEGER, parent_device_id INTEGER
    );
    CREATE TABLE IF NOT EXISTS map_connections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_device_id INTEGER, from_port INTEGER,
        to_device_id INTEGER, to_port INTEGER, note TEXT
    );
    CREATE TABLE IF NOT EXISTS port_marks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER, port INTEGER, port_type TEXT, label TEXT, vlan INTEGER, mac TEXT
    );
    CREATE TABLE IF NOT EXISTS switch_inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT, serial TEXT, last_ip TEXT, status TEXT DEFAULT 'in_stock',
        order_number TEXT, notes TEXT, updated_at TEXT
    );
    CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT, entity_id INTEGER, filename TEXT, original_name TEXT,
        description TEXT, created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS order_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER, step_text TEXT, done INTEGER DEFAULT 0, pos INTEGER
    );
    CREATE TABLE IF NOT EXISTS app_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_key TEXT UNIQUE, content TEXT
    );
    CREATE TABLE IF NOT EXISTS update_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT, source TEXT, rc INTEGER, out TEXT, code TEXT
    );
    ''')
    conn.commit()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS work_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE,
            created_at TEXT,
            old_switch_ip TEXT,
            old_switch_model TEXT,
            old_switch_ports INTEGER DEFAULT 28,
            old_switch_location TEXT,
            new_switch_ip TEXT,
            new_switch_model TEXT,
            new_switch_ports INTEGER DEFAULT 28,
            status TEXT DEFAULT 'created'
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscribers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            old_port INTEGER,
            new_port INTEGER,
            login TEXT,
            ip_address TEXT,
            subscriber_name TEXT,
            address TEXT,
            vlan INTEGER,
            mac_address TEXT,
            is_broken INTEGER DEFAULT 0,
            is_camera INTEGER DEFAULT 0,
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES work_orders (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            link_type TEXT,
            old_port INTEGER,
            new_port INTEGER,
            upstream_device TEXT,
            upstream_port INTEGER,
            is_broken INTEGER DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES work_orders (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fdb_tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            switch_type TEXT,
            port INTEGER,
            vlan TEXT,
            mac_address TEXT,
            subscriber TEXT,
            FOREIGN KEY (order_id) REFERENCES work_orders (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS network_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_type TEXT,
            name TEXT,
            ip_address TEXT,
            model TEXT,
            location TEXT,
            total_ports INTEGER,
            position_x INTEGER,
            position_y INTEGER,
            parent_device_id INTEGER,
            FOREIGN KEY (parent_device_id) REFERENCES network_devices (id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS map_connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_device_id INTEGER,
            from_port INTEGER,
            to_device_id INTEGER,
            to_port INTEGER,
            note TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS port_marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER,
            port INTEGER,
            port_type TEXT,
            label TEXT,
            vlan INTEGER,
            mac TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

# ==================== HTML ШАБЛОНЫ ====================

BASE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Замена коммутаторов{% endblock %}</title>
    <script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .navbar { background: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        .nav-brand { font-size: 1.5rem; font-weight: bold; }
        .nav-links { display: flex; gap: 2rem; }
        .nav-link { color: white; text-decoration: none; padding: 0.5rem 1rem; border-radius: 4px; }
        .nav-link:hover { background: #34495e; }
        .container { padding: 2rem; max-width: 1400px; margin: 0 auto; }
        .page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        .page-header h1 { color: #2c3e50; }
        .btn { padding: 0.75rem 1.5rem; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; transition: all 0.3s; text-decoration: none; display: inline-block; margin: 0.25rem; }
        .btn-primary { background: #3498db; color: white; }
        .btn-primary:hover { background: #2980b9; }
        .btn-secondary { background: #95a5a6; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-danger { background: #e74c3c; color: white; }
        .orders-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 1.5rem; }
        .order-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer; transition: transform 0.3s; }
        .order-card:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
        .order-card h3 { color: #2c3e50; margin-bottom: 1rem; }
        .order-card p { margin: 0.5rem 0; color: #7f8c8d; }
        .status-badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.85rem; margin-top: 1rem; }
        .status-created { background: #3498db; color: white; }
        .status-in-progress { background: #f39c12; color: white; }
        .status-completed { background: #27ae60; color: white; }
        .status-closed { background: #95a5a6; color: white; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; overflow-y: auto; }
        .modal-content { background: white; max-width: 800px; margin: 2rem auto; padding: 2rem; border-radius: 8px; }
        .modal-content h2 { margin-bottom: 1.5rem; color: #2c3e50; }
        .form-group { margin-bottom: 1rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; color: #2c3e50; font-weight: 500; }
        .form-group input, .form-group select { width: 100%; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; }
        .form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
        .uplink-field { display: flex; gap: 1rem; margin-bottom: 0.5rem; }
        .uplink-field input { flex: 1; padding: 0.5rem; border: 1px solid #ddd; border-radius: 4px; }
        .modal-actions { display: flex; gap: 1rem; margin-top: 2rem; justify-content: flex-end; }
        .planner-info { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .info-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .info-card h4 { color: #2c3e50; margin-bottom: 1rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }
        .data-table { width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; border-collapse: collapse; }
        .data-table th, .data-table td { padding: 1rem; text-align: left; border-bottom: 1px solid #ecf0f1; }
        .data-table th { background: #34495e; color: white; font-weight: 600; }
        .data-table tr:hover { background: #f8f9fa; }
        .port-input { width: 80px; padding: 0.25rem; border: 1px solid #ddd; border-radius: 4px; }
        .map-container { background: white; padding: 1rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .map-controls { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h3 { color: #2c3e50; margin: 1.5rem 0 1rem; }
        .header-actions { display: flex; gap: 1rem; }
        .badge { padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.85rem; }
        .badge-broken { background: #e74c3c; color: white; }
        .badge-camera { background: #9b59b6; color: white; }
        .badge-ok { background: #27ae60; color: white; }
    </style>
</head>
<body>
    <nav class="navbar">
        <div class="nav-brand">🔄 Замена коммутаторов</div>
        <div class="nav-links">
            <a href="/" class="nav-link">📋 Наряды</a>
            <a href="/map" class="nav-link">🗺️ Карта сети</a>
            <a href="/commands" class="nav-link">📚 Команды</a>
            <a href="/field" class="nav-link">📱 Полевой</a>
            <a href="/tools" class="nav-link">🖥️ Тулза</a>
            <a href="/gen" class="nav-link">🧬 Команды</a>
            <a href="/vlans" class="nav-link">🗂 VLANы</a>
            <a href="/kb" class="nav-link">📖 База знаний</a>
            
            
            
        </div>
    </nav>
    <div class="container">
        {% block content %}{% endblock %}
    </div>
    <script src="/static/common.js?v=2"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
'''

INDEX_HTML = '''
{% extends "base.html" %}
{% block title %}Наряды - Главная{% endblock %}
{% block content %}
<div class="page-header">
    <h1>📋 Список нарядов</h1>
    <button class="btn btn-primary" onclick="showCreateOrderModal()">➕ Новый наряд</button>
</div>
<div id="todoBox" style="background:#fff8e1;border:1px solid #f1c40f;border-radius:8px;padding:1rem;margin-bottom:1rem;"></div>
<div style="margin-bottom:1rem;">
    <input id="orderSearch" onkeyup="filterOrders()"
        placeholder="🔍 Поиск: номер наряда, IP, адрес, модель..."
        style="width:100%;padding:.6rem;border:1px solid #ddd;border-radius:6px;">
</div>
<div id="ordersList" class="orders-grid"></div>

<div id="createOrderModal" class="modal">
    <div class="modal-content">
        <h2 id="orderModalTitle">📝 Новый наряд</h2>
        <form id="createOrderForm">
        <input type="hidden" id="editingOrderId" value="">
            <div class="form-group">
                <label>Номер наряда:</label>
                <input type="text" id="orderNumber" required>
            </div>
            <div class="form-group">
                <label>Тип наряда:</label>
                <select id="orderType" onchange="toggleCamMode()">
                    <option value="replace">🔄 Замена коммутатора</option>
                    <option value="new">🆕 Новая установка (без старого)</option>
                    <option value="service">🔧 Сервис / ремонт</option>
                    <option value="camera">📹 Замена камеры</option>
                </select>
            </div>
            <h3>Старый коммутатор</h3>
            <div class="form-row">
                <div class="form-group">
                    <label>IP адрес:</label>
                    <input type="text" id="oldSwitchIp">
                </div>
                <div class="form-group">
                    <label>Модель:</label>
                    <input type="text" id="oldSwitchModel">
                </div>
                <div class="form-group">
                    <label>Портов:</label>
                    <input type="number" id="oldSwitchPorts" value="28">
                </div>
            </div>
            <div class="form-group">
                <label>Местоположение:</label>
                <input type="text" id="oldSwitchLocation">
            </div>
            <div class="form-group">
                <label>Подъезд (старый):</label>
                <input type="text" id="oldPodyezd" placeholder="Напр.: 2">
            </div>
            <h3>Новый коммутатор</h3>
            <div class="form-row">
                <div class="form-group">
                    <label>IP адрес:</label>
                    <input type="text" id="newSwitchIp">
                </div>
                <div class="form-group">
                    <label>Модель:</label>
                    <input type="text" id="newSwitchModel">
                </div>
                <div class="form-group">
                    <label>Портов:</label>
                    <input type="number" id="newSwitchPorts" value="28">
                </div>
            </div>
            <div class="form-group">
                <label>Адрес нового коммутатора:</label>
                <input type="text" id="newSwitchLocation" placeholder="Где стоит / будет стоять">
            </div>
            <div class="form-group">
                <label>Подъезд (новый):</label>
                <input type="text" id="newPodyezd" placeholder="Напр.: 2">
            </div>
            <div id="uplinksWrap"><h3>Uplink подключения</h3>
            <div id="uplinksContainer"></div>
            <button type="button" class="btn btn-secondary" onclick="addUplinkField()">+ Добавить uplink</button>
            <h3>Downlink подключения (к соседним коммутаторам)</h3>
            <div id="downlinksContainer"></div>
            <button type="button" class="btn btn-secondary" onclick="addDownlinkField()">+ Добавить downlink</button></div>
            <div class="modal-actions">
                <button type="submit" class="btn btn-primary">💾 Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="closeModal()">Отмена</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
if(typeof devList==='undefined'){ window.devList=function(){ return Promise.resolve([]); }; }
if(typeof devLocSync==='undefined'){ window.devLocSync=function(){ return ''; }; }
let uplinkCount = 0;

var allOrders=[];
function renderTodo(orders){
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
function filterOrders(){ loadOrders(); }
function loadOrders() {
    fetch('/api/orders')
        .then(r => r.json())
        .then(orders => {
            allOrders=orders;
            var qEl=document.getElementById('orderSearch');
            var q=qEl? qEl.value.toLowerCase():'';
            if(q){
              orders=orders.filter(function(o){
                var s=JSON.stringify(o).toLowerCase();
                return s.indexOf(q)>=0;
              });
            }
            const container = document.getElementById('ordersList');
            if (orders.length === 0) {
                container.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: #7f8c8d;">Нет нарядов. Создайте первый!</p>';
                return;
            }
            container.innerHTML = orders.map(order => `
                <div class="order-card" onclick="window.location.href='/order/${order.id}'">
                    <h3>Наряд #${order.order_number}</h3>
                    <p><strong>Старый:</strong> ${order.old_switch_ip || 'Не указан'} (${order.old_switch_model || '?'})</p>
                    <p><strong>Новый:</strong> ${order.new_switch_ip || 'Не указан'} (${order.new_switch_model || '?'})</p>
                    <p><strong>Тип:</strong> ${order.order_type==='new'?'🆕 новая установка':order.order_type==='service'?'🔧 сервис':' замена'}</p>
                    <p><strong>Адрес:</strong> ${order.new_switch_location || order.old_switch_location || 'Не указан'}</p>
                    <p><strong>Дата:</strong> ${order.created_at}</p>
                    <span class="status-badge status-${order.status}">${order.status==='closed'?'🔒 закрыт':order.status}</span>
                    <button class="btn btn-secondary" style="padding:2px 8px;font-size:12px;float:right;margin-left:4px;" onclick="event.stopPropagation();editOrder(${order.id})">✏️</button>
                    <button class="btn btn-danger" style="padding:2px 8px;font-size:12px;float:right;" onclick="event.stopPropagation();delOrder(${order.id})">🗑</button>
                </div>
            `).join('');
            renderTodo(orders);
        });
}

var editingId=null;
function showCreateOrderModal() {
    editingId=null;
    document.getElementById('orderModalTitle').textContent='📝 Новый наряд';
    document.getElementById('editingOrderId').value='';
    document.getElementById('createOrderModal').style.display = 'block';
    addUplinkField();
    toggleCamMode();
}

function toggleCamMode(){
  var t=document.getElementById('orderType');
  var cam=(t && t.value==='camera');
  ['oldSwitchPorts','newSwitchPorts'].forEach(function(id){
    var el=document.getElementById(id);
    if(el && el.closest('.form-group')){ el.closest('.form-group').style.display=cam?'none':''; }
  });
  var uw=document.getElementById('uplinksWrap');
  if(uw){ uw.style.display=cam?'none':''; }
  var hs=document.querySelectorAll('#createOrderModal h3');
  if(hs.length>=2){
    if(cam){ hs[0].textContent='Старая камера (адрес, подъезд)'; hs[1].textContent='Новая камера'; }
    else { hs[0].textContent='Старый коммутатор'; hs[1].textContent='Новый коммутатор'; }
  }
}
function editOrder(id){
  editingId=id; window.linkDeletes=[];
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
    document.getElementById('oldPodyezd').value=o.old_podyezd||'';
    document.getElementById('newPodyezd').value=o.new_podyezd||'';
    document.getElementById('uplinksContainer').innerHTML='';
    document.getElementById('downlinksContainer').innerHTML='';
    uplinkCount=0;
    toggleCamMode();
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
function closeModal() {
    document.getElementById('createOrderModal').style.display = 'none';
    document.getElementById('createOrderForm').reset();
    document.getElementById('uplinksContainer').innerHTML = '';
    document.getElementById('downlinksContainer').innerHTML = '';
    uplinkCount = 0;
}

function addUplinkField() {
    uplinkCount++;
    const container = document.getElementById('uplinksContainer');
    const div = document.createElement('div');
    div.className = 'uplink-field';
    div.innerHTML = `
        <input type="number" placeholder="Порт" class="uplink-port">
        <select class="uplink-device" onchange="devSelect(this)"></select>
        <input type="number" placeholder="Порт устр." class="uplink-upstream-port">
        <button type="button" class="btn btn-danger" style="padding:2px 8px;" onclick="rmRow(this)">🗑</button>
    `;
    container.appendChild(div);
    fillDevSelect(div.querySelector('.dl-device'));
    fillDevSelect(div.querySelector('.uplink-device'));
    fillDevSelect(div.querySelector('.dl-device'));
    fillDevSelect(div.querySelector('.uplink-device'));
    fillDevSelect(div.querySelector('.dl-device'));
    fillDevSelect(div.querySelector('.uplink-device'));
}

document.getElementById('createOrderForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const orderData = {
        order_number: document.getElementById('orderNumber').value,
        old_switch_ip: document.getElementById('oldSwitchIp').value,
        old_switch_model: document.getElementById('oldSwitchModel').value,
        old_switch_ports: document.getElementById('oldSwitchPorts').value,
        old_switch_location: document.getElementById('oldSwitchLocation').value,
        new_switch_ip: document.getElementById('newSwitchIp').value,
        new_switch_model: document.getElementById('newSwitchModel').value,
        new_switch_ports: document.getElementById('newSwitchPorts').value,
        order_type: document.getElementById('orderType').value,
        new_switch_location: document.getElementById('newSwitchLocation').value,
        old_podyezd: document.getElementById('oldPodyezd').value,
        new_podyezd: document.getElementById('newPodyezd').value
    };
    
    try {
        var targetId = editingId;
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
          if(!targetId){ targetId = result.order_id; }
            const uplinkPorts = document.querySelectorAll('.uplink-port');
            const uplinkDevices = document.querySelectorAll('.uplink-device');
            const uplinkUpstreamPorts = document.querySelectorAll('.uplink-upstream-port');
            
            var upFields=document.querySelectorAll('#uplinksContainer .uplink-field');
            for (let i = 0; i < upFields.length; i++) {
              var port=upFields[i].querySelector('.uplink-port').value;
              var dev=upFields[i].querySelector('.uplink-device').value;
              var up=upFields[i].querySelector('.uplink-upstream-port').value;
              if(!port) continue;
              var lid=upFields[i].dataset.linkId;
              if(!dev && lid){ continue; }
              if(lid && editingId){
                await fetch('/api/links/'+lid,{method:'PUT',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up})});
              } else {
                await fetch('/api/links/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,link_type:'uplink'})});
              }
            }
            const dlPorts = document.querySelectorAll('.dl-port');
            const dlDevices = document.querySelectorAll('.dl-device');
            const dlUp = document.querySelectorAll('.dl-upstream-port');
            const dlNew = document.querySelectorAll('.dl-new-port');
            var dlFields=document.querySelectorAll('#downlinksContainer .uplink-field');
            for (let i = 0; i < dlFields.length; i++) {
              var port=dlFields[i].querySelector('.dl-port').value;
              var dev=dlFields[i].querySelector('.dl-device').value;
              var up=dlFields[i].querySelector('.dl-upstream-port').value;
              var np=dlFields[i].querySelector('.dl-new-port').value;
              if(!port && !dev) continue;
              var lid=dlFields[i].dataset.linkId;
              if(!dev && lid){ continue; }
              if(lid && editingId){
                await fetch('/api/links/'+lid,{method:'PUT',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,new_port:np})});
              } else {
                await fetch('/api/downlinks/'+targetId,{method:'POST',headers:{'Content-Type':'application/json'},
                  body:JSON.stringify({old_port:port,upstream_device:dev,upstream_port:up,new_port:np})});
              }
            }
            if(window.linkDeletes && window.linkDeletes.length){
              try{
                for(const id of window.linkDeletes){
                  await fetch('/api/links/'+id,{method:'DELETE'});
                }
              } finally { window.linkDeletes=[]; }
            }
            closeModal();
            loadOrders();
            if(editingId && typeof loadOrder==='function'){ function updLink(id, field, val){
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
loadOrder(); }
            if(editingId && typeof loadLinks==='function'){ loadLinks(); }
            if(editingId){ location.reload(); }
        } else {
            alert('Ошибка: ' + result.error);
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
});

function rmRow(btn){
  var row=btn.closest('.uplink-field');
  if(!row) return;
  if(row.dataset.linkId){
    window.linkDeletes=window.linkDeletes||[];
    window.linkDeletes.push(row.dataset.linkId);
  }
  row.remove();
}
function fillDevSelect(sel, pre){
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
function devSelect(sel){
  if(sel.value==='__manual'){
    var v=prompt('Устройство вручную (имя / IP):');
    if(v){
      var loc=prompt('Адрес этого устройства (или оставьте пустым):','');
      var o=document.createElement('option');
      o.value=v; o.textContent=v+(loc?' · 📍 '+loc:'');
      sel.appendChild(o); sel.value=v;
      if(loc){
        if(confirm('Добавить устройство "'+v+'" на карту сети с этим адресом?')){
          var ipm=v.match(/(\d{1,3}\.){3}\d{1,3}/);
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
function addDownlinkField() {
    const container = document.getElementById('downlinksContainer');
    const div = document.createElement('div');
    div.className = 'uplink-field';
    div.innerHTML = `
        <input type="number" placeholder="Порт (стар)" class="dl-port">
        <select class="dl-device" onchange="devSelect(this)"></select>
        <input type="number" placeholder="Порт там" class="dl-upstream-port">
        <input type="number" placeholder="Порт (нов)" class="dl-new-port">
        <button type="button" class="btn btn-danger" style="padding:2px 8px;" onclick="rmRow(this)">🗑</button>
    `;
    container.appendChild(div);
}

window.onclick = function(event) {
    const modal = document.getElementById('createOrderModal');
    if (event.target == modal) {
        closeModal();
    }
}

async function delOrder(id){
    if(!confirm('Удалить наряд со всеми данными?')) return;
    const r = await fetch('/api/orders/'+id, {method:'DELETE'});
    if(!r.ok){
        const t = await r.text();
        alert('Ошибка сервера ' + r.status + ': ' + t.slice(0,300));
        return;
    }
    loadOrders();
}

loadOrders();
</script>
{% endblock %}
'''

ORDER_HTML = '''
{% extends "base.html" %}
{% block title %}Наряд №{{ order_number }}{% endblock %}
{% block content %}
<div class="page-header">
    <h1> Наряд #{{ order_number }}</h1>
    <div class="header-actions">
        <a href="/planner/{{ order_id }}" class="btn btn-primary">🗺️ Планировщик</a>
        <a href="/" class="btn btn-secondary">← Назад</a>
    </div>
</div>
<div class="header-actions" style="margin-bottom:1rem;">
    <button id="closeBtn" class="btn btn-success" onclick="toggleOrderStatus()">✅ Закрыть наряд</button>
    <a class="btn btn-secondary" href="/api/report/{{ order_id }}" target="_blank">📄 Отчёт</a>
    <a href="/planner/{{ order_id }}" class="btn btn-primary">🗺️ Планировщик</a>
    <a href="/fdb/{{ order_id }}" class="btn btn-success">📊 FDB</a>
</div>
<div id="orderDetails"></div>
<h3>Uplink подключения</h3>
<div id="uplinksList"></div>
<h3>🔽 Downlink — НЕ ЗАБЫТЬ прописать на новом свитче!</h3>
<div id="downlinksList"></div>
<h3>✅ Этапы замены</h3>
<div id="stepsList" style="background:#fff;padding:1rem;border-radius:8px;"></div>
<h3>📹 Камеры (замена / конфигурация)</h3>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
    <div id="camsBox"></div>
    <button class="btn btn-secondary" onclick="addCam('old')">+ Старая камера</button>
    <button class="btn btn-secondary" onclick="addCam('new')">+ Новая камера</button>
</div>
<h3>📚 Команды и ресурсы</h3>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
    <div id="cmdUsedBox"></div>
    <div class="form-group"><label>Использованные команды (можно править руками):</label>
        <textarea id="cmdsUsed" style="width:100%;height:70px;"></textarea></div>
    <label><input type="checkbox" id="vehNeed"> Нужна была машина (вышка/авто)</label>
    <button class="btn btn-primary" onclick="saveCmds()">💾 Сохранить</button>
</div>
<h3>Абоненты</h3>
<div id="subscribersList"></div>
{% endblock %}

{% block scripts %}
<script>
const orderId = {{ order_id }};

function loadOrder() {
    fetch(`/api/orders/${orderId}`)
        .then(r => r.json())
        .then(order => {
            orderStatus=order.status||'created';
            var badge=document.getElementById('orderStatusBadge');
            var cbtn=document.getElementById('closeBtn');
            if(orderStatus==='closed'){
              badge.textContent='🔒 ЗАКРЫТ';
              cbtn.textContent='↩️ Открыть снова';
              cbtn.className='btn btn-secondary';
            } else {
              badge.textContent='';
              cbtn.textContent='✅ Закрыть наряд';
              cbtn.className='btn btn-success';
            }
            document.getElementById('orderDetails').innerHTML = `
                <div class="planner-info">
                    <div class="info-card">
                        <h4>Старый коммутатор</h4>
                        <p><strong>IP:</strong> ${order.old_switch_ip || 'Не указан'}</p>
                        <p><strong>Модель:</strong> ${order.old_switch_model || 'Не указана'}</p>
                        <p><strong>Портов:</strong> ${order.old_switch_ports}</p>
                        <p><strong>Адрес:</strong> ${order.old_switch_location || 'Не указан'}${order.old_podyezd? ', подъезд '+order.old_podyezd : ''}</p>
                    </div>
                    <div class="info-card">
                        <h4>Новый коммутатор</h4>
                        <p><strong>IP:</strong> ${order.new_switch_ip || 'Не указан'}</p>
                        <p><strong>Модель:</strong> ${order.new_switch_model || 'Не указана'}</p>
                        <p><strong>Портов:</strong> ${order.new_switch_ports}</p>
                        <p><strong>Адрес:</strong> ${order.new_switch_location || '—'}${order.new_podyezd? ', подъезд '+order.new_podyezd : ''}</p>
                    </div>
                </div>
            `;
        });
    
    fetch('/api/orders/'+orderId).then(function(r){return r.json();}).then(function(o){
      if(o.order_type==='new'){
        var cds=document.querySelectorAll('#orderDetails .info-card');
        if(cds[0]){ cds[0].innerHTML='<h4>Старый коммутатор</h4><p>— отсутствует (новая установка)</p>'; }
      }
    });
    fetch(`/api/links/${orderId}`)
        .then(r => r.json())
        .then(alllinks => {
            const links = alllinks.filter(l => l.link_type === 'uplink');
            renderDownlinks(alllinks.filter(l => l.link_type === 'downlink'));
            const container = document.getElementById('uplinksList');
            if (links.length === 0) {
                container.innerHTML = '<p>Uplink не настроены</p>';
                return;
            }
            container.innerHTML = `
                <table class="data-table">
                    <thead><tr><th>Порт</th><th>Устройство</th><th>Адрес</th><th>Порт устройства</th><th></th></tr></thead>
                    <tbody>
                        ${links.map(link => `
                            <tr data-lid="${link.id}">
                                <td><input type="number" class="port-input" value="${link.old_port}" onchange="updLink(${link.id}, 'old_port', this.value)"></td>
                                <td><select class="port-input devsel" data-cur="${link.upstream_device||''}" onchange="updLink(${link.id}, 'upstream_device', this.value)"></select></td>
                                <td>${devLocSync(link.upstream_device)?'📍 '+devLocSync(link.upstream_device):''} <a href="#" data-dev="${link.upstream_device||''}" onclick="openDevTools(this.dataset.dev);return false;">🔗</a></td>
                                <td><input type="number" class="port-input" value="${link.upstream_port||''}" onchange="updLink(${link.id}, 'upstream_port', this.value)"></td>
                                <td><button class="btn btn-danger" style="padding:2px 8px;" onclick="delLink(${link.id})">🗑</button></td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
                <button class="btn btn-secondary" onclick="addLinkToOrder('uplink')">+ uplink</button>
            `;
        });
    
    fetch(`/api/subscribers/${orderId}`)
        .then(r => r.json())
        .then(subs => {
            const container = document.getElementById('subscribersList');
            if (subs.length === 0) {
                container.innerHTML = '<p>Абонентов нет. Добавьте в планировщике.</p>';
                return;
            }
            container.innerHTML = `
                <table class="data-table">
                    <thead>
                        <tr><th>Порт</th><th>Абонент</th><th>Адрес</th><th>VLAN</th><th>Статус</th></tr>
                    </thead>
                    <tbody>
                        ${subs.map(sub => `
                            <tr>
                                <td>${sub.old_port}</td>
                                <td>${sub.subscriber_name || '-'}</td>
                                <td>${sub.address || '-'}</td>
                                <td>${sub.vlan || '-'}</td>
                                <td>
                                    ${sub.is_broken ? '<span class="badge badge-broken">❌ Битый</span>' : 
                                      sub.is_camera ? '<span class="badge badge-camera">📹 Камера</span>' : 
                                      '<span class="badge badge-ok">✅ ОК</span>'}
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        });
}

loadOrder();
</script>
{% endblock %}
'''

PLANNER_HTML = '''
{% extends "base.html" %}
{% block title %}Планировщик - Наряд №{{ order_number }}{% endblock %}
{% block content %}
<div class="page-header">
    <h1>🗺️ Планировщик портов - Наряд №{{ order_number }}</h1>
    <div class="header-actions">
        <button class="btn btn-primary" onclick="autoPlan()"> Авто-планирование</button>
        <a class="btn btn-secondary" href="/passport/{{ order_id }}" target="_blank">🖨️ Паспорт</a>
        <button class="btn btn-success" onclick="exportReport()">📄 Экспорт отчета</button>
        <a href="/order/{{ order_id }}" class="btn btn-secondary">← Назад</a>
    </div>
</div>

<div class="planner-info">
    <div class="info-card">
        <h4>Старый коммутатор</h4>
        <div id="oldSwitchInfo">Загрузка...</div>
    </div>
    <div class="info-card">
        <h4>Новый коммутатор</h4>
        <div id="newSwitchInfo">Загрузка...</div>
    </div>
    <div class="info-card">
        <h4>Статистика</h4>
        <div id="statsInfo">Загрузка...</div>
    </div>
</div>

<div class="header-actions" style="margin-bottom:1rem;">
    <a href="/fdb/{{ order_id }}" class="btn btn-success">📊 FDB: загрузить / ввести / сравнить</a>
</div>
<h3>⬆️ Uplink — куда воткнуть новый свитч</h3>
<div id="uplinksPlan"></div>
<h3>⬇️ Downlink — не забыть переподключить и прописать!</h3>
<div id="downlinksPlan"></div>
<h3>🔔 НЕ ЗАБЫТЬ указать (соседнее оборудование и база)</h3>
<div id="reminders" style="background:#fff8e1;padding:1rem;border-radius:8px;border:1px solid #f1c40f;"></div>
<h3 id="camPlanH" style="display:none;">📹 План установки камер</h3>
<div id="camPlan" style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;display:none;"></div>
<h3>🗺️ Карта наряда: как было / как станет</h3>
<div id="orderMap" style="background:#fff;padding:1rem;border-radius:8px;overflow-x:auto;"></div>
<div id="subsBlock">
<h3>👥 Абоненты (необязательно)</h3>
<div class="data-table" style="overflow-x: auto;">
    <table class="data-table">
        <thead>
            <tr>
                <th>Старый порт</th>
                <th>Абонент</th>
                <th>Адрес</th>
                <th>VLAN</th>
                <th>MAC</th>
                <th>Новый порт</th>
                <th>Статус</th>
                <th>Действия</th>
            </tr>
        </thead>
        <tbody id="subscribersTable"></tbody>
    </table>
</div>

<button class="btn btn-primary" id="addSubBtn" onclick="showAddSubscriberModal()">+ Добавить абонента</button>
</div>

<div id="addSubscriberModal" class="modal">
    <div class="modal-content">
        <h2>➕ Добавить абонента</h2>
        <form id="addSubscriberForm">
            <div class="form-row">
                <div class="form-group">
                    <label>Старый порт:</label>
                    <input type="number" id="subOldPort" required>
                </div>
                <div class="form-group">
                    <label>VLAN:</label>
                    <input type="number" id="subVlan" value="2301">
                </div>
            </div>
            <div class="form-group">
                <label>Абонент:</label>
                <input type="text" id="subName">
            </div>
            <div class="form-group">
                <label>Адрес:</label>
                <input type="text" id="subAddress">
            </div>
            <div class="form-group">
                <label>MAC адрес:</label>
                <input type="text" id="subMac">
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="subBroken"> Битый порт (удалить)
                </label>
            </div>
            <div class="form-group">
                <label>
                    <input type="checkbox" id="subCamera"> Камера (VLAN 135)
                </label>
            </div>
            <div class="modal-actions">
                <button type="submit" class="btn btn-primary">💾 Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="closeSubscriberModal()">Отмена</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
const orderId = {{ order_id }};

if(typeof devLocSync==='undefined'){ window.devLocSync=function(){ return ''; }; }
if(typeof devList==='undefined'){ window.devList=function(){ return Promise.resolve([]); }; }
function renderCamPlan(){
  fetch('/api/cameras?order_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    var hEl=document.getElementById('camPlanH');
    var box=document.getElementById('camPlan');
    if(!box) return;
    if(!rows.length){ if(hEl){hEl.style.display='none';} box.style.display='none'; return; }
    if(hEl){hEl.style.display='';} box.style.display='';
    var h='';
    rows.forEach(function(c){
      h+='<div style="border:1px solid #ddd;border-radius:8px;padding:.7rem;margin:.4rem 0;">';
      h+='<button class="btn btn-danger" style="padding:1px 6px;margin-right:.4rem;" onclick="delCamPlan('+c.id+')" title="Удалить камеру">🗑</button>';
      h+='<b>📹 '+(c.side==='old'?'СТАРНАЯ':'НОВАЯ')+' камера:</b> '+(c.model||'—')+' | IP/ID: '+(c.ip?'<a href="http://'+c.ip+'" target="_blank">'+c.ip+'</a>':'без IP')+' | логин: '+(c.login||'—');
      h+='<br>📍 зона/надпись: '+(c.zone||'—')+' | серийник: '+(c.serial||'—');
      h+='<br>🔌 свитч: <b>'+(c.switch_name||'—')+'</b>'+(devLocSync(c.switch_name)?' 📍 '+devLocSync(c.switch_name):'')+', порт '+(c.switch_port||'—')+' | порт/VLAN: '+(c.port||'—')+'/'+(c.vlan||'—');
      if(c.rtsp){
        h+='<br>🎬 RTSP: <a href="'+c.rtsp+'" target="_blank">'+c.rtsp+'</a> <button class="btn btn-secondary" style="padding:1px 6px;" data-t="'+c.rtsp+'" onclick="copyTxt(this.dataset.t)">📋</button>';
      }
      if(c.notes){ h+='<br>📝 '+c.notes; }
      h+='</div>';
    });
    var nc=rows.filter(function(c){return c.side==='new';})[0]||rows[0];
    h+='<h3>🔔 НЕ ЗАБЫТЬ (камеры):</h3><ul style="margin-left:1.2rem;line-height:1.7;">'
      +'<li>Настроить новую камеру: логин/пароль, время, RTSP.</li>'
      +'<li>Переподключить в биллинге: порт '+(nc.port||'—')+' / VLAN '+(nc.vlan||'—')+'.</li>'
      +'<li>Проверить поток и архив записи ('+(nc.rtsp||'rtsp новой камеры')+').</li>'
      +'<li>Обновить карточку: номер БР, подъезд, надпись.</li>'
      +'</ul>';
    h='<button class="btn btn-secondary" style="margin-bottom:.5rem;" onclick="cleanEmptyCams()">🧹 Убрать пустые камеры</button>'+h;
    box.innerHTML=h;
  });
}
function loadSubscribers() {
    fetch(`/api/orders/${orderId}`)
        .then(r => r.json())
        .then(order => {
            window.orderType=order.order_type||'replace';
            applyNewMode(order);
            if((order.order_type||'')==='camera'){
              var om=document.getElementById('orderMap');
              if(om){ if(om.previousElementSibling){ om.previousElementSibling.style.display='none'; } om.style.display='none'; }
            }
            document.getElementById('oldSwitchInfo').innerHTML = `
                <p><strong>IP:</strong> ${order.old_switch_ip}</p>
                <p><strong>Модель:</strong> ${order.old_switch_model}</p>
                <p><strong>Портов:</strong> ${order.old_switch_ports}</p>
            `;
            document.getElementById('newSwitchInfo').innerHTML = `
                <p><strong>IP:</strong> ${order.new_switch_ip}</p>
                <p><strong>Модель:</strong> ${order.new_switch_model}</p>
                <p><strong>Портов:</strong> ${order.new_switch_ports}</p>
            `;
        });
    
    fetch(`/api/subscribers/${orderId}`)
        .then(r => r.json())
        .then(subs => {
            const tbody = document.getElementById('subscribersTable');
            if (subs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Нет абонентов. Добавьте вручную или импортируйте.</td></tr>';
                updateStats([]);
                return;
            }
            
            tbody.innerHTML = subs.map(sub => `
                <tr>
                    <td>${sub.old_port}</td>
                    <td>${sub.subscriber_name || '-'}</td>
                    <td>${sub.address || '-'}</td>
                    <td>${sub.vlan || '-'}</td>
                    <td>${sub.mac_address || '-'}</td>
                    <td>
                        <input type="number" value="${sub.new_port || ''}" 
                               onchange="updateNewPort(${sub.id}, this.value)" 
                               class="port-input" placeholder="Новый">
                    </td>
                    <td>
                        ${sub.is_broken ? '<span class="badge badge-broken">❌ Битый</span>' : 
                          sub.is_camera ? '<span class="badge badge-camera">📹 Камера</span>' : 
                          '<span class="badge badge-ok">✅ ОК</span>'}
                    </td>
                    <td>
                        <button class="btn btn-secondary" onclick="toggleBroken(${sub.id})">🔧</button>
                        <button class="btn btn-secondary" onclick="toggleCamera(${sub.id})">📹</button>
                        <button class="btn btn-danger" onclick="deleteSubscriber(${sub.id})">🗑️</button>
                    </td>
                </tr>
            `).join('');
            
            updateStats(subs);
        });
}

function updateNewPort(subscriberId, newPort) {
    fetch(`/api/subscribers/${subscriberId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({new_port: parseInt(newPort) || 0})
    }).then(() => loadSubscribers());
}

function toggleBroken(subscriberId) {
    fetch(`/api/subscribers/${subscriberId}`)
        .then(r => r.json())
        .then(sub => {
            fetch(`/api/subscribers/${subscriberId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({is_broken: sub.is_broken ? 0 : 1})
            }).then(() => loadSubscribers());
        });
}

function toggleCamera(subscriberId) {
    fetch(`/api/subscribers/${subscriberId}`)
        .then(r => r.json())
        .then(sub => {
            fetch(`/api/subscribers/${subscriberId}`, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({is_camera: sub.is_camera ? 0 : 1})
            }).then(() => loadSubscribers());
        });
}

function deleteSubscriber(subscriberId) {
    if (confirm('Удалить абонента?')) {
        fetch(`/api/subscribers/${subscriberId}`, {method: 'DELETE'})
            .then(() => loadSubscribers());
    }
}

function autoPlan() {
    if (confirm('Автоматически распределить порты?')) {
        fetch(`/api/auto-plan/${orderId}`, {method: 'POST'})
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    alert(`✅ Распределено ${result.assigned} абонентов!`);
                    loadSubscribers();
                } else {
                    alert('Ошибка: ' + result.error);
                }
            });
    }
}

function updateStats(subs) {
    const total = subs.length;
    const broken = subs.filter(s => s.is_broken).length;
    const cameras = subs.filter(s => s.is_camera).length;
    const active = total - broken;
    const planned = subs.filter(s => s.new_port).length;
    
    document.getElementById('statsInfo').innerHTML = `
        <p><strong>Всего:</strong> ${total}</p>
        <p><strong>Активных:</strong> ${active}</p>
        <p><strong>Битых:</strong> ${broken}</p>
        <p><strong>Камер:</strong> ${cameras}</p>
        <p><strong>Запланировано:</strong> ${planned}</p>
    `;
}

function showAddSubscriberModal() {
    document.getElementById('addSubscriberModal').style.display = 'block';
}

function closeSubscriberModal() {
    document.getElementById('addSubscriberModal').style.display = 'none';
    document.getElementById('addSubscriberForm').reset();
}

document.getElementById('addSubscriberForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        order_id: orderId,
        old_port: parseInt(document.getElementById('subOldPort').value),
        subscriber_name: document.getElementById('subName').value,
        address: document.getElementById('subAddress').value,
        vlan: parseInt(document.getElementById('subVlan').value),
        mac_address: document.getElementById('subMac').value,
        is_broken: document.getElementById('subBroken').checked ? 1 : 0,
        is_camera: document.getElementById('subCamera').checked ? 1 : 0
    };
    
    try {
        const response = await fetch('/api/subscribers', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.success) {
            closeSubscriberModal();
            loadSubscribers();
        }
    } catch (error) {
        alert('Ошибка: ' + error.message);
    }
});

function exportReport() {
    window.open(`/api/report/${orderId}`, '_blank');
}

window.onclick = function(event) {
    const modal = document.getElementById('addSubscriberModal');
    if (event.target == modal) {
        closeSubscriberModal();
    }
}

async function setLinkNewPort(id,val){
    await fetch('/api/links/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_port:parseInt(val)||0})});
    loadLinks();
}

async function loadLinks(){
    const order=await (await fetch('/api/orders/'+orderId)).json();
    const links=await (await fetch('/api/links/'+orderId)).json();
    const ups=links.filter(l=>l.link_type==='uplink');
    const dls=links.filter(l=>l.link_type==='downlink');
    document.getElementById('uplinksPlan').innerHTML = ups.length ? `
        <table class="data-table"><thead><tr><th>Порт (стар)</th><th>Порт (НОВЫЙ)</th><th>Вышестоящее устройство</th><th>Порт там</th></tr></thead>
        <tbody>${ups.map(l=>`<tr><td>${l.old_port}</td>
            <td><input type="number" class="port-input" value="${l.new_port||''}" placeholder="порт нов" onchange="setLinkNewPort(${l.id},this.value)"></td>
            <td>${l.upstream_device||'-'}${devLocSync(l.upstream_device)?' 📍 '+devLocSync(l.upstream_device):''}</td><td>${l.upstream_port||'-'}</td></tr>`).join('')}</tbody></table>`
        : '<p>Аплинков нет</p>';
    document.getElementById('downlinksPlan').innerHTML = dls.length ? `
        <table class="data-table"><thead><tr><th>Порт (стар)</th><th>Порт (НОВЫЙ)</th><th>Соседний свитч</th><th>Порт там</th><th>Статус</th></tr></thead>
        <tbody>${dls.map(l=>`<tr><td>${l.old_port}</td>
            <td><input type="number" class="port-input" value="${l.new_port||''}" placeholder="порт нов" onchange="setLinkNewPort(${l.id},this.value)"></td>
            <td>${l.upstream_device||'-'}${devLocSync(l.upstream_device)?' 📍 '+devLocSync(l.upstream_device):''}</td><td>${l.upstream_port||'-'}</td>
            <td>${l.new_port?'<span class="badge badge-ok">✅ назначен</span>':'<span class="badge badge-broken">⚠️ назначь порт!</span>'}</td></tr>`).join('')}</tbody></table>`
        : '<p>Даунлинков нет</p>';
    document.querySelectorAll('.devsel').forEach(function(sel){
      fillDevSelect(sel, sel.dataset.cur||'');
    });
    renderReminders(order, links);
    renderOrderMap(order, links);
}

function applyNewMode(order){
  if((order.order_type||'replace')!=='new') return;
  var oc=document.getElementById('oldSwitchInfo');
  if(oc){ var c=oc.closest('.info-card'); if(c){ c.style.display='none'; } }
  var sb=document.getElementById('subsBlock');
  if(sb){ sb.style.display='none'; }
  var ab=document.getElementById('addSubBtn');
  if(ab){ ab.style.display='none'; }
  var h=document.querySelector('.page-header h1');
  if(h){ h.textContent='🗺️ Планировщик установки — наряд №'+(order.order_number||''); }
}
function renderNewReminders(order, ups, dls){
  var h='';
  ups.forEach(function(l){
    h+='<li>На <b>'+(l.upstream_device||'?')+'</b> порт '+(l.upstream_port||'?')+': настроить uplink на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||l.old_port||'??')+'</b> (адрес: '+(devLocSync(l.upstream_device)||'—')+')</li>';
  });
  dls.forEach(function(l){
    h+='<li>На <b>'+(l.upstream_device||'?')+'</b> порт '+(l.upstream_port||'?')+': настроить линк на НОВЫЙ свитч <b>'+order.new_switch_ip+'</b> порт <b>'+(l.new_port||'?? — назначьте выше!')+'</b> (адрес: '+(devLocSync(l.upstream_device)||'—')+')</li>';
  });
  h+='<li>Завести карточку нового свитча в базе: адрес <b>'+(order.new_switch_location||'—')+'</b>, модель '+(order.new_switch_model||'')+', фото узла.</li>';
  h+='<li>Занести FDB нового свитча (кнопка «ПОСЛЕ замены») для истории.</li>';
  h+='<li>Добавить новый свитч на карту сети с адресом установки.</li>';
  return h;
}
function renderReminders(order, links){
    const ups=links.filter(l=>l.link_type==='uplink');
    const dls=links.filter(l=>l.link_type==='downlink');
    if((order.order_type||'replace')==='new'){
      document.getElementById('reminders').innerHTML='<ul style="margin-left:1.2rem;line-height:1.7;">'+renderNewReminders(order, ups, dls)+'</ul>';
      return;
    }
    let html='<ul style="margin-left:1.2rem;line-height:1.7;">';
    ups.forEach(l=>{
        html+='<li>На <b>'+ (l.upstream_device||'?') +'</b> (порт '+ (l.upstream_port||'?') +') аплинк был с <b>'+ order.old_switch_ip +'</b> п'+ l.old_port +' → станет с <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b> (адрес: '+ (devLocSync(l.upstream_device)||'—') +')</li>';
    });
    dls.forEach(l=>{
        html+='<li>На <b>'+ (l.upstream_device||'?') +'</b> (порт '+ (l.upstream_port||'?') +') даунлинк был на <b>'+ order.old_switch_ip +'</b> п'+ l.old_port +' → станет на <b>'+ order.new_switch_ip +'</b> п<b>'+ (l.new_port||'?? — назначьте выше!') +'</b> (адрес: '+ (devLocSync(l.upstream_device)||'—') +')</li>';
    });
    html+='<li>Обновить карточку в базе: IP <b>'+ order.new_switch_ip +'</b>, модель '+ (order.new_switch_model||'') +', фото нового узла.</li>';
    html+='<li>Старый <b>'+ order.old_switch_ip +'</b>: сбросить конфиг → на склад (чек-лист + вкладка Склад).</li>';
    html+='</ul>';
    document.getElementById('reminders').innerHTML=html;
}

function renderOrderMap(order, links){
    const ups=links.filter(l=>l.link_type==='uplink');
    const dls=links.filter(l=>l.link_type==='downlink');
    function diagram(title, swIp, swModel, getPort){
        const conns=[];
        ups.forEach(l=>conns.push({side:'left', port:getPort(l), dev:l.upstream_device, dport:l.upstream_port}));
        dls.forEach(l=>conns.push({side:'right', port:getPort(l), dev:l.upstream_device, dport:l.upstream_port}));
        const W=920, rowH=56, H=Math.max(220, conns.length*rowH+100);
        const cx=W/2, cy=H/2;
        let svg='<svg width="'+W+'" height="'+H+'">';
        svg+='<rect x="'+(cx-120)+'" y="'+(cy-35)+'" width="240" height="70" rx="8" fill="#22303c"/>';
        svg+='<text x="145" y="26" text-anchor="middle" font-size="12" fill="#2980b9">⬆️ UPLINK (вверх, к ядру)</text>';
        svg+='<text x="'+(W-145)+'" y="26" text-anchor="middle" font-size="12" fill="#27ae60">⬇️ DOWNLINK (соседние свитчи)</text>';
        svg+='<text x="'+cx+'" y="'+(cy-5)+'" fill="#fff" text-anchor="middle" font-size="13">'+swIp+'</text>';
        svg+='<text x="'+cx+'" y="'+(cy+15)+'" fill="#9fb3c8" text-anchor="middle" font-size="11">'+(swModel||'')+'</text>';
        let li=0, ri=0;
        conns.forEach(c=>{
            if(c.side==='left'){
                const y=60+li*rowH; li++;
                svg+='<rect x="20" y="'+(y-20)+'" width="250" height="40" rx="6" fill="#eaf2f8" stroke="#2980b9"/>';
                svg+='<text x="145" y="'+(y-3)+'" text-anchor="middle" font-size="11" fill="#2c3e50">'+(c.dev||'?')+'</text>';
                svg+='<text x="145" y="'+(y+12)+'" text-anchor="middle" font-size="10" fill="#7f8c8d">порт там: '+(c.dport||'?')+'</text>';
                svg+='<line x1="270" y1="'+y+'" x2="'+(cx-120)+'" y2="'+cy+'" stroke="#2980b9" stroke-width="2"/>';
                svg+='<text x="'+((270+cx-120)/2)+'" y="'+((y+cy)/2-4)+'" font-size="11" fill="#2980b9">п'+(c.port||'?')+'</text>';
            } else {
                const y=60+ri*rowH; ri++;
                svg+='<rect x="'+(W-270)+'" y="'+(y-20)+'" width="250" height="40" rx="6" fill="#eafaf0" stroke="#27ae60"/>';
                svg+='<text x="'+(W-145)+'" y="'+(y-3)+'" text-anchor="middle" font-size="11" fill="#2c3e50">'+(c.dev||'?')+'</text>';
                svg+='<text x="'+(W-145)+'" y="'+(y+12)+'" text-anchor="middle" font-size="10" fill="#7f8c8d">порт там: '+(c.dport||'?')+'</text>';
                svg+='<line x1="'+(cx+120)+'" y1="'+cy+'" x2="'+(W-270)+'" y2="'+y+'" stroke="#27ae60" stroke-width="2"/>';
                svg+='<text x="'+((cx+120+W-270)/2)+'" y="'+((cy+y)/2-4)+'" font-size="11" fill="#27ae60">п'+(c.port||'?')+'</text>';
            }
        });
        svg+='</svg>';
        return '<h4>'+title+'</h4>'+svg;
    }
    var mapHtml='';
    if((order.order_type||'replace')!=='new'){
        mapHtml+=diagram('КАК БЫЛО (старый '+order.old_switch_ip+')', order.old_switch_ip, order.old_switch_model, l=>l.old_port) +
        '<hr style="margin:1rem 0;">';
    }
    mapHtml+=diagram('КАК СТАНЕТ (новый '+order.new_switch_ip+')', order.new_switch_ip, order.new_switch_model, l=>l.new_port||l.old_port);
    document.getElementById('orderMap').innerHTML=mapHtml;
}

loadSubscribers();
loadLinks();
renderCamPlan();
</script>
{% endblock %}
'''

MAP_HTML = '''
{% extends "base.html" %}
{% block title %}Карта сети{% endblock %}
{% block content %}
<style>
#mapCanvas{position:relative;height:760px;background:#eef2f5;border-radius:8px;overflow:auto;border:1px solid #ddd;}
#wireSvg{position:absolute;top:0;left:0;pointer-events:none;}
#wireSvg .hit{pointer-events:stroke;cursor:pointer;}
.sw-panel{position:absolute;background:#22303c;border-radius:6px;box-shadow:0 4px 10px rgba(0,0,0,.35);padding:8px;user-select:none;z-index:2;}
.sw-header{display:flex;justify-content:space-between;align-items:center;cursor:move;color:#fff;font-weight:600;font-size:13px;margin-bottom:4px;gap:8px;}
.sw-btns button{background:#e74c3c;border:none;color:#fff;border-radius:4px;cursor:pointer;margin-left:4px;font-size:11px;padding:2px 6px;}
.sw-btns button.edit{background:#f39c12;}
.sw-model{color:#9fb3c8;font-size:11px;margin-bottom:6px;}
.sw-ports{display:grid;grid-template-columns:repeat(12,24px);gap:3px;}
.sw-port{width:24px;height:24px;background:#55606a;border:1px solid #39424b;border-radius:3px;color:#cfd8e3;font-size:10px;display:flex;align-items:center;justify-content:center;cursor:pointer;}
.sw-port.used{background:#27ae60;border-color:#1e8449;color:#fff;}
.sw-port.sub{background:#e67e22;border-color:#ba4a00;color:#fff;}
.sw-port.broken{background:#e74c3c;border-color:#943126;color:#fff;}
.sw-port.reserved{background:#8e44ad;border-color:#6c3483;color:#fff;}
.sw-port.sel{outline:2px solid #f1c40f;background:#f1c40f;color:#22303c;}
.map-legend{display:flex;gap:1.2rem;margin-bottom:.75rem;font-size:.85rem;align-items:center;flex-wrap:wrap;}
.chip{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:middle;margin-right:5px;}
.map-hint{margin-top:.75rem;color:#7f8c8d;font-size:.9rem;}
</style>

<div class="page-header">
    <h1>🗺️ Карта сети</h1>
    <div class="header-actions">
        <button class="btn btn-primary" onclick="addDevice()">+ Коммутатор</button>
        <button class="btn btn-success" id="connectBtn" onclick="toggleConnectMode()">🔌 Соединить порты</button>
    </div>
</div>

<div class="map-legend">
    <span><span class="chip" style="background:#55606a"></span>Свободен</span>
    <span><span class="chip" style="background:#27ae60"></span>Занят (линия)</span>
    <span><span class="chip" style="background:#f1c40f"></span>Выбран</span>
    <span><span class="chip" style="background:#e67e22"></span>Абонент</span>
    <span><span class="chip" style="background:#e74c3c"></span>Битый</span>
    <span><span class="chip" style="background:#8e44ad"></span>Резерв</span>
    <span>✎ имя · ✕ удалить · тянуть за шапку · клик по проводу = удалить линию</span>
</div>

<div class="map-container">
    <div id="mapCanvas">
        <svg id="wireSvg" width="2400" height="1400"></svg>
    </div>
</div>
<div class="map-controls" style="margin-top:1rem;">
    <h3>Устройства на карте</h3>
    <div id="devicesList"></div>
</div>
<div id="hint" class="map-hint">Добавьте коммутаторы, нажмите «Соединить порты», кликните порт на одном устройстве, затем порт на другом.</div>

<div id="portMenuModal" class="modal">
    <div class="modal-content" style="max-width:480px;">
        <h2 id="portMenuTitle">Порт</h2>
        <div class="form-group"><label>Тип порта:</label>
            <select id="pmType">
                <option value="subscriber">👤 Абонентский</option>
                <option value="trunk">🔗 Магистральный</option>
                <option value="reserved">📌 Резерв</option>
                <option value="broken">❌ Битый</option>
                <option value="free">⬜ Свободен (сбросить метку)</option>
            </select>
        </div>
        <div class="form-group"><label>Метка (абонент / адрес / куда идёт):</label>
            <input type="text" id="pmLabel" placeholder="Напр.: Иванов, кв.17 / uplink на ядро"></div>
        <div class="form-row">
            <div class="form-group"><label>VLAN:</label><input type="number" id="pmVlan"></div>
            <div class="form-group"><label>MAC:</label><input type="text" id="pmMac"></div>
        </div>
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="savePortMark()">💾 Сохранить</button>
            <button class="btn btn-secondary" onclick="closePortMenu()">Отмена</button>
        </div>
    </div>
</div>

<div id="addDeviceModal" class="modal">
    <div class="modal-content">
        <h2>➕ Добавить коммутатор</h2>
        <form id="addDeviceForm">
            <div class="form-group"><label>Название:</label><input type="text" id="deviceName" required></div>
            <div class="form-row">
                <div class="form-group"><label>IP адрес:</label><input type="text" id="deviceIp"></div>
                <div class="form-group"><label>Модель:</label><input type="text" id="deviceModel"></div>
            </div>
            <div class="form-row">
                <div class="form-group"><label>Портов:</label><input type="number" id="devicePorts" value="28"></div>
            <div class="form-group"><label>Адрес:</label><input type="text" id="deviceLocation" placeholder="Где стоит"></div>
                <div class="form-group"><label>Тип:</label>
                    <select id="deviceType"><option value="switch">Коммутатор</option><option value="core">Ядро</option></select>
                </div>
            </div>
            <div class="modal-actions">
                <button type="submit" class="btn btn-primary">💾 Сохранить</button>
                <button type="button" class="btn btn-secondary" onclick="closeDeviceModal()">Отмена</button>
            </div>
        </form>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
let devices=[], conns=[], connectMode=false, sel=null, drag=null, marks={};

async function loadMap(){
    devices = await (await fetch('/api/network-map')).json();
    conns = await (await fetch('/api/map-connections')).json();
    const allmarks = await (await fetch('/api/port-marks')).json();
    marks={};
    allmarks.forEach(m=>{ (marks[m.device_id]=marks[m.device_id]||{})[m.port]=m; });
    renderAll();
}

function renderAll(){
    const canvas = document.getElementById('mapCanvas');
    canvas.querySelectorAll('.sw-panel').forEach(el=>el.remove());
    devices.forEach(dev=>canvas.appendChild(makePanel(dev)));
    requestAnimationFrame(drawWires);
    renderDevicesList();
}

function portClass(devId,port,used){
    const m=(marks[devId]||{})[port];
    if(m){
        if(m.port_type==='broken') return 'broken';
        if(m.port_type==='trunk') return 'used';
        if(m.port_type==='subscriber') return 'sub';
        if(m.port_type==='reserved') return 'reserved';
    }
    if(used[port]) return 'used';
    return '';
}
function portTitle(devId,port,used){
    const m=(marks[devId]||{})[port];
    let t='';
    if(m){
        t='Порт '+port+' ['+m.port_type+']';
        if(m.label) t+=' '+m.label;
        if(m.vlan) t+=' | VLAN '+m.vlan;
        if(m.mac) t+=' | '+m.mac;
    } else if(used[port]){
        t='Порт '+port+': магистраль (линия на карте)';
    } else {
        t='Порт '+port+': свободен';
    }
    return t.replace(/"/g,'&quot;');
}
function makePanel(dev){
    const used={};
    conns.forEach(c=>{
        if(c.from_device_id===dev.id) used[c.from_port]=1;
        if(c.to_device_id===dev.id) used[c.to_port]=1;
    });
    const n=dev.total_ports||24;
    let ports='';
    for(let i=1;i<=n;i++){
        const cls=portClass(dev.id,i,used);
        ports+=`<div class="sw-port ${cls}" data-port="${i}" title="${portTitle(dev.id,i,used)}" onclick="portClick(${dev.id},${i},this)">${i}</div>`;
    }
    const p=document.createElement('div');
    p.className='sw-panel'; p.dataset.id=dev.id;
    p.style.left=(dev.position_x||40)+'px';
    p.style.top=(dev.position_y||40)+'px';
    p.innerHTML=`
        <div class="sw-header" onpointerdown="startDrag(event,${dev.id})">
            <span>🖧 ${dev.name}${dev.ip_address?' · '+dev.ip_address:''}</span>
            <span class="sw-btns">
                <button class="edit" title="Переименовать" onclick="event.stopPropagation();renameDevice(${dev.id})">✎</button>
                <button title="Удалить" onclick="event.stopPropagation();deleteDevice(${dev.id})">✕</button>
            </span>
        </div>
        <div class="sw-model">${dev.model||'—'} · портов: ${n}</div>
        <div class="sw-model">📍 ${dev.location||'адрес не указан'}</div>
        <div class="sw-ports">${ports}</div>`;
    return p;
}

function portEl(devId,port){
    return document.querySelector(`.sw-panel[data-id="${devId}"] .sw-port[data-port="${port}"]`);
}

function center(el){
    const canvas=document.getElementById('mapCanvas');
    const c=canvas.getBoundingClientRect();
    const r=el.getBoundingClientRect();
    return {x:r.left-c.left+canvas.scrollLeft+r.width/2,
            y:r.top-c.top+canvas.scrollTop+r.height/2};
}

function drawWires(){
    const svg=document.getElementById('wireSvg');
    svg.innerHTML='';
    conns.forEach(c=>{
        const a=portEl(c.from_device_id,c.from_port);
        const b=portEl(c.to_device_id,c.to_port);
        if(!a||!b) return;
        const p1=center(a), p2=center(b);
        const mx=(p1.x+p2.x)/2, my=(p1.y+p2.y)/2;
        svg.innerHTML+=`
            <line x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="#2980b9" stroke-width="3"/>
            <line class="hit" x1="${p1.x}" y1="${p1.y}" x2="${p2.x}" y2="${p2.y}" stroke="transparent" stroke-width="14" onclick="deleteConn(${c.id})"/>
            <text x="${mx}" y="${my-6}" font-size="11" fill="#2c3e50" text-anchor="middle">p${c.from_port} - p${c.to_port}</text>`;
    });
}

function portClick(devId,port,el){
    if(!connectMode){ openPortMenu(devId,port); return; }
    if(sel && sel.devId===devId && sel.port===port){ el.classList.remove('sel'); sel=null; setHint('Выбор сброшен.'); return; }
    if(!sel){ sel={devId,port}; el.classList.add('sel'); setHint('Выбран порт '+port+'. Теперь кликните порт на ДРУГОМ коммутаторе.'); return; }
    const a=portEl(sel.devId,sel.port);
    if(a) a.classList.remove('sel');
    const from=sel; sel=null;
    fetch('/api/map-connections',{method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({from_device:from.devId,from_port:from.port,to_device:devId,to_port:port})})
        .then(()=>{ setHint('Линия создана.'); loadMap(); });
}

function deleteConn(id){
    if(!confirm('Удалить эту линию?')) return;
    fetch('/api/map-connections/'+id,{method:'DELETE'}).then(()=>loadMap());
}

function toggleConnectMode(){
    connectMode=!connectMode;
    const b=document.getElementById('connectBtn');
    b.className = connectMode?'btn btn-danger':'btn btn-success';
    b.textContent = connectMode?'⛔ Отключить режим':'🔌 Соединить порты';
    setHint(connectMode?'Режим соединения ВКЛ: кликните порт на одном коммутаторе, затем порт на другом.':'Режим соединения выключен.');
}

function setHint(t){ document.getElementById('hint').textContent=t; }

function deleteDevice(id){
    if(!confirm('Удалить коммутатор и все его линии?')) return;
    fetch('/api/network-map/'+id,{method:'DELETE'}).then(()=>loadMap());
}

function renameDevice(id){
    const dev=devices.find(d=>d.id===id);
    const name=prompt('Новое название:',dev.name);
    if(name===null) return;
    fetch('/api/network-map/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name})}).then(()=>loadMap());
}

function startDrag(e,id){
    const panel=e.currentTarget.closest('.sw-panel');
    drag={id,el:panel,sx:e.clientX,sy:e.clientY,ox:panel.offsetLeft,oy:panel.offsetTop};
    e.preventDefault();
}
document.addEventListener('pointermove',e=>{
    if(!drag) return;
    drag.el.style.left=(drag.ox+e.clientX-drag.sx)+'px';
    drag.el.style.top=(drag.oy+e.clientY-drag.sy)+'px';
    drawWires();
});
document.addEventListener('pointerup',()=>{
    if(!drag) return;
    fetch('/api/network-map/'+drag.id,{method:'PUT',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({position_x:drag.el.offsetLeft,position_y:drag.el.offsetTop})});
    drag=null;
});

function addDevice(){ document.getElementById('addDeviceModal').style.display='block'; }
function closeDeviceModal(){ document.getElementById('addDeviceModal').style.display='none'; document.getElementById('addDeviceForm').reset(); }

document.getElementById('addDeviceForm').addEventListener('submit',async e=>{
    e.preventDefault();
    const data={
        name:document.getElementById('deviceName').value,
        ip_address:document.getElementById('deviceIp').value,
        model:document.getElementById('deviceModel').value,
        total_ports:parseInt(document.getElementById('devicePorts').value)||24,
        device_type:document.getElementById('deviceType').value,
        position_x:60+Math.random()*500,
        position_y:60+Math.random()*400
    };
    var r=await fetch('/api/network-map',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
    var j=await r.json();
    if(j && j.id){
      await fetch('/api/network-map/'+j.id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:document.getElementById('deviceLocation').value})});
    }
    closeDeviceModal(); loadMap();
});

window.onclick=function(ev){
    if(ev.target===document.getElementById('addDeviceModal')) closeDeviceModal();
    if(ev.target===document.getElementById('portMenuModal')) closePortMenu();
};

function renderDevicesList(){
    const box=document.getElementById('devicesList');
    if(!box) return;
    if(devices.length===0){ box.innerHTML='<p>Нет устройств</p>'; return; }
    box.innerHTML=devices.map(d=>`
        <div style="padding:.5rem;margin:.4rem 0;background:#f8f9fa;border-radius:4px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
            <span><strong>${d.name}</strong> ${d.ip_address?'· '+d.ip_address:''} <small>· ${d.model||''} · портов: ${d.total_ports||24}</small></span>
            <button class="btn btn-primary" style="padding:.3rem .8rem;" onclick="focusDevice(${d.id})">🎯 Показать</button>
            <button class="btn btn-secondary" style="padding:.3rem .8rem;" onclick="setLoc(${d.id})">📍</button>
        </div>`).join('');
}

function setLoc(id){
  var dev=devices.find(function(d){return d.id===id;});
  var v=prompt('Адрес коммутатора:', dev? (dev.location||'') : '');
  if(v===null) return;
  fetch('/api/network-map/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:v})}).then(function(){loadMap();});
}
function focusDevice(id){
    const panel=document.querySelector('.sw-panel[data-id="'+id+'"]');
    if(!panel) return;
    const canvas=document.getElementById('mapCanvas');
    canvas.scrollTo({left: Math.max(0,panel.offsetLeft-80), top: Math.max(0,panel.offsetTop-80), behavior:'smooth'});
    panel.style.outline='3px solid #f1c40f';
    setTimeout(()=>{panel.style.outline='';},1500);
}

let pmDev=null, pmPort=null;
function openPortMenu(devId,port){
    pmDev=devId; pmPort=port;
    const dev=devices.find(d=>d.id===devId);
    document.getElementById('portMenuTitle').textContent='Порт '+port+' · '+dev.name;
    const m=(marks[devId]||{})[port];
    document.getElementById('pmType').value = m ? m.port_type : 'subscriber';
    document.getElementById('pmLabel').value = m ? (m.label||'') : '';
    document.getElementById('pmVlan').value = m ? (m.vlan||'') : '';
    document.getElementById('pmMac').value = m ? (m.mac||'') : '';
    document.getElementById('portMenuModal').style.display='block';
}
function closePortMenu(){ document.getElementById('portMenuModal').style.display='none'; }
async function savePortMark(){
    const type=document.getElementById('pmType').value;
    await fetch('/api/port-marks',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        device_id:pmDev, port:pmPort, port_type:type,
        label:document.getElementById('pmLabel').value,
        vlan:parseInt(document.getElementById('pmVlan').value)||0,
        mac:document.getElementById('pmMac').value
    })});
    closePortMenu(); loadMap();
}

loadMap();
</script>
{% endblock %}
'''

app.jinja_loader = DictLoader({'base.html': BASE_HTML})

# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

def get_order_number(order_id):
    conn = get_db()
    q = 'SELECT order_number FROM work_orders WHERE id=?'
    row = conn.execute(q, (order_id,)).fetchone()
    conn.close()
    return row['order_number'] if row else str(order_id)

@app.route('/order/<int:order_id>')
def order_page(order_id):
    return render_template_string(ORDER_HTML, order_id=order_id, order_number=get_order_number(order_id))

@app.route('/planner/<int:order_id>')
def planner_page(order_id):
    return render_template_string(PLANNER_HTML, order_id=order_id, order_number=get_order_number(order_id))

@app.route('/map')
def network_map():
    return render_template_string(MAP_HTML)

# ==================== API ====================

@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db()
    orders = conn.execute('SELECT * FROM work_orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(order) for order in orders])

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.json
    conn = get_db()
    try:
        cursor = conn.cursor()
        existing = cursor.execute('SELECT id FROM work_orders WHERE order_number = ?', (data['order_number'],)).fetchone()
        if existing:
            order_id = existing['id']
            cursor.execute('''
                UPDATE work_orders SET
                old_switch_ip = ?, old_switch_model = ?, old_switch_ports = ?,
                old_switch_location = ?, new_switch_ip = ?, new_switch_model = ?, new_switch_ports = ?
                WHERE id = ?
            ''', (data.get('old_switch_ip',''), data.get('old_switch_model',''), int(data.get('old_switch_ports',28)),
                  data.get('old_switch_location',''), data.get('new_switch_ip',''), data.get('new_switch_model',''),
                  int(data.get('new_switch_ports',28)), order_id))
            cursor.execute('DELETE FROM links WHERE order_id = ?', (order_id,))
        else:
            cursor.execute('''
                INSERT INTO work_orders 
                (order_number, created_at, old_switch_ip, old_switch_model, old_switch_ports,
                 old_switch_location, new_switch_ip, new_switch_model, new_switch_ports, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['order_number'],
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                data.get('old_switch_ip', ''),
                data.get('old_switch_model', ''),
                int(data.get('old_switch_ports', 28)),
                data.get('old_switch_location', ''),
                data.get('new_switch_ip', ''),
                data.get('new_switch_model', ''),
                int(data.get('new_switch_ports', 28)),
                'created'
            ))
            order_id = cursor.lastrowid
        conn.commit()
        cnt = cursor.execute('SELECT COUNT(*) c FROM order_steps WHERE order_id = ?', (order_id,)).fetchone()['c']
        if not cnt:
            for i, st in enumerate(DEFAULT_STEPS):
                cursor.execute('INSERT INTO order_steps (order_id, step_text, done, pos) VALUES (?,?,0,?)', (order_id, st, i))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'order_id': order_id})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    conn = get_db()
    order = conn.execute('SELECT * FROM work_orders WHERE id = ?', (order_id,)).fetchone()
    conn.close()
    if order:
        return jsonify(dict(order))
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/subscribers/<int:order_id>', methods=['GET'])
def get_subscribers(order_id):
    conn = get_db()
    subscribers = conn.execute('''
        SELECT * FROM subscribers WHERE order_id = ? ORDER BY old_port
    ''', (order_id,)).fetchall()
    conn.close()
    return jsonify([dict(sub) for sub in subscribers])

@app.route('/api/subscribers', methods=['POST'])
def add_subscriber():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscribers 
        (order_id, old_port, new_port, subscriber_name, address, vlan, mac_address, is_broken, is_camera, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['order_id'],
        data.get('old_port', 0),
        data.get('new_port', 0),
        data.get('subscriber_name', ''),
        data.get('address', ''),
        data.get('vlan', 0),
        data.get('mac_address', ''),
        data.get('is_broken', 0),
        data.get('is_camera', 0),
        data.get('notes', '')
    ))
    conn.commit()
    subscriber_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'subscriber_id': subscriber_id})

@app.route('/api/subscribers/<int:subscriber_id>', methods=['PUT'])
def update_subscriber(subscriber_id):
    data = request.json
    conn = get_db()
    
    sets = []
    values = []
    
    if 'new_port' in data:
        sets.append('new_port = ?')
        values.append(data['new_port'])
    if 'is_broken' in data:
        sets.append('is_broken = ?')
        values.append(data['is_broken'])
    if 'is_camera' in data:
        sets.append('is_camera = ?')
        values.append(data['is_camera'])
    
    if sets:
        values.append(subscriber_id)
        conn.execute(f'''
            UPDATE subscribers SET {', '.join(sets)} WHERE id = ?
        ''', values)
        conn.commit()
    
    conn.close()
    return jsonify({'success': True})

@app.route('/api/subscribers/<int:subscriber_id>', methods=['DELETE'])
def delete_subscriber(subscriber_id):
    conn = get_db()
    conn.execute('DELETE FROM subscribers WHERE id = ?', (subscriber_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/links/<int:order_id>', methods=['GET', 'POST'])
def handle_links(order_id):
    conn = get_db()
    if request.method == 'GET':
        links = conn.execute('''
            SELECT * FROM links WHERE order_id = ?
        ''', (order_id,)).fetchall()
        conn.close()
        return jsonify([dict(link) for link in links])
    elif request.method == 'POST':
        data = request.json
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO links 
            (order_id, link_type, old_port, upstream_device, upstream_port)
            VALUES (?, 'uplink', ?, ?, ?)
        ''', (order_id, data['old_port'], data.get('upstream_device', ''), 
              data.get('upstream_port', 0)))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/network-map', methods=['GET'])
def get_network_map():
    conn = get_db()
    devices = conn.execute('SELECT * FROM network_devices').fetchall()
    conn.close()
    return jsonify([dict(dev) for dev in devices])

@app.route('/api/network-map', methods=['POST'])
def save_network_device():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO network_devices 
        (device_type, name, ip_address, model, location, total_ports, 
         position_x, position_y, parent_device_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('device_type', 'switch'),
        data.get('name', ''),
        data.get('ip_address', ''),
        data.get('model', ''),
        data.get('location', ''),
        data.get('total_ports', 28),
        data.get('position_x', 0),
        data.get('position_y', 0),
        data.get('parent_device_id')
    ))
    conn.commit()
    device_id = cursor.lastrowid
    conn.close()
    return jsonify({'success': True, 'device_id': device_id})

@app.route('/api/auto-plan/<int:order_id>', methods=['POST'])
def auto_plan(order_id):
    conn = get_db()
    
    order = conn.execute('''
        SELECT old_switch_ports, new_switch_ports FROM work_orders WHERE id = ?
    ''', (order_id,)).fetchone()
    
    if not order:
        conn.close()
        return jsonify({'success': False, 'error': 'Order not found'}), 404
    
    new_ports_count = order['new_switch_ports']
    
    uplink_ports = []
    links = conn.execute('SELECT old_port FROM links WHERE order_id = ?', (order_id,)).fetchall()
    uplink_ports = [link['old_port'] for link in links]
    
    subscribers = conn.execute('''
        SELECT id, old_port FROM subscribers 
        WHERE order_id = ? AND (new_port = 0 OR new_port IS NULL) AND is_broken = 0
        ORDER BY old_port
    ''', (order_id,)).fetchall()
    
    new_port = 1
    assigned = 0
    for sub in subscribers:
        while new_port in uplink_ports or new_port > new_ports_count:
            new_port += 1
        
        if new_port > new_ports_count:
            break
        
        conn.execute('''
            UPDATE subscribers SET new_port = ? WHERE id = ?
        ''', (new_port, sub['id']))
        new_port += 1
        assigned += 1
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'assigned': assigned})


@app.route('/api/network-map/<int:device_id>', methods=['PUT'])
def update_network_device(device_id):
    data = request.json
    conn = get_db()
    sets, vals = [], []
    for f in ('name','ip_address','model','location','total_ports','position_x','position_y'):
        if f in data:
            sets.append(f + ' = ?')
            vals.append(data[f])
    if sets:
        vals.append(device_id)
        conn.execute('UPDATE network_devices SET ' + ', '.join(sets) + ' WHERE id = ?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/network-map/<int:device_id>', methods=['DELETE'])
def delete_network_device(device_id):
    conn = get_db()
    conn.execute('DELETE FROM map_connections WHERE from_device_id = ? OR to_device_id = ?', (device_id, device_id))
    conn.execute('DELETE FROM network_devices WHERE id = ?', (device_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/map-connections', methods=['GET'])
def get_map_connections():
    conn = get_db()
    rows = conn.execute('SELECT * FROM map_connections').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/map-connections', methods=['POST'])
def add_map_connection():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO map_connections (from_device_id, from_port, to_device_id, to_port, note) VALUES (?,?,?,?,?)',
                (data['from_device'], data['from_port'], data['to_device'], data['to_port'], data.get('note','')))
    conn.commit()
    cid = cur.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': cid})

@app.route('/api/map-connections/<int:conn_id>', methods=['DELETE'])
def delete_map_connection(conn_id):
    conn = get_db()
    conn.execute('DELETE FROM map_connections WHERE id = ?', (conn_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/port-marks', methods=['GET'])
def get_all_port_marks():
    conn = get_db()
    rows = conn.execute('SELECT * FROM port_marks').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/port-marks', methods=['POST'])
def set_port_mark():
    data = request.json
    conn = get_db()
    conn.execute('DELETE FROM port_marks WHERE device_id = ? AND port = ?', (data['device_id'], data['port']))
    if data.get('port_type') and data['port_type'] != 'free':
        conn.execute('INSERT INTO port_marks (device_id, port, port_type, label, vlan, mac) VALUES (?,?,?,?,?,?)',
                     (data['device_id'], data['port'], data['port_type'], data.get('label',''), data.get('vlan') or 0, data.get('mac','')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/downlinks/<int:order_id>', methods=['POST'])
def add_downlink(order_id):
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO links (order_id, link_type, old_port, new_port, upstream_device, upstream_port) VALUES (?,?,?,?,?,?)',
                (order_id, 'downlink', data['old_port'], data.get('new_port') or 0,
                 data.get('upstream_device',''), data.get('upstream_port') or 0))
    conn.commit(); conn.close()
    return jsonify({'success': True})

@app.route('/api/links/<int:link_id>', methods=['PUT', 'DELETE'])
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


@app.route('/api/steps/<int:order_id>', methods=['GET'])
def get_steps(order_id):
    conn = get_db()
    rows = conn.execute('SELECT * FROM order_steps WHERE order_id = ? ORDER BY pos', (order_id,)).fetchall()
    conn.close()
    rows = [dict(r) for r in rows]
    fl = auto_flags(order_id)
    for k, r in enumerate(rows):
        if fl.get(k):
            r['done'] = 1
    return jsonify(rows)

@app.route('/api/steps-create/<int:order_id>', methods=['POST'])
def create_steps(order_id):
    conn = get_db()
    cnt = conn.execute('SELECT COUNT(*) c FROM order_steps WHERE order_id = ?', (order_id,)).fetchone()['c']
    if not cnt:
        for i, st in enumerate(DEFAULT_STEPS):
            conn.execute('INSERT INTO order_steps (order_id, step_text, done, pos) VALUES (?,?,0,?)', (order_id, st, i))
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/steps/<int:step_id>', methods=['PUT'])
def toggle_step(step_id):
    data = request.json
    conn = get_db()
    conn.execute('UPDATE order_steps SET done = ? WHERE id = ?', (1 if data.get('done') else 0, step_id))
    conn.commit(); conn.close()
    return jsonify({'success': True})


@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db()
    for t in ('links','subscribers','fdb_tables','order_steps'):
        conn.execute('DELETE FROM ' + t + ' WHERE order_id = ?', (order_id,))
    conn.execute('DELETE FROM work_orders WHERE id = ?', (order_id,))
    conn.commit(); conn.close()
    return jsonify({'success': True})


@app.route('/api/orders-upsert', methods=['POST'])
def upsert_order():
    data = request.json
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute('SELECT id FROM work_orders WHERE order_number = ?', (data['order_number'],)).fetchone()
    if row:
        order_id = row['id']
        cur.execute('''UPDATE work_orders SET old_switch_ip=?, old_switch_model=?, old_switch_ports=?,
            old_switch_location=?, new_switch_ip=?, new_switch_model=?, new_switch_ports=? WHERE id=?''',
            (data.get('old_switch_ip',''), data.get('old_switch_model',''), int(data.get('old_switch_ports',28)),
             data.get('old_switch_location',''), data.get('new_switch_ip',''), data.get('new_switch_model',''),
             int(data.get('new_switch_ports',28)), order_id))
        cur.execute('DELETE FROM links WHERE order_id = ?', (order_id,))
    else:
        cur.execute('''INSERT INTO work_orders (order_number, created_at, old_switch_ip, old_switch_model,
            old_switch_ports, old_switch_location, new_switch_ip, new_switch_model, new_switch_ports, status)
            VALUES (?,?,?,?,?,?,?,?,?,?)''',
            (data['order_number'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
             data.get('old_switch_ip',''), data.get('old_switch_model',''), int(data.get('old_switch_ports',28)),
             data.get('old_switch_location',''), data.get('new_switch_ip',''), data.get('new_switch_model',''),
             int(data.get('new_switch_ports',28)), 'created'))
        order_id = cur.lastrowid
    conn.commit()
    cnt = cur.execute('SELECT COUNT(*) c FROM order_steps WHERE order_id = ?', (order_id,)).fetchone()['c']
    if not cnt:
        for i, st in enumerate(DEFAULT_STEPS):
            cur.execute('INSERT INTO order_steps (order_id, step_text, done, pos) VALUES (?,?,0,?)', (order_id, st, i))
        conn.commit()
    cur.execute('UPDATE work_orders SET order_type=?, new_switch_location=?, old_podyezd=?, new_podyezd=? WHERE id=?',
        (data.get('order_type', 'replace'), data.get('new_switch_location', ''),
         data.get('old_podyezd', ''), data.get('new_podyezd', ''), order_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'order_id': order_id})



STOCK_HTML = """{% extends "base.html" %}
{% block title %}Склад коммутаторов{% endblock %}
{% block content %}
<div class="page-header">
    <h1>📦 Склад / жизненный цикл коммутаторов</h1>
    <button class="btn btn-primary" onclick="document.getElementById('addStockModal').style.display='block'">➕ Добавить</button>
</div>
<table class="data-table">
<thead><tr><th>Модель</th><th>Серийник</th><th>Последний IP</th><th>Адрес</th><th>Наряд</th><th>Статус</th><th>Заметки</th><th>Действия</th></tr></thead>
<tbody id="stockTable"></tbody>
</table>
<h3>📷 Фото выбранного коммутатора</h3>
<div id="stockPhotoTitle" style="color:#7f8c8d;">Нажмите 📷 в строке таблицы</div>
<div id="stockPhotos"></div>
<input type="file" id="stockPhotoInput" accept="image/*" onchange="uploadAttachment('inventory',curStockId,'stockPhotos',this)">
<div id="addStockModal" class="modal"><div class="modal-content">
<h2>➕ Добавить коммутатор на учёт</h2>
<form id="addStockForm">
<div class="form-row">
<div class="form-group"><label>Модель:</label><input id="stModel" required></div>
<div class="form-group"><label>Серийный номер:</label><input id="stSerial"></div>
</div>
<div class="form-row">
<div class="form-group"><label>Последний IP:</label><input id="stIp"></div>
<div class="form-group"><label>Наряд №:</label><input id="stOrder"></div>
<div class="form-group"><label>Адрес:</label><input id="stLoc" placeholder="Где стоит"></div>
</div>
<div class="form-group"><label>Статус:</label><select id="stStatus">
<option value="in_stock">📦 На складе</option><option value="in_use">🔌 В работе</option>
<option value="removed">📤 Снят (ожидает)</option><option value="to_reset">🔄 Нужно сбросить</option>
<option value="reset_done">✅ Сброшен</option><option value="written_off">🗑 Списан</option>
</select></div>
<div class="form-group"><label>Заметки:</label><input id="stNotes"></div>
<div class="modal-actions">
<button type="submit" class="btn btn-primary">💾 Сохранить</button>
<button type="button" class="btn btn-secondary" onclick="document.getElementById('addStockModal').style.display='none'">Отмена</button>
</div>
</form>
</div></div>
{% endblock %}
{% block scripts %}
<script>
const STATUS={in_stock:'📦 На складе',in_use:'🔌 В работе',removed:'📤 Снят (ожидает)',to_reset:'🔄 Нужно сбросить',reset_done:'✅ Сброшен',written_off:'🗑 Списан'};
const STATUS_COLOR={in_stock:'#95a5a6',in_use:'#27ae60',removed:'#f39c12',to_reset:'#e74c3c',reset_done:'#3498db',written_off:'#7f8c8d'};
let curStockId=null, stockRows=[];
async function loadStock(){
    stockRows=await (await fetch('/api/inventory')).json();
    document.getElementById('stockTable').innerHTML=stockRows.map(r=>`
        <tr style="background:${r.status==='to_reset'?'#fdecea':r.status==='removed'?'#fef9e7':''}">
        <td>${r.model||'-'}</td><td>${r.serial||'-'}</td><td>${r.last_ip||'-'}</td><td>${r.location||'-'}</td><td>${r.order_number||'-'}</td>
        <td><span class="badge" style="background:${STATUS_COLOR[r.status]||'#95a5a6'};color:#fff;">${STATUS[r.status]||r.status}</span></td>
        <td>${r.notes||''}</td>
        <td><select id="sel_${r.id}">${Object.keys(STATUS).map(k=>`<option value="${k}" ${k===r.status?'selected':''}>${STATUS[k]}</option>`).join('')}</select>
            <button class="btn btn-primary" style="padding:4px 8px;" onclick="applyStatus(${r.id})">✔</button>
            <button class="btn btn-secondary" style="padding:4px 8px;" onclick="openStockPhotos(${r.id})">📷</button>
            <button class="btn btn-danger" style="padding:4px 8px;" onclick="delStock(${r.id})">🗑</button>
        </td></tr>`).join('')||'<tr><td colspan=7>Пока пусто</td></tr>';
}
async function applyStatus(id){
    await fetch('/api/inventory/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:document.getElementById('sel_'+id).value})});
    loadStock();
}
function delStock(id){ if(confirm('Удалить запись?')) fetch('/api/inventory/'+id,{method:'DELETE'}).then(()=>loadStock()); }
function openStockPhotos(id){
    curStockId=id;
    const r=stockRows.find(x=>x.id===id);
    document.getElementById('stockPhotoTitle').textContent='Фото: '+(r?r.model:'');
    loadAttachments('inventory',id,'stockPhotos');
}
document.getElementById('addStockForm').addEventListener('submit',async e=>{
    e.preventDefault();
    await fetch('/api/inventory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        model:document.getElementById('stModel').value, serial:document.getElementById('stSerial').value,
        last_ip:document.getElementById('stIp').value, order_number:document.getElementById('stOrder').value,
        location:document.getElementById('stLoc').value,
        status:document.getElementById('stStatus').value, notes:document.getElementById('stNotes').value})});
    document.getElementById('addStockModal').style.display='none';
    loadStock();
});
loadStock();
</script>
{% endblock %}"""

FDB_HTML = """{% extends "base.html" %}
{% block title %}FDB таблицы{% endblock %}
{% block content %}
<div class="page-header">
    <h1>📊 FDB таблицы — наряд №{{ order_number }}</h1>
    <div class="header-actions">
        <button class="btn btn-success" onclick="compareFdb()">🔍 Сравнить</button>
        <a href="/order/{{ order_id }}" class="btn btn-secondary">← К наряду</a>
    </div>
</div>
<div class="header-actions" style="margin-bottom:1rem;">
    <button class="btn btn-primary" id="btnOld" onclick="setType('old')">ДО замены</button>
    <button class="btn btn-secondary" id="btnNew" onclick="setType('new')">ПОСЛЕ замены</button>
    <label class="btn btn-secondary" style="cursor:pointer;">📥 Импорт CSV
        <input type="file" id="csvInput" accept=".csv" style="display:none" onchange="importCsv(this)">
    </label>
    <button class="btn btn-primary" onclick="showPaste()">📋 Вставить из буфера</button>
</div>
<div id="pasteBox" style="display:none;margin:1rem 0;background:#fff;padding:1rem;border-radius:8px;">
    <p style="color:#7f8c8d;font-size:.9rem;">Выделите таблицу FDB на базе → Ctrl+C → сюда Ctrl+V → «Разобрать и сохранить».</p>
    <textarea id="pasteArea" style="width:100%;height:220px;font-family:monospace;font-size:12px;"></textarea>
    <div class="header-actions" style="margin-top:.5rem;">
        <button class="btn btn-success" onclick="parseAndSave()">✅ Разобрать и сохранить</button>
        <button class="btn btn-secondary" onclick="hidePaste()">Скрыть</button>
    </div>
</div>
<h3>➕ Добавить запись вручную</h3>
<div class="form-row" style="max-width:950px;">
    <div class="form-group"><label>Порт:</label><input type="number" id="fPort"></div>
    <div class="form-group"><label>VLAN:</label><input type="number" id="fVlan"></div>
    <div class="form-group"><label>MAC:</label><input type="text" id="fMac"></div>
    <div class="form-group"><label>Абонент:</label><input type="text" id="fSub"></div>
    <div class="form-group"><label>&nbsp;</label><button class="btn btn-primary" onclick="addFdb()">Добавить</button></div>
</div>
<p id="fdbCount" style="color:#7f8c8d;font-size:.9rem;"></p>
<table class="data-table">
<thead><tr><th>Порт</th><th>Vlan MAC</th><th>Абонент</th><th></th></tr></thead>
<tbody id="fdbTable"></tbody>
</table>
<h3>🔍 Отчёт сравнения</h3>
<pre id="compareReport" style="background:#fff;padding:1rem;border-radius:8px;white-space:pre-wrap;"></pre>
<h3>📷 Фото (FDB / шильдики / монтаж)</h3>
<div id="fdbPhotos"></div>
<input type="file" id="fdbPhotoInput" accept="image/*" onchange="uploadAttachment('fdb',{{ order_id }},'fdbPhotos',this)">
{% endblock %}
{% block scripts %}
<script>
var orderId={{ order_id }};
var curType='old';
function showPaste(){
  document.getElementById('pasteBox').style.display='block';
}
function hidePaste(){
  document.getElementById('pasteBox').style.display='none';
}
function setType(t){
  curType=t;
  var bo=document.getElementById('btnOld');
  var bn=document.getElementById('btnNew');
  bo.className=(t==='old')?'btn btn-primary':'btn btn-secondary';
  bn.className=(t==='new')?'btn btn-primary':'btn btn-secondary';
  loadFdb();
}
async function loadFdb(){
  try{
  var url='/api/fdb/'+orderId+'?switch_type='+curType;
  var resp=await fetch(url);
  var rows=await resp.json();
  var st=document.getElementById('fdbCount');
  if(st){ st.textContent='Загружено записей: '+rows.length+' (вариант '+curType+')'; }
  if(!Array.isArray(rows)){
    alert('Сервер вернул не список: '+JSON.stringify(rows).slice(0,200));
    return;
  }
  var byPort={};
  rows.forEach(function(r){
    if(!byPort[r.port]) byPort[r.port]=[];
    byPort[r.port].push(r);
  });
  var ports=Object.keys(byPort).sort(function(a,b){return a-b;});
  var html='';
  ports.forEach(function(p){
    var list=byPort[p];
    var subs='';
    var ids=[];
    var macs='';
    list.forEach(function(x){
      ids.push(x.id);
      macs+='vlan: '+x.vlan+' mac: '+x.mac_address+'<br>';
      if(x.subscriber && subs.indexOf(x.subscriber)<0){
        subs=subs? subs+', '+x.subscriber : x.subscriber;
      }
    });
    html+='<tr><td>'+p+'</td>';
    html+='<td style="font-family:monospace;font-size:12px;">'+macs+'</td>';
    html+='<td>'+subs+'</td>';
    var btn='<td><button class="btn btn-danger"';
    btn+=' style="padding:3px 8px"';
    btn+=' onclick="delPort(this.dataset.ids)"';
    btn+=' data-ids="'+ids.join(',')+'">🗑</button></td></tr>';
    html+=btn;
  });
  var tb=document.getElementById('fdbTable');
  tb.innerHTML=html||'<tr><td colspan="4">Пусто</td></tr>';
  }catch(e){
    alert('Ошибка loadFdb: '+e.message);
  }
}
async function delPort(ids){
  if(!confirm('Удалить все записи этого порта?')) return;
  var a=ids.split(',');
  for(var i=0;i<a.length;i++){
    await fetch('/api/fdb/'+a[i],{method:'DELETE'});
  }
  loadFdb();
}
async function addFdb(){
  var body={
    order_id:orderId, switch_type:curType,
    port:parseInt(document.getElementById('fPort').value)||0,
    vlan:document.getElementById('fVlan').value,
    mac_address:document.getElementById('fMac').value,
    subscriber:document.getElementById('fSub').value
  };
  await fetch('/api/fdb',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)});
  loadFdb();
}
function delFdb(id){
  fetch('/api/fdb/'+id,{method:'DELETE'}).then(loadFdb);
}
function importCsv(input){
  var f=input.files[0];
  if(!f) return;
  var fd=new FormData();
  fd.append('file',f);
  fd.append('switch_type',curType);
  fetch('/api/fdb-import/'+orderId,{method:'POST',body:fd})
    .then(function(r){return r.json();})
    .then(function(res){
      alert('Импортировано строк: '+res.count);
      loadFdb();
      input.value='';
    });
}
async function compareFdb(){
  var r=await fetch('/api/fdb-compare/'+orderId);
  var res=await r.json();
  document.getElementById('compareReport').textContent=res.report;
}
async function parseAndSave(){
  var ta=document.getElementById('pasteArea');
  var text=ta.value;
  if(!text.trim()){
    alert('Сначала вставьте таблицу (Ctrl+V)');
    return;
  }
  var body={order_id:orderId, switch_type:curType, text:text};
  var r=await fetch('/api/fdb-paste',{method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify(body)});
  if(!r.ok){ alert('Ошибка сервера '+r.status); return; }
  var res=await r.json();
  if(res.count>0){
    alert('Разобрано и сохранено записей: '+res.count);
    hidePaste();
    ta.value='';
    loadFdb();
    autoCompare();
  }else{
    alert('0 записей. Сервер увидел: '+(res.echo||'').slice(0,300));
  }
}
async function autoCompare(){
  var u1='/api/fdb/'+orderId+'?switch_type=old';
  var u2='/api/fdb/'+orderId+'?switch_type=new';
  var o=await (await fetch(u1)).json();
  var n=await (await fetch(u2)).json();
  if(o.length && n.length){
    compareFdb();
    setTimeout(function(){
      document.getElementById('compareReport').scrollIntoView({behavior:'smooth'});
    },300);
  }
}
loadFdb();
loadAttachments('fdb',orderId,'fdbPhotos');
</script>
{% endblock %}"""

@app.route('/stock')
def stock_page():
    return render_template_string(STOCK_HTML)

@app.route('/fdb/<int:order_id>')
def fdb_page(order_id):
    return render_template_string(FDB_HTML, order_id=order_id, order_number=get_order_number(order_id))

DEFAULT_STEPS = [
    '📋 Выписал данные старого свитча (IP, модель, серийник, фото)',
    '📊 Сохранил FDB таблицу ДО замены',
    '🔌 Выписал uplink и downlink старого свитча',
    '🧰 Подготовил новый свитч (конфиг, VLAN, IP, пароли)',
    '📦 Новый свитч получен / выдан со склада',
    '🔧 Физически заменил коммутатор',
    '⬆️ Подключил uplink (линк поднялся)',
    '⬇️ ПРОПИСАЛ downlink на новом свитче (к соседним свитчам)',
    '👥 Перенёс абонентов по портам',
    '📊 Сохранил FDB таблицу ПОСЛЕ замены',
    '🔍 Сравнил FDB (все на месте, магистрали подняты)',
    '📹 Проверил камеры (VLAN 135)',
    '🗂️ Обновил карточку свитча в базе (base.khotkovo.ru)',
    '🔄 Старый свитч: сбросил конфиг',
    '📦 Старый свитч: вернул на склад (отметил на складе)',
]


@app.route('/api/fdb-paste', methods=['POST'])
def fdb_paste():
    import re as _re
    data = request.json
    order_id = data['order_id']
    st = data.get('switch_type','old')
    text = data.get('text','')
    text = text.replace('\xa0', ' ').replace('\u200b', '').replace('\r', '')
    entries = []
    cur_port = 0
    pat = _re.compile(r'vlan:\s*(\d+)\s*mac:\s*([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2})+)', _re.I)
    mac_only = _re.compile(r'mac:\s*([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2})+)', _re.I)
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _re.match(r'^(\d{1,3})\s*$', line)
        if m:
            cur_port = int(m.group(1))
            continue
        m = _re.match(r'^(\d{1,3})[\s:]+(?=vlan)', line, _re.I)
        if m:
            cur_port = int(m.group(1))
        found = pat.findall(line)
        if not found and 'mac:' in line.lower():
            found = [('', mm) for mm in mac_only.findall(line)]
        if found:
            clean = pat.sub('', line)
            clean = mac_only.sub('', clean)
            clean = _re.sub(r'[\t|]+', ' ', clean)
            clean = _re.sub(r'\s{2,}', ' ', clean).strip()
            for vlan, mac in found:
                entries.append({'port': cur_port, 'vlan': vlan or '', 'mac': mac.upper(),
                                'sub': clean if len(found) == 1 else ''})
        else:
            if entries and not entries[-1]['sub'] and _re.search(r'[A-Za-zА-Яа-я]', line):
                entries[-1]['sub'] = line
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM fdb_tables WHERE order_id = ? AND switch_type = ?', (order_id, st))
    seen = set()
    count = 0
    for e in entries:
        k = (e['port'], e['mac'])
        if k in seen:
            continue
        seen.add(k)
        cur.execute('INSERT INTO fdb_tables (order_id, switch_type, port, vlan, mac_address, subscriber) VALUES (?,?,?,?,?,?)',
                    (order_id, st, e['port'], e['vlan'], e['mac'], e['sub']))
        count += 1
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'count': count, 'echo': text[:300]})



@app.route('/api/fdb/<int:order_id>', methods=['GET'])
def get_fdb(order_id):
    st = request.args.get('switch_type','old')
    conn = get_db()
    q = 'SELECT * FROM fdb_tables WHERE order_id=? AND switch_type=? ORDER BY port'
    rows = conn.execute(q, (order_id, st)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/fdb', methods=['POST'])
def add_fdb():
    d = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO fdb_tables (order_id, switch_type, port, vlan, mac_address, subscriber) VALUES (?,?,?,?,?,?)',
        (d['order_id'], d.get('switch_type','old'), d.get('port',0),
         str(d.get('vlan','')), d.get('mac_address',''), d.get('subscriber','')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': i})

@app.route('/api/fdb/<int:row_id>', methods=['DELETE'])
def delete_fdb(row_id):
    conn = get_db()
    conn.execute('DELETE FROM fdb_tables WHERE id=?', (row_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/fdb-import/<int:order_id>', methods=['POST'])
def import_fdb(order_id):
    f = request.files.get('file')
    st = request.form.get('switch_type','old')
    if not f:
        return jsonify({'success': False, 'count': 0}), 400
    text = f.read().decode('utf-8', errors='ignore')
    first = text.split('\n')[0]
    dl = ';' if ';' in first else ','
    rows = [r for r in csv.reader(io.StringIO(text), delimiter=dl) if r and any(c.strip() for c in r)]
    conn = get_db()
    c = conn.cursor()
    c.execute('DELETE FROM fdb_tables WHERE order_id=? AND switch_type=?', (order_id, st))
    n = 0
    start = 1 if (rows and rows[0][0].strip().lower() in ('порт','port')) else 0
    for r in rows[start:]:
        port = int(''.join(ch for ch in r[0] if ch.isdigit()) or 0)
        vlan = r[1].strip() if len(r) > 1 else ''
        mac = r[2].strip() if len(r) > 2 else ''
        sub = r[3].strip() if len(r) > 3 else ''
        c.execute('INSERT INTO fdb_tables (order_id, switch_type, port, vlan, mac_address, subscriber) VALUES (?,?,?,?,?,?)',
            (order_id, st, port, vlan, mac, sub))
        n += 1
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'count': n})

@app.route('/api/fdb-compare/<int:order_id>', methods=['GET'])
def compare_fdb(order_id):
    conn = get_db()
    old = conn.execute("SELECT port, vlan, mac_address, subscriber FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchall()
    new = conn.execute("SELECT port, vlan, mac_address, subscriber FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchall()
    ups = conn.execute("SELECT old_port, upstream_device, upstream_port FROM links WHERE order_id=? AND link_type='uplink'", (order_id,)).fetchall()
    conn.close()
    om = {r['mac_address'].upper(): r for r in old if r['mac_address']}
    nm = {r['mac_address'].upper(): r for r in new if r['mac_address']}
    nports = {r['port'] for r in new}
    L = []
    L.append('=' * 60)
    L.append('СРАВНЕНИЕ FDB — наряд #%s' % order_id)
    L.append('=' * 60)
    L.append('')
    L.append('МАГИСТРАЛИ (uplink):')
    if not ups:
        L.append('  (uplink не указаны)')
    for u in ups:
        if u['old_port'] in nports:
            L.append('  OK порт %s -> %s порт %s: поднят' % (u['old_port'], u['upstream_device'], u['upstream_port']))
        else:
            L.append('  FAIL порт %s -> %s порт %s: НЕТ МАКОВ' % (u['old_port'], u['upstream_device'], u['upstream_port']))
    L.append('')
    L.append('ПОТЕРЯНЫ:')
    lost = set(om) - set(nm)
    if lost:
        for m in sorted(lost):
            r = om[m]
            L.append('  MAC %s | порт %s | %s' % (m, r['port'], r['subscriber'] or ''))
    else:
        L.append('  все MAC на месте')
    L.append('')
    L.append('НОВЫЕ:')
    added = set(nm) - set(om)
    if added:
        for m in sorted(added):
            r = nm[m]
            L.append('  MAC %s | порт %s | %s' % (m, r['port'], r['subscriber'] or ''))
    else:
        L.append('  (нет)')
    L.append('')
    co = [r for r in old if '135' in str(r['vlan'])]
    cn = [r for r in new if '135' in str(r['vlan'])]
    L.append('КАМЕРЫ (VLAN 135): было %s, стало %s' % (len(co), len(cn)))
    L.append('')
    L.append('ИТОГО: было %s, стало %s' % (len(old), len(new)))
    return jsonify({'report': '\n'.join(L)})

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    conn = get_db()
    rows = conn.execute('SELECT * FROM switch_inventory ORDER BY updated_at DESC').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/inventory', methods=['POST'])
def add_inventory():
    d = request.json
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO switch_inventory (model, serial, last_ip, location, status, order_number, notes, updated_at) VALUES (?,?,?,?,?,?,?,?)',
        (d.get('model',''), d.get('serial',''), d.get('last_ip',''), d.get('location',''),
         d.get('status','in_stock'), d.get('order_number',''), d.get('notes',''),
         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': i})

@app.route('/api/inventory/<int:item_id>', methods=['PUT'])
def update_inventory(item_id):
    d = request.json
    conn = get_db()
    sets = []
    vals = []
    for f in ('model','serial','last_ip','status','order_number','notes','location'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    sets.append('updated_at=?')
    vals.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    vals.append(item_id)
    conn.execute('UPDATE switch_inventory SET ' + ','.join(sets) + ' WHERE id=?', vals)
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/inventory/<int:item_id>', methods=['DELETE'])
def delete_inventory(item_id):
    conn = get_db()
    conn.execute('DELETE FROM switch_inventory WHERE id=?', (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/attachments', methods=['GET'])
def get_attachments():
    et = request.args.get('entity_type')
    eid = request.args.get('entity_id')
    conn = get_db()
    rows = conn.execute('SELECT * FROM attachments WHERE entity_type=? AND entity_id=? ORDER BY created_at', (et, eid)).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/attachments', methods=['POST'])
def add_attachment():
    f = request.files.get('file')
    if not f:
        return jsonify({'success': False}), 400
    ext = os.path.splitext(f.filename)[1] or '.jpg'
    name = uuid.uuid4().hex + ext
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    f.save(os.path.join(UPLOAD_DIR, name))
    if not os.path.exists(os.path.join(UPLOAD_DIR, name)):
        return jsonify({'error': 'файл не записался на диск (место/права?)'}), 500

    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO attachments (entity_type, entity_id, filename, original_name, description, created_at) VALUES (?,?,?,?,?,?)',
        (request.form.get('entity_type','order'), int(request.form.get('entity_id',0)),
         name, f.filename, request.form.get('description',''),
         datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': i})

@app.route('/api/attachments/<int:att_id>', methods=['DELETE'])
def delete_attachment(att_id):
    conn = get_db()
    row = conn.execute('SELECT filename FROM attachments WHERE id=?', (att_id,)).fetchone()
    if row:
        try:
            os.remove(os.path.join(UPLOAD_DIR, row['filename']))
        except OSError:
            pass
        conn.execute('DELETE FROM attachments WHERE id=?', (att_id,))
        conn.commit()
    conn.close()
    return jsonify({'success': True})


DEFAULT_HELP = '''ПАМЯТКА ПО ЗАМЕНЕ КОММУТАТОРА
1. Создать наряд: номер, старый/новый свитч (IP, модель, портов), uplink и downlink.
2. Планировщик: назначить НОВЫЕ порты uplink/downlink; читать блок «НЕ ЗАБЫТЬ» и карту «как было / как станет».
3. FDB: «ДО замены» вставить таблицу со старого свитча; после замены «ПОСЛЕ» с нового; отчёт сравнения строится сам.
4. Страница наряда: чек-лист этапов, фото, кнопка «Закрыть наряд», кнопка «Отчёт».
5. Старый свитч: сбросить конфиг, на вкладке «Склад» поставить статус.
(этот текст можно редактировать)'''

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    d = request.json
    conn = get_db()
    sets = []
    vals = []
    for f in ('status','old_switch_ip','new_switch_ip','old_switch_location','commands_used','vehicle_needed','order_type','new_switch_location','old_podyezd','new_podyezd','old_switch_model','new_switch_model','old_switch_ports','new_switch_ports','order_number'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    if sets:
        vals.append(order_id)
        conn.execute('UPDATE work_orders SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/notes/<key>', methods=['GET','POST'])
def app_notes(key):
    conn = get_db()
    if request.method == 'GET':
        row = conn.execute('SELECT content FROM app_notes WHERE note_key=?', (key,)).fetchone()
        if not row:
            conn.execute('INSERT INTO app_notes (note_key, content) VALUES (?,?)', (key, DEFAULT_HELP))
            conn.commit()
            row = conn.execute('SELECT content FROM app_notes WHERE note_key=?', (key,)).fetchone()
        conn.close()
        return jsonify({'content': row['content']})
    d = request.json
    conn.execute('UPDATE app_notes SET content=? WHERE note_key=?', (d.get('content',''), key))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/report/<int:order_id>')
def order_report(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    if not o:
        conn.close()
        return Response('Наряд не найден', status=404)
    links = conn.execute('SELECT * FROM links WHERE order_id=? ORDER BY link_type, old_port', (order_id,)).fetchall()
    steps = conn.execute('SELECT * FROM order_steps WHERE order_id=? ORDER BY pos', (order_id,)).fetchall()
    subs = conn.execute('SELECT * FROM subscribers WHERE order_id=? ORDER BY old_port', (order_id,)).fetchall()
    oldf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchall()
    newf = conn.execute("SELECT * FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchall()
    conn.close()
    L = []
    L.append('=' * 64)
    L.append('ОТЧЁТ ПО ЗАМЕНЕ КОММУТАТОРА — наряд %s' % o['order_number'])
    L.append('Создан: %s | Статус: %s' % (o['created_at'], o['status']))
    L.append('=' * 64)
    L.append('СТАРЫЙ: %s | %s | портов: %s' % (o['old_switch_ip'], o['old_switch_model'], o['old_switch_ports']))
    L.append('Адрес: %s' % (o['old_switch_location'] or ''))
    L.append('Тип наряда: %s' % ('новая установка' if o['order_type'] == 'new' else 'сервис' if o['order_type'] == 'service' else 'замена'))
    L.append('Адрес нового: %s' % (o['new_switch_location'] or '—'))
    L.append('Подъезды: старый %s / новый %s' % (o['old_podyezd'] or '—', o['new_podyezd'] or '—'))
    L.append('НОВЫЙ:  %s | %s | портов: %s' % (o['new_switch_ip'], o['new_switch_model'], o['new_switch_ports']))
    L.append('')
    L.append('UPLINK:')
    for l in links:
        if l['link_type'] != 'uplink':
            continue
        np = l['new_port'] or 'НЕ НАЗНАЧЕН'
        loc = dev_loc(l['upstream_device'])
        L.append('  порт %s (стар) -> порт %s (нов) | %s%s : порт %s' % (l['old_port'], np, l['upstream_device'], (' 📍 '+loc) if loc else '', l['upstream_port']))
    L.append('')
    L.append('DOWNLINK:')
    for l in links:
        if l['link_type'] != 'downlink':
            continue
        np = l['new_port'] or 'НЕ НАЗНАЧЕН!'
        loc = dev_loc(l['upstream_device'])
        L.append('  порт %s (стар) -> порт %s (нов) | %s%s : порт %s' % (l['old_port'], np, l['upstream_device'], (' 📍 '+loc) if loc else '', l['upstream_port']))
    L.append('')
    L.append('ЭТАПЫ:')
    fl = auto_flags(order_id)
    for k, s in enumerate(steps):
        mark = '[x]' if (s['done'] or fl.get(k)) else '[ ]'
        L.append('  %s %s' % (mark, s['step_text']))
    L.append('')
    om = {r['mac_address'].upper(): r for r in oldf if r['mac_address']}
    nm = {r['mac_address'].upper(): r for r in newf if r['mac_address']}
    L.append('FDB: было %s, стало %s' % (len(oldf), len(newf)))
    lost = set(om) - set(nm)
    added = set(nm) - set(om)
    if lost:
        L.append('  ПОТЕРЯНЫ:')
        for m in sorted(lost):
            r = om[m]
            L.append('    %s порт %s %s' % (m, r['port'], r['subscriber'] or ''))
    if added:
        L.append('  НОВЫЕ:')
        for m in sorted(added):
            r = nm[m]
            L.append('    %s порт %s %s' % (m, r['port'], r['subscriber'] or ''))
    if subs:
        L.append('')
        L.append('АБОНЕНТЫ:')
        for s in subs:
            L.append('  порт %s -> %s | %s | %s' % (s['old_port'], s['new_port'] or '?', s['subscriber_name'] or '', s['address'] or ''))
    conn2 = get_db()
    cams = conn2.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
    conn2.close()
    if cams:
        L.append('')
        L.append('КАМЕРЫ:')
        for c in cams:
            L.append('  %s: %s | серийник %s | IP/ID %s | логин %s | зона: %s' % (
                'СТАР' if c['side'] == 'old' else 'НОВ', c['model'] or '?', c['serial'] or '—',
                c['ip'] or '—', c['login'] or '—', c['zone'] or '—'))
            if c['rtsp']:
                L.append('      RTSP: %s' % c['rtsp'])
            if c['switch_name'] or c['switch_port']:
                L.append('      стоит на: %s, порт %s' % (c['switch_name'] or '—', c['switch_port'] or '—'))
            if c['port'] or c['vlan']:
                L.append('      порт %s / VLAN %s' % (c['port'] or '—', c['vlan'] or '—'))
    L.append('')
    L.append('НАПОМИНАНИЯ:')
    for l in links:
        kind = 'аплинк' if l['link_type'] == 'uplink' else 'линк'
        L.append('  На %s порт %s: %s теперь с %s порт %s' % (l['upstream_device'], l['upstream_port'], kind, o['new_switch_ip'], l['new_port'] or '?'))
    L.append('  Старый %s: сбросить конфиг и вернуть на склад.' % o['old_switch_ip'])
    L.append('')
    L.append('ИСПОЛЬЗОВАННЫЕ КОМАНДЫ: ' + (o['commands_used'] or 'не указаны'))
    L.append('НУЖНА БЫЛА МАШИНА: ' + ('ДА' if o['vehicle_needed'] else 'нет'))
    text = '\n'.join(L)
    return Response(text, mimetype='text/plain; charset=utf-8')


ADMIN_HTML = """{% extends "base.html" %}
{% block title %}Центр обновлений{% endblock %}
{% block content %}
<h1>🛠 Центр обновлений и диагностики</h1>
<style>#prog{display:none;height:8px;background:#ecf0f1;border-radius:4px;overflow:hidden;margin:.5rem 0;}#prog div{width:40%;height:100%;background:#27ae60;animation:mv 1.2s infinite ease-in-out;}@keyframes mv{0%{margin-left:-40%;}100%{margin-left:100%;}}</style>
<div id="prog"><div></div></div>
<div id="aiStatus" style="color:#7f8c8d;margin:.3rem 0;"></div>
<span id="jsBadge" style="color:#c0392b;font-weight:600;">JS не загружен ❌</span>
<pre id="liveLog" style="background:#111;color:#0f0;height:130px;overflow:auto;padding:.5rem;font-size:12px;margin:.5rem 0;"></pre>
<div class="form-group" style="max-width:300px;">
<label>PIN:</label>
<input type="password" id="adminPin" placeholder="введите PIN">
</div>
<div class="header-actions" style="margin:1rem 0;">
<button class="btn btn-primary" onclick="applyPatch(false)">✅ Применить патч</button>
<button class="btn btn-success" onclick="applyPatch(true)">🔄 Применить и перезапустить</button>
<button class="btn btn-secondary" onclick="showDiag()">🩺 Диагностика</button>
</div>
<p style="color:#7f8c8d;font-size:.9rem;">Вставьте блок патча целиком (можно с bash-обёрткой heredoc — сервер сам вырежет python-часть). Результат и ошибки появятся ниже.</p>
<textarea id="patchArea" style="width:100%;height:300px;font-family:monospace;font-size:12px;"></textarea>
<div class="header-actions" style="margin:1rem 0;">
<button class="btn btn-secondary" onclick="showUpdates()">🗂 История обновлений</button>
<button class="btn btn-secondary" onclick="showBackups()">💾 Бэкапы / откат</button>
<button class="btn btn-secondary" onclick="askAi(false)">🤖 Спросить Qwen</button>
<button class="btn btn-secondary" onclick="askAi(true)">🤖 Анализ диагностики</button>
<button class="btn btn-danger" onclick="selfHeal()">🚑 Самопочинка (Qwen)</button>
</div>
<div class="form-group" style="max-width:640px;">
<label>Вопрос нейронке:</label>
<input type="text" id="aiPrompt" placeholder="Напр.: почему не работает кнопка...">
<select id="aiAttach" style="margin-top:.5rem;padding:.5rem;max-width:420px;">
<option value="smart" selected>🧠 Прикрепить: умное (релевантное задаче)</option>
<option value="all">📦 Прикрепить: ВСЁ (долго думает, возможен таймаут)</option>
<option value="routes">Прикрепить: список маршрутов (кратко)</option>
<option value="orders">Прикрепить: код главной (наряды)</option>
<option value="order">Прикрепить: код страницы наряда</option>
<option value="planner">Прикрепить: код планировщика</option>
<option value="fdb">Прикрепить: код FDB-страницы</option>
<option value="stock">Прикрепить: код склада</option>
<option value="map">Прикрепить: код карты сети</option>
<option value="admin">Прикрепить: код админ-центра</option>
</select>
<button class="btn btn-primary" onclick="askAiCode()">🧩 С кодом: разработать / проверить</button>
<button class="btn btn-secondary" onclick="auditCode()">🔍 Аудит багов</button>
<button class="btn btn-success" onclick="autoWish()">🤖 Автономка: воплотить желание</button>
<button class="btn btn-primary" onclick="migrate()">🚚 Миграция: собрать архив</button>
<button class="btn" style="background:#c0392b;" onclick="uninstallPanel()">☠️ Полное удаление</button>
<div style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>🔄 Автозапуск после ребута и обновлений</h3>
<p id="asStatus" style="color:#7f8c8d;">Статус: проверяю…</p>
<button class="btn btn-success" onclick="autostartSet(true)">✅ Включить автозапуск</button>
<button class="btn btn-secondary" onclick="autostartSet(false)">⛔ Выключить автозапуск</button>
<small style="display:block;margin-top:.5rem;color:#7f8c8d;">Когда включено: cron поднимает панель сам после перезагрузки сервера и после любого обновления с перезапуском (проверка каждую минуту). Выключили — панель живёт только до ребута.</small>
</div>
</div>
<div class="form-group" style="max-width:640px;">
<label>Токен GitHub (для приватного репо, необязательно):</label>
<input type="password" id="ghToken" placeholder="ghp_... оставьте пустым для public">
</div>
<div class="form-group" style="max-width:640px;margin-top:1rem;">
<label>GitHub raw-URL файла update.py:</label>
<input type="text" id="ghUrl" placeholder="https://raw.githubusercontent.com/vasa57kam/zmkup/main/update.py">
</div>
<button class="btn btn-primary" onclick="ghUpdate()">📥 Тянуть обновление с GitHub</button>
<button id="applyAiBtn" style="display:none;margin:.5rem 0;" class="btn btn-success" onclick="applyAiPatch()">⚡ Применить предложенный патч</button>
<div style="background:#fff;padding:1rem;border-radius:8px;margin:1rem 0;">
<h3>📝 Журнал изменений (связь вы ↔ нейронка ↔ мастер)</h3>
<p style="color:#7f8c8d;font-size:.9rem;">Опишите проблему своими словами — нейронка читает журнал при каждом анализе, все применённые патчи пишутся сюда сами. Мастеру достаточно показать журнал.</p>
<textarea id="clText" style="width:100%;height:70px;" placeholder="Напр.: ХОЧУ: чтобы кнопка Закрыть наряд работала... или описание бага"></textarea>
<button class="btn btn-primary" onclick="addCL()">➕ Добавить в журнал</button>
<div id="clList" style="margin-top:.5rem;max-height:220px;overflow:auto;"></div>
</div>
<div id="histBox" style="margin:1rem 0;"></div>
<h3>Результат</h3>
<pre id="patchResult" style="background:#fff;padding:1rem;border-radius:8px;white-space:pre-wrap;"></pre>
{% endblock %}
{% block scripts %}
<script src="/static/admin.js?v=5"></script>
<script>
function autoWish(){
  var p=document.getElementById('aiPrompt').value;
  if(!p || !p.trim()){ p='Выполни последнее желание из журнала изменений (строка, начинающаяся с ХОЧУ:). Если такого нет - ответь текстом, что желаний нет.'; }
  startJob('auto',{prompt:p});
}
function auditCode(){
  var s=document.getElementById('aiAttach');
  if(s){ s.value='all'; }
  document.getElementById('aiPrompt').value='Проанализируй прикреплённый код и диагностику: перечисли ВСЕ найденные баги и несоответствия по пунктам, затем дай один исправляющий патч для swh.py между ===PATCH=== и ===END===';
  askAiCode();
}
function loadCL(){
  fetch('/api/changelog?pin='+encodeURIComponent(getPin())).then(function(r){return r.json();}).then(function(rows){
    var h='';
    rows.forEach(function(x){
      h+='<div style="background:#f8f9fa;padding:.4rem;margin:.2rem 0;border-radius:4px;"><small>'+x.ts+' ['+x.author+']</small> '+x.text+'</div>';
    });
    document.getElementById('clList').innerHTML=h||'<small>Журнал пуст</small>';
  });
}
function addCL(){
  var t=document.getElementById('clText').value;
  if(!t.trim()) return;
  fetch('/api/changelog',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({pin:getPin(),author:'user',text:t})}).then(function(){
    document.getElementById('clText').value='';
    loadCL();
  });
}
function askAiCode(){
  var p=document.getElementById('aiPrompt').value||'Разработай новый функционал для панели';
  var a=document.getElementById('aiAttach').value;
  startJob('ai',{prompt:p, with_diag:true, attach:a, want_patch:1});
}
</script>
{% endblock %}"""

ADMIN_PIN = '1958'

def pick_model(want='qwen3-coder:30b'):
    import urllib.request
    import json as _json
    try:
        r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
        tags = [m.get('name', '') for m in _json.loads(r.read().decode()).get('models', [])]
    except Exception:
        return want
    if want in tags:
        return want
    for t in tags:
        if 'qwen' in t.lower():
            return t
    return tags[0] if tags else want

def make_backup():
    import shutil, time
    base = os.path.dirname(os.path.abspath(__file__))
    bd = os.path.join(base, 'backups')
    os.makedirs(bd, exist_ok=True)
    ts = time.strftime('%Y%m%d_%H%M%S')
    dst = os.path.join(bd, 'swh_' + ts + '.py')
    shutil.copy(os.path.join(base, 'swh.py'), dst)
    files = sorted(os.listdir(bd))
    while len(files) > 10:
        os.remove(os.path.join(bd, files.pop(0)))
    return dst

def log_update(source, rc, out, code):
    conn = get_db()
    conn.execute('INSERT INTO update_log (ts, source, rc, out, code) VALUES (?,?,?,?,?)',
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), source, rc, (out or '')[-2000:], code or ''))
    conn.commit()
    conn.close()

@app.route('/admin')
def admin_page():
    return render_template_string(ADMIN_HTML)

@app.route('/api/admin/apply', methods=['POST'])
def admin_apply():
    import subprocess
    d = request.json
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'ok': False, 'rc': -1, 'out': 'Неверный PIN'}), 403
    code = d.get('code', '')
    if 'PYEOF' in code:
        ls = code.split('\n')
        out_ls = []
        inside = False
        for ln in ls:
            if not inside and 'PYEOF' in ln and '<<' in ln:
                inside = True
                continue
            if inside and ln.strip() == 'PYEOF':
                inside = False
                continue
            if inside:
                out_ls.append(ln)
        if out_ls:
            code = '\n'.join(out_ls)
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    make_backup()
    try:
        p = subprocess.run(['python3', fn], cwd=base,
            capture_output=True, text=True, timeout=120)
        out = (p.stdout or '') + (p.stderr or '')
        rc = p.returncode
    except Exception as e:
        out = str(e)
        rc = -2
    log_update('admin', rc, out, code)
    if d.get('restart') and rc == 0:
        cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
        subprocess.Popen(['bash', '-c', cmd], start_new_session=True)
    return jsonify({'ok': rc == 0, 'rc': rc, 'out': out[-4000:]})

@app.route('/api/admin/diag')
def admin_diag():
    import ast as _ast
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'Неверный PIN'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'swh.py')
    src = open(fn).read()
    res = {}
    try:
        _ast.parse(src)
        res['syntax'] = 'OK'
    except Exception as e:
        res['syntax'] = 'ОШИБКА: ' + str(e)
    markers = [
        "@app.route('/stock')",
        "@app.route('/fdb/<int:order_id>')",
        "@app.route('/api/orders-upsert'",
        "@app.route('/api/fdb-paste'",
        "@app.route('/api/report/<int:order_id>')",
        "@app.route('/api/fdb/<int:order_id>', methods=['GET'])",
        "@app.route('/api/inventory', methods=['GET'])",
        "@app.route('/api/attachments', methods=['GET'])",
        "@app.route('/api/map-connections', methods=['GET'])",
        "@app.route('/api/notes/<key>'",
        "@app.route('/api/orders/<int:order_id>', methods=['PUT'])",
        'DEFAULT_STEPS = [',
        'def injectHeader',
        'orderSearch',
        'from flask import',
    ]
    res['markers'] = {m: (m in src) for m in markers}
    conn = get_db()
    tabs = [r['name'] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    conn.close()
    res['tables'] = tabs
    try:
        log = open(os.path.join(base, 'swh.log')).read()
        res['log_tail'] = log[-1500:]
    except Exception as e:
        res['log_tail'] = str(e)
    try:
        import urllib.request as _ur
        import json as _jm
        rr = _ur.urlopen('http://localhost:11434/api/tags', timeout=5)
        res['ollama_models'] = [m.get('name') for m in _jm.loads(rr.read().decode()).get('models', [])]
    except Exception as e2:
        res['ollama_models'] = 'ollama недоступна: ' + str(e2)[:80]
    return jsonify(res)


@app.route('/api/admin/backups')
def admin_backups():
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    bd = os.path.join(base, 'backups')
    out = []
    if os.path.isdir(bd):
        for f in sorted(os.listdir(bd), reverse=True):
            out.append(f)
    return jsonify({'backups': out})

@app.route('/api/admin/rollback', methods=['POST'])
def admin_rollback():
    import shutil, subprocess
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'ok': False, 'out': 'Неверный PIN'}), 403
    name = d.get('name', '')
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'backups', name)
    if not os.path.isfile(fn):
        return jsonify({'ok': False, 'out': 'Не найден бэкап: ' + name})
    shutil.copy(fn, os.path.join(base, 'swh.py'))
    cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
    subprocess.Popen(['bash', '-c', cmd], start_new_session=True)
    return jsonify({'ok': True, 'out': 'Откат до ' + name + '. Перезапуск...'})

@app.route('/api/admin/updates')
def admin_updates():
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    conn = get_db()
    rows = conn.execute('SELECT ts, source, rc, out FROM update_log ORDER BY id DESC LIMIT 20').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/admin/ai', methods=['POST'])
def admin_ai():
    import urllib.request
    import urllib.parse
    import json as _json
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'ok': False, 'out': 'Неверный PIN'}), 403
    prompt = d.get('prompt', '')
    if d.get('with_diag'):
        try:
            u = 'http://localhost:9500/api/admin/diag?pin=' + urllib.parse.quote(ADMIN_PIN)
            rr = urllib.request.urlopen(u, timeout=30)
            prompt = prompt + '\n\nДиагностика:\n' + rr.read().decode()[:6000]
        except Exception as e:
            prompt = prompt + ' (диагностика недоступна: ' + str(e) + ')'
    body = _json.dumps({'model': pick_model(), 'prompt': prompt, 'stream': False}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(rq, timeout=600)
        res = _json.loads(r.read().decode())
        return jsonify({'ok': True, 'out': res.get('response', '')[:8000]})
    except Exception as e:
        return jsonify({'ok': False, 'out': 'Ошибка ollama: ' + str(e)})


@app.route('/api/admin/ghupdate', methods=['POST'])
def admin_ghupdate():
    import subprocess
    import urllib.request
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'ok': False, 'rc': -1, 'out': 'Неверный PIN'}), 403
    url = d.get('url', '')
    if not url:
        conn = get_db()
        row = conn.execute("SELECT content FROM app_notes WHERE note_key='github_raw_url'").fetchone()
        conn.close()
        url = row['content'] if row else ''
    if not url:
        return jsonify({'ok': False, 'rc': -3, 'out': 'Нет URL: впишите и нажмите ещё раз'})
    tok = ''
    conn = get_db()
    trow = conn.execute("SELECT content FROM app_notes WHERE note_key='github_token'").fetchone()
    conn.close()
    tok = trow['content'] if trow else ''
    if d.get('token'):
        tok = d['token']
    try:
        rq = urllib.request.Request(url)
        if tok:
            rq.add_header('Authorization', 'token ' + tok)
        code = urllib.request.urlopen(rq, timeout=30).read().decode('utf-8')
    except Exception as e:
        return jsonify({'ok': False, 'rc': -4, 'out': 'Ошибка скачивания: ' + str(e)})
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    make_backup()
    try:
        p = subprocess.run(['python3', fn], cwd=base, capture_output=True, text=True, timeout=120)
        out = (p.stdout or '') + (p.stderr or '')
        rc = p.returncode
    except Exception as e:
        out = str(e)
        rc = -2
    log_update('github', rc, out, code)
    if rc == 0:
        conn = get_db()
        conn.execute("DELETE FROM app_notes WHERE note_key='github_raw_url'")
        conn.execute("INSERT INTO app_notes (note_key, content) VALUES ('github_raw_url', ?)", (url,))
        conn.commit()
        conn.close()
        cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
        subprocess.Popen(['bash', '-c', cmd], start_new_session=True)
        out += '\n\n⏳ Перезапуск — обновите через 5-7 секунд.'
    return jsonify({'ok': rc == 0, 'rc': rc, 'out': out[-4000:]})


@app.route('/api/admin/selfheal', methods=['POST'])
def admin_selfheal():
    import subprocess
    import urllib.request
    import urllib.parse
    import json as _json
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'ok': False, 'rc': -1, 'out': 'Неверный PIN'}), 403
    try:
        u = 'http://localhost:9500/api/admin/diag?pin=' + urllib.parse.quote(ADMIN_PIN)
        diag = urllib.request.urlopen(u, timeout=30).read().decode()
    except Exception as e:
        diag = str(e)
    prompt = 'Ты сопровождаешь панель swh.py. Вот диагностика. '
    prompt += 'Найди ВСЕ неисправности (BAD, ошибки, отсутствующие маршруты). '
    prompt += 'Составь ОДИН python-патч: читает swh.py, правит через replace с точными якорями, '
    prompt += 'записывает обратно, делает ast.parse. Код ТОЛЬКО между ===PATCH=== и ===END===. '
    prompt += 'Диагностика:' + diag[:6000]
    body = _json.dumps({'model': pick_model(), 'prompt': prompt, 'stream': False}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(rq, timeout=600)
        text = _json.loads(r.read().decode()).get('response', '')
    except Exception as e:
        return jsonify({'ok': False, 'rc': -4, 'out': 'ollama недоступна: ' + str(e), 'ai': ''})
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    if not code.strip():
        return jsonify({'ok': False, 'rc': -5, 'out': 'Нейронка не дала код', 'ai': text[:1500]})
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    make_backup()
    try:
        p = subprocess.run(['python3', fn], cwd=base, capture_output=True, text=True, timeout=120)
        out = (p.stdout or '') + (p.stderr or '')
        rc = p.returncode
    except Exception as e:
        out = str(e)
        rc = -2
    log_update('selfheal', rc, out, code)
    if rc == 0:
        cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
        subprocess.Popen(['bash', '-c', cmd], start_new_session=True)
        out += ' || ПЕРЕЗАПУСК — обновите через 5-7 секунд'
    return jsonify({'ok': rc == 0, 'rc': rc, 'out': out[-4000:], 'ai': text[:2000]})



import threading
import time as _time

JOB = {'state': 'idle', 'lines': [], 'result': None, 'kind': '', 'ts': 0}

def job_log(t):
    JOB['lines'].append(t)
    if len(JOB['lines']) > 300:
        JOB['lines'] = JOB['lines'][-300:]

def _ollama_tags():
    import urllib.request
    import json as _json
    try:
        r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
        return [m.get('name', '') for m in _json.loads(r.read().decode()).get('models', [])]
    except Exception:
        return []

def _ollama_gen(prompt, ctx=16384, timeout=900):
    import urllib.request
    import json as _json
    tags = _ollama_tags()
    if not tags:
        raise RuntimeError('ollama: моделей нет')
    model = 'qwen3-coder:30b'
    if model not in tags:
        model = next((t for t in tags if 'qwen' in t.lower()), tags[0])
    job_log('модель: ' + model)
    body = _json.dumps({'model': model, 'prompt': prompt, 'stream': False, 'num_ctx': ctx}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    r = urllib.request.urlopen(rq, timeout=timeout)
    return _json.loads(r.read().decode()).get('response', '')

def _diag_text():
    import urllib.request
    import urllib.parse
    u = 'http://localhost:9500/api/admin/diag?pin=' + urllib.parse.quote(ADMIN_PIN)
    return urllib.request.urlopen(u, timeout=30).read().decode()

def _run_patch_code(code, source):
    import subprocess
    import ast as _ast
    import shutil
    base = os.path.dirname(os.path.abspath(__file__))
    fn = os.path.join(base, 'patch_tmp.py')
    open(fn, 'w').write(code)
    backup_path = make_backup()
    p = subprocess.run(['python3', fn], cwd=base, capture_output=True, text=True, timeout=300)
    out = (p.stdout or '') + (p.stderr or '')
    rc = p.returncode
    if rc == 0:
        try:
            _ast.parse(open(os.path.join(base, 'swh.py')).read())
        except Exception as e:
            shutil.copy(backup_path, os.path.join(base, 'swh.py'))
            out += ' || PATCH BROKE swh.py - AUTO-ROLLBACK: ' + str(e)[:200]
            rc = -6
    log_update(source, rc, out, code)
    log_change(source, 'патч rc=%s: %s' % (rc, (out or '')[:200].replace('\n', ' ')))
    return rc, out

def _restart_later():
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    cmd = 'sleep 2; pkill -f swh.py; sleep 1; cd ' + base + ' && nohup python3 swh.py > swh.log 2>&1 &'
    subprocess.Popen(['bash', '-c', cmd], start_new_session=True)

def do_selfheal():
    job_log('[selfheal] читаю диагностику...')
    diag = _diag_text()
    prompt = ('Ты сопровождаешь панель swh.py. Вот диагностика. '
              'Найди ВСЕ неисправности. Дай ОДИН python-патч между ===PATCH=== и ===END===: '
              'читает swh.py, правит через replace с точными якорями, пишет обратно, ast.parse. '
              'НИКОГДА не используй экранированные апострофы. '
              'Диагностика: ' + diag[:6000])
    prompt = prompt + '\n\nЖУРНАЛ ИЗМЕНЕНИЙ (последние записи):\n' + changelog_text()
    job_log('[selfheal] нейронка думает (минуты)...')
    text = _ollama_gen(prompt)
    code = ''
    if '===PATCH===' in text:
        code = text.split('===PATCH===')[1].split('===END===')[0]
    elif '```python' in text:
        code = text.split('```python')[1].split('```')[0]
    if not code.strip():
        JOB['result'] = {'ok': False, 'rc': -5, 'out': 'Нейронка не дала код', 'ai': text[:1500]}
        return
    job_log('[selfheal] патч ГОТОВ — примените кнопкой ⚡ после просмотра')
    JOB['result'] = {'ok': True, 'rc': 0,
        'out': 'Самопочинка подготовила патч, но НЕ применила его. Просмотрите ответ и нажмите ⚡ Применить предложенный патч (или пришлите ответ мастеру на проверку).',
        'ai': text[:6000]}

def do_gh(url, token):
    import urllib.request
    job_log('[github] скачиваю update.py: ' + url)
    rq = urllib.request.Request(url)
    if token:
        rq.add_header('Authorization', 'token ' + token)
    code = urllib.request.urlopen(rq, timeout=60).read().decode('utf-8')
    job_log('[github] скачано ' + str(len(code)) + ' байт, применяю...')
    rc, out = _run_patch_code(code, 'github')
    job_log('[github] результат патча rc=' + str(rc))
    conn = get_db()
    conn.execute("DELETE FROM app_notes WHERE note_key='github_raw_url'")
    conn.execute("INSERT INTO app_notes (note_key, content) VALUES ('github_raw_url', ?)", (url,))
    conn.commit()
    conn.close()
    JOB['result'] = {'ok': rc == 0, 'rc': rc, 'out': out[-4000:]}
    if rc == 0:
        job_log('[github] применено, перезапуск...')
        _restart_later()
    else:
        job_log('[github] ОШИБКА применения, перезапуска НЕ будет')

def do_ai(prompt, with_diag, payload=None):
    if with_diag:
        job_log('[ai] собираю диагностику...')
        prompt = prompt + '\n\nДиагностика:\n' + _diag_text()[:6000]
    wish0 = (payload or {}).get('prompt', '')
    clear = clarify_wish(wish0)
    job_log('[ai] задача после нормализации: ' + clear[:150])
    attach = (payload or {}).get('attach', 'smart')
    if attach == 'all':
        ctx = routes_list() + '\n\nПОЛНЫЙ КОД (первые 60000 символов):\n' + open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'swh.py')).read()[:60000]
        ctxsize = 32768
    elif attach == 'routes':
        ctx = routes_list()
        ctxsize = 8192
    elif attach in SECTS:
        ctx = routes_list() + '\n\n' + code_slice(*SECTS[attach])
        ctxsize = 16384
    else:
        ctx = smart_ctx(clear)
        ctxsize = 16384
    job_log('[ai] прикрепляю код: ' + attach + ' (' + str(len(ctx)) + ' симв)')
    prompt = ('Ты разработчик и аудитор панели swh.py (Flask+SQLite, JS внутри шаблонов). '
              'Если нужна правка или функция — дай ГОТОВЫЙ python-патч между ===PATCH=== и ===END=== '
              '(читает swh.py, правит через replace с точными якорями, пишет обратно, в конце ast.parse). '
              'Пояснения кратко по-русски.\nЗАДАЧА: ' + clear +
              '\n\nЖУРНАЛ ИЗМЕНЕНИЙ:\n' + changelog_text() +
              '\n\nРЕЛЕВАНТНЫЙ КОД:\n' + ctx)
    try:
        text = _ollama_gen(prompt, ctxsize)
    except Exception:
        job_log('[ai] таймаут на большом контексте — переход на умную нарезку')
        ctx = smart_ctx(clear)
        prompt = prompt + '\n\nКОД (умная нарезка):\n' + ctx
        text = _ollama_gen(prompt, 12000, 1200)
    job_log('[ai] нейронка думает...')
    # text уже получен выше
    code_ai = _extract_patch(text)
    if code_ai.strip() and not patch_looks_valid(code_ai):
        job_log('[ai] отсев: патч не про swh.py — строгий повтор')
        text = _ollama_gen(prompt + '\n\nТвой прошлый ответ содержал НЕ патч для swh.py, а постороннюю программу. Выдай патч, который читает swh.py, правит через replace и записывает обратно.', 16384, 900)
    if (payload or {}).get('want_patch') and not _extract_patch(text).strip():
        job_log('[ai] патча нет при want_patch — строгий повтор...')
        text = _ollama_gen(prompt + '\n\nВАЖНО: ты ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-патч между ===PATCH=== и ===END=== (читает swh.py, правит через replace с точными якорями, пишет обратно, ast.parse). Формат git diff ЗАПРЕЩЁН. Пояснения — после патча, кратко.', 16384, 900)
    JOB['result'] = {'ok': True, 'rc': 0, 'out': text[:8000]}
    job_log('[ai] ответ готов')

def _job_work(kind, payload):
    try:
        if kind == 'selfheal':
            do_selfheal()
        elif kind == 'gh':
            do_gh(payload.get('url', ''), payload.get('token', ''))
        elif kind == 'auto':
            do_autonomous(payload)
        elif kind == 'ai':
            do_ai(payload.get('prompt', ''), payload.get('with_diag'), payload)
        if JOB['state'] == 'running':
            JOB['state'] = 'done'
    except Exception as e:
        job_log('[error] ' + str(e))
        JOB['state'] = 'error'
        JOB['result'] = {'ok': False, 'rc': -9, 'out': str(e)}

@app.route('/api/admin/job', methods=['GET', 'POST'])
def admin_job():
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        sec = int(_time.time() - JOB['ts']) if JOB['ts'] else 0
        return jsonify({'state': JOB['state'], 'lines': JOB['lines'],
                        'sec': sec, 'result': JOB['result'], 'kind': JOB['kind']})
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    if JOB['state'] == 'running':
        return jsonify({'started': False, 'busy': True})
    kind = d.get('kind', '')
    JOB['state'] = 'running'
    JOB['lines'] = []
    JOB['result'] = None
    JOB['kind'] = kind
    JOB['ts'] = _time.time()
    threading.Thread(target=_job_work, args=(kind, d), daemon=True).start()
    return jsonify({'started': True})



def auto_flags(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    oldc = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='old'", (order_id,)).fetchone()['c']
    newc = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='new'", (order_id,)).fetchone()['c']
    oldcam = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='old' AND vlan LIKE '%135%'", (order_id,)).fetchone()['c']
    newcam = conn.execute("SELECT COUNT(*) c FROM fdb_tables WHERE order_id=? AND switch_type='new' AND vlan LIKE '%135%'", (order_id,)).fetchone()['c']
    ups = conn.execute("SELECT * FROM links WHERE order_id=? AND link_type='uplink'", (order_id,)).fetchall()
    dls = conn.execute("SELECT * FROM links WHERE order_id=? AND link_type='downlink'", (order_id,)).fetchall()
    subs = conn.execute('SELECT * FROM subscribers WHERE order_id=?', (order_id,)).fetchall()
    inv = conn.execute('SELECT * FROM switch_inventory', ()).fetchall()
    conn.close()
    old_ip = (o['old_switch_ip'] or '') if o else ''
    f = {}
    f[0] = bool(o and o['old_switch_ip'] and o['old_switch_model'])
    f[1] = oldc > 0
    f[2] = len(ups) > 0 or len(dls) > 0
    f[3] = False
    f[4] = False
    f[5] = False
    f[6] = len(ups) > 0 and all(u['new_port'] for u in ups)
    f[7] = len(dls) > 0 and all(d['new_port'] for d in dls)
    f[8] = (len(subs) == 0) or all(s['new_port'] for s in subs)
    f[9] = newc > 0
    f[10] = oldc > 0 and newc > 0
    f[11] = (oldcam == 0) or (newcam > 0)
    f[12] = False
    f[13] = any(i['last_ip'] == old_ip and i['status'] in ('reset_done', 'in_stock', 'written_off') for i in inv)
    f[14] = any(i['last_ip'] == old_ip and i['status'] in ('in_stock', 'written_off') for i in inv)
    return f

CMD_HTML = """{% extends "base.html" %}
{% block title %}Справочник команд{% endblock %}
{% block content %}
<div class="page-header">
    <h1>📚 Справочник команд</h1>
</div>
<div style="background:#fff;padding:1rem;border-radius:8px;margin-bottom:1rem;">
<h3>➕ Добавить команду</h3>
<div class="form-row">
<div class="form-group"><label>Название:</label><input id="cmdTitle"></div>
<div class="form-group"><label>Категория:</label><input id="cmdCat" placeholder="волокно / LAN / uplink..."></div>
</div>
<div class="form-group"><label>Команда / порядок действий:</label><textarea id="cmdBody" style="width:100%;height:90px;font-family:monospace;"></textarea></div>
<div class="form-group"><label>Примечание:</label><input id="cmdNotes"></div>
<button class="btn btn-primary" onclick="addCmd()">💾 Сохранить</button>
</div>
<div id="cmdList"></div>
{% endblock %}
{% block scripts %}
<script>
function copyCmd(id){
  var c=(window.cmdRows||[]).find(function(x){ return String(x.id)===String(id); });
  if(c && navigator.clipboard){
    navigator.clipboard.writeText(c.body||'');
    alert('Команда скопирована в буфер');
  }
}
function loadCmds(){
  fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){
    var h='';
    rows.forEach(function(c){
      h+='<div style="background:#fff;padding:.8rem;margin:.4rem 0;border-radius:8px;">';
      h+='<b>'+c.title+'</b> <span class="badge badge-ok">'+(c.category||'')+'</span> ';
      h+='<button class="btn btn-danger" style="padding:2px 8px;" data-id="'+c.id+'" onclick="delCmd(this.dataset.id)">🗑</button> ';
      h+='<button class="btn btn-secondary" style="padding:2px 8px;" data-id="'+c.id+'" onclick="copyCmd(this.dataset.id)">📋 копировать</button>';
      h+='<pre style="background:#f4f6f7;padding:.5rem;margin:.5rem 0;white-space:pre-wrap;">'+(c.body||'')+'</pre>';
      if(c.notes){h+='<small style="color:#7f8c8d;">'+c.notes+'</small>';}
      h+='</div>';
    });
    window.cmdRows=rows;
    document.getElementById('cmdList').innerHTML=h||'<p>Справочник пуст</p>';
  });
}
function addCmd(){
  var b={title:document.getElementById('cmdTitle').value,
    category:document.getElementById('cmdCat').value,
    body:document.getElementById('cmdBody').value,
    notes:document.getElementById('cmdNotes').value};
  fetch('/api/commands',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)}).then(loadCmds);
}
function delCmd(id){
  if(!confirm('Удалить команду?')) return;
  fetch('/api/commands/'+id,{method:'DELETE'}).then(loadCmds);
}
loadCmds();
</script>
{% endblock %}"""

@app.route('/commands')
def commands_page():
    return render_template_string(CMD_HTML)

@app.route('/api/commands', methods=['GET'])
def get_commands():
    conn = get_db()
    rows = conn.execute('SELECT * FROM commands_dict ORDER BY id').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/commands', methods=['POST'])
def add_command():
    d = request.json or {}
    conn = get_db()
    c = conn.cursor()
    c.execute('INSERT INTO commands_dict (title, category, body, notes) VALUES (?,?,?,?)',
        (d.get('title',''), d.get('category',''), d.get('body',''), d.get('notes','')))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/commands/<int:cmd_id>', methods=['DELETE'])
def del_command(cmd_id):
    conn = get_db()
    conn.execute('DELETE FROM commands_dict WHERE id=?', (cmd_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})



def code_slice(a, b):
    base = os.path.dirname(os.path.abspath(__file__))
    t = open(os.path.join(base, 'swh.py')).read()
    i = t.find(a)
    if i < 0:
        return ''
    j = t.find(b, i + 10)
    if j < 0 or j <= i:
        j = i + 20000
    return t[i:j]

def routes_list():
    base = os.path.dirname(os.path.abspath(__file__))
    t = open(os.path.join(base, 'swh.py')).read()
    out = []
    for line in t.split('\n'):
        s = line.strip()
        if s.startswith('@app.route') or s.startswith('def '):
            out.append(s)
    return '\n'.join(out)

SECTS = {
    'orders': ('INDEX_HTML = ', 'ORDER_HTML = '),
    'order': ('ORDER_HTML = ', 'PLANNER_HTML = '),
    'planner': ('PLANNER_HTML = ', 'FDB_HTML = '),
    'fdb': ('FDB_HTML = ', 'STOCK_HTML = '),
    'stock': ('STOCK_HTML = ', 'MAP_HTML = '),
    'map': ('MAP_HTML = ', 'ADMIN_HTML = '),
    'admin': ('ADMIN_HTML = ', 'def get_order_number'),
}


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


def log_change(author, text):
    conn = get_db()
    conn.execute('INSERT INTO change_log (ts, author, text) VALUES (?,?,?)',
        (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), author, text))
    conn.commit()
    conn.close()

def changelog_text(n=15):
    conn = get_db()
    rows = conn.execute('SELECT ts, author, text FROM change_log ORDER BY id DESC LIMIT ?', (n,)).fetchall()
    conn.close()
    return '\n'.join('%s [%s] %s' % (r['ts'], r['author'], r['text']) for r in reversed(rows)) or '(журнал пуст)'


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
import sqlite3 as _sq
_oid = 1
try:
    _c = _sq.connect('switch_replacements.db')
    _r = _c.execute('SELECT id FROM work_orders ORDER BY id LIMIT 1').fetchone()
    _c.close()
    if _r:
        _oid = _r[0]
except Exception:
    pass
import sqlite3 as _sq
_oid = 1
try:
    _c = _sq.connect('switch_replacements.db')
    _r = _c.execute('SELECT id FROM work_orders ORDER BY id LIMIT 1').fetchone()
    _c.close()
    if _r:
        _oid = _r[0]
except Exception:
    pass
urls = ['/', '/map', '/commands', '/admin', '/stock', '/api/orders', '/api/inventory',
        '/api/network-map', '/api/commands', '/api/cameras',
        '/passport/%d' % _oid, '/order/%d' % _oid, '/planner/%d' % _oid]
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
    c = code.strip()
    if c.startswith('diff ') or c.startswith('--- ') or c.startswith('index ') or 'diff --git' in c[:200]:
        return ''
    return code

def do_autonomous(payload):
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
              'Если явно невыполнимо — ответь текстом.\n'
              'ЗАДАЧА: ' + clear +
              '\n\nЖУРНАЛ ИЗМЕНЕНИЙ:\n' + changelog_text() +
              '\n\nДИАГНОСТИКА:\n' + _diag_text()[:3000] +
              '\n\nРЕЛЕВАНТНЫЙ КОД:\n' + ctx)
    last_gate = ''
    code = ''
    text = ''
    for attempt in (1, 2, 3):
        job_log('[auto] попытка ' + str(attempt) + ': нейронка думает...')
        extra = ('\n\nТвой прошлый патч НЕ прошёл sandbox: ' + last_gate[:1200] + '\nИсправь и дай исправленный патч.') if last_gate else ''
        text = _ollama_gen(prompt + extra, 16384, 900)
        code = _extract_patch(text)
        if not code.strip():
            job_log('[auto] патча нет — строгий повтор...')
            text = _ollama_gen(prompt + '\n\nВАЖНО: ты ОБЯЗАН выдать готовый ИСПОЛНЯЕМЫЙ python-скрипт между ===PATCH=== и ===END=== (read/replace/write/ast.parse). Форматы git diff и patch ЗАПРЕЩЕНЫ. Объяснения вместо кода ЗАПРЕЩЕНЫ.', 16384, 1200)
            code = _extract_patch(text)
        if not code.strip():
            JOB['result'] = {'ok': True, 'rc': 0, 'out': 'Нейронка не дала патч (см. ответ).', 'ai': text[:6000]}
            log_change('ai', 'без патча: ' + text[:150].replace('\n', ' '))
            return
        if not patch_looks_valid(code):
            last_gate = 'патч не модифицирует swh.py (посторонний код)'
            job_log('[auto] отсев: ' + last_gate)
            continue
        ok, gate = sandbox_check(code)
        job_log('[auto] sandbox: ' + gate[:150])
        if ok:
            job_log('[auto] применяю к боевому файлу...')
            rc, out = _run_patch_code(code, 'ai-auto')
            JOB['result'] = {'ok': rc == 0, 'rc': rc,
                'out': 'Sandbox OK (попытка ' + str(attempt) + '). Боевой: rc=' + str(rc) + '\n' + out[-2000:],
                'ai': text[:1500]}
            log_change('ai-auto', 'патч применён (попытка ' + str(attempt) + '), rc=' + str(rc) + ' | ' + wish[:100])
            if rc == 0:
                _restart_later()
            return
        last_gate = gate
    open(os.path.join(base, 'pending_patch.py'), 'w').write(code)
    JOB['result'] = {'ok': False, 'rc': -7,
        'out': '3 попытки, sandbox не пройден. Патч в pending_patch.py. НУЖЕН МАСТЕР.\n' + last_gate[:1500],
        'ai': text[:3000]}
    log_change('ai', 'НУЖЕН МАСТЕР: ' + last_gate[:200].replace('\n', ' ') + ' | ' + wish[:100])

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



def clarify_wish(wish):
    p = ('Ты нормализатор голосового ввода: задачи диктуются голосом для разработчика панели swh.py '
         '(замена коммутаторов: наряды, планировщик портов, FDB-таблицы, карта сети, склад, отчёты, паспорт наряда, админ-центр). '
         'Перепиши диктовку в чёткое техническое задание 1-3 предложения, исправь ошибки распознавания по смыслу '
         '(напр. "паспорт не найден" -> "кнопка Паспорт отдаёт 404", "аплинк" -> "uplink"). '
         'Ответь ТОЛЬКО текстом задания.\nДиктовка: ' + wish[:1000])
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
    return '\n\n'.join(p for p in parts if p)[:30000]


@app.route('/api/cameras', methods=['GET', 'POST'])
def cameras_api():
    conn = get_db()
    if request.method == 'GET':
        oid = request.args.get('order_id')
        rows = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side, id', (oid,)).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    c = conn.cursor()
    c.execute('INSERT INTO cameras (order_id, side, model, serial, ip, mac, zone, notes, config_text) VALUES (?,?,?,?,?,?,?,?,?)',
        (d.get('order_id'), d.get('side', 'new'), d.get('model', ''), d.get('serial', ''),
         d.get('ip', ''), d.get('mac', ''), d.get('zone', ''), d.get('notes', ''), d.get('config_text', '')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'success': True, 'id': i})

@app.route('/api/cameras/<int:cam_id>', methods=['GET', 'PUT', 'DELETE'])
def camera_api(cam_id):
    conn = get_db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM cameras WHERE id=?', (cam_id,)).fetchone()
        conn.close()
        if not r:
            return jsonify({'error': 'nf'}), 404
        return jsonify(dict(r))
    if request.method == 'DELETE':
        conn.execute('DELETE FROM cameras WHERE id=?', (cam_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    d = request.json or {}
    sets = []
    vals = []
    for f in ('model', 'serial', 'ip', 'mac', 'zone', 'notes', 'config_text', 'side', 'login', 'password', 'rtsp', 'vlan', 'port', 'switch_name', 'switch_port'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    if sets:
        vals.append(cam_id)
        conn.execute('UPDATE cameras SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'success': True})



def patch_looks_valid(code):
    return ('swh.py' in code) and ('replace(' in code or 'write(' in code)


@app.route('/api/vision', methods=['POST'])
def vision_api():
    import base64
    import json as _json
    import urllib.request
    pin = request.form.get('pin') or (request.json or {}).get('pin')
    if pin != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    f = request.files.get('file')
    if not f:
        return jsonify({'error': 'нет файла'}), 400
    b64 = base64.b64encode(f.read()).decode()
    try:
        r = urllib.request.urlopen('http://localhost:11434/api/tags', timeout=10)
        tags = [m.get('name', '') for m in _json.loads(r.read().decode()).get('models', [])]
    except Exception:
        return jsonify({'error': 'ollama недоступна'}), 503
    model = next((t for t in tags if 'vl' in t.lower() or 'llava' in t.lower()), None)
    if not model:
        return jsonify({'error': 'нет зрячей модели (нужна qwen2.5vl или llava)'}), 503
    prompt = ('Извлеки данные со скриншота (биллинг, карточка камеры, табличка). '
              'Верни СТРОГО JSON без пояснений, ключи: login,password,ip,port,vlan,address,mac,rtsp,model,serial,name. '
              'Отсутствующие значения - пустая строка.')
    body = _json.dumps({'model': model, 'prompt': prompt, 'images': [b64], 'stream': False}).encode()
    rq = urllib.request.Request('http://localhost:11434/api/generate', data=body, headers={'Content-Type': 'application/json'})
    try:
        r = urllib.request.urlopen(rq, timeout=300)
        text = _json.loads(r.read().decode()).get('response', '')
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500
    t = text.strip()
    if t.startswith('```'):
        t = t.split('```')[1]
        if t.startswith('json'):
            t = t[4:]
    data = None
    try:
        data = _json.loads(t)
    except Exception:
        i = t.find('{'); j = t.rfind('}')
        if i >= 0 and j > i:
            try:
                data = _json.loads(t[i:j+1])
            except Exception:
                data = None
    if data is None:
        return jsonify({'error': 'модель не дала JSON', 'raw': text[:500]}), 502
    return jsonify({'ok': True, 'data': data})



@app.route('/api/fdb_fetch', methods=['POST'])
def fdb_fetch():
    import subprocess
    import re as _re
    d = request.json or {}
    ip = d.get('ip', '')
    community = d.get('community', 'public')
    order_id = d.get('order_id')
    side = d.get('side', 'old')
    if not ip or not order_id:
        return jsonify({'error': 'нужны ip и order_id'}), 400
    try:
        p = subprocess.run(['snmpwalk', '-v2c', '-c', community, ip, '1.3.6.1.2.1.17.7.1.2.2.1.2'],
                           capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        return jsonify({'error': 'на сервере нет snmpwalk. Установите: apt-get install -y snmp'}), 503
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500
    if p.returncode != 0:
        return jsonify({'error': 'snmpwalk: ' + (p.stderr or p.stdout)[:300]}), 502
    rows = []
    for line in p.stdout.splitlines():
        m = _re.search(r'\.1\.2\.2\.1\.2\.(\d+)((?:\.\d+){6})\s+=\s+INTEGER:\s*(\d+)', line)
        if m:
            vlan = m.group(1)
            hx = ''.join('%02X' % int(x) for x in m.group(2).strip('.').split('.'))
            mac = ':'.join(hx[i:i+2] for i in range(0, 12, 2))
            rows.append((int(m.group(3)), vlan, mac))
    if not rows:
        return jsonify({'error': 'FDB пуста или неверный community', 'out': p.stdout[:300]}), 502
    conn = get_db()
    conn.execute("DELETE FROM fdb_tables WHERE order_id=? AND switch_type=?", (order_id, side))
    for port, vlan, mac in rows:
        conn.execute('INSERT INTO fdb_tables (order_id, switch_type, port, vlan, mac_address, subscriber) VALUES (?,?,?,?,?,?)',
                     (order_id, side, port, vlan, mac, ''))
    conn.commit()
    conn.close()
    return jsonify({'ok': True, 'count': len(rows)})


FIELD_LIST_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Полевой режим</title>
<style>body{font-family:Arial;font-size:18px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
a.btn{display:block;background:#3498db;color:#fff;padding:14px;border-radius:8px;text-decoration:none;text-align:center;font-size:20px;margin:8px 0;}
.big{font-size:22px;font-weight:600;} label.step{display:block;background:#fff;margin:8px;padding:14px;border-radius:10px;font-size:19px;}
input[type=checkbox]{width:28px;height:28px;vertical-align:middle;margin-right:10px;}
.ph{width:110px;height:85px;object-fit:cover;border-radius:6px;margin:4px;}</style></head>
<body><div class="card big">📱 Полевой режим — открытые наряды</div>
{% for o in orders %}<div class="card"><div class="big">Наряд {{ o.order_number }}</div>
<div>{{ o.old_switch_ip or '—' }} → {{ o.new_switch_ip or '—' }}</div>
<div>{{ o.old_switch_location or o.new_switch_location or '' }}</div>
<a class="btn" href="/field/{{ o.id }}">Открыть ▶</a></div>{% endfor %}
</body></html>"""

FIELD_ORDER_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Наряд {{ o.order_number }} — полевой</title>
<style>body{font-family:Arial;font-size:18px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:16px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
a.btn{display:inline-block;background:#3498db;color:#fff;padding:12px;border-radius:8px;text-decoration:none;font-size:18px;margin:6px 4px 6px 0;}
.big{font-size:22px;font-weight:600;} label.step{display:block;background:#fff;margin:8px;padding:14px;border-radius:10px;font-size:19px;}
input[type=checkbox]{width:28px;height:28px;vertical-align:middle;margin-right:10px;}
.ph{width:110px;height:85px;object-fit:cover;border-radius:6px;margin:4px;}</style></head>
<body>
<div class="card big">📱 Наряд {{ o.order_number }}</div>
<div class="card">
<div><b>Адрес:</b> {{ o.old_switch_location or o.new_switch_location or '—' }}</div>
<div><b>Старый:</b> {{ o.old_switch_ip or '—' }} ({{ o.old_switch_model or '—' }})</div>
<div><b>Новый:</b> {{ o.new_switch_ip or '—' }} ({{ o.new_switch_model or '—' }})</div>
<a class="btn" href="/passport/{{ o.id }}" target="_blank">🖨️ Паспорт</a>
<a class="btn" href="/field">← Список</a>
</div>
<div class="card big">✅ Этапы</div>
{% for s in steps %}<label class="step"><input type="checkbox" {% if s.done or fl.get(loop.index0) %}checked{% endif %} onchange="tgStep({{ s.id }}, this.checked)"> {{ s.step_text }}</label>{% endfor %}
<div class="card big">🔌 Подключения</div>
<div class="card">{% for l in links %}<div>{{ '⬆️' if l.link_type=='uplink' else '⬇️' }} порт {{ l.old_port }} → <b>{{ l.new_port or '??' }}</b> | {{ l.upstream_device }} : {{ l.upstream_port }}</div>{% endfor %}
{% for c in cams %}<div>📹 {{ c.model }}: <a href="{{ c.rtsp }}" target="_blank">поток</a> | {{ c.switch_name }}:{{ c.switch_port }}</div>{% endfor %}
</div>
<div class="card big">📷 Фото ДО</div>
<div class="card"><div id="phBefore"></div><input type="file" accept="image/*" capture="environment" onchange="upF('field_before', this)"></div>
<div class="card big">📷 Фото ПОСЛЕ</div>
<div class="card"><div id="phAfter"></div><input type="file" accept="image/*" capture="environment" onchange="upF('field_after', this)"></div>
<script>
var orderId={{ o.id }};
function tgStep(id, done){
  fetch('/api/steps/'+id,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({done:done?1:0})});
}
function upF(type, input){
  var f=input.files[0];
  if(!f) return;
  var fd=new FormData();
  fd.append('file', f);
  fd.append('entity_type', type);
  fd.append('entity_id', orderId);
  fd.append('description', type);
  fetch('/api/attachments',{method:'POST', body:fd}).then(function(){ loadF(type); });
  input.value='';
}
function loadF(type){
  var box=document.getElementById(type==='field_before'?'phBefore':'phAfter');
  fetch('/api/attachments?entity_type='+type+'&entity_id='+orderId).then(function(r){return r.json();}).then(function(rows){
    box.innerHTML=rows.map(function(a){ return '<a href="/uploads/'+a.filename+'" target="_blank"><img class="ph" src="/uploads/'+a.filename+'"></a>'; }).join('');
  });
}
loadF('field_before'); loadF('field_after');
</script>
</body></html>"""

@app.route('/field')
def field_page():
    conn = get_db()
    orders = conn.execute("SELECT * FROM work_orders WHERE status!='closed' ORDER BY id DESC").fetchall()
    conn.close()
    return render_template_string(FIELD_LIST_HTML, orders=orders)

@app.route('/field/<int:order_id>')
def field_order(order_id):
    conn = get_db()
    o = conn.execute('SELECT * FROM work_orders WHERE id=?', (order_id,)).fetchone()
    if not o:
        conn.close()
        return 'Наряд не найден', 404
    steps = conn.execute('SELECT * FROM order_steps WHERE order_id=? ORDER BY pos', (order_id,)).fetchall()
    links = conn.execute('SELECT * FROM links WHERE order_id=? ORDER BY link_type, old_port', (order_id,)).fetchall()
    try:
        cams = conn.execute('SELECT * FROM cameras WHERE order_id=? ORDER BY side', (order_id,)).fetchall()
    except Exception:
        cams = []
    conn.close()
    return render_template_string(FIELD_ORDER_HTML, o=o, steps=steps, links=links, cams=cams, fl=auto_flags(order_id))


passport_mod.register(app, get_db, auto_flags)


@app.route('/api/tools/run', methods=['POST'])
def tools_run():
    import subprocess
    import socket as _sock
    import shutil
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    tool = d.get('tool', '')
    tgt = (d.get('target') or '').strip()
    cmd = d.get('cmd') or ''
    if not tgt and tool != 'ssh':
        return jsonify({'error': 'нет цели'}), 400
    ok_chars = set('abcdefghijklmnopqrstuvwxyz0123456789.-_:')
    if tgt and not set(tgt.lower()) <= ok_chars:
        return jsonify({'error': 'цель содержит запрещённые символы'}), 400
    try:
        if tool == 'ping':
            p = subprocess.run(['ping', '-c', '4', tgt], capture_output=True, text=True, timeout=20)
        elif tool == 'nslookup':
            p = subprocess.run(['nslookup', tgt], capture_output=True, text=True, timeout=20)
        elif tool == 'traceroute':
            if not shutil.which('traceroute'):
                return jsonify({'error': 'на сервере нет traceroute: apt-get install -y traceroute'}), 503
            p = subprocess.run(['traceroute', '-n', '-m', '15', tgt], capture_output=True, text=True, timeout=60)
        elif tool == 'tcp':
            port = int(d.get('port') or 23)
            s = _sock.socket(); s.settimeout(5)
            r = s.connect_ex((tgt, port)); s.close()
            return jsonify({'out': ('Порт %d ОТКРЫТ' % port) if r == 0 else ('Порт %d закрыт/недоступен (код %d)' % (port, r))})
        elif tool == 'snmpfdb':
            if not shutil.which('snmpwalk'):
                return jsonify({'error': 'нет snmpwalk: apt-get install -y snmp'}), 503
            p = subprocess.run(['snmpwalk', '-v2c', '-c', d.get('community') or 'public', tgt,
                                '1.3.6.1.2.1.17.7.1.2.2.1.2'], capture_output=True, text=True, timeout=60)
        elif tool == 'ssh':
            if not cmd.strip():
                return jsonify({'error': 'для SSH нужна команда в поле'}), 400
            if not shutil.which('sshpass'):
                return jsonify({'error': 'нет sshpass: apt-get install -y sshpass (или используйте кнопку копирования подключения)'}), 503
            p = subprocess.run(['sshpass', '-p', d.get('pass') or '', 'ssh',
                                '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=8',
                                (d.get('user') or 'admin') + '@' + tgt, cmd],
                               capture_output=True, text=True, timeout=60)
        elif tool == 'curl':
            p = subprocess.run(['curl', '-s', '-m', '10', '-o', '-', tgt if tgt.startswith('http') or tgt.startswith('rtsp') else ('http://' + tgt)],
                               capture_output=True, text=True, timeout=20)
        elif tool == 'whois':
            if not shutil.which('whois'):
                return jsonify({'error': 'на сервере нет whois: apt-get install -y whois'}), 503
            p = subprocess.run(['whois', tgt], capture_output=True, text=True, timeout=40)
        elif tool == 'myip':
            import urllib.request as _ur
            try:
                ip = _ur.urlopen('https://api.ipify.org?format=text', timeout=10).read().decode().strip()
            except Exception:
                ip = _ur.urlopen('https://ifconfig.me/ip', timeout=10).read().decode().strip()
            return jsonify({'out': 'Внешний IP сервера: ' + ip})
        elif tool == 'dig':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            p = subprocess.run(['dig', tgt, (cmd.strip() or 'A'), '+short'], capture_output=True, text=True, timeout=20)
        elif tool == 'dnsall':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            outs = []
            for t in ('A', 'AAAA', 'MX', 'NS', 'TXT'):
                q = subprocess.run(['dig', tgt, t, '+short'], capture_output=True, text=True, timeout=20)
                outs.append('== ' + t + ' ==\n' + (q.stdout or '(пусто)'))
            return jsonify({'out': '\n'.join(outs)})
        elif tool == 'ptr':
            if not shutil.which('dig'):
                return jsonify({'error': 'нет dig: apt-get install -y dnsutils'}), 503
            p = subprocess.run(['dig', '-x', tgt, '+short'], capture_output=True, text=True, timeout=20)
        elif tool == 'ssl':
            port = int(d.get('port') or 443)
            if not shutil.which('openssl'):
                return jsonify({'error': 'на сервере нет openssl'}), 503
            q1 = subprocess.run(['openssl', 's_client', '-connect', tgt + ':' + str(port), '-servername', tgt],
                                capture_output=True, text=True, timeout=20, input='')
            q2 = subprocess.run(['openssl', 'x509', '-noout', '-dates', '-subject', '-issuer'],
                                capture_output=True, text=True, timeout=20, input=q1.stdout)
            return jsonify({'out': q2.stdout or q1.stderr[:500]})
        elif tool == 'rkn':
            import urllib.request as _ur
            import json as _json
            is_ip = set(tgt) <= set('0123456789.')
            url = ('https://api.reestr.rublacklist.net/v2/ip/' if is_ip else 'https://api.reestr.rublacklist.net/v2/domain/') + tgt + '/json'
            try:
                r = _ur.urlopen(url, timeout=15)
                data = _json.loads(r.read().decode())
                return jsonify({'out': 'НАЙДЕНО в реестре РКН: ' + _json.dumps(data, ensure_ascii=False)[:2000]})
            except Exception as e:
                if '404' in str(e):
                    return jsonify({'out': 'Не найдено в реестре РКН (цель: ' + tgt + ')'})
                return jsonify({'error': 'реестр РКН недоступен: ' + str(e)[:150]}), 503
        elif tool == 'httphead':
            p = subprocess.run(['curl', '-sI', '-m', '10', tgt if tgt.startswith('http') else ('http://' + tgt)],
                               capture_output=True, text=True, timeout=20)
        else:
            return jsonify({'error': 'неизвестный инструмент'}), 400
        out = (p.stdout or '') + (p.stderr or '')
        return jsonify({'out': out[:8000] or '(пусто)', 'rc': p.returncode})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'таймаут выполнения'}), 504
    except Exception as e:
        return jsonify({'error': str(e)[:300]}), 500


TOOLS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🖥️ Тулза</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
button.q{margin:3px;padding:8px 12px;border:1px solid #bbb;border-radius:6px;background:#eef3f7;cursor:pointer;font-size:14px;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}</style></head>
<body>
<div class="card big">🖥️ Тулза — сетевой ящик инструментов</div>
<div class="card">
Устройство: <select id="devSel" onchange="pickDev()"></select>
Цель (IP/имя): <input id="tgt" style="width:150px;">
Инструмент: <select id="tool">
<option value="ping">ping</option>
<option value="nslookup">nslookup (DNS)</option>
<option value="traceroute">traceroute</option>
<option value="tcp">проверка порта (TCP)</option>
<option value="snmpfdb">SNMP: FDB свитча</option>
<option value="ssh">SSH: команда</option>
<option value="curl">HTTP/RTSP проверка (curl)</option>
<option value="whois">WHOIS (владелец домена/IP)</option>
<option value="myip">Мой внешний IP (сервер)</option>
<option value="dig">DIG (тип записи в поле «Текст»: A/MX/NS/TXT)</option>
<option value="dnsall">Все DNS-записи (A/AAAA/MX/NS/TXT)</option>
<option value="ptr">PTR (обратная запись IP)</option>
<option value="ssl">SSL-сертификат (сроки/владелец, порт 443)</option>
<option value="rkn">Реестр РКН (домен/IP)</option>
<option value="httphead">HTTP-заголовки сайта (curl -I)</option>
</select>
Порт: <input id="port" value="23" style="width:60px;">
SSH user: <input id="sshUser" value="admin" style="width:90px;">
SSH pass: <input id="sshPass" type="password" style="width:90px;">
community: <input id="com" value="public" style="width:90px;">
</div>
<div class="card">
<b>⌨️ Команда (для SSH; кнопки вставляют):</b>
<textarea id="cmd" style="width:100%;height:90px;font-family:monospace;"></textarea>
<div id="quickBtns"></div><br>
<button class="btn" style="background:#27ae60;" onclick="runTool()">▶ Выполнить</button>
<button class="btn" style="background:#3498db;" onclick="copyConn()">📋 Скопировать подключение</button>
<button class="btn" style="background:#7f8c8d;" onclick="copyCmd()">📋 Команду</button>
<span id="msg"></span>
</div>
<div class="card"><pre id="out" style="background:#111;color:#0f0;padding:10px;min-height:140px;white-space:pre-wrap;font-size:13px;"></pre></div>
<script>
var _g=sessionStorage.getItem('gen2tools');
if(_g){
  sessionStorage.removeItem('gen2tools');
  window.addEventListener('DOMContentLoaded', function(){
    document.getElementById('cmd').value=_g;
    document.getElementById('tool').value='ssh';
  });
}
var _t=sessionStorage.getItem('toolz_tgt');
if(_t){
  sessionStorage.removeItem('toolz_tgt');
  var _tt=sessionStorage.getItem('toolz_tool');
  if(_tt){ sessionStorage.removeItem('toolz_tool'); }
  window.addEventListener('DOMContentLoaded', function(){
    document.getElementById('tgt').value=_t;
    if(_tt){ document.getElementById('tool').value=_tt; }
  });
}
function pin(){ if(sessionStorage.pinp){ return sessionStorage.pinp; } var p=prompt('PIN:'); sessionStorage.pinp=p; return p; }
function pickDev(){
  var s=document.getElementById('devSel');
  var v=s.value;
  if(v){ document.getElementById('tgt').value=v; }
}
fetch('/api/network-map').then(function(r){return r.json();}).then(function(ds){
  var s=document.getElementById('devSel');
  s.innerHTML='<option value="">— устройство —</option>'+ds.map(function(d){
    return '<option value="'+(d.ip_address||'')+'">'+d.name+' · '+(d.ip_address||'')+' · 📍 '+(d.location||'—')+'</option>';
  }).join('');
});
var QUICK=['apt install ','apt update','show fdb','show ports','save','reboot','ping ','snmpwalk -v2c -c public ','telnet ','ssh '];
function renderQuick(extra){
  var b=document.getElementById('quickBtns');
  b.innerHTML=QUICK.concat(extra).map(function(t){
    return '<button class="q" onclick="insCmd(this.dataset.c)" data-c="'+t.replace(/"/g,'&quot;')+'">'+t.trim()+'</button>';
  }).join('');
}
fetch('/api/commands').then(function(r){return r.json();}).then(function(rows){
  renderQuick((rows||[]).map(function(c){ return c.title; }).slice(0,12));
  window.cmdDict=rows||[];
}).catch(function(){ renderQuick([]); });
function insCmd(t){
  var c=document.getElementById('cmd');
  var dict=(window.cmdDict||[]).find(function(x){ return x.title===t; });
  c.value += (dict? dict.body : t);
  c.focus();
}
function runTool(){
  document.getElementById('msg').textContent='Выполняю...';
  var body={pin:pin(), tool:document.getElementById('tool').value,
    target:document.getElementById('tgt').value, cmd:document.getElementById('cmd').value,
    port:document.getElementById('port').value, user:document.getElementById('sshUser').value,
    pass:document.getElementById('sshPass').value, community:document.getElementById('com').value};
  fetch('/api/tools/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
  .then(function(r){return r.json();}).then(function(res){
    document.getElementById('msg').textContent='';
    document.getElementById('out').textContent=res.out||res.error||'(пусто)';
  }).catch(function(e){ document.getElementById('msg').textContent=''; document.getElementById('out').textContent='Ошибка: '+e.message; });
}
function copyConn(){
  var t=document.getElementById('tool').value;
  var ip=document.getElementById('tgt').value;
  var u=document.getElementById('sshUser').value;
  var s=(t==='ssh')? ('ssh '+u+'@'+ip) : (t==='tcp'? ('telnet '+ip+' '+document.getElementById('port').value) : ('telnet '+ip));
  navigator.clipboard.writeText(s);
  alert('Скопировано: '+s);
}
function copyCmd(){ navigator.clipboard.writeText(document.getElementById('cmd').value); alert('Команда скопирована'); }

</script>
</body></html>"""

@app.route('/tools')
def tools_page():
    return render_template_string(TOOLS_HTML)



DEPLOY_SH = """#!/bin/bash
set -e
cd "$(dirname "$0")"
echo '=== Развёртывание панели замены коммутаторов ==='
apt-get update && apt-get install -y python3-pip snmp sshpass traceroute || true
pip3 install flask flask-cors || apt-get install -y python3-flask python3-flask-cors || true
( crontab -l 2>/dev/null | grep -v 'swh.py' ; echo "* * * * * cd $PWD && (curl -s -o /dev/null --max-time 3 http://localhost:9500/ || nohup python3 swh.py >> swh.log 2>&1 &)" ; echo "@reboot sleep 5 && cd $PWD && nohup python3 swh.py >> swh.log 2>&1 &" ) | crontab -
nohup python3 swh.py > swh.log 2>&1 &
sleep 3
echo '=== Готово: http://<IP_ЭТОГО_СЕРВЕРА>:9500/ ==='
echo 'PIN прежний. Ollama-модели при необходимости поставьте отдельно на новом сервере.'
"""

@app.route('/api/admin/migrate', methods=['POST'])
def migrate_create():
    import tarfile
    from datetime import datetime
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    name = 'swh_migrate_' + ts + '.tar.gz'
    path = os.path.join(base, name)
    dep = os.path.join(base, 'deploy_tmp.sh')
    open(dep, 'w').write(DEPLOY_SH)
    with tarfile.open(path, 'w:gz') as t:
        for item in ('swh.py', 'passport_mod.py', 'switch_replacements.db', 'static', 'uploads', 'backups'):
            p = os.path.join(base, item)
            if os.path.exists(p):
                t.add(p, arcname='swh_migrate/' + item)
        rd = os.path.join(base, 'readme_tmp.txt')
        open(rd, 'w').write(README_TXT)
        t.add(rd, arcname='swh_migrate/README.txt')
        os.remove(rd)
        t.add(dep, arcname='swh_migrate/deploy.sh')
        dep2 = os.path.join(base, 'uninstall_tmp.sh')
        open(dep2, 'w').write(UNINSTALL_SH)
        t.add(dep2, arcname='swh_migrate/uninstall.sh')
        os.remove(dep2)
    os.remove(dep)
    return jsonify({'file': name,
                    'size_mb': round(os.path.getsize(path) / 1048576.0, 1),
                    'url': '/api/admin/migrate_get?f=' + name + '&pin=' + ADMIN_PIN})

@app.route('/api/admin/migrate_get')
def migrate_get():
    f = os.path.basename(request.args.get('f', ''))
    if not (f.startswith('swh_migrate_') and f.endswith('.tar.gz')):
        return jsonify({'error': 'плохое имя'}), 400
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), f, as_attachment=True)


GEN_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🧬 Генератор команд</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:12px 18px;border:none;border-radius:8px;color:#fff;font-size:16px;cursor:pointer;margin:4px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}
#hint{background:#fff8e1;border:1px solid #f1c40f;border-radius:8px;padding:10px;margin:8px 0;}</style></head>
<body>
<div class="card big">🧬 Генератор команд — D-Link L2</div>
<div class="card">
Семейство: <select id="fam" onchange="setFam()"><option value="dlink">D-Link xStack L2 (DES-3200 / DGS-1210)</option><option value="custom">Свой шаблон</option></select>
Операция: <select id="op" onchange="fillTpl()" style="max-width:420px;"></select><br>
VLAN: <input id="v" value="135" style="width:70px;">
Порт(ы): <input id="p" placeholder="21 или 16" style="width:110px;"> Порт(ы) магистрали: <input id="tr" placeholder="26-28 или 28" style="width:130px;">
MAC: <input id="m" placeholder="00:1A:79:.." style="width:150px;">
IP: <input id="ip" placeholder="10.163.x.x" style="width:130px;">
<span id="spdRow" style="display:none;">Скорость: <select id="spd"><option value="auto">auto</option><option value="10">10</option><option value="100">100</option><option value="1000">1000</option></select>
Duplex: <select id="dpx"><option value="">—</option><option value="half">half</option><option value="full">full</option></select></span>
Текст: <input id="txt" style="width:140px;">
<div id="hint">💡 Выберите операцию — здесь появится пояснение, что вводить.</div>
Шаблон (можно править руками): <textarea id="tpl" style="width:100%;height:80px;font-family:monospace;"></textarea>
<button class="btn" style="background:#8e44ad;" onclick="gen()">🧬 Сгенерировать</button>
<button class="btn" style="background:#3498db;" onclick="cpy()">📋 Копировать команды</button>
<button class="btn" style="background:#27ae60;" onclick="toTools()">🔗 В Тулзу (выполнить по SSH)</button>
<button class="btn" style="background:#7f8c8d;" onclick="sav()">💾 В справочник</button>
<textarea id="outg" style="width:100%;height:120px;font-family:monospace;margin-top:6px;" placeholder="Здесь появятся готовые команды"></textarea>
</div>
<div class="card"><b>📝 Памятка (шаги для этой операции):</b><textarea id="memo" style="width:100%;height:110px;margin-top:6px;"></textarea>
<div style="color:#7f8c8d;font-size:14px;margin-top:6px;">Плейсхолдеры шаблона: {vlan} {ports} {mac} {ip} {text}. Комбо-операции дают несколько команд сразу. Памятка сохраняется вместе с командой в справочник.</div></div>
<script src="/static/gen.js?v=7"></script>
</body></html>"""

@app.route('/gen')
def gen_page():
    return render_template_string(GEN_HTML)


VLANS_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>🗂 VLANы по районам</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
table{width:100%;border-collapse:collapse;}
td,th{border:1px solid #ddd;padding:6px 8px;font-size:14px;text-align:left;}
th{background:#eef3f7;}
.btn{padding:8px 14px;border:none;border-radius:6px;color:#fff;cursor:pointer;margin:2px;}
input{padding:10px;border:1px solid #ccc;border-radius:6px;font-size:16px;width:70%;}</style></head>
<body>
<div class="card big">🗂 VLANы по районам (помощь по прошивке свитчей)</div>
<div class="card"><input id="q" placeholder="Поиск: район (Михеенко), VLAN (2301), сегмент (PON, Клевер), IP свитча..." oninput="render()">
<span id="cnt"></span></div>
<div id="vwarn" class="card" style="display:none;background:#ffebee;border:1px solid #e57373;">
⚠️ Данные не загрузились. <button class="btn" style="background:#e57373;" onclick="reloadVlans()">🔄 Загрузить данные</button>
<small>(или Ctrl+F5; если не помогло — «Тянуть обновление с GitHub»)</small></div>
<div class="card"><table><thead><tr><th>Район</th><th>Свитч</th><th>Сегмент</th><th>VLAN</th><th></th></tr></thead>
<tbody id="tb"></tbody></table></div>
<div class="card"><b>📥 Импорт файла (xlsx / csv)</b><br>
<input type="file" id="impFile" accept=".xlsx,.csv,.txt">
<button class="btn" style="background:#8e44ad;" onclick="if(window.impVlans){impVlans();}else{alert('JS страницы не загрузился — нажмите Ctrl+F5 и повторите');}">Загрузить и импортировать</button>
<span id="impMsg"></span>
<div style="color:#7f8c8d;font-size:13px;margin-top:4px;">Колонки: Район | IP свитча | Сегмент | Номер VLAN (как в вашем файле). Повторный импорт обновляет строки без дублей.</div></div>
<div class="card"><b>➕ Добавить строку</b><br>
Район: <input id="nReg" style="width:140px;"> IP свитча: <input id="nIp" style="width:130px;">
Сегмент: <input id="nSeg" style="width:180px;"> VLAN: <input id="nVlan" style="width:80px;">
<button class="btn" style="background:#27ae60;" onclick="addRow()">Добавить</button></div>
<script src="/static/vlanspage.js?v=2"></script>
<script>window.addEventListener("load",function(){ if(!window.impVlans){ var m=document.getElementById("impMsg"); if(m){ m.textContent="⚠️ JS страницы не загрузился — нажмите Ctrl+F5"; } } });</script>
</body></html>"""

@app.route('/vlans')
def vlans_page():
    return render_template_string(VLANS_HTML)

@app.route('/api/vlans', methods=['GET', 'POST'])
def vlans_api():
    conn = get_db()
    if request.method == 'GET':
        ensure_vlans(conn)
        rows = conn.execute('SELECT region, switch_ip, segment, vlan FROM region_vlans ORDER BY region, vlan').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    try:
        conn.execute('INSERT OR REPLACE INTO region_vlans (region, switch_ip, segment, vlan) VALUES (?,?,?,?)',
                     (d.get('region', ''), d.get('switch_ip', ''), d.get('segment', ''), int(d.get('vlan') or 0)))
        conn.commit()
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)[:200]}), 400
    conn.close()
    return jsonify({'ok': True})


SEED_VLANS = [('Тура', '10.163.201.40', [(2101, 'красный'), (2102, 'оранжевый'), (2103, 'желтый'), (2104, 'зеленый'), (2105, 'голубой'), (2106, 'синий'), (2107, 'фиолетовый'), (2109, 'Зона 09'), (2110, 'Морозово'), (2111, 'Зона 11'), (2112, 'Зона 12'), (2113, 'Зона 13'), (2115, 'Север'), (2116, 'Резерв'), (2117, 'ЖК Клевер к1'), (2118, 'ЖК Клевер к2'), (2119, 'ЖК Клевер к3'), (2120, 'ЖК Клевер к4')]), ('Михеенко', '10.163.202.13', [(2201, 'красный'), (2202, 'оранжевый'), (2203, 'желтый'), (2204, 'зеленый'), (2205, 'голубой'), (2206, 'синий'), (2207, 'фиолетовый'), (2208, 'Зона 08 Лихачева 6')]), ('Королёва', '10.163.203.102', [(2301, 'красный'), (2302, 'оранжевый'), (2303, 'желтый'), (2304, 'зеленый'), (2305, 'голубой'), (2306, 'синий'), (2307, 'фиолетовый'), (2308, 'Зона 08')]), ('Черняховка', '10.163.204.34', [(2401, 'красный'), (2402, 'оранжевый'), (2403, 'желтый'), (2404, 'зеленый'), (2405, 'голубой'), (2406, 'синий'), (2407, 'фиолетовый'), (2409, 'Олимп к. 1-3'), (2410, 'Олимп к. 4-5'), (2411, 'Олимп к. 6-7')]), ('Жучки', '10.163.206.8', [(2601, 'красный'), (2602, 'оранжевый'), (2603, 'PON 1'), (2604, 'PON 2')]), ('Горбуновка, ОРГРЭС', '10.163.207.16', [(2701, 'красный'), (2702, 'оранжевый'), (2703, 'желтый'), (2704, 'PON Горбуновская'), (2705, 'PON Васильки')]), ('ГОП', '10.163.208.16', [(2801, 'красный'), (2802, 'оранжевый'), (2803, 'PON 1 Гоп'), (2804, 'новые дома')]), ('Сегмент 02 Заречный', '10.163.2.12', [(2020, 'Сегмент 02-01 МКД'), (2021, 'Сегмент 02-02 PON'), (2022, 'Сегмент 02-03 PON'), (2023, 'Сегмент 02-04 Зубцово'), (2024, 'Сегмент 02-05'), (2025, 'Сегмент 02-06'), (2026, 'Сегмент 02-07'), (2027, 'Сегмент 02-08'), (2028, 'Сегмент 02-09'), (2029, 'Сегмент 02-10')]), ('Сегмент 03 Росхмель', '10.163.3.1', [(2030, 'Сегмент 03-01 МКД'), (2031, 'Сегмент 03-02'), (2032, 'Сегмент 03-03'), (2033, 'Сегмент 03-04'), (2034, 'Сегмент 03-05'), (2035, 'Сегмент 03-06'), (2036, 'Сегмент 03-07'), (2037, 'Сегмент 03-08'), (2038, 'Сегмент 03-09'), (2039, 'Сегмент 03-10')]), ('Сегмент 04 СП Северный', '10.163.4.1', [(2040, 'Сегмент 04-01 PON'), (2041, 'Сегмент 04-02'), (2042, 'Сегмент 04-03'), (2043, 'Сегмент 04-04'), (2044, 'Сегмент 04-05'), (2045, 'Сегмент 04-06'), (2046, 'Сегмент 04-07'), (2047, 'Сегмент 04-08'), (2048, 'Сегмент 04-09'), (2049, 'Сегмент 04-10')]), ('Сегмент 05 Мостовик, Васильевское', '10.163.5.3', [(2050, 'Сегмент 05-01 МКД'), (2051, 'Сегмент 05-02 МКД'), (2052, 'Сегмент 05-03 МКД'), (2053, 'Сегмент 05-04 МКД'), (2054, 'Сегмент 05-05 PON'), (2055, 'Сегмент 05-06 PON'), (2056, 'Сегмент 05-07 МКД'), (2057, 'Сегмент 05-08 PON'), (2058, 'Сегмент 05-09 PON'), (2059, 'Сегмент 05-10 PON')]), ('Сегмент 06 Абрамцево', '10.163.6.1', [(2060, 'Сегмент 06-01 PON'), (2061, 'Сегмент 06-02'), (2062, 'Сегмент 06-03'), (2063, 'Сегмент 06-04'), (2064, 'Сегмент 06-05'), (2065, 'Сегмент 06-06'), (2066, 'Сегмент 06-07'), (2067, 'Сегмент 06-08'), (2068, 'Сегмент 06-09'), (2069, 'Сегмент 06-10')]), ('Сегмент 07 Семхоз', '10.163.7.5', [(2070, 'Сегмент 07-01 PON'), (2071, 'Сегмент 07-02 PON'), (2072, 'Сегмент 07-03'), (2073, 'Сегмент 07-04'), (2074, 'Сегмент 07-05'), (2075, 'Сегмент 07-06'), (2076, 'Сегмент 07-07'), (2077, 'Сегмент 07-08'), (2078, 'Сегмент 07-09'), (2079, 'Сегмент 07-10')]), ('Сегмент 08 Ашукино', '10.163.8.34', [(2080, 'Сегмент 08-01 PON запад'), (2081, 'Сегмент 08-02 PON восток'), (2082, 'Сегмент 08-03 МКД ВЧ 3641'), (2083, 'Сегмент 08-04'), (2084, 'Сегмент 08-05'), (2085, 'Сегмент 08-06'), (2086, 'Сегмент 08-07'), (2087, 'Сегмент 08-08'), (2088, 'Сегмент 08-09'), (2089, 'Сегмент 08-10')]), ('Сегмент 09 КП Хотьковский', '10.163.9.2', [(2090, 'Сегмент 09-01 PON'), (2092, 'Сегмент 09-03 PON'), (2093, 'Сегмент 09-04'), (2094, 'Сегмент 09-05'), (2095, 'Сегмент 09-06'), (2096, 'Сегмент 09-07'), (2097, 'Сегмент 09-08'), (2098, 'Сегмент 09-09'), (2099, 'Сегмент 09-10')]), ('Сегмент 11 SP-6 Vaksina', '10.163.11.38', [(2110, 'Сегмент 11-01 МКД'), (2111, 'Сегмент 11-02 МКД'), (2112, 'Сегмент 11-03 МКД'), (2113, 'Сегмент 11-04 МКД'), (2114, 'Сегмент 11-05 PON'), (2115, 'Сегмент 11-06'), (2116, 'Сегмент 11-07'), (2117, 'Сегмент 11-08'), (2118, 'Сегмент 11-09'), (2119, 'Сегмент 11-10')]), ('Сегмент 12 СП Кировка', '10.163.12.9', [(2120, 'Сегмент 12-01 PON Гражданка'), (2121, 'Сегмент 12-02 МАЯК'), (2122, 'Сегмент 12-03 PON Кировка'), (2123, 'Сегмент 12-04 PON Дружба'), (2124, 'Сегмент 12-05'), (2125, 'Сегмент 12-06'), (2126, 'Сегмент 12-07'), (2127, 'Сегмент 12-08'), (2128, 'Сегмент 12-09'), (2129, 'Сегмент 12-10')]), ('Сегмент 13 Васильевское', '10.163.13.8', [(2130, 'Сегмент 13-01 МКД'), (2131, 'Сегмент 13-02 PON'), (2132, 'Сегмент 13-03'), (2133, 'Сегмент 13-04'), (2134, 'Сегмент 13-05'), (2135, 'Сегмент 13-06'), (2136, 'Сегмент 13-07'), (2137, 'Сегмент 13-08'), (2138, 'Сегмент 13-09'), (2139, 'Сегмент 13-10')]), ('Сегмент 14 СП Владимирская', '10.163.14.5', [(2140, 'Сегмент 14-01 PON'), (2141, 'Сегмент 14-02'), (2142, 'Сегмент 14-03'), (2143, 'Сегмент 14-04'), (2144, 'Сегмент 14-05'), (2145, 'Сегмент 14-06'), (2146, 'Сегмент 14-07'), (2147, 'Сегмент 14-08'), (2148, 'Сегмент 14-09'), (2149, 'Сегмент 14-10')]), ('Сегмент 15 Зубцово', '10.163.15.3', [(2150, 'Сегмент 15-01 PON'), (2151, 'Сегмент 15-02'), (2152, 'Сегмент 15-03'), (2153, 'Сегмент 15-04'), (2154, 'Сегмент 15-05'), (2155, 'Сегмент 15-06'), (2156, 'Сегмент 15-07'), (2157, 'Сегмент 15-08'), (2158, 'Сегмент 15-09'), (2159, 'Сегмент 15-10')]), ('Сегмент 16 Воронцово', '10.163.16.2', [(2160, 'Сегмент 16-01 PON'), (2161, 'Сегмент 16-02'), (2162, 'Сегмент 16-03'), (2163, 'Сегмент 16-04'), (2164, 'Сегмент 16-05'), (2165, 'Сегмент 16-06'), (2166, 'Сегмент 16-07'), (2167, 'Сегмент 16-08'), (2168, 'Сегмент 16-09'), (2169, 'Сегмент 16-10')]), ('Сегмент 17 Афанасовский', '10.163.17.1', [(2170, 'Сегмент 17-01 МКД'), (2171, 'Сегмент 17-02 PON'), (2172, 'Сегмент 17-03'), (2173, 'Сегмент 17-04'), (2174, 'Сегмент 17-05'), (2175, 'Сегмент 17-06'), (2176, 'Сегмент 17-07'), (2177, 'Сегмент 17-08'), (2178, 'Сегмент 17-09'), (2179, 'Сегмент 17-10')])]

def ensure_vlans(conn):
    n = conn.execute('SELECT COUNT(*) c FROM region_vlans').fetchone()['c']
    if n == 0:
        for region, ip, rows in SEED_VLANS:
            for vlan, seg in rows:
                conn.execute('INSERT OR IGNORE INTO region_vlans (region, switch_ip, segment, vlan) VALUES (?,?,?,?)',
                             (region, ip, seg, vlan))
        conn.commit()


def _vlans_count():
    try:
        conn = get_db()
        n = conn.execute('SELECT COUNT(*) c FROM region_vlans').fetchone()['c']
        conn.close()
        return n
    except Exception:
        return -1

VL_NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'

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
        sep = '\t' if '\t' in line else (';' if line.count(';') >= line.count(',') else ',')
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



@app.route('/kb')
def kb_page():
    return render_template_string(KB_HTML)

@app.route('/api/kb', methods=['GET', 'POST'])
def kb_api():
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('SELECT id, title, category, tags, body, created_at FROM kb_articles ORDER BY id DESC').fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    c = conn.cursor()
    c.execute('INSERT INTO kb_articles (title, category, tags, body, schema, created_at) VALUES (?,?,?,?,?,?)',
              (d.get('title', ''), d.get('category', 'Прочее'), d.get('tags', ''), d.get('body', ''), '',
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    i = c.lastrowid
    conn.close()
    return jsonify({'ok': True, 'id': i})

@app.route('/api/kb/<int:aid>', methods=['GET', 'PUT', 'DELETE'])
def kb_item(aid):
    conn = get_db()
    if request.method == 'GET':
        r = conn.execute('SELECT * FROM kb_articles WHERE id=?', (aid,)).fetchone()
        conn.close()
        if not r:
            return jsonify({'error': 'nf'}), 404
        return jsonify(dict(r))
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        conn.close()
        return jsonify({'error': 'pin'}), 403
    if request.method == 'DELETE':
        conn.execute('DELETE FROM kb_articles WHERE id=?', (aid,))
        conn.commit()
        conn.close()
        return jsonify({'ok': True})
    sets = []
    vals = []
    for f in ('title', 'category', 'tags', 'body', 'schema'):
        if f in d:
            sets.append(f + '=?')
            vals.append(d[f])
    if sets:
        vals.append(aid)
        conn.execute('UPDATE kb_articles SET ' + ','.join(sets) + ' WHERE id=?', vals)
        conn.commit()
    conn.close()
    return jsonify({'ok': True})


KB_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>📖 База знаний</title>
<style>body{font-family:Arial;font-size:16px;margin:0;background:#f5f5f5;}
.card{background:#fff;margin:10px;padding:14px;border-radius:10px;box-shadow:0 1px 4px rgba(0,0,0,.15);}
.big{font-size:22px;font-weight:600;}
.btn{padding:10px 16px;border:none;border-radius:8px;color:#fff;font-size:15px;cursor:pointer;margin:3px;}
input,select,textarea{padding:8px;border:1px solid #ccc;border-radius:6px;font-size:15px;margin:3px;}
.badge{background:#1565c0;color:#fff;border-radius:10px;padding:2px 10px;font-size:13px;}
@media print{.noprint{display:none !important;}}
</style></head>
<body>
<div class="card big noprint">📖 База знаний (схемы, инструкции, пояснения)</div>
<div class="card noprint">
<input id="q" placeholder="Поиск: заголовок, теги, текст (напр. RS485, домофон, камера)" oninput="renderList()" style="width:55%;">
<select id="cat" onchange="renderList()">
<option value="">Все категории</option><option>Домофон</option><option>Камеры</option><option>Свитчи</option><option>VLAN</option><option>Питание</option><option>Прочее</option>
</select>
<button class="btn" style="background:#27ae60;" onclick="showCreate()">➕ Новая статья</button>
</div>
<div id="content"></div>
<script src="/static/common.js?v=3"></script>
<script src="/static/kb.js?v=1"></script>
</body></html>"""

@app.route('/api/attachments/file/<int:att_id>')
def attachment_file(att_id):
    conn = get_db()
    r = conn.execute('SELECT filename FROM attachments WHERE id=?', (att_id,)).fetchone()
    conn.close()
    if not r:
        return 'Файл не найден', 404
    return send_from_directory(UPLOAD_DIR, r['filename'])



@app.route('/uploads/<path:filename>')
def uploads_serve(filename):
    return send_from_directory(UPLOAD_DIR, filename)



def _missing_files():
    try:
        conn = get_db()
        rows = conn.execute('SELECT id, filename FROM attachments').fetchall()
        conn.close()
        return [r['id'] for r in rows if not os.path.exists(os.path.join(UPLOAD_DIR, r['filename']))]
    except Exception:
        return [-1]

@app.route('/api/admin/files_check')
def files_check():
    if request.args.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    conn = get_db()
    rows = conn.execute('SELECT id, filename, original_name FROM attachments').fetchall()
    conn.close()
    missing = [{'id': r['id'], 'filename': r['filename'], 'original': r['original_name']}
               for r in rows if not os.path.exists(os.path.join(UPLOAD_DIR, r['filename']))]
    return jsonify({'missing': missing, 'uploads_dir': UPLOAD_DIR,
                    'dir_exists': os.path.isdir(UPLOAD_DIR),
                    'sample': (sorted(os.listdir(UPLOAD_DIR))[:20] if os.path.isdir(UPLOAD_DIR) else [])})

UNINSTALL_SH = """#!/bin/bash
DIR="${1:-$(cd "$(dirname "$0")" && pwd)}"
echo "=== Полное удаление панели в $DIR ==="
pkill -f "python3 $DIR/swh.py" 2>/dev/null
pkill -f "python3 swh.py" 2>/dev/null
sleep 2
( crontab -l 2>/dev/null | grep -v 'swh.py' ) | crontab - 2>/dev/null
if [ "$FULL" == "1" ]; then
  echo '=== Сносим поставленные пакеты ==='
  apt-get remove -y snmp sshpass traceroute 2>/dev/null
  pip3 uninstall -y flask flask-cors 2>/dev/null
fi
cd /tmp
rm -rf "$DIR"
rm -f /tmp/swh_uninstall.sh
echo '=== Панель удалена полностью. Сервер как до установки. ==='
"""

@app.route('/api/admin/uninstall', methods=['POST'])
def admin_uninstall():
    import subprocess
    import threading
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN or d.get('confirm') != 'УДАЛИТЬ':
        return jsonify({'error': 'нужен PIN и слово подтверждения УДАЛИТЬ'}), 403
    base = os.path.dirname(os.path.abspath(__file__))
    sh = '/tmp/swh_uninstall.sh'
    open(sh, 'w').write(UNINSTALL_SH)
    os.chmod(sh, 0o755)
    env = dict(os.environ)
    env['FULL'] = '1' if d.get('full') else '0'
    subprocess.Popen(['bash', sh, base], env=env, start_new_session=True)
    threading.Timer(3.0, lambda: os._exit(0)).start()
    return jsonify({'ok': True, 'out': 'Удаление запущено: процесс остановлен, cron снят, файлы стираются.'})



@app.route('/api/admin/autostart', methods=['GET', 'POST'])
def admin_autostart():
    import subprocess
    base = os.path.dirname(os.path.abspath(__file__))
    if request.method == 'GET':
        if request.args.get('pin') != ADMIN_PIN:
            return jsonify({'error': 'pin'}), 403
        cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        return jsonify({'enabled': 'swh.py' in (cur.stdout or '')})
    d = request.json or {}
    if d.get('pin') != ADMIN_PIN:
        return jsonify({'error': 'pin'}), 403
    enable = bool(d.get('enable'))
    cur = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
    lines = [l for l in (cur.stdout or '').splitlines() if l.strip() and 'swh.py' not in l]
    if enable:
        lines.append('* * * * * cd ' + base + ' && (curl -s -o /dev/null --max-time 3 http://localhost:9500/ || nohup python3 swh.py >> swh.log 2>&1 &)')
        lines.append('@reboot sleep 5 && cd ' + base + ' && nohup python3 swh.py >> swh.log 2>&1 &')
    p = subprocess.run(['crontab', '-'], input='\n'.join(lines) + '\n', capture_output=True, text=True)
    if p.returncode != 0:
        return jsonify({'error': 'crontab: ' + (p.stderr or '')[:200]}), 500
    return jsonify({'ok': True, 'enabled': enable})


README_TXT = """УСТАНОВКА И УДАЛЕНИЕ ПАНЕЛИ ЗАМЕНЫ КОММУТАТОРОВ
================================================
1) Распаковать архив:  tar xzf swh_migrate_*.tar.gz
2) Перейти в папку:   cd swh_migrate
3) Установить и запустить:  bash deploy.sh
   (поставит flask/snmp/sshpass/traceroute, поднимет панель на порту 9500,
    пропишет автозапуск после перезагрузки и сторожа каждую минуту)
4) Автозапуск вкл/выкл: админка -> блок «🔄 Автозапуск» (кнопки Включить/Выключить).
5) Полное удаление со всеми следами:  bash uninstall.sh
   вместе с системными пакетами:      FULL=1 bash uninstall.sh
6) Все данные лежат в этой папке: база нарядов/камер/VLAN, фото (uploads),
   бэкапы (backups). Архив храните как точку отката.
7) Ollama-модели на новый сервер ставятся отдельно (без них панель работает,
   кнопки ИИ скажут «ollama недоступна»).
"""

if __name__ == '__main__':
    print("🚀 Запуск сервера...")
    print("📍 Откройте в браузере: http://localhost:9500")
    print("📊 База данных: switch_replacements.db")
    init_db()
    app.run(host='0.0.0.0', port=9500, debug=True, use_reloader=False)
