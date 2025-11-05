#!/usr/bin/env python3
"""
Bot Twitter OPTIMISÉ - Respecte les limites API gratuites
100 requêtes/15 min, 500K tweets/mois
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.data_ingestion.market_data import MarketDataIngestion
from src.data_ingestion.news_ingestion import SocialMediaIngestion
from src.ml.sentiment_analyzer import SentimentAnalyzer
from src.strategy.twitter_trader import TwitterTrader
from src.utils.twitter_rate_limiter import TwitterRateLimiter


class OptimizedTwitterBot:
    """Bot Twitter optimisé pour API gratuite"""
    
    def __init__(self):
        self.market_data = None
        self.social_ingestion = None
        self.sentiment_analyzer = None
        self.twitter_trader = None
        self.rate_limiter = TwitterRateLimiter()
        self.running = False
        
        # Priorités des cryptos (basé sur backtest + volume)
        self.high_priority = ['ATOM', 'ETH']  # Validées par backtest
        self.normal_priority = ['BTC', 'SOL', 'AVAX']  # Volume élevé
        self.low_priority = ['XRP', 'ADA', 'DOT', 'LINK', 'MATIC']  # Autres
        
        self.all_cryptos = self.high_priority + self.normal_priority + self.low_priority
        
        logger.info("🐦 Twitter Bot Optimisé initialisé")
        logger.info(f"   Cryptos prioritaires: {', '.join(self.high_priority)}")
        logger.info(f"   Cryptos normales: {', '.join(self.normal_priority)}")
    
    async def initialize(self):
        """Initialiser les composants"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 Initialisation Bot Twitter Optimisé...")
            logger.info("=" * 80)
            
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.success("✅ Market Data")
            
            self.social_ingestion = SocialMediaIngestion()
            logger.success("✅ Social Media")
            
            self.sentiment_analyzer = SentimentAnalyzer()
            self.sentiment_analyzer.initialize()
            logger.success("✅ FinBERT")
            
            self.twitter_trader = TwitterTrader(
                social_ingestion=self.social_ingestion,
                sentiment_analyzer=self.sentiment_analyzer
            )
            logger.success("✅ Twitter Trader")
            
            logger.success("\n🎉 BOT OPTIMISÉ PRÊT!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            raise
    
    def select_cryptos_to_scan(self) -> list:
        """
        Sélectionner intelligemment les cryptos à scanner
        selon l'usage API actuel
        """
        stats = self.rate_limiter.get_stats()
        usage = stats['window_usage_percent']
        
        # Si usage faible: scanner toutes
        if usage < 50:
            return self.all_cryptos
        
        # Si usage moyen: high + normal
        if usage < 80:
            return self.high_priority + self.normal_priority
        
        # Si usage élevé: high priority seulement
        return self.high_priority
    
    async def smart_twitter_scan(self):
        """Scanner Twitter de manière optimisée"""
        try:
            # Vérifier le cache d'abord
            cache_key = 'twitter_scan'
            cached = self.rate_limiter.get_cache(cache_key)
            
            if cached:
                logger.info("💾 Utilisation données Twitter en cache")
                return cached
            
            # Vérifier si on peut faire une requête
            if not self.rate_limiter.can_make_request():
                wait_time = self.rate_limiter.wait_if_needed()
                logger.warning(f"⏰ Rate limit: attendez {wait_time}s avant prochaine requête")
                logger.info("💡 Utilisation du cache en attendant...")
                return {}
            
            # Sélectionner cryptos selon usage
            cryptos_to_scan = self.select_cryptos_to_scan()
            logger.info(f"🔍 Scan Twitter de {len(cryptos_to_scan)} cryptos: {', '.join(cryptos_to_scan)}")
            
            # Fetch et analyser
            twitter_analysis = await self.twitter_trader.fetch_and_analyze_tweets(cryptos_to_scan)
            
            # Enregistrer la requête
            tweets_count = sum(a.get('total_mentions', 0) for a in twitter_analysis.values())
            self.rate_limiter.record_request(tweets_count)
            
            # Mettre en cache
            self.rate_limiter.set_cache(cache_key, twitter_analysis)
            
            logger.info(f"✅ {tweets_count} tweets analysés")
            
            return twitter_analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur scan Twitter: {e}")
            self.rate_limiter.rate_limit_hits += 1
            return {}
    
    async def run(self):
        """Boucle principale optimisée"""
        self.running = True
        iteration = 0
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE BOT TWITTER OPTIMISÉ")
        logger.info("=" * 80)
        logger.info("")
        logger.info("🔒 OPTIMISATIONS API GRATUITE:")
        logger.info("   ✅ Rate limiting intelligent (max 100 req/15min)")
        logger.info("   ✅ Cache de 5 minutes (réduit requêtes)")
        logger.info("   ✅ Priorité cryptos validées (ATOM, ETH)")
        logger.info("   ✅ Ajustement automatique de fréquence")
        logger.info("   ✅ Gestion erreurs 429 (Too Many Requests)")
        logger.info("")
        logger.info("📊 STRATÉGIE:")
        logger.info("   • Usage < 50%: Scan toutes les 10 min (toutes cryptos)")
        logger.info("   • Usage < 80%: Scan toutes les 15 min (prioritaires)")
        logger.info("   • Usage > 80%: Scan toutes les 20 min (ATOM + ETH)")
        logger.info("")
        logger.info("💡 Le bot s'adapte automatiquement pour ne JAMAIS dépasser les limites")
        logger.info("=" * 80)
        
        try:
            while self.running:
                iteration += 1
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🐦 CYCLE #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # Afficher stats API
                self.rate_limiter.print_stats()
                logger.info("")
                
                # Scanner Twitter (avec rate limiting)
                twitter_analysis = await self.smart_twitter_scan()
                
                if twitter_analysis:
                    # Récupérer prix
                    symbols = [f"{crypto}/EUR" for crypto in twitter_analysis.keys()]
                    price_data = await self.market_data.fetch_multiple_tickers(symbols)
                    
                    # Générer signaux
                    signals = self.twitter_trader.generate_trading_signals(
                        twitter_analysis,
                        price_data
                    )
                    
                    # Afficher résultats
                    logger.info("")
                    logger.info("🐦 BUZZ TWITTER:")
                    logger.info("-" * 80)
                    
                    # Trier par buzz
                    sorted_analysis = sorted(
                        twitter_analysis.items(),
                        key=lambda x: x[1].get('buzz_score', 0),
                        reverse=True
                    )
                    
                    for i, (crypto, data) in enumerate(sorted_analysis[:10], 1):
                        status = data.get('status', 'NEUTRAL')
                        mentions = data.get('total_mentions', 0)
                        sentiment = data.get('avg_sentiment', 0)
                        buzz = data.get('buzz_score', 0)
                        
                        emoji = {"HOT": "🔥", "TRENDING": "📈", "NEGATIVE": "⚠️"}.get(status, "⚪")
                        sent_emoji = "😊" if sentiment > 0.5 else "🙂" if sentiment > 0 else "😐" if sentiment > -0.5 else "😟"
                        
                        logger.info(
                            f"{i:2}. {emoji} {crypto:6} | "
                            f"Mentions: {mentions:3} | "
                            f"Buzz: {buzz*100:5.1f}% | "
                            f"Sentiment: {sent_emoji} {sentiment:>5.2f}"
                        )
                    
                    # Signaux de trading
                    if signals:
                        logger.info("")
                        logger.info("🎯 SIGNAUX DE TRADING:")
                        logger.info("-" * 80)
                        
                        for i, signal in enumerate(signals[:5], 1):
                            symbol = signal['symbol']
                            action = signal['action']
                            strategy = signal['strategy']
                            confidence = signal['confidence']
                            reason = signal['reason']
                            
                            emoji = "🟢" if action == 'BUY' else "🔴" if action == 'SELL' else "⚪"
                            log_func = logger.success if action == 'BUY' else logger.warning if action == 'SELL' else logger.info
                            
                            amount = settings.trading.initial_capital * signal['position_size']
                            
                            log_func(
                                f"{i}. {emoji} {symbol:12} {action:4} {strategy:4} | "
                                f"~{amount:>5,.0f}€ | Conf: {confidence*100:>4.0f}%"
                            )
                            logger.info(f"     💡 {reason}")
                    else:
                        logger.info("\n⚪ Aucun signal fort - Bot en attente")
                
                else:
                    logger.info("⚪ Pas de données Twitter disponibles (cache ou rate limit)")
                
                # Calculer intervalle optimal
                optimal_interval = self.rate_limiter.calculate_optimal_interval()
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"💰 Capital: {settings.trading.initial_capital:,.0f}€")
                logger.info(f"⏰ Prochain scan dans {optimal_interval//60} minutes")
                logger.info(f"💡 Intervalle ajusté selon usage API")
                logger.info("=" * 80)
                
                # Attendre
                await asyncio.sleep(optimal_interval)
                
        except KeyboardInterrupt:
            logger.info("\n⏸️ Arrêt demandé")
        except Exception as e:
            logger.error(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Arrêter proprement"""
        logger.info("\n🛑 Arrêt du bot...")
        
        # Afficher stats finales
        logger.info("")
        logger.info("📊 STATISTIQUES FINALES:")
        self.rate_limiter.print_stats()
        
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.social_ingestion:
            await self.social_ingestion.close()
        
        logger.success("\n✅ Bot arrêté proprement")


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🐦 TRADOPS - BOT TWITTER OPTIMISÉ (API Gratuite)")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🔒 RESPECT DES LIMITES API GRATUITE:")
    logger.info("")
    logger.info("   ✅ Max 100 requêtes / 15 minutes")
    logger.info("   ✅ Max 500,000 tweets / mois")
    logger.info("   ✅ Cache intelligent (5 minutes)")
    logger.info("   ✅ Intervalle adaptatif (10-20 minutes)")
    logger.info("   ✅ Priorité aux cryptos validées")
    logger.info("")
    logger.info("📊 UTILISATION OPTIMALE:")
    logger.info("")
    logger.info("   • 6 requêtes/heure = 144 requêtes/jour")
    logger.info("   • ~100 tweets/requête = 14,400 tweets/jour")
    logger.info("   • 432,000 tweets/mois (sous la limite!)")
    logger.info("")
    logger.info("✅ Vous ne serez JAMAIS banni ni limité!")
    logger.info("")
    logger.info("=" * 80)
    
    # Vérifier Bearer Token
    if not settings.data_sources.twitter_bearer_token:
        logger.warning("")
        logger.warning("⚠️ TWITTER BEARER TOKEN PAS CONFIGURÉ!")
        logger.warning("")
        logger.warning("Pour activer Twitter:")
        logger.warning("   1. https://developer.twitter.com/")
        logger.warning("   2. Create Developer Account (gratuit)")
        logger.warning("   3. Create App → Get Bearer Token")
        logger.warning("   4. Ajoutez dans .env:")
        logger.warning("      TWITTER_BEARER_TOKEN=votre_token")
        logger.warning("")
        logger.warning("📖 Voir: docs/TWITTER_SETUP.md")
        logger.warning("")
        logger.info("Le bot continuera mais sans analyse Twitter...")
        logger.info("")
        await asyncio.sleep(5)
    else:
        logger.success("")
        logger.success("✅ Twitter Bearer Token configuré!")
        logger.success("   Le bot analysera Twitter de manière optimisée")
        logger.success("")
    
    # Lancer
    bot = OptimizedTwitterBot()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot arrêté")
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

