# 📊 Dashboard en Mode LIVE - Argent Réel

## ✅ Changements Effectués

1. **Affichage KPIs corrigé** : Texte réduit (`text-xl` au lieu de `text-2xl`) + `break-words` pour éviter le débordement
2. **Connexion aux vraies données** : Le script d'export lit maintenant depuis Redis les données réelles du bot
3. **Path mis à jour** : Export vers `/docs/data/latest.json` (compatible GitHub Pages)

---

## 🚀 Utilisation avec Argent Réel

### Étape 1 : Configurer le Bot en Mode LIVE

Dans votre `.env`, assurez-vous d'avoir :

```env
# Mode de trading
TRADING_MODE=live  # ⚠️ ARGENT RÉEL !

# API Kraken (ou votre exchange)
KRAKEN_API_KEY=votre_clé_api
KRAKEN_API_SECRET=votre_clé_secrète

# Capital initial (pour référence)
INITIAL_CAPITAL=1000  # Votre capital de départ en USD

# Redis (pour stocker les données)
REDIS_HOST=localhost
REDIS_PORT=6379
```

---

### Étape 2 : Lancer le Bot

```bash
cd ~/TradOps
source venv/bin/activate

# Option A : Bot avec Twitter + LLM
./run.sh llm

# Option B : Bot autonome
./run.sh auto

# Option C : Bot simple
python src/main.py
```

**Le bot va maintenant** :
- Trader avec de l'argent réel ⚠️
- Sauvegarder les trades dans Redis
- Mettre à jour l'historique du solde

---

### Étape 3 : Exporter les Données vers le Dashboard

**Méthode A - Automatique (Recommandé)**

Ajoutez cette ligne dans votre `src/main.py`, à la fin de chaque cycle de trading :

```python
from scripts.export_dashboard_data import DashboardExporter

# ... votre code de trading ...

# À la fin du cycle
exporter = DashboardExporter()
exporter.export()
```

**Méthode B - Manuel**

Exportez manuellement quand vous voulez :

```bash
python scripts/export_dashboard_data.py
```

**Méthode C - Cron (Auto toutes les heures)**

```bash
crontab -e
```

Ajoutez :

```
0 * * * * cd /home/aylan/TradOps && source venv/bin/activate && python scripts/export_dashboard_data.py >> /tmp/dashboard-export.log 2>&1
```

---

### Étape 4 : Pousser vers GitHub Pages

Une fois les données exportées vers `docs/data/latest.json` :

```bash
cd ~/TradOps
git add docs/data/latest.json
git commit -m "Update dashboard with live trading data"
git push origin main
```

**Le dashboard se met à jour en 1-2 minutes !** ⚡

---

## 📊 Structure des Données

Le script `export_dashboard_data.py` récupère :

### 1. Série d'Équité (Balance dans le temps)

Depuis Redis : `tradops:balance_history` (sorted set)

Format :
```
timestamp (score) → balance (valeur)
```

### 2. Historique des Trades

Depuis Redis : `tradops:trades_history` (liste)

Chaque trade contient :
- `entry_time` : Heure d'entrée
- `exit_time` : Heure de sortie
- `symbol` : Paire tradée (ex: BTCUSDT)
- `side` : long ou short
- `size` : Taille de la position
- `entry_price` : Prix d'entrée
- `exit_price` : Prix de sortie
- `pnl` : Profit/Perte en USD
- `tags` : Tags optionnels

---

## 🔄 Workflow Complet

```
1. Bot trade en LIVE
       ↓
2. Données sauvegardées dans Redis
       ↓
3. Export vers docs/data/latest.json
       ↓
4. Commit + Push vers GitHub
       ↓
5. GitHub Pages se met à jour
       ↓
6. Dashboard live à : https://kusayla.github.io/TradOps/
```

---

## 📈 Surveillance Continue

### Option 1 : Script Automatique

Créez `scripts/auto_update_dashboard.sh` :

```bash
#!/bin/bash
cd /home/aylan/TradOps
source venv/bin/activate

# Exporter les données
python scripts/export_dashboard_data.py

# Si export réussi, push vers GitHub
if [ $? -eq 0 ]; then
    git add docs/data/latest.json
    git commit -m "Auto-update dashboard - $(date '+%Y-%m-%d %H:%M')"
    git push origin main
    echo "✅ Dashboard mis à jour"
else
    echo "❌ Erreur lors de l'export"
fi

