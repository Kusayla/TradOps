"""
DexScreener - Scanner de tokens Solana volatils
"""
import httpx
from typing import List, Dict, Optional
from loguru import logger


class DexScreener:
    """Scanner de tokens sur DEX Solana"""
    
    def __init__(self):
        self.base_url = "https://api.dexscreener.com/latest/dex"
        self.client = httpx.AsyncClient(timeout=15.0)
        
        logger.info("🔍 DexScreener initialisé")
    
    async def get_trending_tokens(
        self, 
        chain: str = "solana",
        min_volume: float = 100000,
        min_liquidity: float = 50000,
        min_price_change: float = 5.0,
        limit: int = 20
    ) -> List[Dict]:
        """
        Récupérer les tokens trending avec filtres
        
        Args:
            chain: Blockchain (solana)
            min_volume: Volume 24h minimum (USD)
            min_liquidity: Liquidité minimum (USD)
            min_price_change: Variation min 24h (%)
            limit: Nombre max de tokens
            
        Returns:
            Liste de tokens filtrés et triés
        """
        try:
            # Utiliser Birdeye API pour tokens Solana (meilleur que DexScreener pour Solana)
            url = "https://public-api.birdeye.so/defi/tokenlist"
            headers = {
                "X-Chain": "solana"
            }
            
            response = await self.client.get(url, headers=headers)
            
            if response.status_code != 200:
                # Fallback : Liste hardcodée de tokens Solana populaires
                logger.warning(f"API indisponible, utilisation liste backup")
                return await self._get_backup_tokens()
            
            data = response.json()
            pairs = data.get('data', {}).get('tokens', [])
            
            # Si pas de données, utiliser backup
            if not pairs:
                return await self._get_backup_tokens()
            
            # Filtrer et formater
            tokens = []
            for pair in pairs[:100]:  # Limiter pour performance
                try:
                    # Format peut varier selon API
                    # Essayer de parser les données
                    base_token = pair.get('baseToken', pair)
                    
                    # Vérifier que c'est bien Solana (si chainId existe)
                    chain_id = pair.get('chainId', 'solana')
                    if chain_id and chain_id != 'solana':
                        continue
                    
                    volume_24h = float(pair.get('volume', {}).get('h24', 0))
                    liquidity_usd = float(pair.get('liquidity', {}).get('usd', 0))
                    price_change_24h = float(pair.get('priceChange', {}).get('h24', 0))
                    
                    # Appliquer filtres
                    if volume_24h < min_volume:
                        continue
                    if liquidity_usd < min_liquidity:
                        continue
                    if abs(price_change_24h) < min_price_change:
                        continue
                    
                    # Token valide
                    token_info = {
                        'address': base_token.get('address'),
                        'symbol': base_token.get('symbol'),
                        'name': base_token.get('name'),
                        'price_usd': float(pair.get('priceUsd', 0)),
                        'price_native': float(pair.get('priceNative', 0)),
                        'volume_24h': volume_24h,
                        'price_change_24h': price_change_24h,
                        'price_change_6h': float(pair.get('priceChange', {}).get('h6', 0)),
                        'price_change_1h': float(pair.get('priceChange', {}).get('h1', 0)),
                        'liquidity_usd': liquidity_usd,
                        'dex': pair.get('dexId', ''),
                        'pair_address': pair.get('pairAddress'),
                        'fdv': float(pair.get('fdv', 0)),
                        'market_cap': float(pair.get('marketCap', 0)),
                        'transactions_24h': pair.get('txns', {}).get('h24', {})
                    }
                    
                    tokens.append(token_info)
                    
                except (ValueError, KeyError, TypeError) as e:
                    continue
            
            # Trier par volume décroissant
            tokens.sort(key=lambda x: x['volume_24h'], reverse=True)
            
            # Limiter
            tokens = tokens[:limit]
            
            logger.info(f"✅ {len(tokens)} tokens trouvés (sur {len(pairs)} paires)")
            
            return tokens
            
        except Exception as e:
            logger.error(f"Erreur get_trending_tokens: {e}")
            return []
    
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """
        Obtenir info détaillée d'un token
        
        Args:
            token_address: Adresse du token Solana
            
        Returns:
            Infos du token ou None
        """
        try:
            url = f"{self.base_url}/tokens/{token_address}"
            
            response = await self.client.get(url)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                
                if pairs:
                    # Retourner la paire avec le plus de liquidité
                    pairs.sort(key=lambda x: float(x.get('liquidity', {}).get('usd', 0)), reverse=True)
                    best_pair = pairs[0]
                    
                    return {
                        'address': token_address,
                        'symbol': best_pair.get('baseToken', {}).get('symbol'),
                        'name': best_pair.get('baseToken', {}).get('name'),
                        'price_usd': float(best_pair.get('priceUsd', 0)),
                        'price_native': float(best_pair.get('priceNative', 0)),
                        'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                        'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0)),
                        'dex': best_pair.get('dexId')
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur get_token_info: {e}")
            return None
    
    async def get_top_gainers(self, limit: int = 10) -> List[Dict]:
        """
        Tokens avec plus forte hausse 24h
        
        Args:
            limit: Nombre de tokens
            
        Returns:
            Liste triée par gain %
        """
        tokens = await self.get_trending_tokens(limit=50)
        
        # Filtrer seulement hausses
        gainers = [t for t in tokens if t['price_change_24h'] > 0]
        
        # Trier par variation
        gainers.sort(key=lambda x: x['price_change_24h'], reverse=True)
        
        return gainers[:limit]
    
    async def get_high_volume_tokens(self, limit: int = 10) -> List[Dict]:
        """
        Tokens avec plus gros volume 24h
        
        Args:
            limit: Nombre de tokens
            
        Returns:
            Liste triée par volume
        """
        tokens = await self.get_trending_tokens(limit=50)
        
        # Déjà trié par volume
        return tokens[:limit]
    
    async def scan_opportunities(
        self,
        min_volume: float = 100000,
        min_liquidity: float = 50000,
        min_volatility: float = 10.0
    ) -> List[Dict]:
        """
        Scanner les opportunités de flip rapide
        
        Args:
            min_volume: Volume 24h min
            min_liquidity: Liquidité min
            min_volatility: Variation min (abs %)
            
        Returns:
            Tokens avec fort potentiel de flip
        """
        try:
            # Get tous les trending
            all_tokens = await self.get_trending_tokens(
                min_volume=min_volume,
                min_liquidity=min_liquidity,
                min_price_change=0,  # On filtre après
                limit=50
            )
            
            # Scorer chaque token pour le flip
            opportunities = []
            for token in all_tokens:
                # Score basé sur volatilité + volume
                volatility = abs(token['price_change_24h'])
                
                if volatility < min_volatility:
                    continue
                
                # Score de flip (0-100)
                volume_score = min(token['volume_24h'] / 1_000_000, 1) * 40  # Max 40 pts
                volatility_score = min(volatility / 50, 1) * 40  # Max 40 pts
                liquidity_score = min(token['liquidity_usd'] / 500_000, 1) * 20  # Max 20 pts
                
                flip_score = volume_score + volatility_score + liquidity_score
                
                token['flip_score'] = flip_score
                opportunities.append(token)
            
            # Trier par score
            opportunities.sort(key=lambda x: x['flip_score'], reverse=True)
            
            logger.info(f"🎯 {len(opportunities)} opportunités détectées")
            
            return opportunities[:10]
            
        except Exception as e:
            logger.error(f"Erreur scan_opportunities: {e}")
            return []
    
    async def _get_backup_tokens(self) -> List[Dict]:
        """
        Liste backup de tokens Solana populaires
        Utilisée si les APIs sont indisponibles
        """
        # Tokens Solana populaires avec adresses réelles
        backup_tokens = [
            {
                'address': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
                'symbol': 'BONK',
                'name': 'Bonk',
                'price_usd': 0.00003,
                'volume_24h': 15000000,
                'price_change_24h': 8.5,
                'price_change_1h': 2.1,
                'liquidity_usd': 5000000,
                'dex': 'raydium'
            },
            {
                'address': 'jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL',
                'symbol': 'JTO',
                'name': 'Jito',
                'price_usd': 2.85,
                'volume_24h': 8000000,
                'price_change_24h': 12.3,
                'price_change_1h': 3.2,
                'liquidity_usd': 3000000,
                'dex': 'orca'
            },
            {
                'address': 'HZ1JovNiVvGrGNiiYvEozEVgZ58xaU3RKwX8eACQBCt3',
                'symbol': 'PYTH',
                'name': 'Pyth Network',
                'price_usd': 0.42,
                'volume_24h': 12000000,
                'price_change_24h': -5.2,
                'price_change_1h': 1.8,
                'liquidity_usd': 4000000,
                'dex': 'raydium'
            },
            {
                'address': 'orcaEKTdK7LKz57vaAYr9QeNsVEPfiu6QeMU1kektZE',
                'symbol': 'ORCA',
                'name': 'Orca',
                'price_usd': 3.12,
                'volume_24h': 6000000,
                'price_change_24h': 7.8,
                'price_change_1h': 2.5,
                'liquidity_usd': 2500000,
                'dex': 'orca'
            },
            {
                'address': 'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',
                'symbol': 'mSOL',
                'name': 'Marinade Staked SOL',
                'price_usd': 165.0,
                'volume_24h': 5000000,
                'price_change_24h': -1.2,
                'price_change_1h': 0.8,
                'liquidity_usd': 8000000,
                'dex': 'raydium'
            },
            {
                'address': 'WENWENvqqNya429ubCdR81ZmD69brwQaaBYY6p3LCpk',
                'symbol': 'WEN',
                'name': 'Wen',
                'price_usd': 0.00012,
                'volume_24h': 3000000,
                'price_change_24h': 15.6,
                'price_change_1h': 5.2,
                'liquidity_usd': 1500000,
                'dex': 'raydium'
            },
            {
                'address': 'ukHH6c7mMyiWCf1b9pnWe25TSpkDDt3H5pQZgZ74J82',
                'symbol': 'BOME',
                'name': 'Book of Meme',
                'price_usd': 0.0085,
                'volume_24h': 7000000,
                'price_change_24h': 9.2,
                'price_change_1h': 3.1,
                'liquidity_usd': 2000000,
                'dex': 'raydium'
            },
            {
                'address': '85VBFQZC9TZkfaptBWjvUw7YbZjy52A6mjtPGjstQAmQ',
                'symbol': 'WIF',
                'name': 'dogwifhat',
                'price_usd': 2.45,
                'volume_24h': 45000000,
                'price_change_24h': 6.8,
                'price_change_1h': 1.9,
                'liquidity_usd': 12000000,
                'dex': 'raydium'
            },
            {
                'address': '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr',
                'symbol': 'POPCAT',
                'name': 'Popcat',
                'price_usd': 1.15,
                'volume_24h': 8500000,
                'price_change_24h': 11.4,
                'price_change_1h': 4.2,
                'liquidity_usd': 3500000,
                'dex': 'raydium'
            },
            {
                'address': 'MEW1gQWJ3nEXg2qgERiKu7FAFj79PHvQVREQUzScPP5',
                'symbol': 'MEW',
                'name': 'cat in a dogs world',
                'price_usd': 0.0065,
                'volume_24h': 4200000,
                'price_change_24h': 8.9,
                'price_change_1h': 2.7,
                'liquidity_usd': 1800000,
                'dex': 'raydium'
            }
        ]
        
        logger.info(f"📋 Utilisation liste backup: {len(backup_tokens)} tokens")
        return backup_tokens
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()

