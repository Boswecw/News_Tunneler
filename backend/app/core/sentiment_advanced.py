"""
Advanced sentiment analysis using FinBERT.

Combines VADER (rule-based) with FinBERT (transformer-based) for
financial-specific sentiment analysis with confidence scoring.
"""
import logging
from typing import Dict, Optional, Tuple
from functools import lru_cache
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# FinBERT model name
FINBERT_MODEL = "ProsusAI/finbert"

# Cache for model and tokenizer
_finbert_pipeline = None

# VADER analyzer
_vader_analyzer = SentimentIntensityAnalyzer()


@lru_cache(maxsize=1)
def get_finbert_pipeline():
    """
    Get or create FinBERT sentiment analysis pipeline.
    
    Uses LRU cache to load model only once.
    
    Returns:
        HuggingFace pipeline for sentiment analysis
    """
    global _finbert_pipeline
    
    if _finbert_pipeline is None:
        try:
            logger.info(f"Loading FinBERT model: {FINBERT_MODEL}")
            
            # Load model and tokenizer
            tokenizer = AutoTokenizer.from_pretrained(FINBERT_MODEL)
            model = AutoModelForSequenceClassification.from_pretrained(FINBERT_MODEL)
            
            # Create pipeline
            _finbert_pipeline = pipeline(
                "sentiment-analysis",
                model=model,
                tokenizer=tokenizer,
                device=0 if torch.cuda.is_available() else -1  # Use GPU if available
            )
            
            logger.info("FinBERT model loaded successfully")
        
        except Exception as e:
            logger.error(f"Error loading FinBERT model: {e}")
            raise
    
    return _finbert_pipeline


def analyze_finbert_sentiment(text: str, max_length: int = 512) -> Dict:
    """
    Analyze sentiment using FinBERT.
    
    Args:
        text: Text to analyze
        max_length: Maximum text length (FinBERT limit is 512 tokens)
        
    Returns:
        Dict with sentiment label, score, and confidence
    """
    try:
        # Get pipeline
        finbert = get_finbert_pipeline()
        
        # Truncate text if too long
        if len(text) > max_length * 4:  # Rough estimate: 4 chars per token
            text = text[:max_length * 4]
        
        # Analyze sentiment
        result = finbert(text)[0]
        
        # Map FinBERT labels to scores
        # FinBERT outputs: positive, negative, neutral
        label = result['label'].lower()
        confidence = result['score']
        
        if label == 'positive':
            sentiment_score = confidence  # 0 to 1
        elif label == 'negative':
            sentiment_score = -confidence  # -1 to 0
        else:  # neutral
            sentiment_score = 0.0
        
        return {
            'sentiment': float(sentiment_score),
            'label': label,
            'confidence': float(confidence),
            'model': 'finbert'
        }
    
    except Exception as e:
        logger.error(f"Error in FinBERT sentiment analysis: {e}")
        # Return neutral sentiment on error
        return {
            'sentiment': 0.0,
            'label': 'neutral',
            'confidence': 0.0,
            'model': 'finbert',
            'error': str(e)
        }


def analyze_combined_sentiment(
    text: str,
    vader_weight: float = 0.3,
    finbert_weight: float = 0.7
) -> Dict:
    """
    Analyze sentiment using both VADER and FinBERT with weighted combination.
    
    Args:
        text: Text to analyze
        vader_weight: Weight for VADER sentiment (default: 0.3)
        finbert_weight: Weight for FinBERT sentiment (default: 0.7)
        
    Returns:
        Dict with combined sentiment, individual scores, and confidence
    """
    # Normalize weights
    total_weight = vader_weight + finbert_weight
    vader_weight = vader_weight / total_weight
    finbert_weight = finbert_weight / total_weight
    
    # Get VADER sentiment
    vader_result = _vader_analyzer.polarity_scores(text)
    vader_score = vader_result['compound']  # -1 to 1
    
    # Get FinBERT sentiment
    finbert_result = analyze_finbert_sentiment(text)
    finbert_score = finbert_result['sentiment']  # -1 to 1
    finbert_confidence = finbert_result['confidence']
    
    # Combine sentiments with weights
    combined_sentiment = (
        vader_score * vader_weight +
        finbert_score * finbert_weight
    )
    
    # Calculate overall confidence (use FinBERT confidence as primary)
    overall_confidence = finbert_confidence
    
    # Determine label based on combined sentiment
    if combined_sentiment > 0.05:
        label = 'positive'
    elif combined_sentiment < -0.05:
        label = 'negative'
    else:
        label = 'neutral'
    
    return {
        'sentiment': float(combined_sentiment),
        'label': label,
        'confidence': float(overall_confidence),
        'vader_score': float(vader_score),
        'finbert_score': float(finbert_score),
        'vader_weight': float(vader_weight),
        'finbert_weight': float(finbert_weight),
        'model': 'combined'
    }


def analyze_sentiment_with_fallback(text: str, use_finbert: bool = True) -> Dict:
    """
    Analyze sentiment with fallback to VADER if FinBERT fails.
    
    Args:
        text: Text to analyze
        use_finbert: Whether to use FinBERT (falls back to VADER if False or on error)
        
    Returns:
        Dict with sentiment analysis results
    """
    if not use_finbert:
        # Use VADER only
        vader_result = _vader_analyzer.polarity_scores(text)
        return {
            'sentiment': float(vader_result['compound']),
            'label': 'positive' if vader_result['compound'] > 0.05 else 'negative' if vader_result['compound'] < -0.05 else 'neutral',
            'confidence': float(abs(vader_result['compound'])),
            'model': 'vader'
        }

    try:
        # Try combined sentiment
        return analyze_combined_sentiment(text)

    except Exception as e:
        logger.warning(f"FinBERT failed, falling back to VADER: {e}")

        # Fallback to VADER
        vader_result = _vader_analyzer.polarity_scores(text)
        return {
            'sentiment': float(vader_result['compound']),
            'label': 'positive' if vader_result['compound'] > 0.05 else 'negative' if vader_result['compound'] < -0.05 else 'neutral',
            'confidence': float(abs(vader_result['compound'])),
            'model': 'vader',
            'fallback': True,
            'error': str(e)
        }


def batch_analyze_sentiment(
    texts: list[str],
    use_finbert: bool = True,
    batch_size: int = 8
) -> list[Dict]:
    """
    Analyze sentiment for multiple texts in batches.
    
    Args:
        texts: List of texts to analyze
        use_finbert: Whether to use FinBERT
        batch_size: Batch size for FinBERT processing
        
    Returns:
        List of sentiment analysis results
    """
    if not use_finbert:
        # Use VADER for all texts
        return [analyze_sentiment_with_fallback(text, use_finbert=False) for text in texts]
    
    try:
        # Get FinBERT pipeline
        finbert = get_finbert_pipeline()
        
        # Process in batches
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Get FinBERT results for batch
            finbert_results = finbert(batch)
            
            # Get VADER results for batch
            vader_results = [vader_sentiment(text) for text in batch]
            
            # Combine results
            for text, finbert_res, vader_res in zip(batch, finbert_results, vader_results):
                # Map FinBERT result
                label = finbert_res['label'].lower()
                confidence = finbert_res['score']
                
                if label == 'positive':
                    finbert_score = confidence
                elif label == 'negative':
                    finbert_score = -confidence
                else:
                    finbert_score = 0.0
                
                vader_score = vader_res['compound']
                
                # Combine with default weights
                combined_sentiment = vader_score * 0.3 + finbert_score * 0.7
                
                results.append({
                    'sentiment': float(combined_sentiment),
                    'label': 'positive' if combined_sentiment > 0.05 else 'negative' if combined_sentiment < -0.05 else 'neutral',
                    'confidence': float(confidence),
                    'vader_score': float(vader_score),
                    'finbert_score': float(finbert_score),
                    'model': 'combined'
                })
        
        return results
    
    except Exception as e:
        logger.error(f"Batch sentiment analysis failed: {e}")
        # Fallback to VADER for all
        return [analyze_sentiment_with_fallback(text, use_finbert=False) for text in texts]


def get_sentiment_magnitude(sentiment_score: float) -> float:
    """
    Convert sentiment score to magnitude (0-5 scale).
    
    Args:
        sentiment_score: Sentiment score (-1 to 1)
        
    Returns:
        Magnitude score (0-5)
    """
    # Map absolute sentiment to 0-5 scale
    magnitude = abs(sentiment_score) * 5.0
    return float(magnitude)

