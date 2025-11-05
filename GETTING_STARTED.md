# 🚀 Guide de Démarrage Rapide - TradOps

Bienvenue sur TradOps ! Ce guide vous aidera à démarrer rapidement, que vous souhaitiez tester gratuitement ou trader avec de l'argent réel.

## 🎯 Choix de votre Parcours

### Option 1 : Tester Sans Risque (MODE PUBLIC) ⭐ RECOMMANDÉ

**Parfait si vous :**
- Découvrez le trading automatisé
- Voulez tester le bot sans dépenser d'argent
- N'avez pas encore de compte exchange
- Voulez faire du backtesting

**Temps de setup : 5 minutes**

```bash
# 1. Installer les dépendances
./scripts/setup.sh

# 2. Créer le fichier .env
cp env.template .env

# 3. Éditer .env et définir :
TRADING_MODE=public
DEFAULT_EXCHANGE=bybit
WHITELISTED_ASSETS=BTC/USDT,ETH/USDT,SOL/USDT
INITIAL_CAPITAL=10000

# 4. Tester la connexion
python scripts/test_connection.py

# 5. Télécharger des données historiques (optionnel, pour backtesting)
python scripts/download_historical_data.py

# 6. Lancer le bot
python src/main.py
```

**Avantages :**
- ✅ 100% gratuit
- ✅ Aucun risque
- ✅ Pas de clés API nécessaires
- ✅ Données de marché en temps réel
- ✅ Paper trading complet
- ✅ Backtesting sur données historiques

---

### Option 2 : Tester sur Testnet Exchange

**Parfait si vous :**
- Avez testé en mode public
- Voulez tester en conditions quasi-réelles
- Êtes prêt à créer un compte exchange (gratuit)

**Temps de setup : 15 minutes**

```bash
# 1. Créer un compte Bybit (recommandé)
# https://www.bybit.com/
# https://testnet.bybit.com/ (pour testnet)

# 2. Créer des clés API testnet
# Voir docs/EXCHANGE_SETUP.md

# 3. Configurer .env
TRADING_MODE=testnet
DEFAULT_EXCHANGE=bybit
BYBIT_API_KEY=your_testnet_key
BYBIT_API_SECRET=your_testnet_secret
BYBIT_TESTNET=true

# 4. Tester et lancer
python scripts/test_connection.py
python src/main.py
```

**Avantages :**
- ✅ Trading simulé sur vrai exchange
- ✅ Argent fictif
- ✅ Conditions quasi-réelles
- ✅ Test de l'exécution d'ordres

---

### Option 3 : Trading Réel avec Argent Réel ⚠️

**ATTENTION : Utilisez uniquement de l'argent que vous pouvez vous permettre de perdre !**

**Prérequis OBLIGATOIRES :**
- ✅ Backtesting avec Sharpe ratio > 1.5 sur 3+ mois
- ✅ Paper trading profitable pendant 1+ semaine
- ✅ Testnet profitable pendant 1+ semaine
- ✅ Comprendre les risques du trading crypto
- ✅ Capital : 100-500€ pour commencer

**Temps de setup : 30 minutes + période de test**

```bash
# 1. Créer un compte exchange (recommandé: Bybit)
# Voir docs/EXCHANGE_SETUP.md

# 2. Activer 2FA (OBLIGATOIRE)

# 3. Créer des clés API LIVE
# IMPORTANT: Permissions limitées (NO WITHDRAW!)
# IMPORTANT: IP Whitelist activée
# Voir docs/EXCHANGE_SETUP.md et docs/SECURITY.md

# 4. Configurer .env
TRADING_MODE=live
DEFAULT_EXCHANGE=bybit
BYBIT_API_KEY=your_live_key
BYBIT_API_SECRET=your_live_secret
BYBIT_TESTNET=false

# Risk Management (CRITIQUE!)
MAX_POSITION_SIZE=0.05  # 5% max
MAX_DAILY_LOSS=0.02     # 2% max
MAX_DRAWDOWN=0.10       # 10% max
INITIAL_CAPITAL=500     # Votre capital réel

# Alertes (RECOMMANDÉ)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# 5. Tester
python scripts/test_connection.py

# 6. Lancer avec surveillance
python src/main.py
```

**⚠️ CHECKLIST DE SÉCURITÉ AVANT LIVE :**
- [ ] Backtests validés (3+ mois, Sharpe > 1.5)
- [ ] Paper trading profitable (1+ semaine)
- [ ] Testnet profitable (1+ semaine)
- [ ] API keys avec permissions limitées (NO WITHDRAW)
- [ ] IP Whitelist configurée
- [ ] 2FA activé sur exchange
- [ ] Alertes Telegram/Slack configurées
- [ ] Limites de risque définies et comprises
- [ ] Capital = montant que vous pouvez perdre

---

## 📚 Documentation Complète

- **[README.md](README.md)** - Vue d'ensemble du projet
- **[docs/EXCHANGE_SETUP.md](docs/EXCHANGE_SETUP.md)** - Guide détaillé pour choisir et configurer votre exchange
- **[docs/SECURITY.md](docs/SECURITY.md)** - Bonnes pratiques de sécurité (CRITIQUE pour live trading)
- **[env.template](env.template)** - Template de configuration complet

## 🔧 Commandes Utiles

```bash
# Télécharger des données historiques
python scripts/download_historical_data.py --help

# Mettre à jour les données existantes
python scripts/download_historical_data.py --update

# Tester les connexions
python scripts/test_connection.py

# Backtesting
python scripts/backtest.py

# Lancer le bot
python src/main.py

# Docker Compose (tous les services)
./scripts/start.sh
./scripts/stop.sh
```

## 🎓 Workflow d'Apprentissage Recommandé

### Semaine 1-2 : Mode Public
1. Installer et configurer en mode public
2. Observer le bot pendant quelques jours
3. Comprendre les signaux générés
4. Faire du backtesting sur données historiques
5. Optimiser les paramètres

### Semaine 3 : Mode Testnet
1. Créer un compte Bybit
2. Configurer le testnet
3. Laisser tourner pendant 1 semaine
4. Analyser les performances
5. Ajuster si nécessaire

### Semaine 4+ : Décision Live
1. Évaluer les résultats du testnet
2. Si profitable et confiant → passer en live avec PETIT capital
3. Sinon → continuer en testnet et optimiser

---

## ❓ FAQ Rapide

**Q : Puis-je commencer sans clés API ?**
A : Oui ! Le mode `public` fonctionne sans aucune clé API.

**Q : Quel exchange choisir ?**
A : Bybit est recommandé (testnet disponible, interface simple, bon support CCXT).

**Q : Combien de capital pour commencer en live ?**
A : 100-500€ maximum pour débuter. Ne risquez QUE ce que vous pouvez perdre.

**Q : Le bot est-il rentable ?**
A : Les performances passées ne garantissent pas les résultats futurs. Testez toujours d'abord.

**Q : Puis-je trader 24/7 ?**
A : Oui, mais surveillez quotidiennement les premières semaines.

**Q : Que faire si je perds de l'argent ?**
A : Arrêtez le bot, analysez les logs, ajustez la configuration, retestez en paper trading.

---

## 🆘 Support

**Problème de configuration ?**
1. Vérifiez que toutes les dépendances sont installées
2. Vérifiez le fichier .env
3. Lisez les logs dans `logs/`
4. Consultez docs/EXCHANGE_SETUP.md et docs/SECURITY.md

**Le bot ne démarre pas ?**
1. Vérifiez les logs
2. Testez avec `python scripts/test_connection.py`
3. Vérifiez que Redis et TimescaleDB sont accessibles

**Données de marché non disponibles ?**
1. En mode public, c'est normal si CoinGecko/CCXT ont des limites
2. Essayez avec un autre exchange (dans .env)
3. Vérifiez votre connexion Internet

---

## ⚖️ Disclaimer

**CE LOGICIEL EST FOURNI "EN L'ÉTAT" SANS GARANTIE D'AUCUNE SORTE.**

- Le trading de crypto-monnaies comporte des risques élevés
- Vous pouvez perdre tout votre capital
- Ne tradez que ce que vous pouvez vous permettre de perdre
- Testez toujours en paper/testnet avant le live
- Les performances passées ne garantissent pas les résultats futurs
- Respectez les réglementations de votre juridiction
- Sécurisez vos clés API (permissions limitées, IP whitelist)

---

**Bon trading ! 📈**

*Remember: The best trade is the one you don't take when conditions aren't right.*

