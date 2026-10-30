import openpyxl, sys, json, datetime, re

wb = openpyxl.load_workbook(sys.argv[1], data_only=True)

def fmt(v):
    if isinstance(v, datetime.datetime):
        return v.strftime('%Y-%m-%d')
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v

DISP = {'Dispositivo ferias': 'Ferias', 'Dispositivo gremios': 'Gremios',
        'Investigación': 'Investigación', 'Administración II': 'Administración'}

proyectos = []
dispositivos = []
for sheet, dname in DISP.items():
    ws = wb[sheet]
    rows = [[fmt(c) for c in r] for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
    coord = rows[1][1]
    claves = []
    i = 3
    while rows[i][1] and not (i + 1 < len(rows) and rows[i + 1][1] == 'Objetivo:'):
        claves.append({'tarea': rows[i][1], 'resp': rows[i][3]})
        i += 1
    dispositivos.append({'nombre': dname, 'coordinador': coord, 'claves': claves})
    for off in (1, 5):
        cur = None; sec = None
        for r in rows[i:]:
            a = r[off] if off < len(r) else None
            b = r[off + 1] if off + 1 < len(r) else None
            c = r[off + 2] if off + 2 < len(r) else None
            if a is None and b is None:
                continue
            if a == 'Objetivo:':
                cur['objetivo'] = b; continue
            if a == 'Contexto:':
                cur['contexto'] = b; continue
            if a == 'Actores Claves:':
                sec = 'act'; continue
            if a == 'Nombre:':
                continue
            if a == 'Hechos claves:':
                sec = 'hech'; continue
            if a == 'Próximas tareas:':
                sec = 'tar'; continue
            if isinstance(a, str) and a.isupper() and b is None and (sec is None or sec == 'tar') and not a.startswith('•'):
                cur = {'dispositivo': dname, 'bloque': a, 'objetivo': '', 'contexto': '', 'actores': [], 'hechos': []}
                proyectos.append(cur); sec = None; continue
            if cur is None:
                continue
            if sec == 'act':
                cur['actores'].append({'n': a, 'f': b, 't': c})
            elif sec == 'hech':
                if a and a.startswith('•'):
                    a = a.lstrip('• ').strip()
                    if a != '(sin registro)':
                        cur['hechos'].append(a)
                elif a:  # e.g. extra actor row after Hechos header in right column
                    cur['actores'].append({'n': a, 'f': b, 't': c})

# Seguimiento
ws = wb['Seguimiento']
tareas = []
for r in ws.iter_rows(min_row=4, values_only=True):
    r = [fmt(c) for c in r]
    if r[1] and re.match(r'^[FGIAH]-\d+$', str(r[1])):
        tareas.append(dict(zip(['id', 'dispositivo', 'bloque', 'actividad', 'resp', 'fecha', 'estado', 'prioridad', 'obs'], r[1:10])))

def table(name, start, ncols):
    ws = wb[name]
    rows = [[fmt(c) for c in r] for r in ws.iter_rows(values_only=True) if any(c is not None for c in r)]
    hdr = rows[start][1:1 + ncols]
    out = []
    for r in rows[start + 1:]:
        if r[1] is None or str(r[1]).startswith('Avance'): break
        out.append(dict(zip(hdr, r[1:1 + ncols])))
    return out

pipeline = table('Pipeline y metas', 2, 11)
ws = wb['Pipeline y metas']
metas = []
for r in ws.iter_rows(min_row=1, values_only=True):
    if r[1] and isinstance(r[2], (int, float)) and r[3] is not None and isinstance(r[1], str) and not r[1].startswith('Cliente'):
        if r[1] in [p['Cliente / Proyecto'] for p in pipeline]: continue
        metas.append({'meta': r[1], 'objetivo': fmt(r[2]), 'logrado': fmt(r[3])})
calendario = table('Calendario', 2, 5)
actores = table('Mapa de actores', 2, 7)
riesgos = table('Riesgos y decisiones', 2, 7)

corte = None
for r in wb['Portada'].iter_rows(values_only=True):
    if r[1] == 'Fecha de corte:': corte = fmt(r[2])
json.dump({'corte': corte, 'dispositivos': dispositivos, 'proyectos': proyectos, 'tareas': tareas, 'pipeline': pipeline,
           'metas': metas, 'calendario': calendario, 'actores': actores, 'riesgos': riesgos},
          open(sys.argv[2], 'w'), ensure_ascii=False, indent=1)
print(len(proyectos), [p['bloque'] for p in proyectos])
print(len(tareas), len(pipeline), metas, len(calendario), len(actores), len(riesgos))
for p in proyectos: print(p['bloque'], len(p['actores']), len(p['hechos']))
for d in dispositivos: print(d)
