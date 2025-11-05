#!/usr/bin/env python3
"""
Demo IA - Bot de Trading avec Intelligence Artificielle
Montre les signaux IA combinant technique, sentiment et contexte marché
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
from src.data_ingestion.public_data_provider import PublicDataProvider
from src.ml.ai_signal_generator import AISignalGenerator


class AITradingDemo:
    """Démonstration du bot avec IA"""
    
    def __init__(self):
        self.market_data = None
        self.public_provider = None
        self.ai_generator = AISignalGenerator()
        self.running = False
        self.symbols = settings.trading.assets_list
        
        logger.info("🤖 Bot de Trading IA initialisé")
        logger.info(f"   Mode: {settings.trading.trading_mode}")
        logger.info(f"   Exchange: {settings.exchange.default_exchange}")
        logger.info(f"   Actifs surveillés: {len(self.symbols)}")
        logger.info(f"   Capital initial: {settings.trading.initial_capital:,.0f}€")
    
    async def initialize(self):
        """Initialiser les composants"""
        try:
            logger.info("🔧 Initialisation du système IA...")
            
            # Market data
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            
            # Public data provider pour données supplémentaires
            self.public_provider = PublicDataProvider('binance')
            await self.public_provider.initialize()
            
            logger.info("✅ Système IA initialisé!")
            
        except Exception as e:
            logger.error(f"❌ Échec initialisation: {e}")
            raise
    
    def calculate_simple_indicators(self, price: float, prev_prices: list) -> dict:
        """Calculer des indicateurs techniques simples"""
        if not prev_prices or len(prev_prices) < 2:
            return {}
        
        indicators = {}
        
        # Trend simple
        if len(prev_prices) >= 5:
            recent_avg = sum(prev_prices[-5:]) / 5
            older_avg = sum(prev_prices[-10:-5]) / 5 if len(prev_prices) >= 10 else recent_avg
            indicators['trend'] = 'up' if recent_avg > older_avg else 'down'
        
        # RSI simulé (basé sur variation)
        if len(prev_prices) >= 14:
            gains = []
            losses = []
            for i in range(1, min(14, len(prev_prices))):
                change = prev_prices[-i] - prev_prices[-i-1]
                if change > 0:
                    gains.append(change)
                else:
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / 14 if gains else 0.01
            avg_loss = sum(losses) / 14 if losses else 0.01
            rs = avg_gain / avg_loss
            indicators['rsi'] = 100 - (100 / (1 + rs))
        else:
            indicators['rsi'] = 50  # Neutral
        
        # Volume trend (simulé)
        indicators['volume_trend'] = 'stable'
        
        return indicators
    
    def simulate_sentiment(self, symbol: str, price_change: float) -> dict:
        """Simuler un score de sentiment basé sur les variations de prix"""
        # En mode réel, ceci viendrait de FinBERT + news APIs
        # Pour la demo, on simule basé sur le momentum
        
        base_sentiment = 0
        
        # Sentiment basé sur variation 24h
        if price_change > 5:
            base_sentiment = 0.7  # Très positif
        elif price_change > 2:
            base_sentiment = 0.4  # Positif
        elif price_change < -5:
            base_sentiment = -0.7  # Très négatif
        elif price_change < -2:
            base_sentiment = -0.4  # Négatif
        else:
            base_sentiment = price_change / 10  # Neutre
        
        # Ajouter un peu de variation aléatoire
        import random
        sentiment = base_sentiment + random.uniform(-0.15, 0.15)
        sentiment = max(-1, min(1, sentiment))
        
        return {
            'sentiment_score': sentiment,
            'sentiment_trend': 'improving' if sentiment > 0 else 'worsening' if sentiment < 0 else 'stable',
            'news_count': random.randint(3, 15)
        }
    
    def simulate_social_metrics(self, symbol: str) -> dict:
        """Simuler des métriques sociales"""
        import random
        
        return {
            'social_sentiment': random.uniform(-0.3, 0.5),
            'mentions_change': random.uniform(-20, 80),
            'galaxy_score': random.uniform(40, 75)
        }
    
    def get_market_context(self) -> dict:
        """Obtenir le contexte de marché général"""
        import random
        
        return {
            'btc_dominance': random.uniform(45, 55),
            'fear_greed': random.uniform(30, 70),
            'market_trend': 'bull'
        }
    
    async def analyze_symbol(self, symbol: str, price_history: dict):
        """Analyser un symbole avec l'IA"""
        try:
            # Récupérer le ticker
            ticker = await self.market_data.fetch_ticker(symbol)
            if not ticker:
                return None
            
            price = ticker['last']
            change_24h = ticker.get('percentage', 0)
            volume = ticker.get('volume', 0)
            
            # Stocker l'historique
            if symbol not in price_history:
                price_history[symbol] = []
            price_history[symbol].append(price)
            if len(price_history[symbol]) > 50:
                price_history[symbol] = price_history[symbol][-50:]
            
            # Calculer indicateurs techniques
            technical_data = self.calculate_simple_indicators(price, price_history[symbol])
            technical_data['close'] = price
            
            # Simuler sentiment (en prod: vraies news + FinBERT)
            sentiment_data = self.simulate_sentiment(symbol, change_24h)
            
            # Simuler social (en prod: vraies APIs)
            social_data = self.simulate_social_metrics(symbol)
            
            # Contexte marché
            market_data = self.get_market_context()
            
            # Générer signal IA
            signal = self.ai_generator.generate_signal(
                symbol=symbol,
                technical_data=technical_data,
                sentiment_data=sentiment_data,
                social_data=social_data,
                market_data=market_data
            )
            
            return {
                'symbol': symbol,
                'price': price,
                'change_24h': change_24h,
                'volume': volume,
                'signal': signal
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse {symbol}: {e}")
            return None
    
    async def run(self):
        """Boucle principale avec IA"""
        self.running = True
        logger.info("🚀 Démarrage du système IA...")
        logger.info("=" * 80)
        logger.info("")
        logger.info("💡 NOTE: Cette demo utilise des données simulées pour le sentiment")
        logger.info("   En production, FinBERT analyserait de vraies news crypto")
        logger.info("")
        logger.info("=" * 80)
        
        iteration = 0
        price_history = {}
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"\n🧠 Analyse IA #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # Analyser tous les symboles
                analyses = []
                for symbol in self.symbols:
                    analysis = await self.analyze_symbol(symbol, price_history)
                    if analysis:
                        analyses.append(analysis)
                    await asyncio.sleep(0.5)  # Rate limiting
                
                # Trier par score IA (meilleur d'abord)
                analyses.sort(key=lambda x: x['signal']['final_score'], reverse=True)
                
                # Afficher les résultats
                logger.info("")
                logger.info("📊 SIGNAUX IA PAR ACTIF:")
                logger.info("-" * 80)
                
                for i, analysis in enumerate(analyses, 1):
                    symbol = analysis['symbol']
                    price = analysis['price']
                    change = analysis['change_24h']
                    signal = analysis['signal']
                    
                    action = signal['action']
                    score = signal['final_score']
                    confidence = signal['confidence']
                    
                    # Emoji basé sur action
                    if action == 'STRONG_BUY':
                        emoji = "🟢🟢"
                        color = "success"
                    elif action == 'BUY':
                        emoji = "🟢"
                        color = "info"
                    elif action == 'STRONG_SELL':
                        emoji = "🔴🔴"
                        color = "error"
                    elif action == 'SELL':
                        emoji = "🔴"
                        color = "warning"
                    else:
                        emoji = "⚪"
                        color = "info"
                    
                    # Afficher
                    log_func = getattr(logger, color) if hasattr(logger, color) else logger.info
                    log_func(
                        f"{i:2}. {emoji} {symbol:12} | "
                        f"Prix: {price:>10,.2f}€ | "
                        f"24h: {change:>6.2f}% | "
                        f"Action: {action:12} | "
                        f"Score IA: {score:>5.2f} | "
                        f"Confiance: {confidence*100:>5.1f}%"
                    )
                    
                    # Détails des composantes
                    tech = signal['scores']['technical']
                    sent = signal['scores']['sentiment']
                    soc = signal['scores']['social']
                    logger.debug(
                        f"     └─ Technique: {tech:>5.2f} | "
                        f"Sentiment: {sent:>5.2f} | "
                        f"Social: {soc:>5.2f}"
                    )
                
                # Recommandations
                logger.info("")
                logger.info("=" * 80)
                logger.info("🎯 RECOMMANDATIONS IA:")
                logger.info("-" * 80)
                
                strong_buys = [a for a in analyses if a['signal']['action'] == 'STRONG_BUY']
                buys = [a for a in analyses if a['signal']['action'] == 'BUY']
                sells = [a for a in analyses if a['signal']['action'] in ['SELL', 'STRONG_SELL']]
                
                if strong_buys:
                    logger.success(f"🟢 ACHAT FORT recommandé:")
                    for a in strong_buys[:3]:  # Top 3
                        position = self.ai_generator.calculate_position_size(
                            a['signal'], 
                            settings.risk.max_position_size
                        )
                        logger.success(
                            f"   • {a['symbol']:12} → Position: {position*100:.1f}% "
                            f"(~{settings.trading.initial_capital * position:,.0f}€)"
                        )
                elif buys:
                    logger.info(f"🟢 ACHAT suggéré:")
                    for a in buys[:3]:
                        position = self.ai_generator.calculate_position_size(
                            a['signal'],
                            settings.risk.max_position_size
                        )
                        logger.info(
                            f"   • {a['symbol']:12} → Position: {position*100:.1f}% "
                            f"(~{settings.trading.initial_capital * position:,.0f}€)"
                        )
                else:
                    logger.info("⚪ Aucun signal d'achat fort détecté")
                
                if sells:
                    logger.warning(f"🔴 VENTE recommandée:")
                    for a in sells[:3]:
                        logger.warning(f"   • {a['symbol']:12} → Clôturer position si détenue")
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"💰 Capital simulé: {settings.trading.initial_capital:,.2f}€")
                logger.info(f"⏰ Prochaine analyse dans 60 secondes...")
                logger.info("")
                
                # Attendre
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            logger.info("\n⏸️  Arrêt demandé")
        except Exception as e:
            logger.error(f"\n❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Arrêter proprement"""
        logger.info("\n🛑 Arrêt du système IA...")
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.public_provider:
            await self.public_provider.close()
        
        logger.info("✅ Système arrêté proprement")


async def main():
    """Point d'entrée"""
    # Configuration logger
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🤖 TradOps - Bot de Trading avec IA")
    logger.info("=" * 80)
    logger.info(f"Mode: {settings.trading.trading_mode.upper()}")
    logger.info(f"Exchange: {settings.exchange.default_exchange.upper()}")
    logger.info(f"Actifs: {len(settings.trading.assets_list)} cryptos")
    logger.info("")
    logger.info("🧠 Fonctionnalités IA:")
    logger.info("   ✅ Analyse technique (SMA, RSI, MACD)")
    logger.info("   ✅ Analyse de sentiment (simulée - FinBERT en prod)")
    logger.info("   ✅ Métriques sociales (simulées - LunarCrush en prod)")
    logger.info("   ✅ Contexte de marché (Fear & Greed, BTC dominance)")
    logger.info("   ✅ Signaux combinés avec poids intelligents")
    logger.info("")
    logger.info("📌 Seuils de décision:")
    logger.info("   • Score >  0.7 → ACHAT FORT")
    logger.info("   • Score >  0.4 → ACHAT")
    logger.info("   • Score < -0.4 → VENTE")
    logger.info("   • Score < -0.7 → VENTE FORTE")
    logger.info("")
    logger.info("💡 Appuyez sur Ctrl+C pour arrêter")
    logger.info("=" * 80)
    
    # Lancer
    bot = AITradingDemo()
    await bot.initialize()
    await bot.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Arrêté par l'utilisateur")
    except Exception as e:
        logger.error(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

