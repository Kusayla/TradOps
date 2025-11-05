# Guide de Configuration des Exchanges

Ce guide vous aidera à choisir et configurer votre exchange pour TradOps.

## 📊 Recommandations d'Exchanges

### 1. Bybit ⭐ **RECOMMANDÉ POUR DÉBUTER**

**Avantages:**
- ✅ Testnet complet et gratuit
- ✅ Interface intuitive et moderne
- ✅ Support CCXT excellent
- ✅ Frais compétitifs (0.1% maker, 0.1% taker)
- ✅ Pas de KYC pour testnet
- ✅ Documentation claire

**Inconvénients:**
- ❌ Moins de paires que Binance

**Comment créer un compte:**
1. Allez sur [Bybit.com](https://www.bybit.com/)
2. Créez un compte (email + mot de passe fort)
3. Activez 2FA (obligatoire)
4. Pour le testnet: [testnet.bybit.com](https://testnet.bybit.com/)

**Comment obtenir les API Keys:**
1. Connectez-vous à votre compte
2. Allez dans **Account & Security** → **API Management**
3. Cliquez sur **Create New Key**
4. Nommez votre clé (ex: "TradOps Bot")
5. **Permissions importantes:**
   - ✅ Read: Activer
   - ✅ Trade: Activer
   - ❌ Withdraw: **DÉSACTIVER** (sécurité)
   - ❌ Transfer: **DÉSACTIVER** (sécurité)
6. IP Whitelist (recommandé): Ajoutez votre IP
7. Sauvegardez la clé API et le secret **de manière sécurisée**

**Configuration dans .env:**
```bash
DEFAULT_EXCHANGE=bybit
BYBIT_API_KEY=votre_api_key
BYBIT_API_SECRET=votre_api_secret
BYBIT_TESTNET=true  # false pour live trading
TRADING_MODE=testnet  # ou live
```

---

### 2. OKX

**Avantages:**
- ✅ Testnet disponible
- ✅ Grande liquidité
- ✅ Nombreuses paires de trading
- ✅ Support CCXT excellent
- ✅ Interface professionnelle

**Inconvénients:**
- ⚠️ Interface peut être complexe pour débutants
- ⚠️ KYC requis pour testnet

**Comment créer un compte:**
1. Allez sur [OKX.com](https://www.okx.com/)
2. Créez un compte et complétez le KYC
3. Activez 2FA
4. Pour le testnet: [www.okx.com/demo-trading](https://www.okx.com/demo-trading)

**Comment obtenir les API Keys:**
1. Allez dans **Account** → **API**
2. Créez une nouvelle API key
3. **Permissions:**
   - ✅ Read
   - ✅ Trade
   - ❌ Withdraw
4. Notez la **Passphrase** (vous devrez la définir)
5. Sauvegardez API Key, Secret et Passphrase

**Configuration dans .env:**
```bash
DEFAULT_EXCHANGE=okx
OKX_API_KEY=votre_api_key
OKX_API_SECRET=votre_api_secret
OKX_PASSPHRASE=votre_passphrase
OKX_TESTNET=true
TRADING_MODE=testnet
```

---

### 3. KuCoin

**Avantages:**
- ✅ Pas de KYC pour petits montants
- ✅ Grande variété d'altcoins
- ✅ Frais raisonnables
- ✅ Bonne liquidité

**Inconvénients:**
- ❌ Pas de testnet officiel
- ⚠️ Support CCXT bon mais pas parfait

**Comment créer un compte:**
1. Allez sur [KuCoin.com](https://www.kucoin.com/)
2. Créez un compte
3. Activez 2FA

**Comment obtenir les API Keys:**
1. **Security Settings** → **API Management**
2. Créez une nouvelle API
3. **Permissions:**
   - ✅ General (Read)
   - ✅ Spot Trading
   - ❌ Withdraw
   - ❌ Transfer
4. Définissez une passphrase
5. IP Whitelist recommandée

**Configuration dans .env:**
```bash
DEFAULT_EXCHANGE=kucoin
KUCOIN_API_KEY=votre_api_key
KUCOIN_API_SECRET=votre_api_secret
KUCOIN_PASSPHRASE=votre_passphrase
TRADING_MODE=live  # pas de testnet
```

---

### 4. Kraken

**Avantages:**
- ✅ Très régulé et sécurisé
- ✅ Excellent pour l'Europe
- ✅ Bonne réputation
- ✅ Support client réactif

**Inconvénients:**
- ❌ Moins de paires que les concurrents
- ❌ Pas de testnet
- ⚠️ Frais plus élevés (0.26% maker, 0.16% taker)

**Comment créer un compte:**
1. Allez sur [Kraken.com](https://www.kraken.com/)
2. Créez un compte et complétez le KYC
3. Activez 2FA

**Comment obtenir les API Keys:**
1. **Settings** → **API**
2. **Generate New Key**
3. **Permissions:**
   - ✅ Query Funds
   - ✅ Query Open/Closed Orders
   - ✅ Create & Modify Orders
   - ❌ Withdraw Funds
4. Sauvegardez la clé

**Configuration dans .env:**
```bash
DEFAULT_EXCHANGE=kraken
KRAKEN_API_KEY=votre_api_key
KRAKEN_API_SECRET=votre_api_secret
TRADING_MODE=live
```

---

## 🚀 Workflow Recommandé

### Phase 1: Tests Sans Risque (1-2 semaines)

**Mode: `public`**
- Pas besoin d'API keys
- Données de marché gratuites
- Paper trading complet
- Backtesting sur données historiques

```bash
# Dans .env
TRADING_MODE=public
DEFAULT_EXCHANGE=bybit  # ou autre, peu importe en mode public
```

**Actions:**
1. Lancez le bot et observez
2. Testez le backtesting
3. Optimisez les paramètres
4. Vérifiez que Sharpe > 1.5

### Phase 2: Testnet (1 semaine)

**Mode: `testnet`**
- Créez un compte Bybit ou OKX
- Utilisez le testnet (argent fictif)
- Testez le trading réel sans risque

```bash
# Dans .env
TRADING_MODE=testnet
DEFAULT_EXCHANGE=bybit
BYBIT_TESTNET=true
BYBIT_API_KEY=votre_testnet_key
BYBIT_API_SECRET=votre_testnet_secret
```

**Actions:**
1. Créez vos API keys testnet
2. Configurez le bot
3. Lancez et surveillez pendant 1 semaine
4. Vérifiez que tout fonctionne

### Phase 3: Live Trading - Petit Capital (ongoing)

**Mode: `live`**
- Capital recommandé: 100-500€ pour commencer
- Surveillez quotidiennement
- Ajustez les paramètres si nécessaire

```bash
# Dans .env
TRADING_MODE=live
DEFAULT_EXCHANGE=bybit
BYBIT_TESTNET=false  # ATTENTION: MODE RÉEL
BYBIT_API_KEY=votre_live_key
BYBIT_API_SECRET=votre_live_secret

# Limites de risque strictes
MAX_POSITION_SIZE=0.05  # 5% max par position
MAX_DAILY_LOSS=0.02     # 2% max loss quotidien
INITIAL_CAPITAL=500     # Votre capital réel
```

**⚠️ CHECKLIST AVANT LIVE TRADING:**
- [ ] Backtest sur 3+ mois avec Sharpe > 1.5
- [ ] Paper trading profitable sur 1+ semaine
- [ ] Testnet profitable sur 1+ semaine
- [ ] API keys avec permissions limitées (NO WITHDRAW)
- [ ] IP Whitelist configurée
- [ ] 2FA activé sur l'exchange
- [ ] Alertes Telegram/Slack configurées
- [ ] Limites de risque définies
- [ ] Capital que vous pouvez perdre

---

## 🔒 Sécurité des API Keys

### Bonnes Pratiques

1. **Permissions minimales:**
   - ✅ Read/Query
   - ✅ Trade/Spot Trading
   - ❌ **JAMAIS** Withdraw
   - ❌ **JAMAIS** Transfer

2. **IP Whitelist:**
   - Ajoutez uniquement votre IP
   - Mettez à jour si votre IP change

3. **Stockage sécurisé:**
   - Ne commitez JAMAIS le fichier `.env`
   - Utilisez un gestionnaire de mots de passe
   - Sauvegardez les clés de manière sécurisée

4. **Surveillance:**
   - Vérifiez régulièrement l'activité de l'API
   - Configurez des alertes
   - Révoquez les clés non utilisées

5. **Séparation:**
   - Clés différentes pour testnet et live
   - Ne réutilisez pas les clés
   - Une clé par bot/application

### ⚠️ Que Faire en Cas de Problème

**Si vos clés sont compromises:**
1. Révocation immédiate sur l'exchange
2. Changez votre mot de passe
3. Vérifiez l'historique des trades
4. Créez de nouvelles clés

**En cas de perte importante:**
1. Arrêtez le bot immédiatement
2. Analysez les logs
3. Vérifiez la configuration
4. Ne relancez qu'après avoir identifié le problème

---

## 📞 Support

- **Bybit Support:** https://www.bybit.com/en-US/help-center/
- **OKX Support:** https://www.okx.com/support-center.html
- **KuCoin Support:** https://www.kucoin.com/support
- **Kraken Support:** https://support.kraken.com/

---

## 💡 Conseils

1. **Commencez petit:** Ne risquez que ce que vous pouvez perdre
2. **Testez d'abord:** Utilisez public → testnet → petit capital live
3. **Surveillez:** Vérifiez le bot quotidiennement au début
4. **Apprenez:** Analysez chaque trade, comprenez pourquoi
5. **Patience:** Le trading automatique n'est pas un get-rich-quick scheme
6. **Diversifiez:** Ne mettez pas tout sur un seul bot/stratégie

