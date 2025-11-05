"""
Jupiter DEX Executor - Swaps de tokens sur Solana
"""
import httpx
import base64
import json
from typing import Optional, Dict, List
from loguru import logger
from decimal import Decimal

from src.config import settings


class JupiterExecutor:
    """Execute token swaps on Jupiter DEX (Solana)"""
    
    def __init__(self):
        self.base_url = "https://quote-api.jup.ag/v6"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.slippage_bps = 100  # 1% slippage = 100 basis points
        
        # Token addresses (Solana mainnet)
        self.tokens = {
            'SOL': 'So11111111111111111111111111111111111111112',  # Wrapped SOL
            'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
            'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
        }
        
        logger.info("🪙 Jupiter Executor initialisé")
    
    async def get_token_price(self, token_mint: str, vs_token: str = 'SOL') -> Optional[float]:
        """
        Obtenir le prix d'un token
        
        Args:
            token_mint: Adresse du token
            vs_token: Token de référence (SOL, USDC, USDT)
            
        Returns:
            Prix ou None
        """
        try:
            # Get quote pour 1 unité
            quote = await self.get_quote(
                input_mint=self.tokens.get(vs_token, vs_token),
                output_mint=token_mint,
                amount=1_000_000_000  # 1 SOL (9 decimals)
            )
            
            if quote:
                # Prix = output amount / input amount
                price = float(quote['outAmount']) / 1_000_000_000
                return price
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur prix token: {e}")
            return None
    
    async def get_quote(self, input_mint: str, output_mint: str, amount: int) -> Optional[Dict]:
        """
        Obtenir un quote de Jupiter
        
        Args:
            input_mint: Token source (adresse)
            output_mint: Token destination (adresse)
            amount: Montant en lamports/smallest unit
            
        Returns:
            Quote dict ou None
        """
        try:
            params = {
                'inputMint': input_mint,
                'outputMint': output_mint,
                'amount': amount,
                'slippageBps': self.slippage_bps,
            }
            
            response = await self.client.get(f"{self.base_url}/quote", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur quote Jupiter: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur get_quote: {e}")
            return None
    
    async def swap_token(
        self, 
        from_token: str, 
        to_token: str, 
        amount: float,
        wallet_keypair: str = None
    ) -> Optional[Dict]:
        """
        Échanger un token contre un autre
        
        Args:
            from_token: Token source (symbole ou adresse)
            to_token: Token destination (symbole ou adresse)
            amount: Montant à échanger
            wallet_keypair: Clé privée wallet (base58)
            
        Returns:
            Transaction result ou None
        """
        try:
            # Résoudre les adresses
            from_mint = self.tokens.get(from_token, from_token)
            to_mint = self.tokens.get(to_token, to_token)
            
            # Convertir amount en lamports (assume 9 decimals pour SOL)
            amount_lamports = int(amount * 1_000_000_000)
            
            # 1. Get quote
            logger.info(f"💱 Swap {from_token} → {to_token} : {amount}")
            quote = await self.get_quote(from_mint, to_mint, amount_lamports)
            
            if not quote:
                logger.error("❌ Pas de quote disponible")
                return None
            
            # Calculer prix et slippage
            in_amount = float(quote['inAmount']) / 1_000_000_000
            out_amount = float(quote['outAmount']) / 1_000_000_000
            price = out_amount / in_amount if in_amount > 0 else 0
            
            logger.info(f"💰 Quote: {in_amount:.4f} {from_token} → {out_amount:.4f} {to_token}")
            logger.info(f"📊 Prix: {price:.6f}")
            logger.info(f"⚠️ Slippage: {self.slippage_bps / 100:.2f}%")
            
            # 2. Get swap transaction (mode simulation si pas de wallet)
            if not wallet_keypair:
                logger.warning("⚠️ Mode simulation (pas de wallet configuré)")
                return {
                    'success': True,
                    'simulation': True,
                    'from_token': from_token,
                    'to_token': to_token,
                    'in_amount': in_amount,
                    'out_amount': out_amount,
                    'price': price
                }
            
            # En mode réel, on utiliserait la clé privée pour signer
            # Pour l'instant, retour simulation
            logger.warning("⚠️ Swap simulation (implémentation wallet en cours)")
            
            return {
                'success': True,
                'simulation': True,
                'from_token': from_token,
                'to_token': to_token,
                'in_amount': in_amount,
                'out_amount': out_amount,
                'price': price,
                'quote': quote
            }
            
        except Exception as e:
            logger.error(f"Erreur swap: {e}")
            return None
    
    async def get_trending_tokens(self, limit: int = 20) -> List[Dict]:
        """
        Obtenir les tokens trending sur Solana
        
        Args:
            limit: Nombre de tokens à retourner
            
        Returns:
            Liste de tokens avec métadonnées
        """
        try:
            # Utiliser DexScreener pour tokens trending
            url = "https://api.dexscreener.com/latest/dex/tokens/trending/solana"
            
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                tokens = []
                
                for pair in data.get('pairs', [])[:limit]:
                    tokens.append({
                        'address': pair.get('baseToken', {}).get('address'),
                        'symbol': pair.get('baseToken', {}).get('symbol'),
                        'name': pair.get('baseToken', {}).get('name'),
                        'price': float(pair.get('priceUsd', 0)),
                        'volume_24h': float(pair.get('volume', {}).get('h24', 0)),
                        'price_change_24h': float(pair.get('priceChange', {}).get('h24', 0)),
                        'liquidity': float(pair.get('liquidity', {}).get('usd', 0)),
                        'dex': pair.get('dexId', '')
                    })
                
                return tokens
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur trending tokens: {e}")
            return []
    
    async def close(self):
        """Fermer les connexions"""
        await self.client.aclose()

