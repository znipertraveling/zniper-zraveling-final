#!/usr/bin/env bash
# Arranca el sitio en http://127.0.0.1:5002 — deja esta ventana ABIERTA mientras lo revisas.
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  echo "Creando entorno virtual (.venv)..."
  python3 -m venv .venv
fi
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -r requirements.txt
echo ""
echo ">>> Servidor listo. Abre en el navegador: http://127.0.0.1:5002"
echo ">>> Admin: http://127.0.0.1:5002/admin"
echo ">>> Para parar: Ctrl+C"
echo ""
exec python app.py
