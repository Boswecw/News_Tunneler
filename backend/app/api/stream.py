"""Real-time streaming endpoints for live price and sentiment data."""
import asyncio
import json
import time
from typing import AsyncGenerator
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse

from app.core.logging import logger
from app.core.prices import get_daily_prices
from app.core.market_hours import is_market_hours

# Import yfinance for intraday data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available for intraday streaming")

router = APIRouter(prefix="/stream", tags=["stream"])


async def _stream_price_data(symbol: str, interval_sec: float = 1.0) -> AsyncGenerator[str, None]:
    """
    Stream live price data for a symbol.

    During market hours: Fetches real intraday data from yfinance (1-minute intervals)
    After hours: Shows last known price with small simulated movements
    """
    try:
        market_open = is_market_hours()

        # Get initial/base price
        df = get_daily_prices(symbol)
        if df.empty:
            base_price = 100.0
            logger.warning(f"No price data for {symbol}, using base price {base_price}")
        else:
            base_price = float(df.iloc[-1]["close"])

        logger.info(f"Starting stream for {symbol} at ${base_price:.2f} (market_open={market_open})")

        # Track last intraday fetch time
        last_fetch = None
        intraday_data = None
        current_idx = 0

        while True:
            timestamp = int(time.time() * 1000)
            market_open = is_market_hours()

            if market_open and YFINANCE_AVAILABLE:
                # Fetch real intraday data every 60 seconds
                now = time.time()
                if last_fetch is None or (now - last_fetch) > 60:
                    try:
                        ticker = yf.Ticker(symbol)
                        # Get last 1 day of 1-minute data
                        intraday_data = ticker.history(period="1d", interval="1m")
                        last_fetch = now
                        current_idx = 0

                        if not intraday_data.empty:
                            logger.debug(f"Fetched {len(intraday_data)} intraday points for {symbol}")
                    except Exception as e:
                        logger.error(f"Error fetching intraday data for {symbol}: {e}")
                        intraday_data = None

                # Stream from intraday data if available
                if intraday_data is not None and not intraday_data.empty:
                    # Cycle through intraday data points
                    if current_idx >= len(intraday_data):
                        current_idx = 0

                    row = intraday_data.iloc[current_idx]
                    price = float(row['Close'])
                    current_idx += 1

                    data = {
                        "symbol": symbol,
                        "t": timestamp,
                        "v": round(price, 2),
                        "type": "price",
                        "source": "intraday"
                    }
                else:
                    # Fallback to base price if intraday fetch failed
                    data = {
                        "symbol": symbol,
                        "t": timestamp,
                        "v": round(base_price, 2),
                        "type": "price",
                        "source": "daily"
                    }
            else:
                # After hours: send signal to stop streaming and show static prediction
                data = {
                    "symbol": symbol,
                    "type": "price",
                    "source": "after_hours",
                    "message": "Market closed. Fetch prediction chart."
                }
                yield json.dumps(data)
                # Don't continue streaming after hours
                break

            await asyncio.sleep(interval_sec)

    except Exception as e:
        logger.error(f"Error streaming price data for {symbol}: {e}")
        yield json.dumps({"error": str(e), "symbol": symbol})


async def _stream_sentiment_data(symbol: str, interval_sec: float = 2.0) -> AsyncGenerator[str, None]:
    """
    Stream sentiment score updates for a symbol.

    This aggregates recent article sentiment scores and includes ML prediction.
    """
    try:
        from app.core.db import SessionLocal
        from app.models.article import Article
        from app.models.score import Score
        from app.models.signal import Signal
        from sqlalchemy import func, desc

        while True:
            timestamp = int(time.time() * 1000)

            with SessionLocal() as db:
                # Get articles from last 24 hours with this ticker
                recent_articles = (
                    db.query(Article, Score)
                    .join(Score, Article.id == Score.article_id)
                    .filter(Article.ticker_guess == symbol)
                    .filter(Article.published_at >= func.datetime('now', '-1 day'))
                    .order_by(desc(Article.published_at))
                    .limit(10)
                    .all()
                )

                if recent_articles:
                    avg_sentiment = sum(score.sentiment for _, score in recent_articles) / len(recent_articles)
                    article_count = len(recent_articles)
                else:
                    avg_sentiment = 3.0  # Neutral
                    article_count = 0

                # Get latest signal/prediction for this symbol
                latest_signal = (
                    db.query(Signal)
                    .filter(Signal.symbol == symbol)
                    .order_by(desc(Signal.t))
                    .first()
                )

                prediction_score = None
                prediction_label = None
                if latest_signal:
                    prediction_score = latest_signal.score
                    prediction_label = latest_signal.label

            data = {
                "symbol": symbol,
                "t": timestamp,
                "v": round(avg_sentiment, 2),
                "count": article_count,
                "type": "sentiment",
                "prediction_score": prediction_score,
                "prediction_label": prediction_label,
            }

            yield json.dumps(data)
            await asyncio.sleep(interval_sec)

    except Exception as e:
        logger.error(f"Error streaming sentiment data for {symbol}: {e}")
        yield json.dumps({"error": str(e), "symbol": symbol})


@router.get("/sse/price/{symbol}")
async def sse_price(symbol: str, request: Request):
    """
    Server-Sent Events endpoint for real-time price streaming.
    
    Usage: EventSource('http://localhost:8000/stream/sse/price/AAPL')
    """
    async def event_generator():
        try:
            async for data in _stream_price_data(symbol.upper()):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from price stream for {symbol}")
                    break
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"SSE price stream error for {symbol}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.get("/sse/sentiment/{symbol}")
async def sse_sentiment(symbol: str, request: Request):
    """
    Server-Sent Events endpoint for real-time sentiment streaming.
    
    Usage: EventSource('http://localhost:8000/stream/sse/sentiment/AAPL')
    """
    async def event_generator():
        try:
            async for data in _stream_sentiment_data(symbol.upper()):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from sentiment stream for {symbol}")
                    break
                yield f"data: {data}\n\n"
        except Exception as e:
            logger.error(f"SSE sentiment stream error for {symbol}: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.websocket("/ws/price/{symbol}")
async def ws_price(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time price streaming.
    
    Usage: new WebSocket('ws://localhost:8000/stream/ws/price/AAPL')
    """
    await websocket.accept()
    logger.info(f"WebSocket price connection established for {symbol}")
    
    try:
        async for data in _stream_price_data(symbol.upper()):
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket price client disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket price error for {symbol}: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass


@router.websocket("/ws/sentiment/{symbol}")
async def ws_sentiment(websocket: WebSocket, symbol: str):
    """
    WebSocket endpoint for real-time sentiment streaming.
    
    Usage: new WebSocket('ws://localhost:8000/stream/ws/sentiment/AAPL')
    """
    await websocket.accept()
    logger.info(f"WebSocket sentiment connection established for {symbol}")
    
    try:
        async for data in _stream_sentiment_data(symbol.upper()):
            await websocket.send_text(data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket sentiment client disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket sentiment error for {symbol}: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass

