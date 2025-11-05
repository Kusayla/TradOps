#!/bin/bash

################################################################################
# Script de Push Rapide vers GitHub
################################################################################

echo "════════════════════════════════════════════════════════════════════════════"
echo "🚀 PUSH COMPLET VERS GITHUB"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

cd /home/aylan/TradOps

# Vérifier qu'on est bien dans un repo Git
if [ ! -d .git ]; then
    echo "❌ Erreur : Pas un repository Git"
    exit 1
fi

# Afficher le statut
echo "📊 Statut actuel :"
echo ""
git status --short
echo ""

# Demander confirmation
read -p "Voulez-vous ajouter TOUS les fichiers et pousser ? (o/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Oo]$ ]]; then
    echo "❌ Annulé"
    exit 0
fi

echo ""
echo "📦 Ajout de tous les fichiers..."
git add .

echo ""
echo "💾 Création du commit..."
git commit -m "Complete bot setup with dashboard and all features

- Trading bot with AI signals
- Twitter integration with LLM analysis
- Autonomous trading strategies
- Web dashboard for GitHub Pages
- Complete documentation"

echo ""
echo "⬆️  Push vers GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo "✅ PUSH RÉUSSI !"
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "📋 PROCHAINES ÉTAPES :"
    echo ""
    echo "1. Activez GitHub Pages :"
    echo "   → https://github.com/Kusayla/TradOps/settings/pages"
    echo "   → Source : main branch"
    echo "   → Folder : /web"
    echo ""
    echo "2. Attendez 2-3 minutes"
    echo ""
    echo "3. Visitez votre dashboard :"
    echo "   → https://kusayla.github.io/TradOps/"
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
else
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo "❌ ERREUR DE PUSH"
    echo "════════════════════════════════════════════════════════════════════════════"
    echo ""
    echo "Si l'authentification a échoué, créez un Personal Access Token :"
    echo ""
    echo "1. GitHub.com → Settings → Developer settings"
    echo "2. Personal access tokens → Tokens (classic)"
    echo "3. Generate new token"
    echo "4. Cochez 'repo' et 'workflow'"
    echo "5. Utilisez le token comme mot de passe lors du push"
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    exit 1
fi

