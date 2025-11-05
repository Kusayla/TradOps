#!/usr/bin/env python3
"""
BOT AUTONOME - Trading IA Complètement Automatique
Le bot scanne, décide et trade par lui-même
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
from src.data_ingestion.news_ingestion import NewsIngestion
from src.ml.sentiment_analyzer import SentimentAnalyzer
from src.ml.ai_signal_generator import AISignalGenerator
from src.strategy.autonomous_trader import AutonomousTrader


class AutonomousTradingBot:
    """Bot de trading entièrement autonome"""
    
    def __init__(self):
        self.market_data = None
        self.news_ingestion = None
        self.sentiment_analyzer = None
        self.ai_generator = None
        self.autonomous_trader = None
        self.running = False
        
        logger.info("🤖 Bot Autonome initialisé")
    
    async def initialize(self):
        """Initialiser tous les composants"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 Initialisation du Système Autonome...")
            logger.info("=" * 80)
            
            # 1. Market data
            logger.info("📊 Initialisation Market Data...")
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.success("✅ Market Data prêt")
            
            # 2. News ingestion
            logger.info("📰 Initialisation News Ingestion...")
            self.news_ingestion = NewsIngestion()
            logger.success("✅ News Ingestion prêt")
            
            # 3. Sentiment analyzer (FinBERT)
            logger.info("🧠 Chargement de FinBERT...")
            self.sentiment_analyzer = SentimentAnalyzer()
            self.sentiment_analyzer.initialize()
            logger.success("✅ FinBERT chargé")
            
            # 4. AI Signal Generator
            logger.info("🎯 Initialisation AI Signal Generator...")
            self.ai_generator = AISignalGenerator()
            logger.success("✅ AI Generator prêt")
            
            # 5. Autonomous Trader (le cerveau)
            logger.info("🤖 Initialisation Trader Autonome...")
            self.autonomous_trader = AutonomousTrader(
                market_data=self.market_data,
                news_ingestion=self.news_ingestion,
                sentiment_analyzer=self.sentiment_analyzer,
                ai_generator=self.ai_generator
            )
            logger.success("✅ Trader Autonome prêt")
            
            logger.info("")
            logger.success("🎉 SYSTÈME AUTONOME 100% INITIALISÉ!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Échec initialisation: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def run(self):
        """Boucle principale autonome"""
        self.running = True
        iteration = 0
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE DU BOT AUTONOME")
        logger.info("=" * 80)
        logger.info("")
        logger.info("🧠 Le bot va:")
        logger.info("   1. Scanner TOUTES les cryptos EUR disponibles")
        logger.info("   2. Analyser les news en temps réel avec FinBERT")
        logger.info("   3. Détecter les opportunités automatiquement")
        logger.info("   4. Décider SEUL quoi acheter/vendre/hold")
        logger.info("   5. Gérer sa watchlist dynamiquement")
        logger.info("   6. Choisir entre FLIP (court terme) ou HOLD (moyen terme)")
        logger.info("")
        logger.info("💡 Le bot analyse le marché toutes les 5 minutes")
        logger.info("💡 Appuyez sur Ctrl+C pour arrêter")
        logger.info("=" * 80)
        
        try:
            while self.running:
                iteration += 1
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🔄 CYCLE AUTONOME #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # Exécuter la stratégie autonome
                recommendations = await self.autonomous_trader.execute_autonomous_strategy()
                
                # Afficher statistiques
                logger.info("")
                logger.info("📈 STATISTIQUES:")
                logger.info(f"   💰 Capital total: {self.autonomous_trader.capital:,.0f}€")
                logger.info(f"   💵 Capital disponible: {self.autonomous_trader.available_capital:,.0f}€")
                logger.info(f"   📊 Positions actives: {len(self.autonomous_trader.active_positions)}")
                logger.info(f"   👀 Watchlist: {len(self.autonomous_trader.watchlist)} cryptos")
                logger.info(f"   ⛔ Blacklist: {len(self.autonomous_trader.blacklist)} cryptos")
                
                if recommendations:
                    logger.info(f"   🎯 Opportunités détectées: {len(recommendations)}")
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"⏰ Prochain scan dans 5 minutes...")
                logger.info(f"💡 Mode: {settings.trading.trading_mode.upper()} (aucun argent réel utilisé)")
                logger.info("=" * 80)
                
                # Attendre 5 minutes
                await asyncio.sleep(300)
                
        except KeyboardInterrupt:
            logger.info("\n⏸️ Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"\n❌ Erreur dans la boucle: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Arrêter proprement"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 Arrêt du Bot Autonome...")
        logger.info("=" * 80)
        
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.news_ingestion:
            await self.news_ingestion.close()
        
        logger.success("✅ Bot arrêté proprement")
        logger.info("=" * 80)


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🤖 TRADOPS - BOT DE TRADING AUTONOME")
    logger.info("=" * 80)
    logger.info("")
    logger.info("🧠 INTELLIGENCE ARTIFICIELLE AUTONOME:")
    logger.info("")
    logger.info("   ✅ Scan automatique de TOUTES les cryptos EUR")
    logger.info("   ✅ Analyse de news en temps réel (FinBERT)")
    logger.info("   ✅ Détection d'opportunités intelligente")
    logger.info("   ✅ Décision autonome (achat/vente/hold)")
    logger.info("   ✅ Gestion dynamique de watchlist")
    logger.info("   ✅ Stratégie FLIP vs HOLD automatique")
    logger.info("   ✅ Blacklist automatique (cryptos à éviter)")
    logger.info("")
    logger.info("🎯 STRATÉGIES DU BOT:")
    logger.info("")
    logger.info("   1. Event-Driven : News très positives → ACHAT rapide")
    logger.info("   2. Trending : Plusieurs news positives → HOLD moyen terme")
    logger.info("   3. Momentum : Prix monte + sentiment + → FLIP court terme")
    logger.info("   4. Contrarian : Prix bas + news + → ACHAT opportuniste")
    logger.info("   5. Risk Exit : News négatives → VENTE immédiate")
    logger.info("")
    logger.info(f"💰 Capital simulé: {settings.trading.initial_capital:,.0f}€")
    logger.info(f"📊 Mode: {settings.trading.trading_mode.upper()}")
    logger.info("")
    logger.info("=" * 80)
    
    # Vérifier les clés API
    if settings.data_sources.cryptopanic_api_key or settings.data_sources.newsapi_key:
        logger.success("")
        logger.success("✅ Clés API news configurées!")
        logger.success("   Le bot analysera les vraies actualités crypto")
        logger.success("")
    else:
        logger.warning("")
        logger.warning("⚠️ Pas de clés API news")
        logger.warning("   Ajoutez dans .env pour activer:")
        logger.warning("   CRYPTOPANIC_API_KEY=votre_clé")
        logger.warning("   NEWSAPI_KEY=votre_clé")
        logger.warning("")
    
    # Créer et lancer
    bot = AutonomousTradingBot()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot autonome arrêté")
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

