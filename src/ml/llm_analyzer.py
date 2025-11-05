"""
LLM-Based Tweet Analyzer
Utilise un LLM (ChatGPT/Claude/Ollama) pour interpréter les tweets
et décider s'il faut acheter/vendre une crypto
"""
import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import httpx
from loguru import logger

from src.config import settings


class LLMAnalyzer:
    """
    Analyse tweets avec un LLM pour décisions de trading contextuelles
    
    Supporte:
    - OpenAI (ChatGPT)
    - Anthropic (Claude)
    - Ollama (local, gratuit)
    """
    
    def __init__(self, provider: str = "ollama"):
        """
        Args:
            provider: 'openai', 'anthropic', ou 'ollama'
        """
        self.provider = provider
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Configuration selon provider
        if provider == "openai":
            self.api_key = getattr(settings.data_sources, 'openai_api_key', '')
            self.base_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-4o-mini"  # Moins cher que gpt-4
        elif provider == "anthropic":
            self.api_key = getattr(settings.data_sources, 'anthropic_api_key', '')
            self.base_url = "https://api.anthropic.com/v1/messages"
            self.model = "claude-3-haiku-20240307"  # Moins cher
        elif provider == "ollama":
            # Ollama local (gratuit!)
            self.api_key = ""
            self.base_url = "http://localhost:11434/api/generate"
            self.model = "llama3.1:8b"  # OU "mistral", "mixtral", etc.
        
        logger.info(f"🤖 LLM Analyzer initialisé (provider: {provider})")
    
    async def analyze_tweets_for_crypto(self,
                                       crypto: str,
                                       tweets: List[Dict],
                                       current_price: float,
                                       price_change_24h: float) -> Dict:
        """
        Analyser les tweets pour une crypto et décider de l'action
        
        Args:
            crypto: Symbole crypto (ex: 'BTC')
            tweets: Liste de tweets
            current_price: Prix actuel
            price_change_24h: Variation 24h en %
            
        Returns:
            Décision de trading avec explication
        """
        try:
            # Préparer le contexte pour le LLM
            tweet_texts = [t.get('text', '') for t in tweets[:20]]  # Max 20 tweets
            
            # Construire le prompt
            prompt = self._build_analysis_prompt(
                crypto=crypto,
                tweets=tweet_texts,
                current_price=current_price,
                price_change_24h=price_change_24h
            )
            
            # Appeler le LLM
            response = await self._call_llm(prompt)
            
            if not response:
                return self._default_decision(crypto)
            
            # Parser la réponse
            decision = self._parse_llm_response(response, crypto)
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Erreur analyse LLM pour {crypto}: {e}")
            return self._default_decision(crypto)
    
    def _build_analysis_prompt(self, crypto: str, tweets: List[str],
                               current_price: float, price_change_24h: float) -> str:
        """Construire le prompt pour le LLM"""
        
        prompt = f"""Tu es un expert en trading crypto. Analyse ces tweets sur {crypto} et décide s'il faut acheter, vendre ou attendre.

CONTEXTE:
- Crypto: {crypto}
- Prix actuel: {current_price:.2f}€
- Variation 24h: {price_change_24h:+.2f}%
- Nombre de tweets: {len(tweets)}

TWEETS RÉCENTS:
"""
        
        for i, tweet in enumerate(tweets, 1):
            prompt += f"\n{i}. {tweet}"
        
        prompt += """

ANALYSE ET DÉCIDE:

1. SENTIMENT GLOBAL (positif/neutre/négatif)
2. BUZZ/HYPE (faible/moyen/fort/très fort)
3. SIGNAUX IMPORTANTS (news, influenceurs, FUD)
4. RISQUES DÉTECTÉS (hack, scam, problème technique)
5. DÉCISION FINALE (acheter/vendre/attendre)

RÈGLES DE DÉCISION:
- ACHETER si: Buzz fort + sentiment positif + pas de risque + prix pas trop haut
- VENDRE si: FUD détecté OU risque important OU sentiment très négatif
- ATTENDRE si: Incertain ou pas assez de signal

Réponds UNIQUEMENT en JSON:
{
  "sentiment": "positif/neutre/négatif",
  "sentiment_score": 0.0 à 1.0 (ou -1.0 à 0 si négatif),
  "buzz_level": "faible/moyen/fort/très_fort",
  "key_signals": ["signal1", "signal2"],
  "risks": ["risque1", "risque2"],
  "decision": "ACHETER/VENDRE/ATTENDRE",
  "strategy": "FLIP/HOLD/EXIT",
  "confidence": 0.0 à 1.0,
  "position_size": 0.0 à 0.05 (% du capital),
  "explanation": "Explication courte de la décision"
}
"""
        
        return prompt
    
    async def _call_llm(self, prompt: str) -> Optional[str]:
        """Appeler le LLM selon le provider"""
        try:
            if self.provider == "ollama":
                return await self._call_ollama(prompt)
            elif self.provider == "openai":
                return await self._call_openai(prompt)
            elif self.provider == "anthropic":
                return await self._call_anthropic(prompt)
            else:
                logger.error(f"Provider inconnu: {self.provider}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur appel LLM: {e}")
            return None
    
    async def _call_ollama(self, prompt: str) -> Optional[str]:
        """Appeler Ollama (local, gratuit)"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Plus déterministe
                    "top_p": 0.9
                }
            }
            
            response = await self.client.post(self.base_url, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('response', '')
            else:
                logger.error(f"Ollama error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Ollama: {e}")
            logger.info("💡 Assurez-vous qu'Ollama tourne: ollama serve")
            return None
    
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """Appeler OpenAI ChatGPT"""
        try:
            if not self.api_key:
                logger.error("OpenAI API key not configured")
                return None
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "Tu es un expert en trading crypto. Analyse et décide."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            response = await self.client.post(self.base_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content']
            else:
                logger.error(f"OpenAI error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur OpenAI: {e}")
            return None
    
    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Appeler Anthropic Claude"""
        try:
            if not self.api_key:
                logger.error("Anthropic API key not configured")
                return None
            
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3
            }
            
            response = await self.client.post(self.base_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return data['content'][0]['text']
            else:
                logger.error(f"Anthropic error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Anthropic: {e}")
            return None
    
    def _parse_llm_response(self, response: str, crypto: str) -> Dict:
        """Parser la réponse JSON du LLM"""
        try:
            # Extraire JSON de la réponse
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("❌ Pas de JSON dans réponse LLM")
                return self._default_decision(crypto)
            
            json_str = response[json_start:json_end]
            decision = json.loads(json_str)
            
            # Valider et normaliser
            decision['symbol'] = f"{crypto}/EUR"
            decision['timestamp'] = datetime.now().isoformat()
            decision['source'] = 'llm'
            decision['provider'] = self.provider
            
            # Convertir décision en format standard
            action = decision.get('decision', 'ATTENDRE').upper()
            if action == 'ACHETER':
                decision['action'] = 'BUY'
            elif action == 'VENDRE':
                decision['action'] = 'SELL'
            else:
                decision['action'] = 'HOLD'
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Erreur parsing JSON: {e}")
            logger.debug(f"Réponse: {response[:200]}")
            return self._default_decision(crypto)
        except Exception as e:
            logger.error(f"❌ Erreur parsing réponse: {e}")
            return self._default_decision(crypto)
    
    def _default_decision(self, crypto: str) -> Dict:
        """Décision par défaut si LLM échoue"""
        return {
            'symbol': f"{crypto}/EUR",
            'action': 'HOLD',
            'strategy': 'wait',
            'confidence': 0,
            'position_size': 0,
            'sentiment': 'neutre',
            'sentiment_score': 0,
            'buzz_level': 'inconnu',
            'key_signals': [],
            'risks': [],
            'explanation': 'Pas assez de données ou erreur LLM',
            'timestamp': datetime.now().isoformat(),
            'source': 'llm_fallback'
        }
    
    async def close(self):
        """Fermer le client HTTP"""
        await self.client.aclose()

