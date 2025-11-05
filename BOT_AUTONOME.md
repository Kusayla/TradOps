# 🤖 BOT DE TRADING AUTONOME - Guide Complet

## 🎯 Concept

Votre bot est maintenant **VRAIMENT autonome**. Il ne trade pas juste une liste fixe de cryptos que vous lui donnez. Il :

### ✅ Ce Que Le Bot Fait SEUL

1. **Scanner le marché complet** (19+ cryptos EUR sur Kraken)
2. **Surveiller les news** crypto en temps réel
3. **Analyser le sentiment** avec FinBERT (IA)
4. **Détecter les opportunités** basées sur actualités
5. **Décider SEUL** quoi acheter/vendre
6. **Ajouter/retirer** des cryptos à son portfolio
7. **Choisir** entre FLIP (court terme) ou HOLD (long terme)
8. **Gérer** sa watchlist et blacklist dynamiquement

### ❌ Ce Que Vous N'Avez Plus à Faire

- ❌ Choisir les cryptos à trader
- ❌ Surveiller les news manuellement
- ❌ Décider quand acheter/vendre
- ❌ Gérer la liste d'actifs

## 🚀 Lancer le Bot Autonome

```bash
cd ~/TradOps
./run.sh auto
```

**Le bot va analyser le marché toutes les 5 minutes et prendre des décisions automatiquement !**

---

## 🧠 Les 5 Stratégies Autonomes

### 1. Event-Driven (Événements Importants)

**Trigger:**
- News TRÈS positive (score > 0.8)
- Événement majeur (partenariat, listing, upgrade)
- Prix pas encore monté (<5%)

**Action:**
- ACHAT FLIP de 5%
- Objectif: Profiter de la hausse post-annonce
- Sortie: Dès que prix monte de 5-10%

**Exemple:**
```
"Ethereum merge successfully completed"
→ FinBERT: +0.92
→ Prix ETH: +2% seulement
→ BOT: ACHAT 5% (500€) en FLIP
→ Objectif: Vendre à +7-10%
```

### 2. Trending Positive (Tendance Haussière)

**Trigger:**
- 3+ news positives en 24h
- Sentiment moyen > 0.6
- Buzz croissant

**Action:**
- ACHAT HOLD de 3%
- Garder moyen terme (semaines)
- Surveiller news continues

**Exemple:**
```
Atom: 5 news positives, partnerships, développement actif
→ Sentiment: +0.68
→ BOT: ACHAT 3% (300€) en HOLD
→ Garder tant que news positives continuent
```

### 3. Momentum Play (Surfer la Vague)

**Trigger:**
- Prix monte fort (+5 à +15%)
- Sentiment positif (> 0.4)
- Pas encore suracheté

**Action:**
- ACHAT FLIP de 2%
- Sortie rapide (+3-5%)

**Exemple:**
```
SOL: +8% aujourd'hui + news positives
→ Sentiment: +0.52
→ BOT: ACHAT 2% (200€) en FLIP
→ Sortie: Dès que +3%
```

### 4. Contrarian (Achat Opportuniste)

**Trigger:**
- Prix chute (-5% ou plus)
- MAIS news positives (> 0.6)
- "Buy the dip"

**Action:**
- ACHAT HOLD de 4%
- Garder jusqu'à récupération

**Exemple:**
```
DOT: -7% mais annonce upgrade + partenariat
→ FinBERT: +0.72
→ BOT: ACHAT 4% (400€) en HOLD
→ Opportunité: Prix bas, fondamentaux bons
```

### 5. Risk Exit (Protection)

**Trigger:**
- News TRÈS négatives (< -0.7)
- Événement de risque (hack, scam, problème)

**Action:**
- VENTE 100% immédiate
- Protection du capital

**Exemple:**
```
"Major security breach in XYZ protocol"
→ FinBERT: -0.91
→ BOT: VENTE 100% si position détenue
→ Raison: Protection, sortir MAINTENANT
```

---

## 🔍 Watchlist & Blacklist Dynamiques

### Watchlist (Ajout Automatique)

**Critères d'ajout:**
- >= 5 news en 24h
- Sentiment moyen > 0.4
- OU événement très positif

**Exemple:**
```
AVAX: 7 news en 24h, sentiment +0.65
→ BOT: ➕ Ajouté à watchlist
→ Sera surveillé prioritairement
→ Position possible si prix favorable
```

### Blacklist (Évitement Automatique)

**Critères d'ajout:**
- News très négatives
- Sentiment < -0.7
- Événements de risque

**Exemple:**
```
LUNA: "Terra collapse, billions lost"
→ FinBERT: -0.95
→ BOT: ⛔ Ajouté à blacklist
→ JAMAIS de position sur cette crypto
→ Vente immédiate si détenue
```

---

## 📊 Cryptos Scannées Automatiquement

Le bot surveille toutes ces cryptos EUR disponibles sur Kraken:

**Principales (toujours):**
- BTC, ETH, SOL, XRP, ADA
- DOT, AVAX, ATOM, LINK, MATIC

**Secondaires (si volume):**
- UNI, LTC, BCH, ALGO, FIL
- AAVE, GRT, SAND, MANA, CRV

**+ TOUTES les autres** disponibles sur Kraken !

---

## 💰 Gestion du Capital

### Allocation Automatique

**Capital total:** 10,000€ (simulé)

**Par opportunité:**
- Event-Driven: 5% (500€)
- Trending: 3% (300€)
- Momentum: 2% (200€)
- Contrarian: 4% (400€)

**Maximum total:** 15% (1,500€) en positions simultanées

**Le reste** (8,500€) reste disponible pour nouvelles opportunités

---

## 🎯 Exemples Réels de Décisions

### Scénario 1: Annonce Partenariat

```
📰 News: "Chainlink partners with Google Cloud"
🧠 FinBERT: +0.89 (très positif)
📊 Prix LINK: +3% (momentum commence)
💡 Volume: +85%

🤖 BOT DÉCIDE:
   Action: ACHAT
   Type: FLIP
   Position: 5% (500€)
   Raison: Event majeur, momentum début
   Objectif: +7-10% puis sortir
   
➕ LINK ajouté à watchlist
```

### Scénario 2: Hack Détecté

```
📰 News: "Major vulnerability found in Protocol XYZ"
🧠 FinBERT: -0.92 (très négatif)
📊 Prix: -12% (chute)
⚠️ Risque: Élevé

🤖 BOT DÉCIDE:
   Action: VENTE (si détenu)
   Type: EXIT
   Position: 100%
   Raison: Protection capital
   
⛔ XYZ ajouté à blacklist
```

### Scénario 3: Accumulation Silencieuse

```
📰 News: 6 news positives sur ATOM (pas majeures)
🧠 FinBERT moyen: +0.68
📊 Prix: Stable, +1%
📈 Tendance: Positive continue

🤖 BOT DÉCIDE:
   Action: ACHAT
   Type: HOLD
   Position: 3% (300€)
   Raison: Tendance positive soutenue
   
💎 HOLD moyen terme (semaines)
```

---

## ⚠️ Limites API Actuelles

Vous avez atteint la limite NewsAPI (100 requêtes/jour). **C'est normal** si vous testez beaucoup !

**Solutions:**

1. **Attendre demain** (limite se réinitialise à minuit)

2. **Utiliser seulement CryptoPanic** (qui fonctionne)
   ```bash
   # Dans .env, commentez temporairement NewsAPI
   # NEWSAPI_KEY=
   ```

3. **Upgrade NewsAPI** (payant mais plus de limites)
   - https://newsapi.org/pricing

4. **Le bot s'adapte !** Il utilisera les news disponibles

---

## 🚀 Lancer le Bot en Production

### Mode Public (Actuel - Recommandé)

```bash
# Lancer le bot autonome
./run.sh auto

# En background
nohup ./run.sh auto > bot_auto.log 2>&1 &

# Suivre les logs
tail -f bot_auto.log
```

### Mode Live (Plus tard - ⚠️ Argent Réel)

**IMPORTANT: Basé sur le backtest, utilisez UNIQUEMENT ATOM/EUR !**

```bash
# Dans .env
TRADING_MODE=live
DEFAULT_EXCHANGE=kraken
KRAKEN_API_KEY=votre_clé
KRAKEN_API_SECRET=votre_secret

# NE TRADER QUE ATOM (meilleure perf: +43%)
WHITELISTED_ASSETS=ATOM/EUR

# Capital MINIMAL
INITIAL_CAPITAL=100

# Limites STRICTES
MAX_POSITION_SIZE=0.05
MAX_DAILY_LOSS=0.015
```

---

## 📈 Résultats Backtest (pour référence)

**Seules cryptos VALIDÉES pour live:**
- ✅ **ATOM/EUR**: +43.30%, Sharpe 2.21 ⭐⭐⭐
- ⚠️ **ETH/EUR**: +13.60%, Sharpe 1.13 ⭐

**À ÉVITER absolument:**
- ❌ SOL/EUR: -34.26%
- ❌ LINK/EUR: -23.14%
- ❌ ADA/EUR: -13.80%
- ❌ BTC/EUR: -6.43%

**Configuration recommandée pour live:**
```bash
# Focus sur la meilleure
WHITELISTED_ASSETS=ATOM/EUR
```

OU

```bash
# Portfolio conservateur
WHITELISTED_ASSETS=ATOM/EUR,ETH/EUR
INITIAL_CAPITAL=200  # 100€ par crypto
```

---

## 💡 Comment Interpréter les Logs

```
🔍 Scan complet du marché...
✅ 19 cryptos actives détectées
```
→ Le bot a trouvé 19 cryptos tradables

```
📰 Analyse des news pour détecter opportunités...
✅ 12 news récupérées
```
→ 12 actualités trouvées pour ces cryptos

```
➕ Ajouté à la watchlist: SOL/EUR
   Raison: 5 news, sentiment 0.72
```
→ Le bot a décidé de surveiller SOL de près

```
🟢 SOL/EUR | Action: BUY FLIP | Prix: 162€ | Montant: 500€ | Conf: 85%
   💡 News très positive, prix pas encore monté
   📰 5 news (sentiment: 0.72)
```
→ Le bot recommande un ACHAT (mais ne l'exécute pas en mode public)

---

## 🎊 VOUS AVEZ MAINTENANT

✅ **Bot Autonome Complet**
- Scanne automatiquement le marché
- Analyse les news avec FinBERT
- Décide seul quoi acheter/vendre
- Gère dynamiquement son portfolio

✅ **5 Stratégies Intelligentes**
- Event-Driven (news majeures)
- Trending (tendances)
- Momentum (vagues)
- Contrarian (opportunités)
- Risk Exit (protection)

✅ **Gestion Dynamique**
- Watchlist auto
- Blacklist auto
- FLIP vs HOLD auto

✅ **100% Gratuit en Mode Public**
- Aucun risque
- Vrai test avant live
- Apprendre comment ça fonctionne

---

## 📚 Commandes

```bash
./run.sh auto          # Bot autonome (RECOMMANDÉ) ⭐⭐
./run.sh ai-news       # Bot IA avec news
./run.sh test          # Tests
./run.sh test-finbert  # Test FinBERT
./run.sh backtest      # Backtest
./run.sh status        # Statut système
```

---

## ⚠️ Avant de Passer en Live

### Checklist Obligatoire

- [ ] Bot testé en mode public pendant 2+ semaines
- [ ] Observé au moins 10 opportunités détectées
- [ ] Vérifié que décisions sont cohérentes
- [ ] Compte Kraken créé + KYC + 2FA
- [ ] Clés API Kraken (Query + Trade, JAMAIS Withdraw)
- [ ] Capital MAX 100-200€
- [ ] Focus sur ATOM/EUR uniquement (meilleure perf)
- [ ] Alertes Telegram configurées
- [ ] Lu docs/SECURITY.md

### Configuration Live Recommandée

```bash
# .env pour LIVE
TRADING_MODE=live
KRAKEN_API_KEY=votre_clé
KRAKEN_API_SECRET=votre_secret

# UNE crypto validée
WHITELISTED_ASSETS=ATOM/EUR

# Capital minimal
INITIAL_CAPITAL=100

# Limites strictes
MAX_POSITION_SIZE=0.05
MAX_DAILY_LOSS=0.015
MAX_DRAWDOWN=0.08
```

---

**🤖 Votre bot est maintenant VRAIMENT intelligent et autonome ! 🧠**

Il scanne, apprend, décide et agit comme un trader professionnel !

