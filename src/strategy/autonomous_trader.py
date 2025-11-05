"""
Autonomous Trading System
Le bot scanne le marché, détecte les opportunités basé sur les news,
et décide lui-même quoi acheter/vendre
"""
import asyncio
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from loguru import logger

from src.config import settings


class AutonomousTrader:
    """
    Trader autonome qui:
    - Scanne TOUTES les cryptos disponibles
    - Détecte les opportunités via news + IA
    - Ajoute/retire des cryptos dynamiquement
    - Décide entre flip (court terme) vs hold (long terme)
    - Gère son propre portfolio
    """
    
    def __init__(self, market_data, news_ingestion, sentiment_analyzer, ai_generator):
        self.market_data = market_data
        self.news_ingestion = news_ingestion
        self.sentiment_analyzer = sentiment_analyzer
        self.ai_generator = ai_generator
        
        # Portfolio dynamique
        self.active_positions = {}  # Positions actuellement détenues
        self.watchlist = set()  # Cryptos à surveiller
        self.blacklist = set()  # Cryptos à éviter
        
        # Cache des données
        self.news_cache = {}
        self.sentiment_scores = {}
        self.price_history = {}
        
        # Configuration
        self.capital = settings.trading.initial_capital
        self.available_capital = self.capital
        
        logger.info("🤖 Trader Autonome initialisé")
        logger.info(f"   Capital: {self.capital:,.0f}€")
    
    async def scan_market(self) -> List[Dict]:
        """
        Scanner TOUTES les cryptos disponibles sur l'exchange
        Retourne celles avec potentiel basé sur news + volume
        """
        try:
            logger.info("🔍 Scan complet du marché...")
            
            # Liste de toutes les cryptos principales disponibles en EUR sur Kraken
            all_cryptos = [
                'BTC/EUR', 'ETH/EUR', 'SOL/EUR', 'XRP/EUR', 'ADA/EUR',
                'DOT/EUR', 'AVAX/EUR', 'ATOM/EUR', 'LINK/EUR', 'MATIC/EUR',
                'UNI/EUR', 'LTC/EUR', 'BCH/EUR', 'ALGO/EUR', 'FIL/EUR',
                'AAVE/EUR', 'GRT/EUR', 'SAND/EUR', 'MANA/EUR', 'CRV/EUR'
            ]
            
            # Récupérer les tickers pour toutes
            tickers = await self.market_data.fetch_multiple_tickers(all_cryptos)
            
            opportunities = []
            
            for symbol, ticker in tickers.items():
                if not ticker:
                    continue
                
                # Critères de base : volume et liquidité
                volume = ticker.get('volume', 0)
                price = ticker.get('last', 0)
                
                if volume == 0 or price == 0:
                    continue
                
                # Ajouter aux opportunités potentielles
                opportunities.append({
                    'symbol': symbol,
                    'price': price,
                    'volume': volume,
                    'change_24h': ticker.get('percentage', 0),
                    'ticker': ticker
                })
            
            logger.info(f"✅ {len(opportunities)} cryptos actives détectées")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Erreur scan marché: {e}")
            return []
    
    async def analyze_news_opportunities(self, cryptos: List[str]) -> Dict:
        """
        Analyser les news pour toutes les cryptos
        Identifier les opportunités basées sur actualités
        """
        try:
            logger.info("📰 Analyse des news pour détecter opportunités...")
            
            # Récupérer les news pour toutes les cryptos
            all_news = await self.news_ingestion.fetch_all_news(cryptos)
            
            if not all_news:
                logger.warning("⚠️ Aucune news récupérée")
                return {}
            
            logger.info(f"✅ {len(all_news)} news récupérées")
            
            # Analyser avec FinBERT
            analyzed_news = self.sentiment_analyzer.analyze_news(all_news)
            
            # Organiser par crypto et détecter opportunités
            opportunities = {}
            
            for news in analyzed_news:
                title = news.get('title', '').upper()
                description = news.get('description', '').upper()
                text = title + ' ' + description
                
                sentiment = news.get('sentiment', {})
                score = sentiment.get('sentiment_score', 0)
                
                # Extraire mentions de cryptos
                for crypto in cryptos:
                    crypto_name = crypto.upper()
                    
                    if crypto_name in text:
                        if crypto not in opportunities:
                            opportunities[crypto] = {
                                'news': [],
                                'scores': [],
                                'positive_count': 0,
                                'negative_count': 0,
                                'total_count': 0
                            }
                        
                        opportunities[crypto]['news'].append(news)
                        opportunities[crypto]['scores'].append(score)
                        opportunities[crypto]['total_count'] += 1
                        
                        if score > 0.5:
                            opportunities[crypto]['positive_count'] += 1
                        elif score < -0.5:
                            opportunities[crypto]['negative_count'] += 1
            
            # Calculer scores moyens et tendances
            for crypto, data in opportunities.items():
                if data['scores']:
                    data['avg_sentiment'] = sum(data['scores']) / len(data['scores'])
                    data['max_sentiment'] = max(data['scores'])
                    data['min_sentiment'] = min(data['scores'])
                    
                    # Détection d'événements majeurs
                    if data['max_sentiment'] > 0.85:
                        data['event_type'] = 'very_positive'
                    elif data['min_sentiment'] < -0.85:
                        data['event_type'] = 'very_negative'
                    elif data['positive_count'] >= 3:
                        data['event_type'] = 'trending_positive'
                    elif data['negative_count'] >= 3:
                        data['event_type'] = 'trending_negative'
                    else:
                        data['event_type'] = 'neutral'
            
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse news: {e}")
            return {}
    
    def decide_action(self, crypto: str, news_data: Dict, ticker: Dict) -> Dict:
        """
        Décider de l'action pour une crypto
        Retourne: action type (buy/sell/hold/flip), taille position, raison
        """
        decision = {
            'symbol': crypto,
            'action': 'HOLD',
            'position_size': 0,
            'strategy': 'wait',
            'reason': '',
            'confidence': 0
        }
        
        if not news_data or not ticker:
            return decision
        
        sentiment = news_data.get('avg_sentiment', 0)
        event_type = news_data.get('event_type', 'neutral')
        news_count = news_data.get('total_count', 0)
        price_change = ticker.get('percentage', 0)
        
        # STRATÉGIE 1: Event-Driven (News très positives)
        if event_type == 'very_positive' and sentiment > 0.8:
            if price_change < 5:  # Pas encore suracheté
                decision['action'] = 'BUY'
                decision['position_size'] = 0.05  # 5% du capital
                decision['strategy'] = 'FLIP'  # Court terme
                decision['reason'] = f"News très positive (score {sentiment:.2f}), prix pas encore monté"
                decision['confidence'] = min(sentiment, 0.95)
                return decision
        
        # STRATÉGIE 2: Trending Positive (Plusieurs news positives)
        if event_type == 'trending_positive' and news_count >= 3:
            if sentiment > 0.6 and price_change < 10:
                decision['action'] = 'BUY'
                decision['position_size'] = 0.03  # 3% du capital
                decision['strategy'] = 'HOLD'  # Moyen terme
                decision['reason'] = f"{news_count} news positives, tendance haussière"
                decision['confidence'] = sentiment * 0.8
                return decision
        
        # STRATÉGIE 3: Momentum Play (Prix monte + sentiment positif)
        if price_change > 5 and sentiment > 0.4:
            if price_change < 15:  # Pas trop tard
                decision['action'] = 'BUY'
                decision['position_size'] = 0.02  # 2% du capital
                decision['strategy'] = 'FLIP'  # Flip rapide
                decision['reason'] = f"Momentum fort (+{price_change:.1f}%) + sentiment positif"
                decision['confidence'] = 0.7
                return decision
        
        # STRATÉGIE 4: Contrarian (Chute avec bonnes nouvelles)
        if price_change < -5 and sentiment > 0.6:
            decision['action'] = 'BUY'
            decision['position_size'] = 0.04  # 4% du capital
            decision['strategy'] = 'HOLD'  # Hold moyen terme
            decision['reason'] = f"Opportunité contrarian: prix bas + news positives"
            decision['confidence'] = sentiment * 0.9
            return decision
        
        # STRATÉGIE 5: Vente si news négatives
        if event_type in ['very_negative', 'trending_negative'] and sentiment < -0.6:
            decision['action'] = 'SELL'
            decision['position_size'] = 1.0  # Vendre 100% si détenu
            decision['strategy'] = 'EXIT'
            decision['reason'] = f"News négatives (score {sentiment:.2f}), sortir!"
            decision['confidence'] = abs(sentiment)
            return decision
        
        # Par défaut: HOLD
        decision['reason'] = "Pas d'opportunité claire"
        return decision
    
    async def manage_portfolio(self, opportunities: List[Dict], news_opportunities: Dict):
        """
        Gérer le portfolio de manière autonome
        Ajouter/retirer des positions selon les opportunités
        """
        logger.info("")
        logger.info("🎯 GESTION AUTONOME DU PORTFOLIO")
        logger.info("=" * 80)
        
        recommendations = []
        
        # Analyser chaque crypto
        for opp in opportunities:
            symbol = opp['symbol']
            crypto_base = symbol.split('/')[0]
            
            # Données news pour cette crypto
            news_data = news_opportunities.get(crypto_base, {})
            
            # Décider action
            decision = self.decide_action(symbol, news_data, opp['ticker'])
            
            if decision['action'] != 'HOLD' or decision['confidence'] > 0.5:
                recommendations.append({
                    'crypto': symbol,
                    'price': opp['price'],
                    'change_24h': opp['change_24h'],
                    'decision': decision,
                    'news_count': news_data.get('total_count', 0),
                    'sentiment': news_data.get('avg_sentiment', 0)
                })
        
        # Trier par confiance (meilleures opportunités d'abord)
        recommendations.sort(key=lambda x: x['decision']['confidence'], reverse=True)
        
        # Afficher recommandations
        if recommendations:
            logger.info(f"📋 {len(recommendations)} OPPORTUNITÉS DÉTECTÉES:")
            logger.info("-" * 80)
            
            for i, rec in enumerate(recommendations[:10], 1):  # Top 10
                crypto = rec['crypto']
                price = rec['price']
                change = rec['change_24h']
                dec = rec['decision']
                sentiment = rec['sentiment']
                news_count = rec['news_count']
                
                # Emoji selon action
                if dec['action'] == 'BUY':
                    emoji = "🟢"
                    log_func = logger.success
                elif dec['action'] == 'SELL':
                    emoji = "🔴"
                    log_func = logger.warning
                else:
                    emoji = "⚪"
                    log_func = logger.info
                
                # Calcul montant
                amount = self.available_capital * dec['position_size']
                
                log_func(
                    f"{i:2}. {emoji} {crypto:12} | "
                    f"Action: {dec['action']:4} {dec['strategy']:4} | "
                    f"Prix: {price:>10,.2f}€ | "
                    f"24h: {change:>6.2f}% | "
                    f"Montant: {amount:>6,.0f}€ | "
                    f"Conf: {dec['confidence']*100:>4.0f}%"
                )
                logger.info(f"       💡 {dec['reason']}")
                if news_count > 0:
                    logger.info(f"       📰 {news_count} news (sentiment: {sentiment:>5.2f})")
        else:
            logger.info("⚪ Aucune opportunité forte détectée")
            logger.info("   Le bot attend les bons moments pour agir")
        
        logger.info("")
        logger.info("=" * 80)
        
        return recommendations
    
    def should_add_to_watchlist(self, crypto: str, news_data: Dict) -> bool:
        """Décider si ajouter une crypto à la watchlist"""
        if not news_data:
            return False
        
        # Ajouter si:
        # - Beaucoup de news (>= 5)
        # - Sentiment positif (> 0.4)
        # - Ou event très positif
        
        event_type = news_data.get('event_type', 'neutral')
        sentiment = news_data.get('avg_sentiment', 0)
        news_count = news_data.get('total_count', 0)
        
        return (
            (news_count >= 5 and sentiment > 0.4) or
            (event_type == 'very_positive') or
            (sentiment > 0.7)
        )
    
    def should_add_to_blacklist(self, crypto: str, news_data: Dict) -> bool:
        """Décider si mettre une crypto en blacklist (à éviter)"""
        if not news_data:
            return False
        
        # Blacklist si:
        # - News très négatives (hack, scam, etc.)
        # - Sentiment très négatif (< -0.7)
        
        event_type = news_data.get('event_type', 'neutral')
        sentiment = news_data.get('avg_sentiment', 0)
        
        return (
            event_type == 'very_negative' or
            sentiment < -0.7
        )
    
    def calculate_position_type(self, decision: Dict, news_data: Dict) -> str:
        """
        Déterminer le type de position: FLIP ou HOLD
        
        FLIP: Trade rapide (quelques heures/jours)
        - News très positive court terme
        - Momentum fort
        - Événement ponctuel
        
        HOLD: Position moyen/long terme (semaines)
        - Fondamentaux solides
        - Tendance positive continue
        - Projet sérieux avec actualités récurrentes
        """
        event_type = news_data.get('event_type', 'neutral')
        news_count = news_data.get('total_count', 0)
        
        # FLIP si:
        # - Événement ponctuel très positif
        # - Peu de news mais très forte
        if event_type == 'very_positive' and news_count < 3:
            return 'FLIP'
        
        # - Momentum play (prix monte vite)
        if decision.get('strategy') == 'FLIP':
            return 'FLIP'
        
        # HOLD si:
        # - Plusieurs news positives (tendance)
        # - Sentiment positif soutenu
        if news_count >= 5 or event_type == 'trending_positive':
            return 'HOLD'
        
        # Par défaut
        return decision.get('strategy', 'HOLD')
    
    async def execute_autonomous_strategy(self):
        """
        Exécuter la stratégie autonome complète
        """
        logger.info("🤖 STRATÉGIE AUTONOME EN ACTION")
        logger.info("=" * 80)
        
        # 1. Scanner le marché
        opportunities = await self.scan_market()
        
        if not opportunities:
            logger.warning("⚠️ Aucune crypto active détectée")
            return
        
        # 2. Analyser les news
        crypto_bases = list(set([o['symbol'].split('/')[0] for o in opportunities]))
        news_opportunities = await self.analyze_news_opportunities(crypto_bases)
        
        # 3. Mettre à jour watchlist et blacklist
        for crypto, news_data in news_opportunities.items():
            full_symbol = f"{crypto}/EUR"
            
            if self.should_add_to_watchlist(crypto, news_data):
                if full_symbol not in self.watchlist:
                    self.watchlist.add(full_symbol)
                    logger.success(f"➕ Ajouté à la watchlist: {full_symbol}")
                    logger.info(f"   Raison: {news_data.get('total_count')} news, sentiment {news_data.get('avg_sentiment', 0):.2f}")
            
            if self.should_add_to_blacklist(crypto, news_data):
                if full_symbol not in self.blacklist:
                    self.blacklist.add(full_symbol)
                    logger.error(f"⛔ Ajouté à la blacklist: {full_symbol}")
                    logger.error(f"   Raison: News négatives, sentiment {news_data.get('avg_sentiment', 0):.2f}")
        
        # 4. Gérer le portfolio
        recommendations = await self.manage_portfolio(opportunities, news_opportunities)
        
        # 5. Afficher résumé
        logger.info("📊 RÉSUMÉ DU PORTFOLIO:")
        logger.info(f"   Capital total: {self.capital:,.0f}€")
        logger.info(f"   Capital disponible: {self.available_capital:,.0f}€")
        logger.info(f"   Positions actives: {len(self.active_positions)}")
        logger.info(f"   Watchlist: {len(self.watchlist)} cryptos")
        logger.info(f"   Blacklist: {len(self.blacklist)} cryptos")
        
        if self.watchlist:
            logger.info(f"   🔍 Watchlist: {', '.join(sorted(self.watchlist))}")
        if self.blacklist:
            logger.warning(f"   ⛔ Blacklist: {', '.join(sorted(self.blacklist))}")
        
        logger.info("")
        
        return recommendations

