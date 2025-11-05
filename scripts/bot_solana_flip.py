#!/usr/bin/env python3
"""
BOT SOLANA FAST FLIP - Trading ultra-rapide sur tokens Solana
"""
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.execution.jupiter_executor import JupiterExecutor
from src.data_ingestion.dex_screener import DexScreener
from src.ml.llm_analyzer import LLMAnalyzer


class SolanaFlipBot:
    """Bot de flip rapide sur tokens Solana"""
    
    def __init__(self):
        self.jupiter = None
        self.dex_screener = None
        self.llm = None
        self.running = False
        
        # Capital et position
        self.capital_sol = settings.trading.initial_capital / 150  # Approx 15€ = 0.1 SOL
        self.current_position = None
        self.position_file = Path(__file__).parent.parent / "data" / "solana_position.json"
        
        # Créer dossier data
        self.position_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("🪙 Solana Flip Bot initialisé")
    
    async def initialize(self):
        """Initialiser les composants"""
        try:
            logger.info("=" * 80)
            logger.info("🔧 Initialisation Solana Fast Trading...")
            logger.info("=" * 80)
            
            # 1. Jupiter (swaps)
            logger.info("💱 Jupiter DEX...")
            self.jupiter = JupiterExecutor()
            logger.success("✅ Jupiter prêt")
            
            # 2. DexScreener (scanner)
            logger.info("🔍 DexScreener...")
            self.dex_screener = DexScreener()
            logger.success("✅ DexScreener prêt")
            
            # 3. LLM (ChatGPT)
            llm_provider = getattr(settings.data_sources, 'llm_provider', 'openai')
            logger.info(f"🧠 ChatGPT ({llm_provider})...")
            self.llm = LLMAnalyzer(provider=llm_provider)
            logger.success("✅ ChatGPT prêt")
            
            logger.info("")
            logger.success("🎉 SYSTÈME SOLANA 100% PRÊT!")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation: {e}")
            raise
    
    async def analyze_token_with_chatgpt(
        self, 
        token: Dict, 
        in_position: bool = False,
        entry_price: float = None,
        current_pnl: float = None
    ) -> Dict:
        """
        Analyser un token avec ChatGPT
        
        Returns:
            {'decision': 'BUY'|'SELL'|'HOLD', 'confidence': float, 'explanation': str}
        """
        try:
            symbol = token['symbol']
            price = token['price_usd']
            change_24h = token.get('price_change_24h', 0)
            change_1h = token.get('price_change_1h', 0)
            volume = token.get('volume_24h', 0)
            liquidity = token.get('liquidity_usd', 0)
            
            if in_position and entry_price:
                # EN POSITION : Décider sortie
                pnl_pct = ((price - entry_price) / entry_price) * 100
                
                prompt = f"""{symbol} @ ${price:.6f}
Entrée: ${entry_price:.6f} | PnL: {pnl_pct:+.1f}%
Δ1h: {change_1h:+.1f}% | Δ24h: {change_24h:+.1f}%
Vol: ${volume/1000:.0f}k

EN POSITION. Sortir maintenant?
DÉCISION: VENDRE/HOLD
CONFIANCE: [0-100]%
RAISON: [1 phrase]"""
            else:
                # PAS DE POSITION : Décider achat
                prompt = f"""{symbol} @ ${price:.6f}
Δ1h: {change_1h:+.1f}% | Δ24h: {change_24h:+.1f}%
Vol: ${volume/1000:.0f}k | Liq: ${liquidity/1000:.0f}k

Fast flip possible?
DÉCISION: ACHETER/ATTENDRE
CONFIANCE: [0-100]%
RAISON: [1 phrase]"""
            
            # Appeler ChatGPT
            if self.llm.provider == "openai":
                response = await self.llm._call_openai(prompt)
            else:
                response = await self.llm._call_ollama(prompt)
            
            # Parser réponse
            decision = "HOLD"
            confidence = 0.5
            explanation = response
            
            if response:
                lines = response.upper().split('\n')
                for line in lines:
                    if 'DÉCISION' in line or 'DECISION' in line:
                        if 'ACHETER' in line or 'BUY' in line:
                            decision = "BUY"
                        elif 'VENDRE' in line or 'SELL' in line:
                            decision = "SELL"
                    
                    if 'CONFIANCE' in line or 'CONFIDENCE' in line:
                        import re
                        match = re.search(r'(\d+)', line)
                        if match:
                            confidence = int(match.group(1)) / 100
            
            return {
                'decision': decision,
                'confidence': confidence,
                'explanation': response[:200]
            }
            
        except Exception as e:
            logger.error(f"Erreur ChatGPT: {e}")
            return {'decision': 'HOLD', 'confidence': 0.0, 'explanation': str(e)}
    
    async def monitor_position_realtime(self):
        """
        Surveillance temps réel de la position active
        Check toutes les 30 secondes avec ChatGPT
        """
        logger.info("")
        logger.info("🚨 MODE SURVEILLANCE TEMPS RÉEL ACTIVÉ")
        logger.info("=" * 80)
        logger.info(f"📌 Position: {self.current_position['symbol']}")
        logger.info(f"💰 Entrée: ${self.current_position['entry_price']:.6f}")
        logger.info(f"⏱️  Check toutes les 30 secondes")
        logger.info("=" * 80)
        logger.info("")
        
        check_count = 0
        start_time = datetime.now()
        
        while self.running and self.current_position:
            check_count += 1
            
            try:
                # Obtenir prix actuel
                token_info = await self.dex_screener.get_token_info(
                    self.current_position['address']
                )
                
                if not token_info:
                    logger.warning("⚠️ Token info indisponible, attente...")
                    await asyncio.sleep(30)
                    continue
                
                current_price = token_info['price_usd']
                entry_price = self.current_position['entry_price']
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Check temps en position
                time_in_position = (datetime.now() - start_time).total_seconds()
                
                logger.info(f"🔄 Check #{check_count} - {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"💰 Prix: ${current_price:.6f} (entrée: ${entry_price:.6f})")
                logger.info(f"📊 PnL: {pnl_pct:+.2f}% | Temps: {time_in_position/60:.1f} min")
                
                # Stop loss forcé
                if pnl_pct <= -3:
                    logger.error("🚨 STOP LOSS ATTEINT (-3%) - SORTIE FORCÉE")
                    await self.close_position("Stop loss", pnl_pct)
                    break
                
                # Take profit auto
                if pnl_pct >= 5:
                    logger.success("🎯 TAKE PROFIT ATTEINT (+5%) - SORTIE")
                    await self.close_position("Take profit", pnl_pct)
                    break
                
                # Max hold time (1h)
                if time_in_position > 3600:
                    logger.warning("⏰ 1h en position - SORTIE AUTOMATIQUE")
                    await self.close_position("Timeout 1h", pnl_pct)
                    break
                
                # Demander à ChatGPT
                logger.info("🧠 Consultation ChatGPT...")
                analysis = await self.analyze_token_with_chatgpt(
                    token_info,
                    in_position=True,
                    entry_price=entry_price,
                    current_pnl=pnl_pct
                )
                
                logger.info(f"🤖 ChatGPT: {analysis['decision']} (confiance: {analysis['confidence']*100:.0f}%)")
                logger.info(f"💭 Raison: {analysis['explanation'][:100]}...")
                
                # Décision
                if analysis['decision'] == "SELL" and analysis['confidence'] > 0.7:
                    logger.success("✅ ChatGPT recommande SORTIE avec haute confiance")
                    await self.close_position("Signal ChatGPT", pnl_pct)
                    break
                elif analysis['decision'] == "HOLD":
                    logger.info("🔒 ChatGPT recommande HOLD - On garde")
                
                logger.info(f"⏰ Prochain check dans 30 secondes...")
                logger.info("-" * 80)
                logger.info("")
                
                # Attendre 30 secondes
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Erreur surveillance: {e}")
                await asyncio.sleep(30)
    
    async def close_position(self, reason: str, pnl_pct: float):
        """Fermer la position actuelle"""
        try:
            logger.info("")
            logger.info("=" * 80)
            logger.warning(f"🚪 FERMETURE POSITION: {reason}")
            logger.info("=" * 80)
            
            # Simuler swap (en attente implémentation wallet)
            result = await self.jupiter.swap_token(
                from_token=self.current_position['address'],
                to_token='SOL',
                amount=self.current_position['amount']
            )
            
            if result:
                # Calculer gains
                initial_sol = self.current_position['sol_amount']
                final_sol = result.get('out_amount', initial_sol * (1 + pnl_pct/100))
                profit_sol = final_sol - initial_sol
                
                self.capital_sol = final_sol
                
                logger.success(f"✅ POSITION FERMÉE")
                logger.info(f"💰 SOL initial: {initial_sol:.4f}")
                logger.info(f"💰 SOL final: {final_sol:.4f}")
                logger.info(f"📊 Profit: {profit_sol:+.4f} SOL ({pnl_pct:+.2f}%)")
                logger.info(f"💵 Nouveau capital: {self.capital_sol:.4f} SOL (~{self.capital_sol * 150:.2f}€)")
                
                # Supprimer position
                self.current_position = None
                if self.position_file.exists():
                    self.position_file.unlink()
                
                logger.success("🔓 Retour en mode SCAN")
            else:
                logger.error("❌ Échec fermeture position")
                
        except Exception as e:
            logger.error(f"Erreur close_position: {e}")
    
    async def run(self):
        """Boucle principale"""
        self.running = True
        cycle = 0
        
        # Restaurer position si existe
        if self.position_file.exists():
            with open(self.position_file, 'r') as f:
                data = json.load(f)
                self.current_position = data.get('position')
                self.capital_sol = data.get('capital_sol', self.capital_sol)
            
            if self.current_position:
                logger.success(f"📌 Position restaurée: {self.current_position['symbol']}")
        
        logger.info("")
        logger.info("🚀 DÉMARRAGE BOT SOLANA FLIP")
        logger.info("=" * 80)
        logger.info("")
        logger.info("⚡ FAST TRADING MODE:")
        logger.info("   • Sans position → Scan tokens trending (3 min)")
        logger.info("   • Avec position → Surveillance TEMPS RÉEL (30 sec)")
        logger.info("   • ChatGPT décide achat/vente")
        logger.info("   • Stop loss: -3% | Take profit: +5%")
        logger.info("   • Max hold: 1h par position")
        logger.info("")
        logger.info(f"💰 Capital: {self.capital_sol:.4f} SOL (~{self.capital_sol * 150:.2f}€)")
        logger.info("=" * 80)
        logger.info("")
        
        try:
            while self.running:
                cycle += 1
                
                if self.current_position:
                    # MODE SURVEILLANCE TEMPS RÉEL
                    await self.monitor_position_realtime()
                    # Après sortie, retour au scan
                else:
                    # MODE SCAN (recherche opportunité)
                    logger.info("=" * 80)
                    logger.info(f"🔄 SCAN #{cycle} - {datetime.now().strftime('%H:%M:%S')}")
                    logger.info("=" * 80)
                    logger.info("🔍 Recherche tokens volatils Solana...")
                    
                    # Scanner tokens (filtres assouplis pour plus d'opportunités)
                    opportunities = await self.dex_screener.scan_opportunities(
                        min_volume=50000,      # 50k au lieu de 100k
                        min_liquidity=25000,   # 25k au lieu de 50k
                        min_volatility=5.0     # 5% au lieu de 10%
                    )
                    
                    if not opportunities:
                        logger.warning("⚠️ Aucune opportunité détectée")
                        logger.info("⏰ Prochain scan dans 3 minutes...")
                        await asyncio.sleep(180)
                        continue
                    
                    logger.info(f"✅ {len(opportunities)} opportunités trouvées")
                    logger.info("")
                    
                    # Analyser top 5 avec ChatGPT
                    for i, token in enumerate(opportunities[:5], 1):
                        logger.info(f"🎯 #{i} - {token['symbol']}")
                        logger.info(f"   Prix: ${token['price_usd']:.6f}")
                        logger.info(f"   Δ24h: {token['price_change_24h']:+.1f}%")
                        logger.info(f"   Volume: ${token['volume_24h']/1000:.0f}k")
                        logger.info(f"   Score flip: {token['flip_score']:.0f}/100")
                        logger.info("")
                        
                        # ChatGPT analyse
                        logger.info(f"🧠 ChatGPT analyse {token['symbol']}...")
                        analysis = await self.analyze_token_with_chatgpt(token)
                        
                        logger.info(f"🤖 Décision: {analysis['decision']} ({analysis['confidence']*100:.0f}%)")
                        logger.info(f"💭 {analysis['explanation'][:120]}...")
                        logger.info("")
                        
                        # Acheter si confiance >= 75%
                        if analysis['decision'] == "BUY" and analysis['confidence'] >= 0.75:
                            await self.open_position(token, analysis)
                            break  # Sortir de la boucle scan
                        
                        # Pause entre analyses
                        await asyncio.sleep(2)
                    
                    if not self.current_position:
                        logger.info("⚪ Aucun signal d'achat fort")
                        logger.info("⏰ Prochain scan dans 3 minutes...")
                        await asyncio.sleep(180)
        
        except KeyboardInterrupt:
            logger.info("\n🛑 Arrêt demandé...")
        except Exception as e:
            logger.error(f"❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.shutdown()
    
    async def open_position(self, token: Dict, analysis: Dict):
        """Ouvrir une position sur un token"""
        try:
            logger.info("")
            logger.info("=" * 80)
            logger.success(f"🚀 ACHAT: {token['symbol']}")
            logger.info(f"💰 Montant: {self.capital_sol * 0.85:.4f} SOL (85%)")
            logger.info(f"🧠 ChatGPT: {analysis['explanation'][:150]}")
            logger.info("=" * 80)
            
            # Simuler swap SOL → Token
            sol_amount = self.capital_sol * 0.85
            
            result = await self.jupiter.swap_token(
                from_token='SOL',
                to_token=token['address'],
                amount=sol_amount
            )
            
            if result:
                # Sauvegarder position
                self.current_position = {
                    'symbol': token['symbol'],
                    'address': token['address'],
                    'entry_price': token['price_usd'],
                    'amount': result.get('out_amount', 0),
                    'sol_amount': sol_amount,
                    'entry_time': datetime.now().isoformat()
                }
                
                self.capital_sol -= sol_amount
                
                # Sauvegarder fichier
                with open(self.position_file, 'w') as f:
                    json.dump({
                        'position': self.current_position,
                        'capital_sol': self.capital_sol
                    }, f, indent=2)
                
                logger.success(f"📌 Position ouverte: {token['symbol']}")
                logger.info(f"   Prix entrée: ${self.current_position['entry_price']:.6f}")
                logger.info(f"   SOL utilisé: {sol_amount:.4f}")
                logger.info("")
                logger.info("🚨 PASSAGE EN MODE SURVEILLANCE TEMPS RÉEL")
                
        except Exception as e:
            logger.error(f"Erreur open_position: {e}")
    
    async def shutdown(self):
        """Arrêt propre"""
        logger.info("")
        logger.info("=" * 80)
        logger.info("🛑 Arrêt Bot Solana...")
        logger.info("=" * 80)
        
        if self.jupiter:
            await self.jupiter.close()
        if self.dex_screener:
            await self.dex_screener.close()
        
        logger.success("✅ Bot arrêté")


async def main():
    """Point d'entrée"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 80)
    logger.info("🪙 SOLANA FAST FLIP BOT")
    logger.info("=" * 80)
    logger.info("")
    logger.info("⚡ BOT ULTRA-RAPIDE:")
    logger.info("")
    logger.info("   ✅ Tokens Solana volatils (DEX)")
    logger.info("   ✅ Surveillance temps réel (30 sec) en position")
    logger.info("   ✅ ChatGPT décisions rapides")
    logger.info("   ✅ Flips 2-5% en quelques minutes")
    logger.info("   ✅ Stop loss -3% | Take profit +5%")
    logger.info("")
    capital_eur = settings.trading.initial_capital
    logger.info(f"💰 Capital: {capital_eur:.0f}€ (~{capital_eur/150:.4f} SOL)")
    logger.info(f"📊 Mode: {'SIMULATION' if True else 'LIVE'}")  # Simulation pour l'instant
    logger.info("")
    logger.info("=" * 80)
    
    # Vérifier ChatGPT
    llm_provider = getattr(settings.data_sources, 'llm_provider', 'ollama')
    if llm_provider == "openai":
        api_key = getattr(settings.data_sources, 'openai_api_key', '')
        if not api_key:
            logger.error("")
            logger.error("❌ Clé OpenAI manquante!")
            logger.error("   Ajoutez dans .env: OPENAI_API_KEY=sk-proj-...")
            logger.error("")
            return
        logger.success("")
        logger.success("✅ ChatGPT (OpenAI) configuré")
        logger.success("")
    
    # Lancer
    bot = SolanaFlipBot()
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

