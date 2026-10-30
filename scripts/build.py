"""Genera index.html a partir de la planilla Excel, con los datos cifrados.

Uso:
    python3 scripts/build.py ruta/a/Planilla.xlsx      genera index.html
    python3 scripts/build.py --extraer-config          descifra config/clasificacion.json para editarla

La contraseña se toma de la variable de entorno II_PASSWORD o se pide por consola.
Si existe config/clasificacion.json (en claro, ignorado por git), se usa y se vuelve a
cifrar en config/clasificacion.enc. Si no existe, se descifra clasificacion.enc al vuelo.
La planilla y los datos en claro nunca se escriben en el repositorio.
"""
import base64, getpass, json, os, secrets, subprocess, sys, tempfile
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = Path(__file__).resolve().parent.parent
CFG_PLAIN = ROOT / 'config/clasificacion.json'
CFG_ENC = ROOT / 'config/clasificacion.enc'
ITER = 600_000
b64e = lambda b: base64.b64encode(b).decode()
b64d = base64.b64decode


def kdf(pw, salt, it=ITER):
    return PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=it).derive(pw.encode())


def encrypt(pw, data: bytes) -> dict:
    salt, iv = secrets.token_bytes(16), secrets.token_bytes(12)
    ct = AESGCM(kdf(pw, salt)).encrypt(iv, data, None)
    return {'v': 1, 'iter': ITER, 'salt': b64e(salt), 'iv': b64e(iv), 'ct': b64e(ct)}


def decrypt(pw, box: dict) -> bytes:
    try:
        return AESGCM(kdf(pw, b64d(box['salt']), box['iter'])).decrypt(b64d(box['iv']), b64d(box['ct']), None)
    except Exception:
        sys.exit('Contraseña incorrecta para config/clasificacion.enc.')


def password():
    pw = os.environ.get('II_PASSWORD') or getpass.getpass('Contraseña del equipo: ')
    if len(pw) < 10:
        sys.exit('Usa una contraseña de al menos 10 caracteres.')
    return pw


def main():
    args = sys.argv[1:]
    if args == ['--extraer-config']:
        pw = password()
        CFG_PLAIN.write_bytes(decrypt(pw, json.loads(CFG_ENC.read_text())))
        print(f'Configuración descifrada en {CFG_PLAIN.relative_to(ROOT)} (no se sube a git).')
        return
    if len(args) != 1:
        sys.exit(__doc__)
    xlsx = Path(args[0]).resolve()
    pw = password()
    if CFG_PLAIN.exists():
        cfg = CFG_PLAIN.read_bytes()
        CFG_ENC.write_text(json.dumps(encrypt(pw, cfg)))
    else:
        cfg = decrypt(pw, json.loads(CFG_ENC.read_text()))
    with tempfile.TemporaryDirectory() as tmp:
        raw, final, cfgp = Path(tmp, 'raw.json'), Path(tmp, 'final.json'), Path(tmp, 'cfg.json')
        cfgp.write_bytes(cfg)
        subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/parse.py'), str(xlsx), str(raw)], check=True, stdout=subprocess.DEVNULL)
        subprocess.run([sys.executable, '-I', str(ROOT / 'scripts/enrich.py'), str(raw), str(final), str(cfgp)], check=True)
        data = final.read_bytes()
    vault = json.dumps(encrypt(pw, data))
    html = (ROOT / 'src/template.html').read_text(encoding='utf-8').replace('/*VAULT*/', vault)
    (ROOT / 'index.html').write_text(html, encoding='utf-8')
    print(f'index.html generado ({len(html) // 1024} KB, datos cifrados con AES-256-GCM).')


if __name__ == '__main__':
    main()
