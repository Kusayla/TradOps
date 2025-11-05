# ?? AI-Powered Automated Crypto Trading Bot

Un bot de trading crypto enti?rement automatis?, pilot? par l'IA, qui capte des signaux depuis X (Twitter), les news, et les donn?es de march? pour prendre des d?cisions de trading intelligentes.

## ?? NOUVEAU : Support Multi-Exchange & Modes Hybrides

**Vous n'avez pas besoin de clés API pour commencer !**

TradOps supporte maintenant 3 modes de fonctionnement :

1. **Mode Public** (gratuit, sans clés API)
   - Données de marché gratuites (CoinGecko + CCXT public)
   - Paper trading complet
   - Backtesting sur données historiques
   - **Parfait pour débuter et tester**

2. **Mode Testnet** (testnet exchange)
   - Trading simulé sur testnet Bybit/OKX
   - Argent fictif, risque zéro
   - Test en conditions réelles

3. **Mode Live** (trading réel)
   - Trading avec argent réel
   - Support : Bybit, OKX, KuCoin, Kraken, Binance, Coinbase

**Exchanges supportés :**
- **Bybit** ⭐ RECOMMANDÉ (testnet disponible)
- **OKX** (testnet disponible)
- **KuCoin**
- **Kraken**
- Binance (legacy)
- Coinbase (legacy)

👉 **Voir [docs/EXCHANGE_SETUP.md](docs/EXCHANGE_SETUP.md) pour choisir et configurer votre exchange**
👉 **Voir [docs/SECURITY.md](docs/SECURITY.md) pour les bonnes pratiques de sécurité**

## ?? Fonctionnalit?s

### ?? Donn?es & Ingestion
- **Donn?es march? temps r?el** : Multi-exchange via CCXT
- **Données publiques gratuites** : CoinGecko, CCXT public (sans API keys)
- **News & Sentiment** : CryptoPanic, NewsAPI, LunarCrush
- **Streaming** : Redpanda/Kafka pour le traitement temps r?el
- **Stockage** : TimescaleDB (time-series) + Redis (cache)

### ?? IA & NLP
- **Analyse de sentiment** : FinBERT pour les news crypto/finance
- **Extraction de mots-cl?s** : KeyBERT
- **Signaux techniques** : RSI, MACD, Bollinger Bands, ATR, etc.
- **G?n?ration de signaux** : Combinaison technique + sentiment

### ?? Strat?gie & Risk Management
- **Position sizing** : Bas? sur l'ATR et la volatilit?
- **Stop Loss / Take Profit** : Automatique avec trailing stop
- **Circuit breakers** : Protection contre les pertes excessives
- **Max drawdown** : Surveillance continue
- **Limits de risque** : Par trade et quotidiennes

### ?? Backtesting
- **Vectorbt** : Backtesting vectoris? ultra-rapide
- **Walk-forward analysis** : Validation robuste
- **M?triques** : Sharpe, Sortino, Drawdown, Win Rate, etc.
- **Optimisation** : Grid search pour les param?tres

### ?? Monitoring & Alerting
- **Prometheus + Grafana** : Dashboards temps r?el
- **MLflow** : Tracking des exp?riences ML
- **Alerts** : Slack + Telegram
- **Logs** : Structured logging avec Loguru

## ??? Architecture

```
[X / News / Flux march?] ? [Ingestion temps r?el] ? [Stockage + Feature Store]
                                     ?
                              [Pipeline ML/NLP]
                                     ?
                          [Moteur de strat?gie & Risk]
                                     ?
                          [Ex?cution ordres (DMA)]
                                     ?
                   [Backtesting]?[Monitoring]?[Alerting]
```

## ?? Quick Start

### 1. Installation

```bash
# Clone le repo
git clone <repo-url>
cd workspace

# Rendre les scripts ex?cutables
chmod +x scripts/*.sh

# Setup (cr?e venv, installe d?pendances)
./scripts/setup.sh
```

### 2. Configuration

Créez votre fichier `.env` à partir du template :

```bash
cp env.template .env
```

Éditez `.env` selon votre mode :

#### Mode Public (recommandé pour débuter - PAS BESOIN DE CLÉS API)
```bash
# Mode de trading
TRADING_MODE=public

# Exchange (peu importe en mode public)
DEFAULT_EXCHANGE=bybit

# Trading
WHITELISTED_ASSETS=BTC/USDT,ETH/USDT,SOL/USDT
INITIAL_CAPITAL=10000

# C'est tout ! Pas besoin de clés API pour commencer
```

#### Mode Testnet (après avoir testé en public)
```bash
# Mode de trading
TRADING_MODE=testnet

# Choisir votre exchange
DEFAULT_EXCHANGE=bybit  # ou okx

# Clés API Bybit Testnet
BYBIT_API_KEY=your_testnet_key
BYBIT_API_SECRET=your_testnet_secret
BYBIT_TESTNET=true

# Trading
WHITELISTED_ASSETS=BTC/USDT,ETH/USDT,SOL/USDT
```

#### Mode Live (trading réel - ⚠️ ATTENTION)
```bash
# Mode de trading
TRADING_MODE=live

# Exchange
DEFAULT_EXCHANGE=bybit  # bybit, okx, kucoin, kraken

# Clés API (avec permissions limitées - NO WITHDRAW!)
BYBIT_API_KEY=your_live_key
BYBIT_API_SECRET=your_live_secret
BYBIT_TESTNET=false

# Risk Management (IMPORTANT!)
MAX_POSITION_SIZE=0.05  # 5% max par position (soyez conservateur!)
MAX_DAILY_LOSS=0.02     # 2% max loss quotidien
MAX_DRAWDOWN=0.10       # 10% max drawdown
INITIAL_CAPITAL=500     # Votre capital réel

# Alertes (RECOMMANDÉ)
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
```

👉 **Voir env.template pour toutes les options disponibles**
👉 **Voir docs/EXCHANGE_SETUP.md pour obtenir vos clés API**
👉 **Voir docs/SECURITY.md pour les bonnes pratiques**

### 3. Tester les connexions

```bash
# Activer l'environnement
source venv/bin/activate

# Tester toutes les connexions
python scripts/test_connection.py
```

### 3bis. Télécharger des Données Historiques (pour backtesting)

**Optionnel mais recommandé** pour faire du backtesting sur données locales :

```bash
# Télécharger 90 jours de données historiques (gratuit, pas de clés API requis)
python scripts/download_historical_data.py \
    --symbols BTC/USDT,ETH/USDT,SOL/USDT \
    --timeframes 1h,4h,1d \
    --days 90 \
    --exchange binance

# Mettre à jour les données existantes
python scripts/download_historical_data.py --update
```

Les données seront sauvegardées dans `data/historical/` et utilisables pour le backtesting.

### 4. Lancer le bot

#### Option A : Docker Compose (Recommand?)

```bash
# D?marrer tous les services
./scripts/start.sh

# Voir les logs
docker-compose logs -f trading_bot

# Arr?ter
./scripts/stop.sh
```

Services disponibles :
- **Grafana** : http://localhost:3000 (admin/admin)
- **Prometheus** : http://localhost:9090
- **MLflow** : http://localhost:5000
- **Redpanda Console** : http://localhost:19644

#### Option B : Ex?cution locale

```bash
source venv/bin/activate
python src/main.py
```

### 5. Backtesting

Avant de trader en live, testez votre strat?gie :

```bash
python scripts/backtest.py
```

## ?? Structure du Projet

```
workspace/
??? src/
?   ??? config/              # Configuration
?   ??? data_ingestion/      # Ingestion donn?es (march?, news, social)
?   ??? storage/             # Stockage (TimescaleDB, Redis, Feature Store)
?   ??? ml/                  # ML & NLP (sentiment, signaux)
?   ??? strategy/            # Moteur de strat?gie & risk management
?   ??? execution/           # Ex?cution des ordres
?   ??? backtesting/         # Backtesting engine
?   ??? monitoring/          # M?triques & alerting
?   ??? main.py             # Point d'entr?e principal
??? scripts/
?   ??? setup.sh            # Setup initial
?   ??? start.sh            # D?marrage
?   ??? stop.sh             # Arr?t
?   ??? backtest.py         # Backtesting
?   ??? test_connection.py  # Tests de connexion
??? config/
?   ??? prometheus.yml      # Config Prometheus
?   ??? grafana/            # Dashboards Grafana
??? docker-compose.yml      # Services Docker
??? Dockerfile
??? requirements.txt
??? .env                    # Configuration (? cr?er)
```

## ?? Stack Technique

- **Langage** : Python 3.11+
- **Exchange** : CCXT (multi-exchanges)
- **Databases** : TimescaleDB, Redis
- **Streaming** : Redpanda (Kafka-compatible)
- **ML/NLP** : PyTorch, Transformers, FinBERT, spaCy
- **Technical Analysis** : pandas-ta, ta
- **Backtesting** : vectorbt
- **MLOps** : MLflow, Feast
- **Monitoring** : Prometheus, Grafana
- **Workflow** : Prefect
- **Containerization** : Docker, Docker Compose

## ?? Strat?gies Impl?ment?es

### 1. Technical Strategy
- RSI (oversold/overbought)
- MACD crossovers
- Moving average crossovers (SMA 20/50)
- Bollinger Bands
- ADX (trend strength)

### 2. Sentiment Strategy
- Analyse de sentiment des news
- Agr?gation des m?triques sociales
- D?tection de tendances sentiment

### 3. Combined Strategy (D?faut)
- 60% technique + 40% sentiment
- D?tection de breakouts
- D?tection de divergences

## ?? Gestion du Risque

Le bot impl?mente plusieurs couches de protection :

1. **Position Sizing** : Bas? sur ATR et force du signal
2. **Stop Loss** : Automatique (2x ATR par d?faut)
3. **Take Profit** : Risk/Reward ratio 2.5:1
4. **Max Position** : 10% du capital par d?faut
5. **Daily Loss Limit** : 5% par d?faut
6. **Max Drawdown** : 15% par d?faut
7. **Circuit Breaker** : Pause automatique si anomalie

## ?? Modes de Trading

### Paper Trading (Par d?faut)
Simulation compl?te sans risque r?el. Parfait pour tester et apprendre.

```bash
TRADING_MODE=paper
```

### Live Trading
?? **ATTENTION** : Trading avec de l'argent r?el !

```bash
TRADING_MODE=live
```

**Recommandations avant le live :**
1. ? Backtest sur 3+ mois de donn?es
2. ? Paper trading pendant 1-2 semaines
3. ? Sharpe ratio > 1.5 en backtest
4. ? Win rate > 50%
5. ? Commencer avec un petit capital
6. ? Utiliser le testnet des exchanges

## ?? M?triques & Monitoring

### Prometheus Metrics
- `trading_trades_total` : Nombre de trades
- `trading_pnl` : P&L par trade
- `trading_portfolio_value` : Valeur du portfolio
- `trading_drawdown` : Drawdown actuel
- `trading_signals_generated` : Signaux g?n?r?s
- `trading_execution_latency` : Latence d'ex?cution

### Grafana Dashboards
Cr?ez vos dashboards avec les m?triques Prometheus :
- Portfolio performance
- Trade history
- Risk metrics
- Signal quality
- System health

## ?? Alerting

Configurez Slack ou Telegram pour recevoir des alertes :

- ? Trades ex?cut?s
- ?? Take profit hit
- ?? Stop loss hit
- ?? Limites de risque atteintes
- ?? Circuit breaker activ?
- ?? Signaux forts d?tect?s
- ? Erreurs API

## ?? Tests

```bash
# Tests de connexion
python scripts/test_connection.py

# Backtesting
python scripts/backtest.py

# Tests unitaires (? venir)
pytest tests/
```

## ?? Documentation Compl?mentaire

- [CCXT Documentation](https://docs.ccxt.com/)
- [FinBERT Paper](https://arxiv.org/abs/1908.10063)
- [vectorbt Documentation](https://vectorbt.dev/)
- [TimescaleDB Docs](https://docs.timescale.com/)
- [Prometheus + Grafana](https://prometheus.io/docs/visualization/grafana/)

## ?? Disclaimer

**CE LOGICIEL EST FOURNI "EN L'?TAT" SANS GARANTIE D'AUCUNE SORTE.**

- ?? Le trading de crypto-monnaies comporte des risques ?lev?s
- ?? Ne tradez que ce que vous pouvez vous permettre de perdre
- ?? Testez toujours en paper trading d'abord
- ?? Les performances pass?es ne garantissent pas les r?sultats futurs
- ?? Respectez les r?glementations de votre juridiction
- ?? S?curisez vos cl?s API (read/write s?par?es, IP whitelist)

## ?? Contribution

Les contributions sont les bienvenues ! 

## ?? Licence

MIT License - Voir LICENSE file

## ?? Remerciements

Construit avec :
- [CCXT](https://github.com/ccxt/ccxt)
- [FinBERT](https://github.com/ProsusAI/finBERT)
- [vectorbt](https://github.com/polakowo/vectorbt)
- [Prometheus](https://prometheus.io/)
- [Grafana](https://grafana.com/)

---

**Happy Trading! ????**

*Remember: The best trade is the one you don't take when conditions aren't right.*
