"""
Twitter-Based Trading Strategy
Le bot base ses décisions principalement sur Twitter/X
"""
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from collections import Counter


class TwitterTrader:
    """
    Trader basé sur Twitter/X
    
    Stratégie:
    - Surveille les tweets crypto en temps réel
    - Détecte les cryptos qui buzzent (volume de mentions)
    - Analyse le sentiment avec FinBERT
    - Trade basé sur le buzz + sentiment
    - Ajoute/retire des cryptos selon l'activité Twitter
    """
    
    def __init__(self, social_ingestion, sentiment_analyzer):
        self.social_ingestion = social_ingestion
        self.sentiment_analyzer = sentiment_analyzer
        
        # Tracking
        self.crypto_mentions = Counter()
        self.crypto_sentiment = {}
        self.trending_cryptos = set()
        
        # Influenceurs crypto connus (à surveiller en priorité)
        self.crypto_influencers = [
            '@elonmusk', '@VitalikButerin', '@APompliano',
            '@CZ_Binance', '@SBF_FTX', '@naval',
            '@maxkeiser', '@aantonop', '@ethereumJoseph'
        ]
        
        logger.info("🐦 Twitter Trader initialisé")
    
    def extract_crypto_mentions(self, text: str) -> List[str]:
        """Extraire les mentions de cryptos d'un tweet"""
        text_upper = text.upper()
        
        # Dictionnaire crypto complet
        crypto_keywords = {
            'BTC': 'BITCOIN',
            'ETH': 'ETHEREUM',
            'SOL': 'SOLANA',
            'XRP': 'RIPPLE',
            'ADA': 'CARDANO',
            'DOT': 'POLKADOT',
            'AVAX': 'AVALANCHE',
            'ATOM': 'COSMOS',
            'LINK': 'CHAINLINK',
            'MATIC': 'POLYGON',
            'UNI': 'UNISWAP',
            'AAVE': 'AAVE',
            'ALGO': 'ALGORAND',
            'FIL': 'FILECOIN'
        }
        
        mentions = []
        
        for symbol, name in crypto_keywords.items():
            # Chercher le symbole ($BTC ou BTC)
            if f'${symbol}' in text_upper or f' {symbol} ' in text_upper or f' {symbol},' in text_upper:
                mentions.append(symbol)
            # Chercher le nom complet
            elif name in text_upper:
                mentions.append(symbol)
        
        return list(set(mentions))
    
    async def fetch_and_analyze_tweets(self, cryptos: List[str]) -> Dict:
        """
        Récupérer et analyser les tweets crypto
        
        Args:
            cryptos: Liste de cryptos à surveiller
            
        Returns:
            Dict avec analyse par crypto
        """
        try:
            logger.info("🐦 Récupération des tweets crypto...")
            
            # Construire query pour Twitter
            query = ' OR '.join([f'${crypto}' for crypto in cryptos[:25]])  # Max 25 cryptos
            query += ' -is:retweet lang:en'  # Pas de retweets, anglais seulement
            
            # Fetch tweets
            tweets = await self.social_ingestion.fetch_twitter_sentiment(query, max_results=100)
            
            if not tweets:
                logger.warning("⚠️ Aucun tweet récupéré (vérifiez Bearer Token)")
                return {}
            
            logger.info(f"✅ {len(tweets)} tweets récupérés")
            
            # Analyser avec FinBERT
            tweet_texts = [
                {
                    'title': t['text'][:100],  # Limiter pour FinBERT
                    'description': t['text'],
                    'source': 'twitter',
                    'metadata': t
                }
                for t in tweets
            ]
            
            analyzed_tweets = self.sentiment_analyzer.analyze_news(tweet_texts)
            
            # Organiser par crypto
            crypto_analysis = {}
            
            for tweet in analyzed_tweets:
                text = tweet.get('description', '')
                sentiment = tweet.get('sentiment', {})
                score = sentiment.get('sentiment_score', 0)
                metadata = tweet.get('metadata', {})
                
                # Extraire mentions de cryptos
                mentioned_cryptos = self.extract_crypto_mentions(text)
                
                for crypto in mentioned_cryptos:
                    if crypto not in crypto_analysis:
                        crypto_analysis[crypto] = {
                            'tweets': [],
                            'scores': [],
                            'total_mentions': 0,
                            'total_likes': 0,
                            'total_retweets': 0,
                            'influencer_mentions': 0
                        }
                    
                    crypto_analysis[crypto]['tweets'].append(tweet)
                    crypto_analysis[crypto]['scores'].append(score)
                    crypto_analysis[crypto]['total_mentions'] += 1
                    crypto_analysis[crypto]['total_likes'] += metadata.get('likes', 0)
                    crypto_analysis[crypto]['total_retweets'] += metadata.get('retweets', 0)
                    
                    # Vérifier si c'est un influenceur (basé sur engagement)
                    if metadata.get('likes', 0) > 100 or metadata.get('retweets', 0) > 50:
                        crypto_analysis[crypto]['influencer_mentions'] += 1
            
            # Calculer métriques
            for crypto, data in crypto_analysis.items():
                if data['scores']:
                    data['avg_sentiment'] = sum(data['scores']) / len(data['scores'])
                    data['max_sentiment'] = max(data['scores'])
                    data['min_sentiment'] = min(data['scores'])
                    
                    # Tendance sentiment
                    if len(data['scores']) >= 10:
                        recent = sum(data['scores'][-5:]) / 5
                        older = sum(data['scores'][:5]) / 5
                        if recent > older + 0.2:
                            data['sentiment_trend'] = 'improving'
                        elif recent < older - 0.2:
                            data['sentiment_trend'] = 'worsening'
                        else:
                            data['sentiment_trend'] = 'stable'
                    else:
                        data['sentiment_trend'] = 'stable'
                    
                    # Score d'engagement
                    data['engagement_score'] = (
                        data['total_likes'] + 
                        data['total_retweets'] * 2 +  # Retweets valent 2x
                        data['influencer_mentions'] * 10  # Influenceurs valent 10x
                    ) / max(data['total_mentions'], 1)
                    
                    # Buzz score (combinaison mentions + engagement + sentiment)
                    buzz_mentions = min(data['total_mentions'] / 10, 1)  # Normalisé
                    buzz_engagement = min(data['engagement_score'] / 100, 1)  # Normalisé
                    buzz_sentiment = (data['avg_sentiment'] + 1) / 2  # 0-1
                    
                    data['buzz_score'] = (
                        buzz_mentions * 0.4 +
                        buzz_engagement * 0.3 +
                        buzz_sentiment * 0.3
                    )
                    
                    # Déterminer statut
                    if data['buzz_score'] > 0.7 and data['avg_sentiment'] > 0.5:
                        data['status'] = 'HOT'  # Très chaud, opportunité
                    elif data['buzz_score'] > 0.5:
                        data['status'] = 'TRENDING'  # En tendance
                    elif data['avg_sentiment'] < -0.6:
                        data['status'] = 'NEGATIVE'  # Buzz négatif
                    else:
                        data['status'] = 'NEUTRAL'
            
            return crypto_analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse Twitter: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def generate_trading_signals(self, twitter_analysis: Dict, price_data: Dict) -> List[Dict]:
        """
        Générer des signaux de trading basés sur Twitter
        
        Args:
            twitter_analysis: Analyse Twitter par crypto
            price_data: Prix actuels
            
        Returns:
            Liste de signaux de trading
        """
        signals = []
        
        for crypto, analysis in twitter_analysis.items():
            symbol = f"{crypto}/EUR"
            
            # Vérifier qu'on a des données de prix
            if symbol not in price_data or not price_data[symbol]:
                continue
            
            ticker = price_data[symbol]
            price = ticker.get('last', 0)
            change_24h = ticker.get('percentage', 0)
            
            status = analysis.get('status', 'NEUTRAL')
            buzz_score = analysis.get('buzz_score', 0)
            sentiment = analysis.get('avg_sentiment', 0)
            mentions = analysis.get('total_mentions', 0)
            engagement = analysis.get('engagement_score', 0)
            
            # Décision de trading
            action = 'HOLD'
            confidence = 0
            strategy = 'wait'
            reason = ''
            position_size = 0
            
            # STRATÉGIE 1: HOT (Buzz très fort + sentiment positif)
            if status == 'HOT':
                if change_24h < 10:  # Pas encore trop monté
                    action = 'BUY'
                    strategy = 'FLIP'  # Flip rapide
                    position_size = min(0.05, buzz_score * 0.07)  # Max 5%
                    confidence = buzz_score
                    reason = f"🔥 TRÈS HOT sur Twitter! {mentions} mentions, sentiment {sentiment:.2f}"
            
            # STRATÉGIE 2: TRENDING (En tendance)
            elif status == 'TRENDING':
                if sentiment > 0.5 and change_24h < 5:
                    action = 'BUY'
                    strategy = 'HOLD'  # Hold si tendance soutenue
                    position_size = 0.03
                    confidence = buzz_score * 0.9
                    reason = f"📈 Trending sur Twitter, {mentions} mentions positives"
            
            # STRATÉGIE 3: Influencer Play
            if analysis.get('influencer_mentions', 0) >= 2 and sentiment > 0.6:
                if change_24h < 8:
                    action = 'BUY'
                    strategy = 'FLIP'
                    position_size = 0.04
                    confidence = min(sentiment + 0.2, 0.95)
                    reason = f"👑 {analysis['influencer_mentions']} influenceurs en parlent!"
            
            # STRATÉGIE 4: NEGATIVE (Buzz négatif)
            if status == 'NEGATIVE' or sentiment < -0.6:
                action = 'SELL'
                strategy = 'EXIT'
                position_size = 1.0  # Vendre 100%
                confidence = abs(sentiment)
                reason = f"⚠️ Buzz négatif sur Twitter, sentiment {sentiment:.2f}"
            
            # STRATÉGIE 5: FUD Detection (Fear Uncertainty Doubt)
            if mentions >= 20 and sentiment < -0.4:
                # Beaucoup de mentions négatives = FUD possible
                if change_24h < -5:
                    # FUD + prix baisse = danger
                    action = 'SELL'
                    strategy = 'EXIT'
                    confidence = 0.8
                    reason = "🚨 FUD détecté + prix baisse"
            
            if action != 'HOLD' or confidence > 0.4:
                signals.append({
                    'symbol': symbol,
                    'action': action,
                    'strategy': strategy,
                    'position_size': position_size,
                    'confidence': confidence,
                    'reason': reason,
                    'twitter_data': {
                        'status': status,
                        'mentions': mentions,
                        'sentiment': sentiment,
                        'buzz_score': buzz_score,
                        'engagement': engagement,
                        'influencer_mentions': analysis.get('influencer_mentions', 0)
                    },
                    'price': price,
                    'change_24h': change_24h
                })
        
        # Trier par confiance
        signals.sort(key=lambda x: x['confidence'], reverse=True)
        
        return signals

