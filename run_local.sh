#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

echo "==> Ensuring PostgreSQL is running"
brew services start postgresql@16 >/dev/null 2>&1 || true
until pg_isready -q; do sleep 1; done

echo "==> Ensuring database exists"
createdb urbancart 2>/dev/null || true

echo "==> Creating / using virtualenv"
PY=python3.12
command -v "$PY" >/dev/null || PY=python3
if [[ ! -d .venv ]]; then
  "$PY" -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install -q -U pip
python -m pip install -r requirements.txt


if [[ ! -f dataset/orders.csv ]]; then
  echo "==> Building UrbanCart tables from dataset/raw (Olist)"
  python transform_olist.py
fi

echo "==> Loading data + building analytics"
python setup_local.py

echo "==> Exporting Power BI dataset (CSV + TMDL)"
python powerbi/export_dataset.py
python powerbi/generate_semantic_model.py

echo "==> Starting Streamlit dashboard"
echo "    Power BI: open powerbi/UrbanCart_Olist.pbip in Power BI Desktop (see powerbi/README.md)"
exec python -m streamlit run app.py --server.headless true
