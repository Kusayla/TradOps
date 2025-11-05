#!/bin/bash
# Afficher le statut du système TradOps

cd /home/aylan/TradOps

echo "================================================================================"
echo "🤖 TRADOPS - STATUT DU SYSTÈME"
echo "================================================================================"
echo ""

# Configuration
echo "📋 CONFIGURATION:"
echo "   Mode de trading: $(grep TRADING_MODE .env | cut -d= -f2)"
echo "   Exchange: $(grep DEFAULT_EXCHANGE .env | cut -d= -f2)"
echo "   Actifs: $(grep WHITELISTED_ASSETS .env | cut -d= -f2 | tr ',' '\n' | wc -l) cryptos"
echo ""

# Environnement
echo "🔧 ENVIRONNEMENT:"
if [ -d "venv" ]; then
    echo "   ✅ Environnement virtuel: Installé"
else
    echo "   ❌ Environnement virtuel: Non installé"
fi

source venv/bin/activate 2>/dev/null
if command -v python &> /dev/null; then
    echo "   ✅ Python: $(python --version 2>&1)"
else
    echo "   ❌ Python: Non disponible"
fi

# Packages IA
if python -c "import torch" 2>/dev/null; then
    echo "   ✅ PyTorch: Installé"
else
    echo "   ❌ PyTorch: Non installé"
fi

if python -c "import transformers" 2>/dev/null; then
    echo "   ✅ Transformers: Installé"
else
    echo "   ❌ Transformers: Non installé"
fi
echo ""

# Données
echo "📊 DONNÉES HISTORIQUES:"
if [ -d "data/historical" ]; then
    file_count=$(ls data/historical/*.csv 2>/dev/null | wc -l)
    total_size=$(du -sh data/historical 2>/dev/null | cut -f1)
    echo "   ✅ Fichiers: $file_count"
    echo "   ✅ Taille totale: $total_size"
    echo ""
    echo "   Fichiers disponibles:"
    ls -1 data/historical/*.csv 2>/dev/null | while read file; do
        filename=$(basename "$file")
        size=$(du -h "$file" | cut -f1)
        echo "      • $filename ($size)"
    done
else
    echo "   ❌ Aucune donnée téléchargée"
fi
echo ""

# Logs
echo "📝 LOGS:"
if [ -d "logs" ]; then
    log_count=$(ls logs/*.log 2>/dev/null | wc -l)
    if [ $log_count -gt 0 ]; then
        echo "   ✅ Fichiers de log: $log_count"
        latest=$(ls -t logs/*.log 2>/dev/null | head -1)
        if [ -n "$latest" ]; then
            echo "   📄 Dernier: $(basename "$latest")"
        fi
    else
        echo "   ℹ️  Aucun log (bot pas encore lancé)"
    fi
else
    echo "   ℹ️  Dossier logs créé"
fi
echo ""

# Scripts
echo "🚀 SCRIPTS DISPONIBLES:"
echo "   ./run.sh ai         → Lancer le bot IA"
echo "   ./run.sh test       → Tester connexions"
echo "   ./run.sh backtest   → Faire un backtest"
echo "   ./run.sh update     → Mettre à jour données"
echo ""

# Documentation
echo "📚 DOCUMENTATION:"
echo "   START_HERE.md          → Démarrage rapide (30 sec)"
echo "   QUICKSTART_AI.md       → Guide IA complet"
echo "   STATUS.md              → État détaillé"
echo "   docs/SECURITY.md       → Sécurité (À LIRE!)"
echo ""

echo "================================================================================"
echo "🎯 PROCHAINE ÉTAPE:"
echo "   ./run.sh ai"
echo "================================================================================"
