import ast, json, os, re, shutil
from datetime import datetime
TS = datetime.now().strftime('%Y%m%d_%H%M%S')
os.makedirs('backups', exist_ok=True)
shutil.copyfile('swh.py', 'backups/swh_pre_v22_' + TS + '.py')
src = open('swh.py', encoding='utf-8').read()
FIXES = []
def rep(old, new, label):
    global src
    if old in src:
        src = src.replace(old, new, 1); FIXES.append(label); print('  ok:', label)
    else:
        print('  ПРОПУСК:', label)

# 1) КРИТИЧНО: /netlab без Jinja (CSS содержит {# → Jinja падал)
rep("def netlab_page():\n    return render_template_string(NETLAB_HTML)",
    "def netlab_page():\n    return Response(NETLAB_HTML, mimetype='text/html')",
    'netlab без Jinja')

# 2) Новый дизайн холста NetLab (миллиметровка, стекло, терминал)
i = src.find('NETLAB_HTML = """')
if i >= 0:
    a = src.find('<style>', i)
    b = src.find('</style>', a)
    if a > 0 and b > a:
        NEWCSS = """<style>
*{box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,Arial,sans-serif;font-size:15px;margin:0;background:#eef2f7;color:#1f2d3d}
#nlTop{background:linear-gradient(90deg,#1f2d3d,#2c3e50);color:#fff;padding:10px 14px;display:flex;gap:6px;flex-wrap:wrap;align-items:center;position:sticky;top:0;z-index:10;box-shadow:0 4px 16px rgba(15,23,42,.25)}
#nlTop b{font-size:16px;letter-spacing:.3px;margin-right:6px}
#nlTop button{padding:8px 13px;border:none;border-radius:10px;cursor:pointer;font-weight:600;font-size:13px;transition:transform .12s,filter .12s}
#nlTop button:hover{transform:translateY(-1px);filter:brightness(1.1)}
#nlWrap{display:flex;gap:10px;padding:10px;height:calc(100vh - 56px)}
#nlPal{width:172px;background:#fff;border-radius:14px;padding:10px;overflow-y:auto;box-shadow:0 6px 18px rgba(31,45,61,.10);border:1px solid #e6ecf4}
#nlPal button{display:block;width:100%;margin:5px 0;padding:9px 10px;border:1px solid #e6ecf4;border-radius:10px;background:#f8fafc;cursor:pointer;text-align:left;font-size:13px;font-weight:600;color:#334155;transition:background .12s,transform .12s}
#nlPal button:hover{background:#e8f0fe;transform:translateX(2px)}
#nlCanvasBox{flex:1;background:#fff;border-radius:14px;position:relative;overflow:hidden;box-shadow:0 6px 18px rgba(31,45,61,.10);border:1px solid #e6ecf4;background-image:linear-gradient(#f1f5f9 1px,transparent 1px),linear-gradient(90deg,#f1f5f9 1px,transparent 1px);background-size:24px 24px}
#nlCanvas{width:100%;height:100%;cursor:grab}
#nlSide{width:312px;background:#fff;border-radius:14px;padding:12px;overflow-y:auto;box-shadow:0 6px 18px rgba(31,45,61,.10);border:1px solid #e6ecf4}
#nlSide b{color:#1f2d3d;font-size:14px}
#nlSide input,#nlSide select{width:100%;padding:7px 9px;margin:4px 0;border:1px solid #d6dfe9;border-radius:9px;font-size:13px;background:#fbfdff}
#nlSide input:focus,#nlSide select:focus{outline:2px solid rgba(37,99,235,.30);border-color:#2563eb}
#nlSide hr{border:none;border-top:1px solid #e6ecf4;margin:10px 0}
#nlLog{background:#0b1220;color:#7cfc00;font-family:Consolas,monospace;font-size:12px;height:170px;overflow-y:auto;border-radius:10px;padding:8px;margin-top:8px;white-space:pre-wrap;border:1px solid #1e293b}
.nlLbl{font-size:12px;fill:#5b6b7c;font-family:'Segoe UI',Arial}
@media print{#nlTop,#nlPal,#nlSide{display:none}#nlWrap{height:auto}#nlCanvasBox{box-shadow:none;border:none}}
</style>"""
        src = src[:a] + NEWCSS + src[b+len('</style>'):]
        FIXES.append('netlab design'); print('  ok: дизайн NetLab')

# 3) Глобальная тема UI22 вместо UI20
i = src.find('UI20_CSS = """')
if i >= 0:
    j = src.find('"""', i + len('UI20_CSS = """'))
    if j > i:
        NEWUI = '''UI20_CSS = """
:root{--bg:#eef2f7;--card:#ffffff;--ink:#1f2d3d;--mut:#64748b;--acc:#2563eb;--acc2:#1e40af;--rad:14px;--line:#e6ecf4}
*{box-sizing:border-box}
body{background:var(--bg)!important;color:var(--ink);font-family:'Segoe UI',system-ui,-apple-system,Arial,sans-serif!important;-webkit-font-smoothing:antialiased}
.navbar{position:sticky;top:0;z-index:60;background:linear-gradient(90deg,#1f2d3d,#2c3e50)!important;box-shadow:0 4px 18px rgba(15,23,42,.28);flex-wrap:wrap;gap:.4rem;padding:.7rem 1.2rem!important}
.nav-brand{font-size:1.15rem!important;letter-spacing:.3px}
.nav-links{flex-wrap:wrap;gap:.3rem!important}
.nav-link{border-radius:9px;padding:.4rem .75rem!important;font-size:.9rem;font-weight:600;transition:background .15s,transform .15s}
.nav-link:hover{background:rgba(255,255,255,.16)!important;transform:translateY(-1px)}
.container{max-width:1540px!important;padding:1.1rem!important}
.page-header h1{font-size:1.5rem;letter-spacing:.2px}
.card,.order-card,.info-card,.map-container,.map-controls,.modal-content{background:var(--card)!important;border-radius:var(--rad)!important;box-shadow:0 6px 18px rgba(31,45,61,.09)!important;border:1px solid var(--line)!important}
.order-card{transition:transform .15s,box-shadow .15s}
.order-card:hover{transform:translateY(-3px);box-shadow:0 12px 26px rgba(31,45,61,.16)!important}
.orders-grid{gap:1rem!important;grid-template-columns:repeat(auto-fill,minmax(330px,1fr))!important}
.btn{border-radius:10px!important;font-weight:600;font-size:.92rem;letter-spacing:.2px;transition:transform .12s,box-shadow .12s,filter .12s;border:none}
.btn:hover{transform:translateY(-1px);box-shadow:0 6px 14px rgba(0,0,0,.18);filter:brightness(1.06)}
.btn-primary{background:linear-gradient(135deg,#2563eb,#1e40af)!important;color:#fff!important}
.btn-success{background:linear-gradient(135deg,#16a34a,#15803d)!important;color:#fff!important}
.btn-danger{background:linear-gradient(135deg,#dc2626,#b91c1c)!important;color:#fff!important}
.btn-secondary{background:#e2e8f0!important;color:#334155!important}
input,select,textarea{border-radius:10px!important;border:1px solid #d6dfe9!important;padding:.55rem .7rem!important;background:#fbfdff;font-size:.95rem;transition:border .15s,outline .15s}
input:focus,select:focus,textarea:focus{outline:2px solid rgba(37,99,235,.28);border-color:var(--acc)!important}
select{max-width:100%}
.data-table{border-radius:12px;overflow:hidden;border:1px solid var(--line)}
.data-table th{background:#334155!important;color:#f1f5f9;font-weight:600;font-size:.85rem;text-transform:uppercase;letter-spacing:.4px}
.data-table td,.data-table th{padding:.6rem .85rem!important}
.data-table tr:nth-child(even){background:#f8fafc}
.data-table tr:hover{background:#eef4ff}
pre{border-radius:10px;background:#0b1220;color:#7cfc00;padding:10px;border:1px solid #1e293b}
.modal{backdrop-filter:blur(3px);background:rgba(15,23,42,.45)!important}
.modal-content{max-width:900px!important;width:94%;max-height:88vh;overflow-y:auto;border-radius:16px!important}
.uplink-field{flex-wrap:wrap;align-items:center;gap:.5rem}
.uplink-field select{flex:2;min-width:230px}
.badge,.status-badge{border-radius:999px!important;font-weight:600;font-size:.78rem;padding:.25rem .7rem!important}
h1,h2,h3{color:var(--ink);letter-spacing:.2px}
h3{font-size:1.05rem;margin:1.2rem 0 .7rem}
#topoSection,#topoCanvas{border-radius:14px}
#topoSection{background:#fff;border:1px solid var(--line);padding:12px;margin-bottom:12px;box-shadow:0 6px 18px rgba(31,45,61,.09)}
#todoBox{border-radius:12px!important;border:1px solid #fde68a!important;background:#fffbeb!important}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:#c3ced9;border-radius:8px;border:2px solid var(--bg)}
::-webkit-scrollbar-track{background:transparent}
@media print{.navbar,.btn,.noprint{display:none!important}.container{max-width:100%!important}}
"""'''
        src = src[:i] + NEWUI + src[j+3:]
        FIXES.append('UI22 theme'); print('  ok: глобальная тема UI22')
rep("'id=\"ui20\"' not in t", "'id=\"ui22\"' not in t", 'маркер ui22 (check)')
rep("'<style id=\"ui20\">'", "'<style id=\"ui22\">'", 'маркер ui22 (inject)')

# 4) Штамп + проверка + запись
try:
    ast.parse(src)
except SyntaxError as e:
    shutil.copyfile('backups/swh_pre_v22_' + TS + '.py', 'swh.py')
    raise SystemExit('СИНТАКСИС НЕ ОК — откат: ' + str(e))
open('swh.py', 'w', encoding='utf-8').write(src)
json.dump({'ts': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'version': 'v22', 'fixes': FIXES},
          open('update_stamp.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ГОТОВО v22. Правок:', len(FIXES), '| бэкап: backups/swh_pre_v22_' + TS + '.py')
