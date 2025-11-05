#!/bin/bash
################################################################################
# Script de mise à jour automatique du dashboard
################################################################################

cd /home/aylan/TradOps
source venv/bin/activate

echo "════════════════════════════════════════════════════════════════"
echo "🔄 Mise à jour du dashboard - $(date '+%Y-%m-%d %H:%M:%S')"
echo "════════════════════════════════════════════════════════════════"

# Exporter les données depuis Redis
echo "📊 Export des données de trading..."
python scripts/export_dashboard_data.py

# Vérifier si l'export a réussi
if [ $? -eq 0 ]; then
    echo "✅ Export réussi"
    
    # Vérifier si le fichier a changé
    if git diff --quiet docs/data/latest.json; then
        echo "ℹ️  Aucun changement détecté"
    else
        echo "📤 Push vers GitHub..."
        git add docs/data/latest.json
        git commit -m "Auto-update dashboard - $(date '+%Y-%m-%d %H:%M')"
        git push origin main
        
        if [ $? -eq 0 ]; then
            echo "✅ Dashboard mis à jour sur GitHub Pages"
            echo "🌐 Visible dans 1-2min : https://kusayla.github.io/TradOps/"
        else
            echo "❌ Erreur lors du push vers GitHub"
            exit 1
        fi
    fi
else
    echo "❌ Erreur lors de l'export des données"
    exit 1
fi

echo "════════════════════════════════════════════════════════════════"
echo "✅ Terminé"
echo "════════════════════════════════════════════════════════════════"

