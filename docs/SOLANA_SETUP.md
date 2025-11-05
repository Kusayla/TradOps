# 🪙 Guide Setup Solana pour Fast Trading

## Objectif

Configurer un wallet Solana pour faire du fast trading sur tokens Solana via Jupiter DEX.

---

## 🏦 Étape 1 : Créer un Wallet Solana

### Option A : Phantom (Recommandé, Facile)

1. **Installer Phantom** : https://phantom.app/
2. **Créer un nouveau wallet**
3. **Sauvegarder votre seed phrase** (12 mots) ⚠️ IMPORTANT
4. **Copier votre adresse** : Ex: `7xKX...abc`

### Option B : Solflare (Alternative)

1. **Installer Solflare** : https://solflare.com/
2. **Créer wallet**
3. **Sauvegarder seed phrase**

### Option C : CLI (Avancé)

```bash
# Installer Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Créer wallet
solana-keygen new --outfile ~/solana-wallet.json

# Voir votre adresse
solana-keygen pubkey ~/solana-wallet.json
```

---

## 💶 Étape 2 : Convertir EUR → SOL

### Sur Kraken (Vous avez déjà un compte)

1. **Vendre vos EUR contre SOL** :
   - Trade → Paire **SOL/EUR**
   - Type: **Market**
   - Vendez: **14€**
   - Recevez: **~0.093 SOL** (selon prix)

2. **Retirer vers votre wallet Solana** :
   - Funding → Withdraw
   - Crypto: **SOL**
   - Adresse: **Votre adresse Phantom**
   - Montant: **~0.09 SOL** (gardez 0.003 SOL sur Kraken pour fees)
   - Réseau: **Solana**
   - Confirmez

3. **Délai** : 5-15 minutes

---

## 🔑 Étape 3 : Exporter la Clé Privée

### Avec Phantom

1. **Ouvrir Phantom**
2. **Menu** (☰) → **Settings**
3. **Security & Privacy**
4. **Export Private Key**
5. **Entrez mot de passe**
6. **Copiez la clé** (commence par [1,2,3...] ou base58)

### Avec Solflare

1. **Settings** → **Backup**
2. **Export Private Key**
3. **Copiez**

### Avec CLI

```bash
cat ~/solana-wallet.json
# Copiez le contenu complet
```

---

## ⚙️ Étape 4 : Configurer le Bot

### Ajoutez dans `.env` :

```env
# Solana Wallet
SOLANA_PRIVATE_KEY=[1,2,3,...]  # Votre clé privée
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# OU si clé base58
SOLANA_PRIVATE_KEY_BASE58=votre_clé_base58

# DEX Configuration
DEX_PLATFORM=jupiter
SLIPPAGE_TOLERANCE=1.0  # 1% max

# Fast Trading
FAST_MODE=true
CHECK_INTERVAL_IN_POSITION=30    # 30 sec surveillance
CHECK_INTERVAL_SCANNING=180      # 3 min scan
TAKE_PROFIT_PERCENT=5.0          # +5% = sortie
STOP_LOSS_PERCENT=3.0            # -3% = stop
MAX_HOLD_TIME_SECONDS=3600       # 1h max
```

---

## 🚀 Étape 5 : Lancer le Bot

```bash
cd ~/TradOps
source venv/bin/activate
./run.sh solana
```

Ou :

```bash
python scripts/bot_solana_flip.py
```

---

## 📊 Comment Ça Marche

### Phase 1 : Scan (Sans Position)

```
🔍 Scan DexScreener (API gratuite)
   → Top 20 tokens volatils Solana
   → Filtre: Volume > $100k, Liquidité > $50k, Variation > 10%
   
🧠 ChatGPT analyse top 5
   → Score chaque token
   → Décide: ACHETER ou ATTENDRE
   
✅ Achat si confiance > 75%
   → Swap 85% SOL vers Token
   → Passage mode surveillance
```

### Phase 2 : Surveillance (Avec Position)

```
⏱️  Toutes les 30 secondes:
   → Récupère prix actuel
   → Calcule PnL
   → ChatGPT: SORTIR ou HOLD ?
   
🚨 Sortie automatique si:
   → PnL >= +5% (take profit)
   → PnL <= -3% (stop loss)
   → Temps > 1h (timeout)
   → ChatGPT signal sortie (confiance > 70%)
```

---

## 💰 Exemple de Flip

```
Capital: 0.1 SOL (~15€)

10:00 - SCAN
  → Trouve $BONK: +15% en 1h, volume $500k
  → ChatGPT: ACHETER (85% confiance)
  → Swap 0.085 SOL → 12M $BONK @ $0.00001

10:05 - SURVEILLANCE
  → Prix $BONK: $0.000010 → $0.0000105 (+5%)
  → ChatGPT: VENDRE (90% confiance, take profit)
  → Swap 12M $BONK → 0.0893 SOL
  → Profit: +0.0043 SOL (+5%)

10:06 - RETOUR SCAN
  → Nouveau capital: 0.1043 SOL
  → Recherche nouvelle opportunité...
```

**En 6 minutes : +5% !** 🚀

---

## ⚠️ Risques Spécifiques Solana

### Slippage
- DEX = 0.5-2% de slippage
- Tokens peu liquides = jusqu'à 5%
- Solution: Slippage limit à 1%

### Rugpulls
- Tokens non vérifiés = risque scam
- Vérifiez: Liquidity locked, Audit, Team doxxed
- Stick to tokens > $100k volume

### Fees Solana
- Transaction fee: ~$0.0002 (quasi gratuit)
- Gardez toujours 0.01 SOL pour fees

### Volatilité Extrême
- Tokens peuvent +50% ou -50% en minutes
- Stop loss -3% essentiel
- Ne jamais FOMO

---

## 💸 Coûts ChatGPT

### Sans Position (Scan)
- 20 appels/heure (1 scan/3min avec 5 tokens)
- ~480 appels/jour
- Coût: ~$0.15/jour = 4.50€/mois

### Avec Position (Surveillance)
- 120 appels/heure (1 check/30sec)
- ~2,880 appels/jour
- Coût: ~$0.86/jour = 26€/mois

### Optimisé (Mix)
- 50% temps en position (12h/jour)
- Coût moyen: ~15€/mois

**Si vous faites +20% sur 15€ (3€ profit), ça couvre largement !**

---

## 🎯 Résultats Attendus

### Conservateur
- 1 flip/jour à +3%
- 15€ → 15.45€/jour
- 1 semaine: +3% = 15.45€

### Optimiste
- 3 flips/jour à +5%
- Gains cumulés: +15%/semaine
- 1 semaine: 15€ → 17.25€

### Réaliste
- 2 flips/jour, 1 gagnant (+5%), 1 perdant (-2%)
- Net: +3%/jour
- 1 semaine: 15€ → 18€ (+20%)

**Vs BTC stable: 12€ → 12.03€ (+0.25%/jour)** 📈

---

## 🔐 Sécurité

### ✅ À FAIRE
- Sauvegarder seed phrase hors ligne
- Ne jamais partager clé privée
- Tester avec petit montant d'abord
- Vérifier tokens avant achat

### ❌ NE PAS FAIRE
- Trader tokens sans liquidité
- Ignorer stop loss
- FOMO sur pump & dump
- Mettre plus que vous pouvez perdre

---

## 📋 Checklist Avant de Lancer

- [ ] Wallet Solana créé
- [ ] Seed phrase sauvegardée
- [ ] 0.09-0.1 SOL dans le wallet
- [ ] Clé privée exportée
- [ ] `.env` configuré
- [ ] ChatGPT API key ajoutée
- [ ] Bot testé en simulation

---

## 🚀 Commandes

```bash
# Lancer le bot
./run.sh solana

# Surveiller
tail -f logs/solana_flip.log

# Arrêter
pkill -f bot_solana_flip
```

---

**Bon flip ! 🚀💰**

