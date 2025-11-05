# 🚀 COMMENCEZ ICI - TradOps

**Votre bot de trading IA est prêt à l'emploi !** 🎉

## ⚡ Démarrage Ultra-Rapide (30 secondes)

```bash
cd ~/TradOps

# Lancer le bot IA
./run.sh ai
```

**C'est tout !** Le bot va :
- 📊 Analyser 10 cryptos en temps réel
- 🧠 Générer des signaux IA
- 💡 Recommander des achats/ventes
- 💰 Simuler des trades (mode paper, aucun risque)

**Pour arrêter :** `Ctrl+C`

---

## 📚 Autres Commandes

```bash
# Tester les connexions
./run.sh test

# Faire un backtest sur 90 jours
./run.sh backtest

# Mettre à jour les données
./run.sh update
```

---

## 🎯 Ce Que Vous Avez

### ✅ Installé et Configuré
- Python 3.10 + environnement virtuel
- PyTorch, Transformers (IA/ML)
- CCXT (connexion exchanges)
- 10 cryptos EUR (BTC, ETH, SOL, XRP, ADA, DOT, AVAX, ATOM, LINK, MATIC)
- 90 jours de données historiques
- Mode PUBLIC (gratuit, sans API keys)

### ✅ Fonctionnalités IA
- Signaux combinés (technique + sentiment + social + marché)
- Décisions intelligentes basées sur plusieurs facteurs
- Adaptation au contexte de marché
- Calcul automatique de taille de position

### ✅ Sécurité
- Mode paper trading (aucun argent réel)
- Limites de risque configurées
- Données publiques gratuites
- Aucune clé API sensible requise

---

## 🧠 Activer les Vraies News (Optionnel - 15 min)

Pour utiliser **FinBERT sur vraies actualités crypto** :

### 1. Obtenir les Clés API (Gratuit)

**CryptoPanic:**
- https://cryptopanic.com/developers/api/
- Gratuit, créez un compte

**NewsAPI:**
- https://newsapi.org/
- Gratuit, 100 requêtes/jour

### 2. Ajouter dans .env

```bash
nano .env
```

Ajoutez :
```bash
CRYPTOPANIC_API_KEY=votre_clé_ici
NEWSAPI_KEY=votre_clé_ici
```

### 3. Installer FinBERT

```bash
cd ~/TradOps
source venv/bin/activate
pip install keybert sentence-transformers
```

### 4. Relancer
```bash
./run.sh ai
```

Le bot analysera maintenant **vraies news crypto** avec FinBERT ! 🤖

---

## 📊 Passer en Mode Live (⚠️ Plus Tard)

**IMPORTANT : Ne faites ceci qu'après 2-3 semaines de tests !**

### Prérequis
- ✅ Bot testé en mode public > 2 semaines
- ✅ Backtest avec Sharpe > 1.5
- ✅ Comprendre les risques
- ✅ Capital que vous pouvez perdre (100-200€ max)

### Étapes

1. **Créer compte Kraken**
   - https://www.kraken.com/fr-fr/
   - Compléter KYC
   - Activer 2FA

2. **Créer clés API**
   - Settings → API
   - Permissions : Query + Trade (JAMAIS Withdraw)
   - IP Whitelist recommandée

3. **Modifier .env**
   ```bash
   TRADING_MODE=live
   KRAKEN_API_KEY=votre_clé
   KRAKEN_API_SECRET=votre_secret
   INITIAL_CAPITAL=200
   ```

4. **Tester puis lancer**
   ```bash
   ./run.sh test
   ./run.sh ai
   ```

---

## 📖 Documentation Complète

| Fichier | Description |
|---------|-------------|
| **STATUS.md** | État actuel du système ✅ |
| **QUICKSTART_AI.md** | Guide IA détaillé 🤖 |
| **GETTING_STARTED.md** | Guide démarrage complet 📚 |
| **docs/EXCHANGE_SETUP.md** | Configuration Kraken 🏦 |
| **docs/SECURITY.md** | Sécurité (CRITIQUE) 🔒 |
| **README.md** | Documentation générale 📋 |

---

## ⚠️ Rappels Importants

✅ **Mode PUBLIC = 100% sûr**
- Aucun argent réel
- Données gratuites
- Testez autant que vous voulez

❌ **Mode LIVE = Argent réel**
- Testez d'abord en public
- Commencez PETIT (100-200€)
- Surveillez quotidiennement
- Lisez docs/SECURITY.md

---

## 🆘 Besoin d'Aide ?

**Le bot ne démarre pas ?**
```bash
./run.sh test  # Diagnostique les problèmes
```

**Erreur "module not found" ?**
```bash
cd ~/TradOps
source venv/bin/activate
pip install [module_name]
```

**Besoin de réinstaller ?**
```bash
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_minimal.txt
pip install torch transformers scikit-learn
```

---

## 🎊 Vous Êtes Prêt !

**Pour commencer :**
```bash
./run.sh ai
```

**Et observez la magie de l'IA ! 🤖✨**

---

*Questions ? Consultez la documentation ou testez différentes commandes !*

