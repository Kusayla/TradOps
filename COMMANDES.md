# 📋 AIDE-MÉMOIRE - Commandes TradOps

## 🚀 Commande Principale

```bash
cd ~/TradOps
./run.sh auto
```

**↑ Cette commande lance le bot autonome qui fait TOUT seul ! ↑**

---

## 🔧 Toutes les Commandes

### Bot de Trading

```bash
# Bot AUTONOME (scanne, décide, trade seul) ⭐⭐ RECOMMANDÉ
./run.sh auto

# Bot IA avec vraies news ⭐
./run.sh ai-news

# Bot IA basique (sentiment simulé)
./run.sh ai
```

### Tests & Diagnostics

```bash
# Tester les connexions
./run.sh test

# Tester FinBERT
./run.sh test-finbert

# Afficher statut du système
./run.sh status
```

### Backtesting & Données

```bash
# Faire un backtest
./run.sh backtest

# Mettre à jour les données historiques
./run.sh update
```

### En Background

```bash
# Lancer le bot en arrière-plan
nohup ./run.sh auto > bot.log 2>&1 &

# Voir les logs en temps réel
tail -f bot.log

# Arrêter le bot
pkill -f bot_autonome
```

---

## 📊 Fichiers Importants

```bash
# Voir la configuration
cat .env

# Modifier la configuration
nano .env

# Voir les données téléchargées
ls -lh data/historical/

# Voir les logs
ls -lh logs/
```

---

## 🎯 Résultats Backtest (Rappel)

**✅ VALIDÉ pour live:**
- ATOM/EUR: +43.30% (Sharpe 2.21)

**⚠️ OK avec prudence:**
- ETH/EUR: +13.60% (Sharpe 1.13)

**❌ À ÉVITER:**
- SOL, LINK, ADA, BTC, XRP, DOT (tous négatifs)

---

## 🔐 Passer en Mode Live (Plus Tard)

```bash
# 1. Modifier .env
nano .env

# 2. Changer ces lignes:
TRADING_MODE=live
KRAKEN_API_KEY=votre_clé
KRAKEN_API_SECRET=votre_secret
WHITELISTED_ASSETS=ATOM/EUR  # Uniquement ATOM!
INITIAL_CAPITAL=100  # MAX 100-200€

# 3. Tester
./run.sh test

# 4. Lancer
./run.sh auto
```

---

## 💡 Conseils

**Pour débuter:**
```bash
./run.sh auto  # Laissez tourner quelques heures
```

**Pour tester sans interruption:**
```bash
nohup ./run.sh auto > bot.log 2>&1 &
tail -f bot.log
```

**Si problème:**
```bash
./run.sh test  # Diagnostique
./show_status.sh  # Voir l'état
```

---

## 📚 Documentation

- **RESUME_FINAL.md** - Résumé complet
- **BOT_AUTONOME.md** - Guide bot autonome
- **START_HERE.md** - Démarrage rapide
- **docs/SECURITY.md** - Sécurité (À LIRE!)

---

**Commande à retenir:**

```bash
./run.sh auto
```

**Tout le reste se fait automatiquement ! 🤖**
