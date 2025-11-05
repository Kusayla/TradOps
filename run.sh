#!/bin/bash
# Script de lancement rapide pour TradOps

cd /home/aylan/TradOps
source venv/bin/activate
export PYTHONPATH=/home/aylan/TradOps:$PYTHONPATH

# Vérifier l'argument
case "$1" in
    llm|chat)
        echo "🤖 Lancement du BOT TWITTER + LLM..."
        echo "   Le LLM interprète les tweets et décide!"
        python scripts/bot_twitter_llm.py --llm ollama
        ;;
    twitter|x)
        echo "🐦 Lancement du BOT TWITTER OPTIMISÉ..."
        echo "   Trade basé sur Twitter - Respecte limites API gratuite"
        python scripts/bot_twitter_optimized.py
        ;;
    auto|autonome|autonomous)
        echo "🤖 Lancement du BOT AUTONOME..."
        echo "   Le bot va scanner, analyser et décider SEUL!"
        python scripts/bot_autonome.py
        ;;
    ai-news|news)
        echo "🤖 Lancement du bot IA avec VRAIES NEWS..."
        python scripts/demo_ai_news.py
        ;;
    ai|demo-ai)
        echo "🤖 Lancement du bot IA..."
        python scripts/demo_ai.py
        ;;
    test)
        echo "🧪 Test des connexions..."
        python scripts/test_simple.py
        ;;
    test-finbert)
        echo "🧠 Test FinBERT..."
        python scripts/test_finbert.py
        ;;
    backtest)
        echo "📊 Lancement du backtest..."
        python scripts/backtest_simple.py
        ;;
    download)
        echo "📥 Téléchargement des données..."
        python scripts/download_historical_data.py --update
        ;;
    update)
        echo "🔄 Mise à jour des données..."
        python scripts/download_historical_data.py --update
        ;;
    status)
        echo "📊 Affichage du statut..."
        ./show_status.sh
        ;;
    smart|intelligent)
        echo "🧠 Lancement du Bot INTELLIGENT (LLM + Analyse Profonde) ⭐⭐⭐⭐⭐"
        python scripts/bot_intelligent.py
        ;;
    solana|flip)
        echo "🪙 Lancement du Bot SOLANA FAST FLIP ⚡⚡⚡⚡⚡ NOUVEAU!"
        python scripts/bot_solana_flip.py
        ;;
    *)
        echo "🤖 TradOps - Bot de Trading IA"
        echo ""
        echo "Usage: ./run.sh [commande]"
        echo ""
        echo "Commandes disponibles:"
        echo "  solana       - Bot SOLANA FAST FLIP (tokens volatils, 30sec check) ⚡⚡⚡⚡⚡ RAPIDE!"
        echo "  smart        - Bot INTELLIGENT (LLM réfléchit sur chaque crypto) ⭐⭐⭐⭐⭐"
        echo "  llm          - Bot TWITTER + LLM (IA interprète tweets) ⭐⭐⭐⭐"
        echo "  twitter      - Bot basé sur TWITTER (buzz + sentiment) ⭐⭐⭐"
        echo "  auto         - Bot AUTONOME (scanne, décide seul) ⭐⭐"
        echo "  ai-news      - Bot IA avec VRAIES news (FinBERT) ⭐"
        echo "  ai           - Bot IA avec sentiment simulé"
        echo "  test         - Tester les connexions"
        echo "  test-finbert - Tester FinBERT"
        echo "  backtest     - Faire un backtest"
        echo "  download     - Mettre à jour les données historiques"
        echo "  update       - Alias pour download"
        echo "  status       - Afficher le statut du système"
        echo ""
        echo "Exemples:"
        echo "  ./run.sh solana      # Bot SOLANA FLIP (ultra-rapide) ⚡⚡⚡⚡⚡ RAPIDE!"
        echo "  ./run.sh smart       # Bot INTELLIGENT (LLM analyse) ⭐⭐⭐⭐⭐"
        echo "  ./run.sh llm         # Bot Twitter + LLM ⭐⭐⭐⭐"
        echo "  ./run.sh backtest    # Lance un backtest"
        echo ""
        echo "💡 Pour LLM: Installez Ollama (gratuit): https://ollama.com/"
        ;;
esac

