#!/usr/bin/env python3
"""
Bot Twitter + LLM (ChatGPT/Claude/Ollama)
Le LLM interprète les tweets et décide s'il faut acheter/vendre
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
from src.ml.llm_analyzer import LLMAnalyzer
from src.utils.twitter_rate_limiter import TwitterRateLimiter


class TwitterLLMBot:
    """Bot avec Twitter + LLM pour décisions intelligentes"""
    
    def __init__(self, llm_provider: str = "ollama"):
        self.market_data = None
        self.social_ingestion = None
        self.llm_analyzer = None
        self.rate_limiter = TwitterRateLimiter()
        self.llm_provider = llm_provider
        self.running = False
        
        # Cryptos prioritaires (backtest)
        self.priority_cryptos = ['ATOM', 'ETH']  # Validées
        self.other_cryptos = ['BTC', 'SOL', 'AVAX', 'XRP', 'ADA']
        
        logger.info(f"🤖 Twitter + LLM Bot initialisé ({llm_provider})")
    
    async def initialize(self):
        """Initialiser"""
        try:
            logger.info("=" * 80)
            logger.info(f"🔧 Initialisation Bot Twitter + LLM ({self.llm_provider})...")
            logger.info("=" * 80)
            
            # Market data
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.success("✅ Market Data")
            
            # Social (Twitter)
            self.social_ingestion = SocialMediaIngestion()
            logger.success("✅ Twitter API")
            
            # LLM
            self.llm_analyzer = LLMAnalyzer(provider=self.llm_provider)
            logger.success(f"✅ LLM ({self.llm_provider})")
            
            logger.success("\n🎉 BOT TWITTER + LLM PRÊT!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Erreur init: {e}")
            raise
    
    async def run(self):
        """Boucle principale"""
        self.running = True
        iteration = 0
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE BOT TWITTER + LLM")
        logger.info("=" * 80)
        logger.info("")
        logger.info("🧠 FONCTIONNEMENT:")
        logger.info("   1. Récupère tweets crypto via Twitter API")
        logger.info(f"   2. Le LLM ({self.llm_provider}) interprète contexte & sentiment")
        logger.info("   3. Le LLM DÉCIDE: ACHETER/VENDRE/ATTENDRE")
        logger.info("   4. Le LLM explique sa décision")
        logger.info("   5. Gestion intelligente du portfolio")
        logger.info("")
        logger.info("🎯 Le LLM comprend:")
        logger.info("   • Contexte des tweets (pas juste sentiment)")
        logger.info("   • Sarcasme et ironie")
        logger.info("   • Références et mèmes crypto")
        logger.info("   • FUD vs vraies préoccupations")
        logger.info("   • Hype vs fondamentaux")
        logger.info("")
        logger.info("=" * 80)
        
        try:
            while self.running:
                iteration += 1
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🐦 CYCLE LLM #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # Stats API
                self.rate_limiter.print_stats()
                logger.info("")
                
                # Sélectionner cryptos selon quota
                if self.rate_limiter.get_stats()['window_usage_percent'] < 50:
                    cryptos_to_scan = self.priority_cryptos + self.other_cryptos
                else:
                    cryptos_to_scan = self.priority_cryptos
                
                logger.info(f"🔍 Analyse LLM de {len(cryptos_to_scan)} cryptos: {', '.join(cryptos_to_scan)}")
                logger.info("")
                
                # Pour chaque crypto
                for crypto in cryptos_to_scan:
                    symbol = f"{crypto}/EUR"
                    
                    # Vérifier rate limit
                    if not self.rate_limiter.can_make_request():
                        wait = self.rate_limiter.wait_if_needed()
                        logger.warning(f"⏰ Rate limit, attente {wait}s...")
                        await asyncio.sleep(wait)
                    
                    # Récupérer prix
                    ticker = await self.market_data.fetch_ticker(symbol)
                    if not ticker:
                        continue
                    
                    price = ticker['last']
                    change_24h = ticker.get('percentage', 0)
                    
                    # Récupérer tweets
                    query = f"${crypto} -is:retweet lang:en"
                    tweets = await self.social_ingestion.fetch_twitter_sentiment(query, max_results=20)
                    
                    self.rate_limiter.record_request(len(tweets))
                    
                    if not tweets:
                        logger.warning(f"⚠️ Pas de tweets pour {crypto}")
                        continue
                    
                    logger.info(f"🐦 {crypto}: {len(tweets)} tweets récupérés")
                    
                    # Analyser avec LLM
                    logger.info(f"🤖 Le LLM analyse {crypto}...")
                    decision = await self.llm_analyzer.analyze_tweets_for_crypto(
                        crypto=crypto,
                        tweets=tweets,
                        current_price=price,
                        price_change_24h=change_24h
                    )
                    
                    # Afficher décision
                    action = decision.get('action', 'HOLD')
                    confidence = decision.get('confidence', 0)
                    sentiment = decision.get('sentiment', 'neutre')
                    buzz = decision.get('buzz_level', 'inconnu')
                    explanation = decision.get('explanation', '')
                    position_size = decision.get('position_size', 0)
                    
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
                    
                    log_func("")
                    log_func(f"{emoji} {symbol:12} | Prix: {price:>10,.2f}€ | 24h: {change_24h:>6.2f}%")
                    log_func(f"   🤖 LLM DÉCISION: {action}")
                    log_func(f"   💡 {explanation}")
                    log_func(f"   📊 Sentiment: {sentiment} | Buzz: {buzz} | Confiance: {confidence*100:.0f}%")
                    
                    if action == 'BUY' and position_size > 0:
                        amount = settings.trading.initial_capital * position_size
                        strategy = decision.get('strategy', 'HOLD')
                        log_func(f"   💰 Position recommandée: {position_size*100:.1f}% (~{amount:,.0f}€) en {strategy}")
                    
                    if decision.get('key_signals'):
                        logger.info(f"   🎯 Signaux: {', '.join(decision['key_signals'][:3])}")
                    
                    if decision.get('risks'):
                        logger.warning(f"   ⚠️ Risques: {', '.join(decision['risks'][:3])}")
                    
                    logger.info("")
                    
                    # Pause entre cryptos
                    await asyncio.sleep(2)
                
                # Calculer intervalle
                optimal_interval = self.rate_limiter.calculate_optimal_interval()
                
                logger.info("=" * 80)
                logger.info(f"💰 Capital: {settings.trading.initial_capital:,.0f}€")
                logger.info(f"⏰ Prochain scan dans {optimal_interval//60} minutes")
                logger.info("=" * 80)
                
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
        """Arrêter"""
        logger.info("\n🛑 Arrêt...")
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.social_ingestion:
            await self.social_ingestion.close()
        if self.llm_analyzer:
            await self.llm_analyzer.close()
        
        logger.success("✅ Bot arrêté")


async def main():
    """Point d'entrée"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot Twitter + LLM')
    parser.add_argument('--llm', type=str, default='ollama',
                       choices=['ollama', 'openai', 'anthropic'],
                       help='LLM provider (default: ollama - gratuit et local)')
    args = parser.parse_args()
    
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🤖 TRADOPS - BOT TWITTER + LLM")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"🧠 LLM Provider: {args.llm.upper()}")
    logger.info("")
    
    if args.llm == 'ollama':
        logger.info("💡 OLLAMA (Local & Gratuit):")
        logger.info("   ✅ 100% gratuit")
        logger.info("   ✅ Aucune limite")
        logger.info("   ✅ Privé (données locales)")
        logger.info("   ✅ Rapide")
        logger.info("")
        logger.info("   Pour installer Ollama:")
        logger.info("   curl -fsSL https://ollama.com/install.sh | sh")
        logger.info("   ollama pull llama3.1:8b")
        logger.info("   ollama serve")
        logger.info("")
    elif args.llm == 'openai':
        logger.info("💡 OPENAI (ChatGPT):")
        logger.info("   • Très performant")
        logger.info("   • Coût: ~$0.15 pour 1000 tweets analysés")
        logger.info("   • Besoin: OPENAI_API_KEY dans .env")
        logger.info("")
    elif args.llm == 'anthropic':
        logger.info("💡 ANTHROPIC (Claude):")
        logger.info("   • Excellent pour nuances")
        logger.info("   • Coût: ~$0.25 pour 1000 tweets analysés")
        logger.info("   • Besoin: ANTHROPIC_API_KEY dans .env")
        logger.info("")
    
    logger.info("🎯 Le LLM va interpréter chaque tweet et décider:")
    logger.info("   • ACHETER si opportunité claire")
    logger.info("   • VENDRE si risque détecté")
    logger.info("   • ATTENDRE si incertain")
    logger.info("")
    logger.info("=" * 80)
    
    # Lancer
    bot = TwitterLLMBot(llm_provider=args.llm)
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot arrêté")
    except Exception as e:
        logger.error(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

