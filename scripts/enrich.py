"""Clasifica los datos de la planilla en capa administrativa / de gestión y por dispositivo.

Uso: python3 enrich.py datos_crudos.json salida.json config/clasificacion.json
La configuración (nombres, separación de textos administrativos, etc.) vive en
config/clasificacion.json, que se guarda cifrado en el repositorio.
"""
import hashlib, json, sys

d = json.load(open(sys.argv[1], encoding='utf-8'))
cfg = json.load(open(sys.argv[3], encoding='utf-8'))
NOMBRES = cfg.get('nombres', {})
PIPE = cfg.get('pipeline_por_bloque', {})
SPLIT = cfg.get('separacion_admin', {})
ADMIN_TASKS = set(cfg.get('tareas_admin', []))
ADMIN_RISKS = set(cfg.get('riesgos_admin', []))
ADMIN_CAL = cfg.get('calendario_admin_prefijos', [])
RISK_D = {int(k): v for k, v in cfg.get('riesgos_dispositivo', {}).items()}

existing = {p['bloque'] for p in d['proyectos']}
for extra in cfg.get('proyectos_extra', []):
    if extra['bloque'] not in existing:
        d['proyectos'].append(extra)

for i, p in enumerate(d['proyectos']):
    p['id'] = 'p%02d' % i
    p['nombre'] = NOMBRES.get(p['bloque'], p['bloque'].title())
    p['capa'] = 'admin' if p['dispositivo'] == 'Administración' else 'gestion'
    p['pipeline'] = PIPE.get(p['bloque'])
    sp = SPLIT.get(p['bloque'], {})
    for k in ('objetivo', 'contexto'):
        if k in sp:
            p[k] = sp[k]
    p['admin'] = sp.get('admin', [])
    p['actores'] = [a for a in p['actores'] if a['n']]

bmap = {p['bloque']: p['id'] for p in d['proyectos']}
disp_first = {}
for p in d['proyectos']:
    disp_first.setdefault(p['dispositivo'], p['id'])
for t in d['tareas']:
    # A task whose block has no sheet is attached to the first project of its dispositivo
    t['proyecto'] = bmap.get(t['bloque']) or disp_first.get(t['dispositivo'])
    t['capa'] = 'admin' if (t['id'] in ADMIN_TASKS or t['dispositivo'] == 'Administración') else 'gestion'
    del t['bloque']
for r in d['riesgos']:
    r['#'] = int(r['#'])
    r['capa'] = 'admin' if r['#'] in ADMIN_RISKS else 'gestion'
    r['disp'] = RISK_D.get(r['#'], 'Transversal')
for c in d['calendario']:
    c['capa'] = 'admin' if any(c['Hito / reunión'].startswith(x) for x in ADMIN_CAL) else 'gestion'
    c['disp'] = c['Dispositivo'] if c['Dispositivo'] in ('Ferias', 'Gremios', 'Investigación') else 'Transversal'
for disp in d['dispositivos']:
    disp['coordinador'] = disp['coordinador'].split(':', 1)[1].strip()
    disp['capa'] = 'admin' if disp['nombre'] == 'Administración' else 'gestion'
    for k in disp['claves']:
        k['capa'] = 'admin' if k['tarea'].startswith('Contrato tipo') or disp['nombre'] == 'Administración' else 'gestion'

def actor_d(t):
    if t.startswith('Gremios') or t == 'Formación':
        return 'Gremios'
    if t == 'Investigación':
        return 'Investigación'
    return 'Ferias'

for a in d['actores']:
    a['disp'] = actor_d(a['Territorio / dispositivo'])
for m in d['metas']:
    m['disp'] = 'Ferias' if 'crowdfunding' in m['meta'].lower() else 'Gremios'
for p in d['pipeline']:
    p['disp'] = p['Dispositivo']

d['corte'] = d.get('corte') or ''
d['ver'] = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
json.dump(d, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(sum(t['capa'] == 'admin' for t in d['tareas']), 'tareas administrativas de', len(d['tareas']))
