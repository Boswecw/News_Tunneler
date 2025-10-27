"""Sentiment analysis using VADER."""
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

analyzer = SentimentIntensityAnalyzer()


def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment of text using VADER.
    
    Returns a score mapped to [1, 3, 4]:
    - 1 for negative (compound <= -0.2)
    - 3 for neutral (-0.2 < compound < 0.2)
    - 4 for positive (compound >= 0.2)
    """
    if not text:
        return 3.0  # Default to neutral
    
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    
    if compound <= -0.2:
        return 1.0
    elif compound < 0.2:
        return 3.0
    else:
        return 4.0

