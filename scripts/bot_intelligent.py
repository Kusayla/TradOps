#!/usr/bin/env python3
"""
BOT INTELLIGENT - Trading avec LLM qui Réfléchit
Le LLM analyse, raisonne et explique chaque décision
"""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.data_ingestion.market_data import MarketDataIngestion
from src.data_ingestion.news_ingestion import NewsIngestion
from src.ml.llm_analyzer import LLMAnalyzer
from src.execution.order_executor import OrderExecutor
from src.storage.redis_client import RedisClient


class IntelligentTradingBot:
    """Bot de trading avec IA qui réfléchit vraiment"""
    
    def __init__(self):
        self.market_data = None
        self.news_ingestion = None
        self.llm_analyzer = None
        self.order_executor = None
        self.redis_client = RedisClient()
        self.running = False
        self.capital = settings.trading.initial_capital
        self.current_position = None  # {symbol, entry_price, size, entry_time}
        
        logger.info("🧠 Bot Intelligent initialisé")
    
    async def initialize(self):
        """Initialiser tous les composants"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 Initialisation Système Intelligent...")
            logger.info("=" * 80)
            
            # 1. Market data
            logger.info("📊 Market Data...")
            self.market_data = MarketDataIngestion()
            await self.market_data.initialize()
            logger.success("✅ Market Data prêt")
            
            # 2. News
            logger.info("📰 News Ingestion...")
            self.news_ingestion = NewsIngestion()
            logger.success("✅ News prêt")
            
            # 3. LLM (le cerveau)
            logger.info("🧠 Chargement du LLM (Llama 3.1)...")
            self.llm_analyzer = LLMAnalyzer()
            logger.success("✅ LLM prêt (Ollama)")
            
            # 4. Order Executor
            logger.info("💰 Order Executor...")
            self.order_executor = OrderExecutor()
            await self.order_executor.initialize()
            logger.success("✅ Executor prêt")
            
            logger.info("")
            logger.success("🎉 SYSTÈME INTELLIGENT 100% OPÉRATIONNEL!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            raise
    
    async def analyze_crypto_with_llm(self, symbol: str, price: float, news_list: list) -> dict:
        """
        Demander au LLM d'analyser une crypto en profondeur
        
        Returns:
            {
                'decision': 'BUY'|'SELL'|'HOLD',
                'confidence': 0.0-1.0,
                'explanation': "...",
                'position_size': % du capital
            }
        """
        # Préparer le contexte pour le LLM
        news_summary = "\n".join([
            f"- {news.get('title', 'No title')}"
            for news in news_list[:3]  # Top 3 news (économie tokens)
        ])
        
        if not news_summary:
            news_summary = "Pas de news"
        
        # Prompt optimisé selon si on a une position ou non
        if self.current_position and self.current_position['symbol'] == symbol:
            # EN POSITION : Décider si on SORT ou HOLD
            entry = self.current_position['entry_price']
            pnl = ((price - entry) / entry) * 100
            
            prompt = f"""{symbol} @ {price:.2f}€
Entrée: {entry:.2f}€ | PnL: {pnl:+.1f}%
NEWS: {news_summary}

EN POSITION. Sortir ou hold?
DÉCISION: VENDRE/HOLD
CONFIANCE: [0-100]%
RAISON: [1 phrase]"""
        else:
            # PAS DE POSITION : Décider si on ACHÈTE
            prompt = f"""{symbol} @ {price:.2f}€
Capital: {self.capital:.2f}€
NEWS: {news_summary}

Acheter maintenant?
DÉCISION: ACHETER/ATTENDRE
CONFIANCE: [0-100]%
TAILLE: [10-80]%
RAISON: [1 phrase]"""

        try:
            # Appeler le LLM (auto-détecte OpenAI ou Ollama)
            if self.llm_analyzer.provider == "openai":
                response = await self.llm_analyzer._call_openai(prompt)
            elif self.llm_analyzer.provider == "anthropic":
                response = await self.llm_analyzer._call_anthropic(prompt)
            else:
                response = await self.llm_analyzer._call_ollama(prompt)
            
            # Parser la réponse
            decision = "HOLD"
            confidence = 0.5
            position_size = 0
            explanation = response
            
            lines = response.upper().split('\n')
            for line in lines:
                if 'DÉCISION' in line or 'DECISION' in line:
                    if 'ACHETER' in line or 'BUY' in line:
                        decision = "BUY"
                    elif 'VENDRE' in line or 'SELL' in line:
                        decision = "SELL"
                    else:
                        decision = "HOLD"
                
                if 'CONFIANCE' in line or 'CONFIDENCE' in line:
                    # Extraire le nombre
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        confidence = int(match.group(1)) / 100
                
                if 'TAILLE' in line or 'SIZE' in line:
                    import re
                    match = re.search(r'(\d+)', line)
                    if match:
                        position_size = int(match.group(1)) / 100
                
                if 'RAISON' in line or 'REASON' in line:
                    explanation = line.split(':', 1)[1].strip() if ':' in line else response
            
            return {
                'decision': decision,
                'confidence': confidence,
                'position_size': position_size,
                'explanation': explanation,
                'raw_response': response
            }
            
        except Exception as e:
            logger.error(f"Erreur LLM: {e}")
            return {
                'decision': 'HOLD',
                'confidence': 0.0,
                'position_size': 0,
                'explanation': f"Erreur d'analyse: {e}",
                'raw_response': str(e)
            }
    
    async def execute_trade(self, symbol: str, decision: str, position_size: float, explanation: str):
        """Exécuter un trade basé sur la décision du LLM"""
        try:
            if decision == "BUY" and position_size > 0:
                amount_eur = self.capital * position_size
                
                # Minimum Kraken
                if amount_eur < 10:
                    logger.warning(f"⚠️ Montant trop petit: {amount_eur:.2f}€ < 10€ minimum")
                    return
                
                logger.info("")
                logger.info("=" * 80)
                logger.success(f"🤖 DÉCISION DU LLM: ACHETER {symbol}")
                logger.info(f"💰 Montant: {amount_eur:.2f}€ ({position_size*100:.0f}% du capital)")
                logger.info(f"🧠 Raison: {explanation}")
                logger.info("=" * 80)
                
                # Exécuter l'ordre
                current_price = await self.market_data.fetch_ticker(symbol)
                quantity = amount_eur / current_price['last']
                
                order = await self.order_executor.place_market_order(
                    symbol=symbol,
                    side='buy',
                    amount=quantity
                )
                
                if order:
                    logger.success(f"✅ ORDRE EXÉCUTÉ: {order}")
                    self.capital -= amount_eur
                    
                    # Sauvegarder la position active
                    self.current_position = {
                        'symbol': symbol,
                        'entry_price': current_price['last'],
                        'size': quantity,
                        'entry_time': datetime.now().isoformat(),
                        'amount_eur': amount_eur
                    }
                    
                    # Sauvegarder dans Redis
                    self.redis_client.set("current_capital", self.capital)
                    self.redis_client.set("current_position", json.dumps(self.current_position))
                    
                    logger.info("")
                    logger.success(f"📌 Position ouverte: {symbol}")
                    logger.info(f"   Taille: {quantity:.6f}")
                    logger.info(f"   Prix entrée: {current_price['last']:.2f}€")
                    logger.info(f"   Montant: {amount_eur:.2f}€")
                else:
                    logger.error("❌ Échec de l'ordre")
            
            elif decision == "SELL" and self.current_position:
                # Fermer la position
                logger.info("")
                logger.info("=" * 80)
                logger.warning(f"🚪 DÉCISION DU LLM: SORTIR de {symbol}")
                logger.info(f"🧠 Raison: {explanation}")
                logger.info("=" * 80)
                
                # Récupérer le prix actuel
                current_price_data = await self.market_data.fetch_ticker(symbol)
                current_price = current_price_data['last']
                
                # Calculer le PnL
                entry = self.current_position['entry_price']
                pnl_pct = ((current_price - entry) / entry) * 100
                pnl_eur = (current_price - entry) * self.current_position['size']
                
                logger.info(f"💰 Prix entrée: {entry:.2f}€")
                logger.info(f"💰 Prix sortie: {current_price:.2f}€")
                logger.info(f"📊 PnL: {pnl_eur:+.2f}€ ({pnl_pct:+.1f}%)")
                
                # Vendre
                order = await self.order_executor.place_market_order(
                    symbol=symbol,
                    side='sell',
                    amount=self.current_position['size']
                )
                
                if order:
                    # Récupérer le capital
                    self.capital += self.current_position['amount_eur'] + pnl_eur
                    
                    logger.success(f"✅ POSITION FERMÉE")
                    logger.info(f"💰 Nouveau capital: {self.capital:.2f}€")
                    
                    # Supprimer la position
                    self.current_position = None
                    self.redis_client.delete("current_position")
                    self.redis_client.set("current_capital", self.capital)
                else:
                    logger.error("❌ Échec de la vente")
            
            elif decision == "HOLD":
                if self.current_position and symbol == self.current_position['symbol']:
                    logger.info(f"🔒 {symbol}: LLM recommande de HOLD (garder la position)")
                    logger.info(f"   Raison: {explanation}")
                else:
                    logger.info(f"⚪ {symbol}: LLM recommande d'ATTENDRE")
                    logger.info(f"   Raison: {explanation}")
        
        except Exception as e:
            logger.error(f"Erreur exécution trade: {e}")
    
    async def run(self):
        """Boucle principale du bot"""
        self.running = True
        cycle = 0
        
        # Restaurer la position depuis Redis si elle existe
        try:
            position_json = self.redis_client.get("current_position")
            if position_json:
                self.current_position = json.loads(position_json)
                logger.info(f"📌 Position restaurée: {self.current_position['symbol']}")
            
            saved_capital = self.redis_client.get("current_capital")
            if saved_capital:
                self.capital = float(saved_capital)
        except Exception as e:
            logger.warning(f"Pas de position sauvegardée: {e}")
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE BOT INTELLIGENT")
        logger.info("=" * 80)
        logger.info("")
        logger.info("🧠 LE LLM VA:")
        logger.info("   1. Récupérer les news sur chaque crypto")
        logger.info("   2. RÉFLÉCHIR sur chaque opportunité")
        logger.info("   3. EXPLIQUER sa décision")
        logger.info("   4. Trader UNIQUEMENT si confiant")
        logger.info("")
        logger.info("💡 LOGIQUE OPTIMISÉE:")
        logger.info("   • Sans position → Scan 11 cryptos pour ACHETER")
        logger.info("   • Avec position → Analyse UNIQUEMENT cette crypto (SORTIR/HOLD)")
        logger.info("   • Cycle toutes les 5 minutes")
        logger.info("=" * 80)
        logger.info("")
        
        try:
            while self.running:
                cycle += 1
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"🔄 CYCLE #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info("=" * 80)
                
                # LOGIQUE OPTIMISÉE : Si en position, analyser UNIQUEMENT cette crypto !
                if self.current_position:
                    logger.info(f"📌 Position active: {self.current_position['symbol']}")
                    logger.info(f"💰 Valeur: {self.current_position['size']:.4f} × prix actuel")
                    logger.info("🎯 Analyse: SORTIR ou HOLD ?")
                    logger.info("")
                    
                    # Analyser uniquement la crypto en position
                    cryptos_to_analyze = [self.current_position['symbol']]
                else:
                    # Pas de position : scanner toutes les cryptos pour ACHETER
                    logger.info("📊 Pas de position active - Scan pour opportunités...")
                    
                    # Cryptos principales à analyser (market cap élevé)
                    top_cryptos = [
                        'BTC/EUR', 'ETH/EUR', 'SOL/EUR', 'BNB/EUR',
                        'XRP/EUR', 'ADA/EUR', 'AVAX/EUR', 'DOT/EUR',
                        'MATIC/EUR', 'LINK/EUR', 'UNI/EUR', 'ATOM/EUR'
                    ]
                    
                    # Vérifier qu'elles existent sur Kraken
                    markets = await self.market_data.exchange.load_markets()
                    cryptos_to_analyze = [s for s in top_cryptos if s in markets and markets[s]['active']]
                    
                    logger.info(f"✅ {len(cryptos_to_analyze)} cryptos à analyser")
                
                logger.info("")
                
                for symbol in cryptos_to_analyze:
                    try:
                        logger.info("")
                        logger.info(f"🔍 Analyse LLM: {symbol}")
                        logger.info("-" * 80)
                        
                        # Prix actuel
                        ticker = await self.market_data.fetch_ticker(symbol)
                        price = ticker['last']
                        
                        # News
                        base_currency = symbol.split('/')[0]
                        news = await self.news_ingestion.fetch_cryptopanic([base_currency])
                        
                        # Demander au LLM d'analyser
                        analysis = await self.analyze_crypto_with_llm(symbol, price, news)
                        
                        logger.info(f"🤖 Décision: {analysis['decision']}")
                        logger.info(f"📊 Confiance: {analysis['confidence']*100:.0f}%")
                        logger.info(f"💭 Réponse LLM:")
                        logger.info(f"   {analysis['raw_response'][:200]}...")
                        
                        # Exécuter si BUY avec confiance élevée
                        if analysis['decision'] == 'BUY' and analysis['confidence'] > 0.7:
                            await self.execute_trade(
                                symbol, 
                                analysis['decision'],
                                analysis['position_size'],
                                analysis['explanation']
                            )
                        
                        # Pause entre chaque crypto
                        await asyncio.sleep(5)
                    
                    except Exception as e:
                        logger.error(f"Erreur analyse {symbol}: {e}")
                        continue
                
                # Résumé
                logger.info("")
                logger.info("=" * 80)
                if self.current_position:
                    logger.info(f"📌 Position: {self.current_position['symbol']} ({self.current_position['amount_eur']:.2f}€)")
                logger.info(f"💰 Capital disponible: {self.capital:.2f}€")
                logger.info(f"⏰ Prochain scan dans 5 minutes...")
                is_live = settings.trading.trading_mode == "live"
                logger.warning(f"⚠️  Mode: {settings.trading.trading_mode.upper()} {'- ARGENT RÉEL !' if is_live else '(Simulation)'}")
                logger.info("=" * 80)
                
                # Attendre 5 minutes
                await asyncio.sleep(300)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt demandé...")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Arrêt propre"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 Arrêt du Bot Intelligent...")
        logger.info("=" * 80)
        
        if self.market_data:
            await self.market_data.close()
        if self.order_executor:
            await self.order_executor.close()
        
        logger.success("✅ Bot arrêté proprement")


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🧠 TRADOPS - BOT INTELLIGENT avec LLM")
    logger.info("=" * 80)
    logger.info("")
    logger.info("💡 SYSTÈME ULTRA-INTELLIGENT:")
    logger.info("")
    logger.info("   ✅ LLM local (Llama 3.1 via Ollama)")
    logger.info("   ✅ Analyse approfondie de chaque crypto")
    logger.info("   ✅ Réflexion contextuelle (pas juste sentiment)")
    logger.info("   ✅ Explications claires de chaque décision")
    logger.info("   ✅ News en temps réel")
    logger.info("   ✅ Trading intelligent (confiance > 70%)")
    logger.info("")
    capital_type = "RÉEL" if settings.trading.trading_mode == "live" else "simulé"
    logger.info(f"💰 Capital {capital_type}: {settings.trading.initial_capital:.0f}€")
    logger.info(f"📊 Mode: {settings.trading.trading_mode.upper()}")
    logger.info("")
    logger.info("=" * 80)
    
    # Vérifier Ollama
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
            if response.status_code == 200:
                logger.success("")
                logger.success("✅ Ollama détecté et actif!")
                logger.success("")
            else:
                raise Exception("Ollama non accessible")
    except Exception as e:
        logger.error("")
        logger.error("❌ Ollama n'est pas lancé!")
        logger.error("   Lancez-le avec: ollama serve &")
        logger.error("")
        return
    
    # Lancer le bot
    bot = IntelligentTradingBot()
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

