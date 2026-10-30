# Gestión de dispositivos · Ingeniería Institucional

Herramienta web para visualizar y hacer seguimiento a los proyectos de Ingeniería Institucional
(dispositivos Ferias, Gremios, Investigación y Administración), construida a partir de la
*Planilla de gestión* del equipo.

**App web:** https://tlaibe.github.io/gestion-ingenieria-institucional/

## Qué hace

- **Selector de dispositivo** (Todos · Ferias · Gremios · Investigación) que filtra todas las vistas.
- **Capa administrativa** que se muestra u oculta con un interruptor: contratos, facturación,
  finanzas, gobierno societario, pipeline y metas de la Circular.
- Vistas: Resumen, Proyectos (fichas por bloque), Tareas (tabla y tablero), Calendario,
  Mapa de actores, Riesgos y decisiones, Comercial y metas.
- Edición de estados, prioridades y tareas nuevas; exportación a CSV (Excel) y respaldo JSON.

## Confidencialidad

El repositorio es público para poder servir la app con GitHub Pages, pero **los datos no**:

- `index.html` contiene los datos **cifrados con AES-256-GCM** (clave derivada con PBKDF2-SHA256,
  600.000 iteraciones). La app pide la contraseña del equipo y descifra en el navegador.
- `config/clasificacion.enc` guarda cifrada la configuración curada (nombres, separación de
  textos administrativos, clasificación de riesgos).
- La planilla `.xlsx` y cualquier JSON en claro están en `.gitignore` y nunca se suben.
- Los cambios que cada persona hace en la app quedan **solo en su navegador** (localStorage).
  Para compartirlos, usar *Datos → Descargar respaldo* e *Importar respaldo*.

Usa una contraseña larga y compártela por un canal privado. Si se filtra, genera de nuevo
con otra contraseña (ver abajo).

## Actualizar con una nueva planilla

Requiere Python 3 con `openpyxl` y `cryptography` (`pip install openpyxl cryptography`).

```bash
python3 scripts/build.py ruta/a/Planilla_Dispositivos.xlsx   # pide la contraseña
git add index.html config/clasificacion.enc
git commit -m "Actualiza datos al corte DD-MM-AAAA"
git push
```

GitHub Pages publica el cambio en uno o dos minutos. Al abrir la app, si los datos cambiaron,
se reemplazan las ediciones locales por los de la nueva planilla.

### Cambiar la contraseña

```bash
python3 scripts/build.py --extraer-config          # con la contraseña actual
II_PASSWORD='nueva-contraseña' python3 scripts/build.py Planilla.xlsx
rm config/clasificacion.json
```

### Editar la clasificación

`python3 scripts/build.py --extraer-config` deja `config/clasificacion.json` en claro (ignorado por
git). Ahí se definen qué tareas y riesgos son administrativos, el dispositivo de cada riesgo, los
nombres visibles de los proyectos y los textos administrativos separados de cada ficha.
Al volver a ejecutar `build.py` se recifra en `clasificacion.enc`.

## Estructura

```
index.html               App publicada (generada; datos cifrados)
src/template.html        Interfaz (HTML, CSS y JS sin dependencias)
scripts/parse.py         Lee la planilla Excel
scripts/enrich.py        Clasifica en capa administrativa / gestión y por dispositivo
scripts/build.py         Cifra los datos y genera index.html
config/clasificacion.enc Configuración curada, cifrada
```
