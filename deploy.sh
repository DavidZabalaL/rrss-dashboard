#!/bin/bash
# deploy.sh — Publica una nueva versión del dashboard
# Uso: ./deploy.sh "descripcion del cambio"
# Ejemplo: ./deploy.sh "v1.1 - nuevo gráfico de tendencias"

cd "$(dirname "$0")"

VERSION_MSG="${1:-actualización}"

echo "📦 Preparando cambios..."
git add -A

# Si no hay nada nuevo, avisar
if git diff --cached --quiet; then
  echo "⚠️  No hay cambios nuevos para publicar."
  exit 0
fi

echo "💾 Guardando versión: $VERSION_MSG"
git commit -m "$VERSION_MSG"

echo "🚀 Publicando en GitHub..."
git push origin main

echo ""
echo "✅ Listo. Streamlit Cloud actualizará la app en ~1 minuto."
echo "   https://rrss-dashboard.streamlit.app"
