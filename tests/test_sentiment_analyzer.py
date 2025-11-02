"""Tests for sentiment analyzer"""
import pytest
from unittest.mock import Mock, patch

from src.ml.sentiment_analyzer import SentimentAnalyzer


@pytest.fixture
def sentiment_analyzer():
    """Create sentiment analyzer with mocked model"""
    with patch('src.ml.sentiment_analyzer.AutoTokenizer'), \
         patch('src.ml.sentiment_analyzer.AutoModelForSequenceClassification'), \
         patch('src.ml.sentiment_analyzer.pipeline') as mock_pipeline:
        
        # Mock pipeline results
        mock_pipeline.return_value = lambda text: [{
            'label': 'positive',
            'score': 0.9
        }]
        
        analyzer = SentimentAnalyzer()
        analyzer.pipeline = mock_pipeline.return_value
        
        return analyzer


def test_analyze_text(sentiment_analyzer):
    """Test single text analysis"""
    result = sentiment_analyzer.analyze_text("Bitcoin is going to the moon!")
    
    assert 'label' in result
    assert 'confidence' in result
    assert 'sentiment_score' in result
    assert result['label'] in ['positive', 'negative', 'neutral']
    assert -1 <= result['sentiment_score'] <= 1


def test_analyze_batch(sentiment_analyzer):
    """Test batch text analysis"""
    texts = [
        "Bitcoin is surging!",
        "Market is crashing",
        "Sideways movement"
    ]
    
    results = sentiment_analyzer.analyze_batch(texts)
    
    assert len(results) == len(texts)
    for result in results:
        assert 'label' in result
        assert 'sentiment_score' in result


def test_analyze_news(sentiment_analyzer):
    """Test news analysis"""
    news_items = [
        {
            'title': 'Bitcoin hits new high',
            'description': 'Price reaches $100k'
        },
        {
            'title': 'Market correction',
            'description': 'Prices falling'
        }
    ]
    
    analyzed = sentiment_analyzer.analyze_news(news_items)
    
    assert len(analyzed) == len(news_items)
    for item in analyzed:
        assert 'sentiment' in item


def test_aggregate_sentiment(sentiment_analyzer):
    """Test sentiment aggregation"""
    items = [
        {'sentiment': {'sentiment_score': 0.8, 'confidence': 0.9}},
        {'sentiment': {'sentiment_score': 0.6, 'confidence': 0.85}},
        {'sentiment': {'sentiment_score': -0.2, 'confidence': 0.7}}
    ]
    
    result = sentiment_analyzer.aggregate_sentiment(items)
    
    assert 'avg_sentiment' in result
    assert 'avg_confidence' in result
    assert 'count' in result
    assert 'positive_count' in result
    assert 'negative_count' in result
    assert 'neutral_count' in result
    
    assert result['count'] == 3
    assert result['positive_count'] >= 0
    assert result['negative_count'] >= 0


def test_aggregate_empty_items(sentiment_analyzer):
    """Test aggregation with empty items"""
    result = sentiment_analyzer.aggregate_sentiment([])
    
    assert result['count'] == 0
    assert result['avg_sentiment'] == 0.0
