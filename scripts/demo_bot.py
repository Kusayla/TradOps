#!/usr/bin/env python3
"""
Demo simplifié du bot de trading
Montre les fonctionnalités principales sans toutes les dépendances
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

class SimpleTradingBot:
    """Version simplifiée du bot pour démonstration"""
    
    def __init__(self):
        self.market_data = None
        self.running = False
        self.symbols = settings.trading.assets_list
        
        logger.info("🤖 Bot de trading initialisé")
        logger.info(f"   Mode: {settings.trading.trading_mode}")
        logger.info(f"   Exchange: {settings.exchange.default_exchange}")
        logger.info(f"   Actifs: {', '.join(self.symbols)}")
        logger.info(f"   Capital initial: {settings.trading.initial_capital}€")
    
    async def initialize(self):
        """Initialiser les composants"""
        try:
            logger.info("🔧 Initialisation du bot...")
            
            # Initialiser l'ingestion de données
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            
            logger.info("✅ Bot initialisé avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Échec de l'initialisation: {e}")
            raise
    
    async def run(self):
        """Boucle principale du bot"""
        self.running = True
        logger.info("🚀 Démarrage du bot...")
        logger.info("=" * 60)
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"\n📊 Itération #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("-" * 60)
                
                # Récupérer les prix pour tous les symboles
                tickers = await self.market_data.fetch_multiple_tickers(self.symbols)
                
                for symbol, ticker in tickers.items():
                    if ticker:
                        price = ticker['last']
                        change = ticker.get('percentage', 0)
                        volume = ticker.get('volume', 0)
                        source = ticker.get('source', 'unknown')
                        
                        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                        
                        logger.info(
                            f"{change_emoji} {symbol:12} | "
                            f"Prix: {price:>10,.2f}€ | "
                            f"Change 24h: {change:>6.2f}% | "
                            f"Volume: {volume:>10,.0f} | "
                            f"Source: {source}"
                        )
                        
                        # Simulation d'analyse de signal (très simple)
                        if change > 5:
                            logger.success(f"   🟢 Signal ACHAT potentiel pour {symbol} (hausse forte)")
                        elif change < -5:
                            logger.warning(f"   🔴 Signal VENTE potentiel pour {symbol} (baisse forte)")
                        else:
                            logger.info(f"   ⚪ Pas de signal fort pour {symbol}")
                
                logger.info("-" * 60)
                logger.info(f"💰 Capital simulé: {settings.trading.initial_capital:,.2f}€")
                logger.info(f"⏰ Prochaine mise à jour dans 30 secondes...")
                
                # Attendre 30 secondes
                await asyncio.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("\n⏸️  Arrêt demandé par l'utilisateur")
        except Exception as e:
            logger.error(f"\n❌ Erreur dans la boucle principale: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Arrêter proprement le bot"""
        logger.info("\n🛑 Arrêt du bot...")
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        
        logger.info("✅ Bot arrêté proprement")


async def main():
    """Point d'entrée principal"""
    # Configuration du logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 60)
    logger.info("🤖 TradOps - Bot de Trading Crypto")
    logger.info("=" * 60)
    logger.info(f"Mode: {settings.trading.trading_mode.upper()}")
    logger.info(f"Exchange: {settings.exchange.default_exchange.upper()}")
    logger.info(f"Symboles: {', '.join(settings.trading.assets_list)}")
    logger.info("=" * 60)
    logger.info("")
    logger.info("💡 Conseils:")
    logger.info("   - Ceci est une DÉMONSTRATION en mode PUBLIC")
    logger.info("   - Aucun argent réel n'est utilisé")
    logger.info("   - Les signaux sont très simplifiés (pour démo)")
    logger.info("   - Appuyez sur Ctrl+C pour arrêter")
    logger.info("")
    logger.info("=" * 60)
    
    # Créer et lancer le bot
    bot = SimpleTradingBot()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Bot arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

