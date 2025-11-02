"""Sentiment analysis for news and social media"""
from typing import List, Dict, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from loguru import logger


class SentimentAnalyzer:
    """Analyze sentiment of text using FinBERT and other models"""
    
    def __init__(self, model_name: str = "ProsusAI/finbert"):
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    def initialize(self):
        """Load model and tokenizer"""
        try:
            logger.info(f"Loading sentiment model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            
            # Create pipeline for easier inference
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1
            )
            
            logger.info(f"Loaded sentiment model on {self.device}")
            
        except Exception as e:
            logger.error(f"Failed to load sentiment model: {e}")
            raise
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text
        Returns: dict with 'label' (positive/negative/neutral) and 'score'
        """
        try:
            if not self.pipeline:
                self.initialize()
            
            # Truncate text if too long
            max_length = 512
            if len(text) > max_length:
                text = text[:max_length]
            
            result = self.pipeline(text)[0]
            
            # Convert label to numeric score
            label = result['label'].lower()
            confidence = result['score']
            
            if label == 'positive':
                sentiment_score = confidence
            elif label == 'negative':
                sentiment_score = -confidence
            else:  # neutral
                sentiment_score = 0.0
            
            return {
                'label': label,
                'confidence': confidence,
                'sentiment_score': sentiment_score,
                'text': text[:100]  # Store snippet
            }
            
        except Exception as e:
            logger.error(f"Error analyzing text: {e}")
            return {
                'label': 'neutral',
                'confidence': 0.0,
                'sentiment_score': 0.0,
                'text': text[:100]
            }
    
    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """Analyze sentiment of multiple texts"""
        try:
            if not self.pipeline:
                self.initialize()
            
            # Truncate texts
            max_length = 512
            texts = [t[:max_length] for t in texts]
            
            results = self.pipeline(texts)
            
            analyzed = []
            for text, result in zip(texts, results):
                label = result['label'].lower()
                confidence = result['score']
                
                if label == 'positive':
                    sentiment_score = confidence
                elif label == 'negative':
                    sentiment_score = -confidence
                else:
                    sentiment_score = 0.0
                
                analyzed.append({
                    'label': label,
                    'confidence': confidence,
                    'sentiment_score': sentiment_score,
                    'text': text[:100]
                })
            
            return analyzed
            
        except Exception as e:
            logger.error(f"Error analyzing batch: {e}")
            return [{'label': 'neutral', 'confidence': 0.0, 'sentiment_score': 0.0} for _ in texts]
    
    def analyze_news(self, news_items: List[Dict]) -> List[Dict]:
        """Analyze sentiment for news items"""
        texts = []
        for item in news_items:
            # Combine title and description for better context
            text = f"{item.get('title', '')} {item.get('description', '')}"
            texts.append(text)
        
        sentiments = self.analyze_batch(texts)
        
        # Add sentiment to news items
        for item, sentiment in zip(news_items, sentiments):
            item['sentiment'] = sentiment
        
        return news_items
    
    def analyze_social(self, posts: List[Dict]) -> List[Dict]:
        """Analyze sentiment for social media posts"""
        texts = [post.get('text', '') for post in posts]
        sentiments = self.analyze_batch(texts)
        
        # Add sentiment to posts
        for post, sentiment in zip(posts, sentiments):
            post['sentiment'] = sentiment
        
        return posts
    
    def aggregate_sentiment(self, items: List[Dict], weights: Optional[List[float]] = None) -> Dict:
        """
        Aggregate sentiment from multiple items
        Returns average sentiment and confidence
        """
        if not items:
            return {'avg_sentiment': 0.0, 'avg_confidence': 0.0, 'count': 0}
        
        sentiments = [item.get('sentiment', {}).get('sentiment_score', 0.0) for item in items]
        confidences = [item.get('sentiment', {}).get('confidence', 0.0) for item in items]
        
        if weights and len(weights) == len(sentiments):
            # Weighted average
            avg_sentiment = sum(s * w for s, w in zip(sentiments, weights)) / sum(weights)
        else:
            # Simple average
            avg_sentiment = sum(sentiments) / len(sentiments)
        
        avg_confidence = sum(confidences) / len(confidences)
        
        # Count positive/negative/neutral
        positive = sum(1 for s in sentiments if s > 0.2)
        negative = sum(1 for s in sentiments if s < -0.2)
        neutral = len(sentiments) - positive - negative
        
        return {
            'avg_sentiment': avg_sentiment,
            'avg_confidence': avg_confidence,
            'count': len(items),
            'positive_count': positive,
            'negative_count': negative,
            'neutral_count': neutral,
            'sentiment_ratio': (positive - negative) / len(sentiments) if sentiments else 0.0
        }


class KeywordExtractor:
    """Extract keywords from text using KeyBERT"""
    
    def __init__(self):
        self.model = None
    
    def initialize(self):
        """Initialize KeyBERT model"""
        try:
            from keybert import KeyBERT
            self.model = KeyBERT()
            logger.info("Initialized KeyBERT model")
        except Exception as e:
            logger.error(f"Failed to initialize KeyBERT: {e}")
            raise
    
    def extract_keywords(self, text: str, top_n: int = 5) -> List[tuple]:
        """Extract top keywords from text"""
        try:
            if not self.model:
                self.initialize()
            
            keywords = self.model.extract_keywords(
                text,
                keyphrase_ngram_range=(1, 2),
                stop_words='english',
                top_n=top_n
            )
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            return []
    
    def extract_crypto_mentions(self, text: str) -> List[str]:
        """Extract cryptocurrency mentions from text"""
        crypto_symbols = [
            'BTC', 'ETH', 'SOL', 'ADA', 'DOT', 'MATIC', 'AVAX', 
            'LINK', 'UNI', 'ATOM', 'XRP', 'DOGE', 'SHIB'
        ]
        crypto_names = [
            'bitcoin', 'ethereum', 'solana', 'cardano', 'polkadot',
            'polygon', 'avalanche', 'chainlink', 'uniswap', 'cosmos'
        ]
        
        text_lower = text.lower()
        mentions = []
        
        for symbol in crypto_symbols:
            if symbol.lower() in text_lower:
                mentions.append(symbol)
        
        for name in crypto_names:
            if name in text_lower:
                mentions.append(name.upper()[:3])
        
        return list(set(mentions))  # Remove duplicates
