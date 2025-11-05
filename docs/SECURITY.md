# 🔒 Guide de Sécurité - TradOps

La sécurité est **CRUCIALE** quand vous tradez avec de l'argent réel. Ce guide couvre toutes les bonnes pratiques pour protéger vos fonds et vos données.

## 📋 Table des Matières

1. [Sécurité des API Keys](#sécurité-des-api-keys)
2. [Configuration de l'Exchange](#configuration-de-lexchange)
3. [Sécurité du Serveur](#sécurité-du-serveur)
4. [Gestion des Secrets](#gestion-des-secrets)
5. [Monitoring et Alertes](#monitoring-et-alertes)
6. [Checklist de Sécurité](#checklist-de-sécurité)
7. [Que Faire en Cas de Problème](#que-faire-en-cas-de-problème)

---

## 🔑 Sécurité des API Keys

### Permissions Minimales (Principe du Moindre Privilège)

**✅ TOUJOURS Activer:**
- Read / Query Funds
- Query Orders (Open/Closed)
- Create & Modify Orders / Trade

**❌ JAMAIS Activer:**
- **Withdraw** (retrait de fonds) - ⚠️ CRITIQUE ⚠️
- **Transfer** (transfert entre comptes)
- **Margin Trading** (si non nécessaire)
- **Futures Trading** (si non nécessaire)

### Exemples de Configuration par Exchange

**Bybit:**
```
✅ Contract - Read
✅ Contract - Order
✅ Spot - Read
✅ Spot - Trade
❌ Spot - Withdraw
❌ Wallet - Transfer
```

**OKX:**
```
✅ Read
✅ Trade
❌ Withdraw
❌ Transfer
```

**KuCoin:**
```
✅ General (Read)
✅ Spot Trading
❌ Withdraw
❌ Transfer
❌ Margin Trading
```

### IP Whitelist

**Hautement recommandé** pour empêcher l'utilisation de vos clés depuis d'autres IP.

1. Trouvez votre IP publique:
```bash
curl ifconfig.me
```

2. Ajoutez cette IP dans la configuration de l'API key sur votre exchange

3. Si vous utilisez un VPS/serveur cloud, utilisez l'IP du serveur

4. **Attention:** Si votre IP change (DHCP), vous devrez mettre à jour la whitelist

### Rotation des Clés

- 🔄 Changez vos API keys **tous les 3 mois** minimum
- 🔄 Changez immédiatement si vous suspectez une compromission
- 🔄 Créez de nouvelles clés si vous déplacez le bot sur un nouveau serveur

### Stockage Sécurisé

**❌ Ne JAMAIS faire:**
- Committer le fichier `.env` dans git
- Partager vos clés par email/Slack/Discord
- Stocker les clés en clair dans du code
- Réutiliser les mêmes clés pour plusieurs bots
- Laisser les clés dans votre historique bash

**✅ À faire:**
- Utiliser un fichier `.env` (ajouté au `.gitignore`)
- Sauvegarder les clés dans un gestionnaire de mots de passe (1Password, Bitwarden, etc.)
- Utiliser un service de secrets management (AWS Secrets Manager, HashiCorp Vault, etc.)
- Chiffrer les backups contenant des clés

---

## 🏦 Configuration de l'Exchange

### 2FA (Authentification à Deux Facteurs)

**OBLIGATOIRE** pour tous les comptes d'exchange.

**Options recommandées (par ordre de préférence):**
1. **Hardware Key** (YubiKey, etc.) - Le plus sécurisé
2. **Authenticator App** (Authy, Google Authenticator, etc.)
3. **SMS** - Moins sécurisé mais mieux que rien

**⚠️ Important:**
- Sauvegardez les codes de récupération 2FA dans un endroit sûr
- Utilisez une app 2FA qui backup automatiquement (Authy)
- Ne désactivez JAMAIS le 2FA

### Anti-Phishing Code

Beaucoup d'exchanges permettent de définir un code anti-phishing visible dans leurs emails.

- Définissez un code unique
- Vérifiez sa présence dans chaque email de l'exchange
- Méfiez-vous des emails sans ce code

### Withdrawal Whitelist

Si l'exchange le permet, créez une whitelist d'adresses de retrait.

- Ajoutez seulement vos adresses de wallet personnelles
- Activez le délai de confirmation (24-48h) pour nouveaux ajouts

---

## 🖥️ Sécurité du Serveur

### Si vous Exécutez sur un VPS/Cloud

**1. Firewall**
```bash
# Autoriser seulement SSH et les ports nécessaires
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 3000  # Grafana (si exposition nécessaire)
sudo ufw enable
```

**2. SSH Sécurisé**
```bash
# Désactiver login root
sudo sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Utiliser des clés SSH au lieu de mots de passe
# Générer une paire de clés:
ssh-keygen -t ed25519 -C "votre_email@example.com"

# Désactiver l'authentification par mot de passe
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd
```

**3. Mises à Jour Automatiques**
```bash
# Ubuntu/Debian
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

**4. Fail2Ban (Protection contre brute force)**
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

**5. Monitoring des Logs**
```bash
# Vérifier régulièrement les logs d'authentification
sudo tail -f /var/log/auth.log
```

### Si vous Exécutez en Local

**1. Antivirus/Antimalware**
- Utilisez un antivirus à jour
- Scannez régulièrement votre système

**2. Chiffrement du Disque**
- Activez BitLocker (Windows) ou FileVault (macOS)
- Chiffrez les partitions contenant des données sensibles

**3. Pare-feu Local**
- Activez le firewall de votre OS
- Bloquez les connexions entrantes non nécessaires

---

## 🗝️ Gestion des Secrets

### Fichier .env

**Structure recommandée:**
```bash
# .env
# Ce fichier ne doit JAMAIS être committé

# Lecture seule pour l'utilisateur propriétaire
chmod 600 .env
```

**Ajoutez au .gitignore:**
```
# .gitignore
.env
.env.local
.env.*.local
*.key
*.pem
secrets/
```

### Variables d'Environnement Système

Pour une sécurité accrue, utilisez des variables d'environnement système:

```bash
# Ajoutez à ~/.bashrc ou ~/.zshrc (pour l'utilisateur courant seulement)
export BYBIT_API_KEY="votre_clé"
export BYBIT_API_SECRET="votre_secret"
```

Puis relancez:
```bash
source ~/.bashrc
```

### Utilisation d'un Vault (Production)

Pour un environnement de production, considérez:

**HashiCorp Vault:**
```bash
# Installation
wget https://releases.hashicorp.com/vault/1.15.0/vault_1.15.0_linux_amd64.zip
unzip vault_1.15.0_linux_amd64.zip
sudo mv vault /usr/local/bin/

# Initialisation
vault server -dev
export VAULT_ADDR='http://127.0.0.1:8200'

# Stocker un secret
vault kv put secret/tradops/bybit api_key="xxx" api_secret="yyy"

# Lire un secret
vault kv get secret/tradops/bybit
```

---

## 📊 Monitoring et Alertes

### Alertes Critiques à Configurer

**1. Alertes Trading:**
- ✅ Trade exécuté (confirmation)
- ⚠️ Stop loss atteint
- ⚠️ Limite de perte quotidienne approchée (80%)
- 🚨 Circuit breaker activé
- 🚨 Drawdown maximum approché

**2. Alertes Système:**
- 🚨 Erreur d'API exchange (authentification échouée)
- 🚨 Connexion perdue avec l'exchange
- ⚠️ CPU/RAM élevé
- ⚠️ Espace disque faible

**3. Alertes Sécurité:**
- 🚨 Tentative de connexion SSH échouée (Fail2Ban)
- 🚨 Changement de configuration détecté
- 🚨 Activité inhabituelle sur l'exchange

### Configuration Telegram

```bash
# .env
TELEGRAM_BOT_TOKEN=votre_token
TELEGRAM_CHAT_ID=votre_chat_id

# Créer un bot:
# 1. Cherchez @BotFather sur Telegram
# 2. /newbot
# 3. Suivez les instructions
# 4. Copiez le token

# Obtenir votre chat ID:
# 1. Envoyez un message à votre bot
# 2. Visitez: https://api.telegram.org/bot<TOKEN>/getUpdates
# 3. Cherchez "chat":{"id":123456789}
```

### Configuration Slack

```bash
# .env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Créer un webhook:
# 1. Allez sur https://api.slack.com/apps
# 2. Create New App
# 3. Incoming Webhooks
# 4. Activate et Add New Webhook
# 5. Copiez l'URL
```

---

## ✅ Checklist de Sécurité

### Avant de Lancer en Production

- [ ] **Exchange Configuration**
  - [ ] 2FA activé
  - [ ] Anti-phishing code défini
  - [ ] Withdrawal whitelist configurée (si disponible)
  - [ ] API keys avec permissions minimales
  - [ ] IP whitelist activée sur API keys
  - [ ] Clés différentes pour testnet et production

- [ ] **Secrets Management**
  - [ ] Fichier .env non committé (vérifié avec `git status`)
  - [ ] .env ajouté au .gitignore
  - [ ] Permissions .env restrictives (`chmod 600 .env`)
  - [ ] Clés sauvegardées dans gestionnaire de mots de passe
  - [ ] Codes de récupération 2FA sauvegardés

- [ ] **Serveur (si VPS/Cloud)**
  - [ ] Firewall configuré
  - [ ] SSH sécurisé (clés seulement, pas de root)
  - [ ] Fail2Ban installé
  - [ ] Mises à jour automatiques activées
  - [ ] Logs régulièrement vérifiés

- [ ] **Application**
  - [ ] Limites de risque configurées et testées
  - [ ] Alertes Telegram/Slack fonctionnelles
  - [ ] Monitoring Prometheus/Grafana opérationnel
  - [ ] Logs configurés avec rotation
  - [ ] Backtests validés (Sharpe > 1.5)
  - [ ] Paper trading testé pendant 1+ semaine
  - [ ] Testnet testé pendant 1+ semaine

- [ ] **Capital et Risque**
  - [ ] Capital de départ = montant que vous pouvez perdre
  - [ ] MAX_POSITION_SIZE ≤ 0.10 (10%)
  - [ ] MAX_DAILY_LOSS ≤ 0.05 (5%)
  - [ ] MAX_DRAWDOWN ≤ 0.15 (15%)
  - [ ] Capital initial < 1000€ pour débuter

---

## 🚨 Que Faire en Cas de Problème

### Clés API Compromises

**Actions immédiates:**
1. ⚡ **Révocation des clés** sur l'exchange (priorité absolue)
2. 🔍 Vérifier l'historique des trades sur l'exchange
3. 🔍 Vérifier l'historique des retraits
4. 🔒 Changer le mot de passe de l'exchange
5. 🔒 Vérifier que 2FA est toujours actif
6. 📧 Contacter le support de l'exchange si activité suspecte
7. 🔑 Créer de nouvelles clés API avec IP whitelist stricte

**Enquête:**
1. Vérifier les logs du bot (`logs/trading_bot_*.log`)
2. Vérifier l'historique bash: `history | grep API`
3. Scanner votre système pour malwares
4. Vérifier les commits git récents
5. Vérifier les accès au serveur (si VPS)

### Pertes Importantes Inattendues

**Actions immédiates:**
1. ⚡ **Arrêter le bot** immédiatement
   ```bash
   docker-compose down
   # ou
   pkill -f "python src/main.py"
   ```
2. 📊 Analyser les logs
3. 📊 Vérifier la configuration (fichier .env)
4. 📊 Vérifier les métriques Grafana
5. 🔍 Analyser chaque trade dans l'historique

**Analyse:**
1. Était-ce un bug du bot ou une mauvaise stratégie?
2. Les limites de risque ont-elles fonctionné?
3. Y a-t-il eu des erreurs dans les logs?
4. Le slippage était-il anormalement élevé?

**Ne relancez le bot qu'après avoir:**
- Identifié la cause exacte
- Corrigé le problème
- Testé à nouveau en paper trading
- Réduit la taille des positions si nécessaire

### Serveur Compromis

**Actions immédiates:**
1. ⚡ Déconnecter le serveur du réseau
2. ⚡ Révoquer toutes les API keys
3. ⚡ Changer tous les mots de passe
4. 🔍 Analyser les logs système
5. 🔍 Identifier le vecteur d'attaque
6. 💾 Sauvegarder les logs pour analyse
7. 🔨 Réinstaller le serveur depuis une image propre
8. 🔒 Renforcer la sécurité avant de remettre en ligne

### Erreurs d'Authentification Répétées

**Possibles causes:**
- Clés API expirées ou révoquées
- IP whitelist ne contient pas votre IP actuelle
- Permissions insuffisantes
- Exchange en maintenance

**Actions:**
1. Vérifier que les clés sont correctes dans `.env`
2. Vérifier votre IP: `curl ifconfig.me`
3. Comparer avec la whitelist sur l'exchange
4. Vérifier les permissions des clés
5. Vérifier le status de l'exchange: https://status.[exchange].com

---

## 📚 Ressources Supplémentaires

### Documentation Sécurité des Exchanges

- **Bybit:** https://www.bybit.com/en-US/help-center/bybitHC_Category?id=360002111755&language=en_US
- **OKX:** https://www.okx.com/support/hc/en-us/articles/360000919211
- **KuCoin:** https://www.kucoin.com/support/360015102174
- **Kraken:** https://support.kraken.com/hc/en-us/articles/360000920166

### Outils de Sécurité

- **Have I Been Pwned:** https://haveibeenpwned.com/ - Vérifiez si vos emails/mots de passe ont fuité
- **2FA Apps:** Authy, Google Authenticator, Microsoft Authenticator
- **Password Managers:** Bitwarden, 1Password, LastPass
- **Secrets Management:** HashiCorp Vault, AWS Secrets Manager

### Best Practices Générales

- **OWASP Cheat Sheets:** https://cheatsheetseries.owasp.org/
- **CIS Benchmarks:** https://www.cisecurity.org/cis-benchmarks/

---

## ⚖️ Responsabilités

**CE LOGICIEL EST FOURNI "EN L'ÉTAT" SANS GARANTIE.**

- Vous êtes seul responsable de la sécurité de vos fonds
- Tradez uniquement avec un capital que vous pouvez perdre
- Testez toujours en environnement sûr avant la production
- Restez informé des risques du trading de crypto-monnaies
- Respectez les réglementations de votre juridiction

---

**🔒 La sécurité est un processus continu, pas une destination.**

Restez vigilant, gardez vos systèmes à jour, et ne prenez jamais la sécurité à la légère quand de l'argent réel est en jeu.

