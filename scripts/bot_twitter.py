#!/usr/bin/env python3
"""
BOT BASÉ SUR TWITTER/X
Trade basé sur le buzz et sentiment Twitter en temps réel
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


class TwitterTradingBot:
    """Bot de trading basé sur Twitter/X"""
    
    def __init__(self):
        self.market_data = None
        self.social_ingestion = None
        self.sentiment_analyzer = None
        self.twitter_trader = None
        self.running = False
        
        # Cryptos à surveiller sur Twitter
        self.crypto_universe = [
            'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT',
            'AVAX', 'ATOM', 'LINK', 'MATIC', 'UNI',
            'AAVE', 'ALGO', 'FIL', 'LTC', 'BCH'
        ]
        
        logger.info("🐦 Twitter Trading Bot initialisé")
        logger.info(f"   Surveillance: {len(self.crypto_universe)} cryptos")
    
    async def initialize(self):
        """Initialiser les composants"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 Initialisation du Bot Twitter...")
            logger.info("=" * 80)
            
            # Market data
            logger.info("📊 Market Data...")
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.success("✅ Market Data OK")
            
            # Social ingestion (Twitter)
            logger.info("🐦 Twitter API...")
            self.social_ingestion = SocialMediaIngestion()
            logger.success("✅ Twitter API OK")
            
            # Sentiment analyzer (FinBERT)
            logger.info("🧠 FinBERT...")
            self.sentiment_analyzer = SentimentAnalyzer()
            self.sentiment_analyzer.initialize()
            logger.success("✅ FinBERT OK")
            
            # Twitter Trader
            logger.info("🎯 Twitter Trader...")
            self.twitter_trader = TwitterTrader(
                social_ingestion=self.social_ingestion,
                sentiment_analyzer=self.sentiment_analyzer
            )
            logger.success("✅ Twitter Trader OK")
            
            logger.info("")
            logger.success("🎉 BOT TWITTER 100% INITIALISÉ!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Échec initialisation: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def run(self):
        """Boucle principale"""
        self.running = True
        iteration = 0
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE DU BOT TWITTER")
        logger.info("=" * 80)
        logger.info("")
        logger.info("🐦 Le bot base ses décisions sur Twitter:")
        logger.info("   1. Surveille les tweets crypto en temps réel")
        logger.info("   2. Détecte les cryptos qui BUZZENT")
        logger.info("   3. Analyse sentiment avec FinBERT")
        logger.info("   4. Détecte mentions d'influenceurs")
        logger.info("   5. ACHÈTE ce qui buzz positivement")
        logger.info("   6. VEND ce qui buzz négativement (FUD)")
        logger.info("   7. AJOUTE/RETIRE des cryptos selon l'activité")
        logger.info("")
        logger.info("💡 Analyse toutes les 3 minutes (limites API Twitter)")
        logger.info("💡 Appuyez sur Ctrl+C pour arrêter")
        logger.info("=" * 80)
        
        try:
            while self.running:
                iteration += 1
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🐦 CYCLE TWITTER #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # 1. Analyser Twitter
                twitter_analysis = await self.twitter_trader.fetch_and_analyze_tweets(
                    self.crypto_universe
                )
                
                if not twitter_analysis:
                    logger.warning("⚠️ Pas de données Twitter (vérifiez Bearer Token)")
                    logger.info("💡 Le bot fonctionne en mode limité sans Twitter")
                    await asyncio.sleep(180)
                    continue
                
                # 2. Récupérer les prix
                logger.info("📊 Récupération des prix...")
                symbols = [f"{crypto}/EUR" for crypto in twitter_analysis.keys()]
                price_data = await self.market_data.fetch_multiple_tickers(symbols)
                
                # 3. Générer signaux de trading
                logger.info("🎯 Génération des signaux basés sur Twitter...")
                signals = self.twitter_trader.generate_trading_signals(
                    twitter_analysis,
                    price_data
                )
                
                # 4. Afficher résultats
                logger.info("")
                logger.info("🐦 ANALYSE TWITTER DES CRYPTOS:")
                logger.info("=" * 80)
                
                # Trier par buzz score
                sorted_analysis = sorted(
                    twitter_analysis.items(),
                    key=lambda x: x[1].get('buzz_score', 0),
                    reverse=True
                )
                
                for i, (crypto, data) in enumerate(sorted_analysis[:15], 1):  # Top 15
                    status = data.get('status', 'NEUTRAL')
                    mentions = data.get('total_mentions', 0)
                    sentiment = data.get('avg_sentiment', 0)
                    buzz = data.get('buzz_score', 0)
                    engagement = data.get('engagement_score', 0)
                    influencers = data.get('influencer_mentions', 0)
                    
                    # Emoji selon status
                    if status == 'HOT':
                        emoji = "🔥"
                        log_func = logger.success
                    elif status == 'TRENDING':
                        emoji = "📈"
                        log_func = logger.info
                    elif status == 'NEGATIVE':
                        emoji = "⚠️"
                        log_func = logger.warning
                    else:
                        emoji = "⚪"
                        log_func = logger.info
                    
                    # Sentiment emoji
                    if sentiment > 0.5:
                        sent_emoji = "😊"
                    elif sentiment > 0:
                        sent_emoji = "🙂"
                    elif sentiment < -0.5:
                        sent_emoji = "😟"
                    elif sentiment < 0:
                        sent_emoji = "😐"
                    else:
                        sent_emoji = "😶"
                    
                    log_func(
                        f"{i:2}. {emoji} {crypto:6} | "
                        f"Status: {status:10} | "
                        f"Mentions: {mentions:3} | "
                        f"Buzz: {buzz*100:5.1f}% | "
                        f"Sentiment: {sent_emoji} {sentiment:>5.2f} | "
                        f"Influencers: {influencers}"
                    )
                
                # 5. Afficher signaux de trading
                logger.info("")
                logger.info("=" * 80)
                logger.info("🎯 SIGNAUX DE TRADING BASÉS SUR TWITTER:")
                logger.info("-" * 80)
                
                if signals:
                    for i, signal in enumerate(signals[:10], 1):  # Top 10
                        symbol = signal['symbol']
                        action = signal['action']
                        strategy = signal['strategy']
                        confidence = signal['confidence']
                        reason = signal['reason']
                        position_size = signal['position_size']
                        twitter = signal['twitter_data']
                        price = signal['price']
                        
                        # Emoji
                        if action == 'BUY':
                            emoji = "🟢"
                            log_func = logger.success
                        elif action == 'SELL':
                            emoji = "🔴"
                            log_func = logger.error
                        else:
                            emoji = "⚪"
                            log_func = logger.info
                        
                        # Montant
                        amount = settings.trading.initial_capital * position_size
                        
                        log_func(
                            f"{i:2}. {emoji} {symbol:12} | "
                            f"{action:4} {strategy:4} | "
                            f"Prix: {price:>10,.2f}€ | "
                            f"Position: {position_size*100:4.1f}% (~{amount:>5,.0f}€) | "
                            f"Conf: {confidence*100:>4.0f}%"
                        )
                        logger.info(f"       💡 {reason}")
                        logger.info(
                            f"       🐦 Twitter: {twitter['mentions']} mentions, "
                            f"{twitter['influencer_mentions']} influenceurs, "
                            f"engagement {twitter['engagement']:.0f}"
                        )
                else:
                    logger.info("⚪ Aucun signal de trading fort")
                    logger.info("   Attendez plus de buzz sur Twitter")
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"💰 Capital simulé: {settings.trading.initial_capital:,.0f}€")
                logger.info(f"⏰ Prochain scan Twitter dans 3 minutes...")
                logger.info("=" * 80)
                
                # Attendre 3 minutes (limites API Twitter)
                await asyncio.sleep(180)
                
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
        logger.info("")
        logger.info("🛑 Arrêt du Bot Twitter...")
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.social_ingestion:
            await self.social_ingestion.close()
        
        logger.success("✅ Bot Twitter arrêté")


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🐦 TRADOPS - BOT BASÉ SUR TWITTER/X")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🎯 STRATÉGIES TWITTER:")
    logger.info("")
    logger.info("   1. 🔥 HOT     : Buzz fort + sentiment + → FLIP rapide")
    logger.info("   2. 📈 TRENDING: Tendance positive soutenue → HOLD")
    logger.info("   3. 👑 INFLUENCER: Mentions d'influenceurs → FLIP")
    logger.info("   4. ⚠️  NEGATIVE: Buzz négatif → VENTE")
    logger.info("   5. 🚨 FUD     : Fear/Uncertainty/Doubt → SORTIE")
    logger.info("")
    logger.info(f"💰 Capital: {settings.trading.initial_capital:,.0f}€")
    logger.info(f"📊 Mode: {settings.trading.trading_mode.upper()}")
    logger.info("")
    logger.info("=" * 80)
    
    # Vérifier Bearer Token
    if not settings.data_sources.twitter_bearer_token:
        logger.warning("")
        logger.warning("⚠️ TWITTER BEARER TOKEN PAS CONFIGURÉ!")
        logger.warning("")
        logger.warning("Pour activer Twitter:")
        logger.warning("   1. Allez sur https://developer.twitter.com/")
        logger.warning("   2. Créez un Developer Account (gratuit)")
        logger.warning("   3. Créez une App et obtenez le Bearer Token")
        logger.warning("   4. Ajoutez dans .env:")
        logger.warning("      TWITTER_BEARER_TOKEN=votre_token")
        logger.warning("")
        logger.warning("Le bot continuera avec sources alternatives...")
        logger.warning("")
        await asyncio.sleep(5)
    else:
        logger.success("")
        logger.success("✅ Twitter Bearer Token détecté!")
        logger.success("   Le bot analysera les tweets en temps réel")
        logger.success("")
    
    # Lancer
    bot = TwitterTradingBot()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot Twitter arrêté")
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

