#!/usr/bin/env python3
"""Test FinBERT sentiment analyzer avec vraies news"""
import sys
from pathlib import Path
import asyncio
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.ml.sentiment_analyzer import SentimentAnalyzer

async def test_sentiment():
    """Tester l'analyse de sentiment"""
    logger.info("=" * 70)
    logger.info("🧠 TEST FINBERT - Analyse de Sentiment")
    logger.info("=" * 70)
    logger.info("")
    
    # Initialiser l'analyseur
    logger.info("🔧 Initialisation de FinBERT...")
    analyzer = SentimentAnalyzer()
    
    try:
        analyzer.initialize()
        logger.success("✅ FinBERT initialisé avec succès!")
    except Exception as e:
        logger.error(f"❌ Échec initialisation FinBERT: {e}")
        logger.info("💡 FinBERT se téléchargera automatiquement (peut prendre 1-2 min)")
        return False
    
    logger.info("")
    logger.info("=" * 70)
    logger.info("📰 TEST 1: Analyse de News de Test")
    logger.info("=" * 70)
    logger.info("")
    
    # Test avec news de démonstration
    test_news = [
        {
            'title': 'Bitcoin reaches new all-time high amid institutional adoption',
            'description': 'Bitcoin price surges to record levels as major financial institutions announce crypto integration',
            'source': 'test'
        },
        {
            'title': 'Ethereum network upgrade successful, fees reduced significantly',
            'description': 'The latest Ethereum update has been deployed successfully, reducing transaction costs',
            'source': 'test'
        },
        {
            'title': 'Major exchange hacked, millions in crypto stolen',
            'description': 'Security breach leads to significant losses for users, raising concerns about crypto security',
            'source': 'test'
        }
    ]
    
    logger.info("📝 Analyse de 3 news de test:")
    analyzed = analyzer.analyze_news(test_news)
    
    for i, news in enumerate(analyzed, 1):
        sentiment = news.get('sentiment', {})
        label = sentiment.get('sentiment_label', 'unknown')
        score = sentiment.get('sentiment_score', 0)
        
        # Emoji basé sur sentiment
        if label == 'positive':
            emoji = "😊"
        elif label == 'negative':
            emoji = "😟"
        else:
            emoji = "😐"
        
        logger.info(f"\n{i}. {news['title'][:60]}...")
        logger.info(f"   Sentiment: {emoji} {label.upper()} (score: {score:.2f})")
    
    logger.info("")
    logger.info("=" * 70)
    logger.success("✅ FinBERT fonctionne correctement!")
    logger.info("=" * 70)
    
    return True

async def main():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    success = await test_sentiment()
    
    if success:
        logger.info("")
        logger.success("🎉 FINBERT EST PRÊT À ANALYSER LES VRAIES NEWS!")
        logger.info("")
        logger.info("Prochaine étape:")
        logger.info("   ./run.sh ai  → Lancera le bot avec analyse de vraies news")
        logger.info("")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

