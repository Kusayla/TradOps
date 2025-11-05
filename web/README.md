# Crypto Bot Dashboard 🤖📊

Dashboard web statique pour visualiser les résultats d'un bot de trading crypto en temps réel.

## ⚠️ Avertissement Important

**Ce dashboard est un outil éducatif et ludique uniquement.**

- ❌ **Ce n'est PAS un conseil financier**
- ❌ **Les performances passées ne préjugent pas des performances futures**
- ❌ **Le trading de crypto-monnaies comporte des risques significatifs de perte en capital**
- ❌ **Même une IA ne peut pas prédire le marché avec certitude**

Utilisez ce dashboard pour apprendre et comprendre les mécaniques du trading algorithmique, pas pour prendre des décisions d'investissement.

## 🚀 Démo Locale

### Prérequis

Aucun ! Le site est 100% statique (HTML + JavaScript).

### Lancement

1. Ouvrez simplement `index.html` dans votre navigateur
2. Ou utilisez un serveur local (recommandé) :

```bash
# Python 3
python3 -m http.server 8000

# Node.js
npx serve

# PHP
php -S localhost:8000
```

Puis visitez `http://localhost:8000`

## 📦 Déploiement sur GitHub Pages

### Étape 1 : Créer le Repository (si nouveau)

```bash
# Initialiser git si pas déjà fait
git init
git add .
git commit -m "Initial commit: Trading bot dashboard"

# Créer un repo sur GitHub puis :
git remote add origin https://github.com/VOTRE-USERNAME/TradOps.git
git branch -M main
git push -u origin main
```

### Étape 2 : Activer GitHub Pages

1. Allez sur **GitHub.com** → Votre repo **TradOps**
2. Cliquez sur **Settings** (⚙️)
3. Dans le menu latéral, cliquez sur **Pages**
4. Sous **Source**, sélectionnez :
   - Branch: `main`
   - Folder: `/web` (ou `/root` si le site est à la racine)
5. Cliquez sur **Save**
6. Attendez 2-3 minutes ⏱️

### Étape 3 : Accéder au Site

Votre dashboard sera disponible à :

```
https://VOTRE-USERNAME.github.io/TradOps/
```

(GitHub affichera l'URL exacte dans Settings → Pages)

## 🔄 Mise à Jour des Données

### Option 1 : Export Automatique (Recommandé)

Le script Python `scripts/export_dashboard_data.py` exporte automatiquement les données de trading vers `web/data/latest.json`.

```bash
# Exporter manuellement
python scripts/export_dashboard_data.py

# Ou intégrer dans votre bot (ajouter dans src/main.py)
from scripts.export_dashboard_data import DashboardExporter
exporter = DashboardExporter()
exporter.export()
```

### Option 2 : Export Manuel

1. Créez ou modifiez `web/data/latest.json` avec vos données
2. Commitez et pushez :

```bash
git add web/data/latest.json
git commit -m "Update dashboard data"
git push
```

3. Le site se met à jour automatiquement en 1-2 minutes ✅

## 📊 Schéma des Données

Le fichier `data/latest.json` doit suivre ce format :

```json
{
  "updated_at": "2025-11-05T12:00:00Z",
  "series": [
    {
      "ts": "2025-10-20T09:00:00Z",
      "equity": 10000
    },
    ...
  ],
  "trades": [
    {
      "enter_ts": "2025-10-21T10:15:00Z",
      "exit_ts": "2025-10-21T12:05:00Z",
      "symbol": "BTCUSDT",
      "side": "long",
      "size": 0.02,
      "entry": 65000.0,
      "exit": 65320.0,
      "pnl": 6.4,
      "tags": ["breakout", "trend"]
    },
    ...
  ]
}
```

### Champs Obligatoires

#### `series` (array)
- `ts` (string, ISO 8601) : Horodatage du point
- `equity` (number) : Valeur du compte en USD

#### `trades` (array)
- `enter_ts` (string, ISO 8601) : Heure d'entrée
- `exit_ts` (string, ISO 8601) : Heure de sortie
- `symbol` (string) : Paire tradée (ex: "BTCUSDT")
- `side` (string) : "long" ou "short"
- `size` (number) : Taille de la position
- `entry` (number) : Prix d'entrée
- `exit` (number) : Prix de sortie
- `pnl` (number) : Profit/Perte en USD
- `tags` (array of strings, optionnel) : Tags descriptifs

## ✨ Fonctionnalités

### 📱 Mobile-First
- Design responsive optimisé pour smartphone
- Safe-area pour iOS (notch compatible)
- Performance 60fps même sur mobile

### 🌗 Dark Mode
- Toggle clair/sombre
- Préférence sauvegardée localement
- Transition douce

### 📹 Mode TikTok
- Active le mode plein écran
- Cache les éléments non essentiels
- Agrandit les graphiques et textes
- Parfait pour filmer des vidéos courtes

### 📊 KPIs Calculés
- **Solde Final** : Valeur actuelle du compte
- **PnL Total** : Profit/Perte depuis le début
- **Winrate** : % de trades gagnants
- **Nombre de Trades** : Total de positions
- **Max Drawdown** : Pire baisse depuis le pic
- **Sharpe Ratio** : Rendement ajusté au risque (annualisé)

### 📈 Graphiques Interactifs
- Courbe d'équité (Chart.js)
- Graphique de drawdown
- Tooltips informatifs
- Responsive et fluide

### 🔍 Filtres de Trades
- Tous
- Long uniquement
- Short uniquement
- Gagnants uniquement
- Perdants uniquement

## 🛠️ Stack Technique

- **HTML5** : Structure sémantique
- **Tailwind CSS** (CDN) : Styling moderne
- **Chart.js** (CDN) : Graphiques interactifs
- **JavaScript Vanilla** : Pas de framework, performance maximale
- **Google Fonts** : Police Inter

## 📁 Structure des Fichiers

```
web/
├── index.html          # Page principale
├── 404.html            # Page d'erreur
├── README.md           # Ce fichier
├── data/
│   └── latest.json     # Données du bot
└── assets/
    └── favicon.svg     # Icône du site
```

## 🎨 Personnalisation

### Modifier les Couleurs

Éditez le fichier `index.html` et modifiez la config Tailwind :

```javascript
tailwind.config = {
    theme: {
        extend: {
            colors: {
                primary: '#votre-couleur'
            }
        }
    }
}
```

### Ajouter des Métriques

1. Ajoutez une card dans la section KPI
2. Calculez la métrique dans `computeMetrics()`
3. Affichez-la dans `renderKPIs()`

## 🐛 Dépannage

### Le site ne charge pas les données

- Vérifiez que `data/latest.json` existe et est valide (JSON validator)
- Ouvrez la console du navigateur (F12) pour voir les erreurs
- Si en local, utilisez un serveur HTTP (pas `file://`)

### Les graphiques ne s'affichent pas

- Vérifiez que Chart.js est chargé (connexion internet)
- Vérifiez que les données `series` contiennent au moins 2 points
- Vérifiez le format ISO 8601 des timestamps

### Le dark mode ne fonctionne pas

- Videz le cache du navigateur
- Vérifiez localStorage (F12 → Application → Local Storage)

## 📄 Licence

MIT License - Utilisez, modifiez et partagez librement.

## 🤝 Contribution

Contributions bienvenues ! Créez une issue ou une pull request sur GitHub.

## 📞 Support

Pour toute question ou problème :
- Ouvrez une issue sur GitHub
- Consultez la documentation du bot principal

---

**Rappel Final** : Ce dashboard affiche les résultats d'un bot de trading à des fins éducatives. 
Ne prenez jamais de décisions financières basées uniquement sur ces données. 
Faites vos propres recherches et consultez un conseiller financier qualifié.

**Trading crypto = Risque élevé de perte** ⚠️

