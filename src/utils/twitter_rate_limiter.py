"""
Twitter API Rate Limiter
Gère intelligemment les limites de l'API gratuite Twitter
"""
import time
from typing import Dict, Optional
from datetime import datetime, timedelta
from collections import deque
from loguru import logger


class TwitterRateLimiter:
    """
    Gestion des rate limits pour Twitter API v2 Gratuit
    
    Limites API Gratuite (Basic):
    - 100 requêtes par 15 minutes (fenêtre glissante)
    - 500,000 tweets par mois
    - 10,000 tweets par requête max
    
    Stratégie:
    - Espacer les requêtes intelligemment
    - Cache des résultats
    - Priorité aux cryptos importantes
    - Gestion des erreurs 429
    """
    
    def __init__(self):
        # Limites API Gratuite
        self.max_requests_per_window = 100  # 100 requêtes
        self.window_seconds = 15 * 60  # 15 minutes
        self.max_tweets_per_month = 500000
        
        # Tracking
        self.request_timestamps = deque(maxlen=self.max_requests_per_window)
        self.monthly_tweet_count = 0
        self.month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        # Cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Stats
        self.total_requests = 0
        self.total_tweets_fetched = 0
        self.cache_hits = 0
        self.rate_limit_hits = 0
        
        logger.info("🔒 Twitter Rate Limiter initialisé")
        logger.info(f"   Limite: {self.max_requests_per_window} requêtes / 15 min")
        logger.info(f"   Limite mensuelle: {self.max_tweets_per_month:,} tweets")
    
    def can_make_request(self) -> bool:
        """Vérifier si on peut faire une requête maintenant"""
        now = time.time()
        
        # Réinitialiser le compteur mensuel si nouveau mois
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
        if current_month > self.month_start:
            self.month_start = current_month
            self.monthly_tweet_count = 0
            logger.info("🔄 Compteur mensuel réinitialisé")
        
        # Vérifier limite mensuelle
        if self.monthly_tweet_count >= self.max_tweets_per_month:
            logger.error("❌ Limite mensuelle atteinte! Attendez le prochain mois")
            return False
        
        # Nettoyer les anciennes requêtes (> 15 min)
        cutoff = now - self.window_seconds
        while self.request_timestamps and self.request_timestamps[0] < cutoff:
            self.request_timestamps.popleft()
        
        # Vérifier limite par fenêtre
        if len(self.request_timestamps) >= self.max_requests_per_window:
            # Calculer temps d'attente
            oldest = self.request_timestamps[0]
            wait_time = int(oldest + self.window_seconds - now)
            logger.warning(f"⏰ Rate limit atteint. Attendez {wait_time}s")
            return False
        
        return True
    
    def wait_if_needed(self) -> int:
        """Attendre si nécessaire. Retourne temps d'attente en secondes"""
        if self.can_make_request():
            return 0
        
        # Calculer temps d'attente
        now = time.time()
        oldest = self.request_timestamps[0]
        wait_time = int(oldest + self.window_seconds - now + 1)
        
        return wait_time
    
    def record_request(self, tweets_fetched: int = 0):
        """Enregistrer une requête effectuée"""
        now = time.time()
        self.request_timestamps.append(now)
        self.total_requests += 1
        self.total_tweets_fetched += tweets_fetched
        self.monthly_tweet_count += tweets_fetched
    
    def get_cache(self, key: str) -> Optional[Dict]:
        """Récupérer du cache si valide"""
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        age = time.time() - entry['timestamp']
        
        if age > self.cache_ttl:
            del self.cache[key]
            return None
        
        self.cache_hits += 1
        logger.debug(f"💾 Cache hit pour {key}")
        return entry['data']
    
    def set_cache(self, key: str, data: Dict):
        """Mettre en cache"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_stats(self) -> Dict:
        """Obtenir statistiques d'utilisation"""
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Compter requêtes dans fenêtre actuelle
        recent_requests = sum(1 for ts in self.request_timestamps if ts >= cutoff)
        
        # Calculer pourcentage utilisation
        usage_percent = (recent_requests / self.max_requests_per_window) * 100
        monthly_percent = (self.monthly_tweet_count / self.max_tweets_per_month) * 100
        
        # Temps restant dans fenêtre
        if self.request_timestamps:
            oldest_in_window = min(ts for ts in self.request_timestamps if ts >= cutoff) if recent_requests > 0 else now
            time_until_reset = int(oldest_in_window + self.window_seconds - now)
        else:
            time_until_reset = 0
        
        return {
            'requests_in_window': recent_requests,
            'requests_available': self.max_requests_per_window - recent_requests,
            'window_usage_percent': usage_percent,
            'monthly_tweets': self.monthly_tweet_count,
            'monthly_available': self.max_tweets_per_month - self.monthly_tweet_count,
            'monthly_usage_percent': monthly_percent,
            'time_until_reset': time_until_reset,
            'total_requests': self.total_requests,
            'total_tweets': self.total_tweets_fetched,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': (self.cache_hits / max(self.total_requests, 1)) * 100,
            'rate_limit_hits': self.rate_limit_hits
        }
    
    def print_stats(self):
        """Afficher les statistiques"""
        stats = self.get_stats()
        
        logger.info("📊 STATS API TWITTER:")
        logger.info(f"   Requêtes (15 min): {stats['requests_in_window']}/{self.max_requests_per_window} "
                   f"({stats['window_usage_percent']:.1f}%)")
        logger.info(f"   Disponible: {stats['requests_available']} requêtes")
        
        if stats['time_until_reset'] > 0:
            logger.info(f"   Reset dans: {stats['time_until_reset']}s")
        
        logger.info(f"   Tweets (mois): {stats['monthly_tweets']:,}/{self.max_tweets_per_month:,} "
                   f"({stats['monthly_usage_percent']:.1f}%)")
        logger.info(f"   Cache: {stats['cache_hit_rate']:.1f}% hit rate")
    
    def calculate_optimal_interval(self) -> int:
        """
        Calculer l'intervalle optimal entre requêtes
        
        Stratégie:
        - Si usage < 50%: requête toutes les 10 min (sûr)
        - Si usage < 80%: requête toutes les 15 min
        - Si usage > 80%: requête toutes les 20 min (conservateur)
        """
        stats = self.get_stats()
        usage = stats['window_usage_percent']
        
        if usage < 50:
            return 600  # 10 minutes (sûr, 6 requêtes/heure)
        elif usage < 80:
            return 900  # 15 minutes (conservateur, 4 requêtes/heure)
        else:
            return 1200  # 20 minutes (très conservateur)
    
    def should_skip_crypto(self, symbol: str, priority: str = 'normal') -> bool:
        """
        Décider si on doit skip une crypto pour économiser requêtes
        
        Args:
            symbol: Symbole crypto
            priority: 'high', 'normal', 'low'
        """
        stats = self.get_stats()
        usage = stats['window_usage_percent']
        
        # Si usage faible, ne skip rien
        if usage < 60:
            return False
        
        # Si usage élevé, skip les low priority
        if usage >= 80 and priority == 'low':
            return True
        
        # Si usage très élevé, garde seulement high priority
        if usage >= 90 and priority != 'high':
            return True
        
        return False

