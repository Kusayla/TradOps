# Contributing to AI Crypto Trading Bot

Merci de votre int?r?t pour contribuer au projet ! ??

## Comment contribuer

### 1. Fork & Clone

```bash
git clone https://github.com/your-username/trading-bot.git
cd trading-bot
```

### 2. Cr?er une branche

```bash
git checkout -b feature/ma-nouvelle-fonctionnalite
```

### 3. Setup de d?veloppement

```bash
./scripts/setup.sh
source venv/bin/activate
```

### 4. D?veloppement

- Suivez le style de code existant (PEP 8)
- Ajoutez des tests pour vos nouvelles fonctionnalit?s
- Documentez votre code avec des docstrings
- Utilisez type hints

### 5. Tests

```bash
# Tests unitaires
pytest tests/

# Tests de connexion
python scripts/test_connection.py

# Backtesting
python scripts/backtest.py
```

### 6. Commit

Utilisez des messages de commit clairs :

```bash
git add .
git commit -m "feat: ajoute d?tection de patterns chart"
```

Format des messages :
- `feat:` nouvelle fonctionnalit?
- `fix:` correction de bug
- `docs:` documentation
- `style:` formatage
- `refactor:` refactoring
- `test:` ajout de tests
- `chore:` maintenance

### 7. Push & Pull Request

```bash
git push origin feature/ma-nouvelle-fonctionnalite
```

Cr?ez ensuite une Pull Request sur GitHub.

## Guidelines

### Code Style

- PEP 8 pour Python
- Maximum 100 caract?res par ligne
- Type hints pour les fonctions
- Docstrings pour les classes et fonctions publiques

### Tests

- Couverture minimum : 70%
- Tests unitaires pour la logique m?tier
- Tests d'int?gration pour les composants

### Documentation

- README pour les nouvelles fonctionnalit?s majeures
- Docstrings style Google
- Commentaires pour la logique complexe

### S?curit?

- Ne commitez JAMAIS de cl?s API
- Utilisez des variables d'environnement
- Passez en revue les d?pendances

## Id?es de contribution

### Nouvelles fonctionnalit?s
- [ ] Support d'autres exchanges (Kraken, KuCoin, etc.)
- [ ] Nouvelles strat?gies de trading
- [ ] Mod?les ML plus avanc?s (LSTM, Transformer)
- [ ] Support de trading de d?riv?s
- [ ] Optimisation automatique des hyperparam?tres
- [ ] Dashboard web interactif
- [ ] Support multi-timeframe

### Am?liorations
- [ ] Performance du backtesting
- [ ] Meilleure gestion des erreurs
- [ ] Plus de tests
- [ ] Documentation
- [ ] Logs plus d?taill?s
- [ ] M?triques suppl?mentaires

### Bugs
Consultez les [Issues](https://github.com/your-repo/issues) pour les bugs connus.

## Questions

Pour toute question, ouvrez une [Discussion](https://github.com/your-repo/discussions).

Merci ! ??
