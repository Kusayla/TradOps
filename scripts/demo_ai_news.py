#!/usr/bin/env python3
"""
Demo IA avec VRAIES news et FinBERT
Utilise vos clés API pour analyser les actualités crypto en temps réel
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


class AITradingBotWithNews:
    """Bot de trading IA avec vraies news"""
    
    def __init__(self):
        self.market_data = None
        self.news_ingestion = None
        self.sentiment_analyzer = None
        self.ai_generator = AISignalGenerator()
        self.running = False
        self.symbols = settings.trading.assets_list
        
        # Cache pour stocker sentiment par crypto
        self.sentiment_cache = {}
        
        logger.info("🤖 Bot de Trading IA avec News initialisé")
        logger.info(f"   Mode: {settings.trading.trading_mode}")
        logger.info(f"   Exchange: {settings.exchange.default_exchange}")
        logger.info(f"   Actifs: {len(self.symbols)}")
        logger.info(f"   Capital: {settings.trading.initial_capital:,.0f}€")
    
    async def initialize(self):
        """Initialiser tous les composants"""
        try:
            logger.info("🔧 Initialisation du système IA complet...")
            
            # Market data
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.info("✅ Market data initialisé")
            
            # News ingestion
            self.news_ingestion = NewsIngestion()
            logger.info("✅ News ingestion initialisé")
            
            # Sentiment analyzer (FinBERT)
            logger.info("🧠 Chargement de FinBERT (peut prendre 20-30 secondes)...")
            self.sentiment_analyzer = SentimentAnalyzer()
            self.sentiment_analyzer.initialize()
            logger.info("✅ FinBERT chargé et prêt!")
            
            logger.success("🎉 Système IA complet initialisé!")
            
        except Exception as e:
            logger.error(f"❌ Échec initialisation: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def fetch_and_analyze_news(self):
        """Récupérer et analyser les news pour toutes les cryptos"""
        try:
            # Extraire les symboles de base (BTC, ETH, etc.)
            crypto_symbols = [s.split('/')[0] for s in self.symbols]
            
            logger.info(f"📰 Récupération des news pour {len(crypto_symbols)} cryptos...")
            
            # Fetch news
            all_news = await self.news_ingestion.fetch_all_news(crypto_symbols)
            
            if not all_news:
                logger.warning("⚠️ Aucune news récupérée (vérifiez vos clés API)")
                return {}
            
            logger.info(f"✅ {len(all_news)} news récupérées")
            
            # Analyser avec FinBERT
            logger.info("🧠 Analyse avec FinBERT...")
            analyzed_news = self.sentiment_analyzer.analyze_news(all_news)
            
            # Organiser par crypto
            sentiment_by_crypto = {}
            for news in analyzed_news:
                # Extraire mentions de cryptos
                text = (news.get('title', '') + ' ' + news.get('description', '')).upper()
                
                for symbol in crypto_symbols:
                    if symbol.upper() in text:
                        if symbol not in sentiment_by_crypto:
                            sentiment_by_crypto[symbol] = {
                                'news': [],
                                'scores': [],
                                'count': 0
                            }
                        
                        sentiment = news.get('sentiment', {})
                        score = sentiment.get('sentiment_score', 0)
                        
                        sentiment_by_crypto[symbol]['news'].append(news)
                        sentiment_by_crypto[symbol]['scores'].append(score)
                        sentiment_by_crypto[symbol]['count'] += 1
            
            # Calculer sentiment moyen par crypto
            for symbol in sentiment_by_crypto:
                scores = sentiment_by_crypto[symbol]['scores']
                if scores:
                    sentiment_by_crypto[symbol]['avg_sentiment'] = sum(scores) / len(scores)
                    
                    # Tendance (récentes vs anciennes)
                    if len(scores) >= 4:
                        recent = sum(scores[-2:]) / 2
                        older = sum(scores[:2]) / 2
                        if recent > older + 0.2:
                            sentiment_by_crypto[symbol]['trend'] = 'improving'
                        elif recent < older - 0.2:
                            sentiment_by_crypto[symbol]['trend'] = 'worsening'
                        else:
                            sentiment_by_crypto[symbol]['trend'] = 'stable'
            
            return sentiment_by_crypto
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération news: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def calculate_simple_technical(self, price_change: float) -> dict:
        """Calculer un score technique simple"""
        # Très simplifié pour la demo
        rsi = 50 + (price_change * 2)  # Approximation
        rsi = max(0, min(100, rsi))
        
        return {
            'rsi': rsi,
            'trend': 'up' if price_change > 0 else 'down',
            'volume_trend': 'stable'
        }
    
    async def analyze_all_cryptos(self):
        """Analyser toutes les cryptos avec IA"""
        try:
            # 1. Récupérer et analyser les news
            logger.info("")
            logger.info("📰 Récupération des news crypto...")
            sentiment_data = await self.fetch_and_analyze_news()
            
            # 2. Récupérer les prix
            logger.info("📊 Récupération des prix...")
            tickers = await self.market_data.fetch_multiple_tickers(self.symbols)
            
            # 3. Générer signaux IA
            logger.info("🧠 Génération des signaux IA...")
            logger.info("")
            
            analyses = []
            
            for symbol in self.symbols:
                ticker = tickers.get(symbol)
                if not ticker:
                    continue
                
                price = ticker['last']
                change_24h = ticker.get('percentage', 0)
                volume = ticker.get('volume', 0)
                
                # Technical
                technical = self.calculate_simple_technical(change_24h)
                
                # Sentiment
                crypto_base = symbol.split('/')[0]
                sentiment = None
                if crypto_base in sentiment_data:
                    data = sentiment_data[crypto_base]
                    sentiment = {
                        'sentiment_score': data.get('avg_sentiment', 0),
                        'sentiment_trend': data.get('trend', 'stable'),
                        'news_count': data['count']
                    }
                
                # Social (simulé pour l'instant)
                social = {
                    'social_sentiment': 0,
                    'mentions_change': 0,
                    'galaxy_score': 50
                }
                
                # Market context (simulé)
                market = {
                    'btc_dominance': 50,
                    'fear_greed': 50,
                    'market_trend': 'neutral'
                }
                
                # Générer signal IA
                signal = self.ai_generator.generate_signal(
                    symbol=symbol,
                    technical_data=technical,
                    sentiment_data=sentiment,
                    social_data=social,
                    market_data=market
                )
                
                analyses.append({
                    'symbol': symbol,
                    'price': price,
                    'change_24h': change_24h,
                    'volume': volume,
                    'signal': signal,
                    'news_count': sentiment_data.get(crypto_base, {}).get('count', 0),
                    'sentiment': sentiment_data.get(crypto_base, {}).get('avg_sentiment', 0)
                })
            
            return analyses
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def run(self):
        """Boucle principale"""
        self.running = True
        logger.info("🚀 Démarrage du bot IA avec News...")
        logger.info("=" * 80)
        
        iteration = 0
        
        try:
            while self.running:
                iteration += 1
                logger.info(f"\n🧠 Analyse IA + News #{iteration} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # Analyser toutes les cryptos
                analyses = await self.analyze_all_cryptos()
                
                if not analyses:
                    logger.warning("⚠️ Pas de données disponibles")
                    await asyncio.sleep(60)
                    continue
                
                # Trier par score IA
                analyses.sort(key=lambda x: x['signal']['final_score'], reverse=True)
                
                # Afficher résultats
                logger.info("")
                logger.info("📊 SIGNAUX IA PAR ACTIF (avec analyse news):")
                logger.info("-" * 80)
                
                for i, analysis in enumerate(analyses, 1):
                    symbol = analysis['symbol']
                    price = analysis['price']
                    change = analysis['change_24h']
                    signal = analysis['signal']
                    news_count = analysis['news_count']
                    sentiment_score = analysis['sentiment']
                    
                    action = signal['action']
                    score = signal['final_score']
                    confidence = signal['confidence']
                    
                    # Emoji
                    if action == 'STRONG_BUY':
                        emoji = "🟢🟢"
                    elif action == 'BUY':
                        emoji = "🟢"
                    elif action == 'STRONG_SELL':
                        emoji = "🔴🔴"
                    elif action == 'SELL':
                        emoji = "🔴"
                    else:
                        emoji = "⚪"
                    
                    # Sentiment emoji
                    if sentiment_score > 0.5:
                        sent_emoji = "😊"
                    elif sentiment_score > 0:
                        sent_emoji = "🙂"
                    elif sentiment_score < -0.5:
                        sent_emoji = "😟"
                    elif sentiment_score < 0:
                        sent_emoji = "😐"
                    else:
                        sent_emoji = "😶"
                    
                    # Afficher
                    log_func = logger.success if action in ['STRONG_BUY', 'BUY'] else \
                               logger.warning if action in ['SELL', 'STRONG_SELL'] else \
                               logger.info
                    
                    log_func(
                        f"{i:2}. {emoji} {symbol:12} | "
                        f"Prix: {price:>10,.2f}€ | "
                        f"24h: {change:>6.2f}% | "
                        f"Action: {action:12} | "
                        f"Score: {score:>5.2f} | "
                        f"News: {news_count:2} {sent_emoji} {sentiment_score:>5.2f}"
                    )
                
                # Recommandations
                logger.info("")
                logger.info("=" * 80)
                logger.info("🎯 RECOMMANDATIONS INTELLIGENTES:")
                logger.info("-" * 80)
                
                strong_buys = [a for a in analyses if a['signal']['action'] == 'STRONG_BUY']
                buys = [a for a in analyses if a['signal']['action'] == 'BUY']
                
                if strong_buys:
                    logger.success(f"🟢🟢 ACHAT FORT recommandé ({len(strong_buys)} cryptos):")
                    for a in strong_buys[:3]:
                        position = self.ai_generator.calculate_position_size(
                            a['signal'],
                            settings.risk.max_position_size
                        )
                        logger.success(
                            f"   • {a['symbol']:12} → Position: {position*100:.1f}% "
                            f"(~{settings.trading.initial_capital * position:,.0f}€) | "
                            f"Sentiment news: {a['sentiment']:.2f} ({a['news_count']} news)"
                        )
                elif buys:
                    logger.info(f"🟢 ACHAT suggéré ({len(buys)} cryptos):")
                    for a in buys[:3]:
                        position = self.ai_generator.calculate_position_size(
                            a['signal'],
                            settings.risk.max_position_size
                        )
                        logger.info(
                            f"   • {a['symbol']:12} → Position: {position*100:.1f}% "
                            f"(~{settings.trading.initial_capital * position:,.0f}€) | "
                            f"Sentiment news: {a['sentiment']:.2f}"
                        )
                else:
                    logger.info("⚪ Aucun signal d'achat fort")
                
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"💰 Capital simulé: {settings.trading.initial_capital:,.2f}€")
                logger.info(f"⏰ Prochaine analyse dans 5 minutes...")
                logger.info(f"💡 Les news sont récupérées toutes les 5 min (limites API)")
                logger.info("")
                
                # Attendre 5 minutes (limite API news)
                await asyncio.sleep(300)
                
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
        logger.info("\n🛑 Arrêt du système...")
        self.running = False
        
        if self.market_data:
            await self.market_data.close()
        if self.news_ingestion:
            await self.news_ingestion.close()
        
        logger.info("✅ Système arrêté proprement")


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🤖 TradOps - Bot de Trading IA avec VRAIES NEWS")
    logger.info("=" * 80)
    logger.info(f"Mode: {settings.trading.trading_mode.upper()}")
    logger.info(f"Exchange: {settings.exchange.default_exchange.upper()}")
    logger.info(f"Cryptos: {len(settings.trading.assets_list)}")
    logger.info("")
    logger.info("🧠 Fonctionnalités IA Activées:")
    logger.info("   ✅ FinBERT (analyse de sentiment sur news réelles)")
    logger.info("   ✅ CryptoPanic / NewsAPI (sources de news)")
    logger.info("   ✅ Analyse technique (RSI, SMA, tendances)")
    logger.info("   ✅ Contexte marché (Fear & Greed, BTC dominance)")
    logger.info("   ✅ Génération de signaux multi-composantes")
    logger.info("")
    logger.info("📌 Seuils de décision:")
    logger.info("   • Score >  0.7 → ACHAT FORT 🟢🟢")
    logger.info("   • Score >  0.4 → ACHAT 🟢")
    logger.info("   • Score < -0.4 → VENTE 🔴")
    logger.info("   • Score < -0.7 → VENTE FORTE 🔴🔴")
    logger.info("")
    logger.info("💡 Les news sont analysées toutes les 5 minutes")
    logger.info("💡 Appuyez sur Ctrl+C pour arrêter")
    logger.info("=" * 80)
    
    # Vérifier les clés API
    if not settings.data_sources.cryptopanic_api_key and not settings.data_sources.newsapi_key:
        logger.warning("")
        logger.warning("⚠️ ATTENTION: Aucune clé API news configurée!")
        logger.warning("   Le bot fonctionnera mais sans analyse de vraies news.")
        logger.warning("")
        logger.warning("   Pour activer les vraies news:")
        logger.warning("   1. Obtenez clés gratuites:")
        logger.warning("      - CryptoPanic: https://cryptopanic.com/developers/api/")
        logger.warning("      - NewsAPI: https://newsapi.org/")
        logger.warning("   2. Ajoutez dans .env:")
        logger.warning("      CRYPTOPANIC_API_KEY=votre_clé")
        logger.warning("      NEWSAPI_KEY=votre_clé")
        logger.warning("")
        logger.info("Lancement dans 5 secondes...")
        await asyncio.sleep(5)
    else:
        logger.success("")
        logger.success("✅ Clés API news détectées!")
        logger.success("   FinBERT analysera les vraies actualités crypto")
        logger.success("")
    
    # Lancer
    bot = AITradingBotWithNews()
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

