"""Real-time streaming endpoints for live price and sentiment data."""
import asyncio
import json
import time
import random
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse

from app.core.logging import logger
from app.core.prices import get_daily_prices
from app.core.market_hours import is_market_hours
from app.middleware.rate_limit import limiter
from app.core.memory_cache import get_prediction_file_cached

# Import yfinance for intraday data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance not available for intraday streaming")

router = APIRouter(prefix="/stream", tags=["stream"])

# Global cache for intraday data (symbol -> data)
_intraday_cache: Dict[str, Dict] = {}

# Global state for simulated prices (symbol -> current_price)
_simulated_prices: Dict[str, float] = {}


def _fetch_and_cache_intraday(symbol: str) -> Optional[Dict]:
    """
    Fetch intraday data and cache it.

    Returns:
        Dict with:
        - data: List of {t: timestamp_ms, v: price, o: open, h: high, l: low, volume: int}
        - fetched_at: timestamp when data was fetched
        - market_open: timestamp of market open
        - market_close: timestamp of market close
    """
    try:
        ticker = yf.Ticker(symbol)
        # Get last 1 day of 1-minute data
        df = ticker.history(period="1d", interval="1m")

        if df.empty:
            logger.warning(f"No intraday data for {symbol}")
            return None

        # Convert to list of data points
        data_points = []
        for idx, row in df.iterrows():
            data_points.append({
                "t": int(idx.timestamp() * 1000),  # Convert to milliseconds
                "v": round(float(row['Close']), 2),
                "o": round(float(row['Open']), 2),
                "h": round(float(row['High']), 2),
                "l": round(float(row['Low']), 2),
                "volume": int(row['Volume'])
            })

        # Calculate market hours for today
        from zoneinfo import ZoneInfo
        et_tz = ZoneInfo("America/New_York")
        now_et = datetime.now(et_tz)

        market_open_time = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close_time = now_et.replace(hour=16, minute=0, second=0, microsecond=0)

        cache_entry = {
            "symbol": symbol,
            "data": data_points,
            "fetched_at": int(time.time() * 1000),
            "market_open": int(market_open_time.timestamp() * 1000),
            "market_close": int(market_close_time.timestamp() * 1000),
            "count": len(data_points)
        }

        # Store in cache
        _intraday_cache[symbol] = cache_entry

        logger.info(f"Cached {len(data_points)} intraday points for {symbol}")
        return cache_entry

    except Exception as e:
        logger.error(f"Error fetching intraday data for {symbol}: {e}")
        return None


async def _stream_price_data(symbol: str, interval_sec: float = 1.0, send_cache: bool = True) -> AsyncGenerator[str, None]:
    """
    Stream live price data for a symbol using unified format: {symbol, ts, value}.

    During market hours:
    - First sends full cached intraday data (if send_cache=True)
    - Then streams live updates every interval_sec
    After hours: Sends signal to fetch prediction chart

    Args:
        symbol: Stock ticker symbol
        interval_sec: Seconds between updates (default: 1.0)
        send_cache: Whether to send full cache on initial connection (default: True)
    """
    try:
        market_open = is_market_hours()

        # Get initial/base price (run in thread to avoid blocking)
        try:
            df = await asyncio.to_thread(get_daily_prices, symbol)
            if df.empty:
                base_price = 100.0
                logger.warning(f"No price data for {symbol}, using base price {base_price}")
            else:
                base_price = float(df.iloc[-1]["close"])
        except Exception as e:
            logger.warning(f"Error getting daily prices for {symbol}: {e}, using base price 100.0")
            base_price = 100.0

        logger.info(f"Starting stream for {symbol} at ${base_price:.2f} (market_open={market_open})")

        if market_open and YFINANCE_AVAILABLE:
            # Fetch and cache intraday data (run in thread to avoid blocking)
            cache_entry = await asyncio.to_thread(_fetch_and_cache_intraday, symbol)

            # Send full cache on initial connection (using unified format)
            if send_cache and cache_entry:
                for point in cache_entry["data"]:
                    msg = {
                        "symbol": symbol,
                        "ts": point["t"],  # Already in milliseconds
                        "value": point["v"]  # Close price
                    }
                    yield json.dumps(msg)
                logger.info(f"Sent {cache_entry['count']} cached points for {symbol}")

            # Now stream live updates
            last_fetch = time.time()

            while True:
                timestamp = int(time.time() * 1000)
                market_open = is_market_hours()

                if not market_open:
                    # Market just closed, send after_hours signal
                    # Use special "after_hours" value to signal market close
                    msg = {
                        "symbol": symbol,
                        "ts": timestamp,
                        "value": -1,  # Special value to indicate after hours
                        "_meta": "after_hours"  # Metadata for client
                    }
                    yield json.dumps(msg)
                    break

                # Refresh cache every 60 seconds
                now = time.time()
                if (now - last_fetch) > 60:
                    cache_entry = await asyncio.to_thread(_fetch_and_cache_intraday, symbol)
                    last_fetch = now

                # Stream latest point from cache
                if cache_entry and cache_entry["data"]:
                    # Get the most recent data point
                    latest_point = cache_entry["data"][-1]
                    msg = {
                        "symbol": symbol,
                        "ts": timestamp,
                        "value": latest_point["v"]
                    }
                else:
                    # Fallback to base price
                    msg = {
                        "symbol": symbol,
                        "ts": timestamp,
                        "value": round(base_price, 2)
                    }

                yield json.dumps(msg)
                await asyncio.sleep(interval_sec)
        else:
            # After hours: send signal to stop streaming and show static prediction
            msg = {
                "symbol": symbol,
                "ts": int(time.time() * 1000),
                "value": -1,  # Special value to indicate after hours
                "_meta": "after_hours"  # Metadata for client
            }
            yield json.dumps(msg)

    except Exception as e:
        logger.error(f"Error streaming price data for {symbol}: {e}")
        yield json.dumps({"error": str(e), "symbol": symbol})


async def _stream_sentiment_data(symbol: str, interval_sec: float = 2.0) -> AsyncGenerator[str, None]:
    """
    Stream sentiment score updates for a symbol using unified format: {symbol, ts, value}.

    This aggregates recent article sentiment scores.
    The value represents the average sentiment score (1-5 scale).
    """
    try:
        from app.core.db import SessionLocal
        from app.models.article import Article
        from app.models.score import Score
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
                else:
                    avg_sentiment = 3.0  # Neutral

            msg = {
                "symbol": symbol,
                "ts": timestamp,
                "value": round(avg_sentiment, 2)
            }

            yield json.dumps(msg)
            await asyncio.sleep(interval_sec)

    except Exception as e:
        logger.error(f"Error streaming sentiment data for {symbol}: {e}")
        yield json.dumps({"error": str(e), "symbol": symbol})


@router.get("/sse/price/{symbol}")
@limiter.limit("100/minute")  # Rate limit: 100 requests per minute for SSE connections
async def sse_price(symbol: str, request: Request):
    """
    Server-Sent Events endpoint for real-time price streaming.

    Streams data in unified format: {symbol: str, ts: int, value: float}

    Usage: EventSource('http://localhost:8000/stream/sse/price/AAPL')
    """
    async def event_generator():
        try:
            async for json_data in _stream_price_data(symbol.upper()):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from price stream for {symbol}")
                    break
                # SSE format: "data: <json>\n\n"
                yield f"data: {json_data}\n\n"
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
@limiter.limit("100/minute")  # Rate limit: 100 requests per minute for SSE connections
async def sse_sentiment(symbol: str, request: Request):
    """
    Server-Sent Events endpoint for real-time sentiment streaming.

    Streams data in unified format: {symbol: str, ts: int, value: float}

    Usage: EventSource('http://localhost:8000/stream/sse/sentiment/AAPL')
    """
    async def event_generator():
        try:
            async for json_data in _stream_sentiment_data(symbol.upper()):
                if await request.is_disconnected():
                    logger.info(f"Client disconnected from sentiment stream for {symbol}")
                    break
                # SSE format: "data: <json>\n\n"
                yield f"data: {json_data}\n\n"
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

    Streams data in unified format: {symbol: str, ts: int, value: float}

    Usage: new WebSocket('ws://localhost:8000/stream/ws/price/AAPL')
    """
    await websocket.accept()
    logger.info(f"WebSocket price connection established for {symbol}")

    try:
        async for json_data in _stream_price_data(symbol.upper()):
            # WebSocket sends plain JSON text
            await websocket.send_text(json_data)
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

    Streams data in unified format: {symbol: str, ts: int, value: float}

    Usage: new WebSocket('ws://localhost:8000/stream/ws/sentiment/AAPL')
    """
    await websocket.accept()
    logger.info(f"WebSocket sentiment connection established for {symbol}")

    try:
        async for json_data in _stream_sentiment_data(symbol.upper()):
            # WebSocket sends plain JSON text
            await websocket.send_text(json_data)
    except WebSocketDisconnect:
        logger.info(f"WebSocket sentiment client disconnected for {symbol}")
    except Exception as e:
        logger.error(f"WebSocket sentiment error for {symbol}: {e}")
        try:
            await websocket.send_text(json.dumps({"error": str(e)}))
        except:
            pass


@router.get("/intraday/{symbol}")
@limiter.limit("100/minute")
async def get_intraday_cache(symbol: str, request: Request):
    """
    Get cached intraday data for a symbol.

    Returns full trading day data (1-minute intervals) if available.
    This allows fast propagation of entire trading day without streaming.

    Response:
        {
            "symbol": "AAPL",
            "data": [{t: timestamp_ms, v: price, o: open, h: high, l: low, volume: int}, ...],
            "market_open": timestamp_ms,
            "market_close": timestamp_ms,
            "count": 390,
            "fetched_at": timestamp_ms
        }
    """
    symbol = symbol.upper()

    # Check if we have cached data
    if symbol in _intraday_cache:
        cache_entry = _intraday_cache[symbol]
        # Check if cache is fresh (less than 5 minutes old)
        age_seconds = (time.time() * 1000 - cache_entry["fetched_at"]) / 1000
        if age_seconds < 300:  # 5 minutes
            logger.info(f"Returning cached intraday data for {symbol} (age: {age_seconds:.0f}s)")
            return JSONResponse(content=cache_entry)

    # Fetch fresh data if not cached or stale
    if not YFINANCE_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={"error": "yfinance not available", "symbol": symbol}
        )

    cache_entry = _fetch_and_cache_intraday(symbol)

    if cache_entry:
        return JSONResponse(content=cache_entry)
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "No intraday data available", "symbol": symbol}
        )


# Predictive endpoints
MODELS_DIR = Path(__file__).parent.parent.parent / "models"


@router.get("/sse/predict/line/{symbol}")
@limiter.limit("100/minute")
async def stream_predict_line(request: Request, symbol: str):
    """
    Stream predicted price line for next trading day.

    Returns SSE stream of predicted prices in unified format: {symbol, ts, value}

    The predictions are generated by the after-hours training job (runs at 4:10 PM ET).
    """
    symbol = symbol.upper()

    async def generate():
        try:
            predict_file = MODELS_DIR / f"{symbol}_predict_line.json"

            # Load predictions from cache (1-hour TTL)
            predictions = get_prediction_file_cached(predict_file)

            if predictions is None:
                error_msg = {"error": f"No predictions available for {symbol}", "symbol": symbol}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return

            logger.info(f"Streaming {len(predictions)} predicted points for {symbol} (cached)")

            # Stream each prediction
            for point in predictions:
                yield f"data: {json.dumps(point)}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming

        except Exception as e:
            logger.error(f"Error streaming predictions for {symbol}: {e}")
            error_msg = {"error": str(e), "symbol": symbol}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/sse/predict/signals/{symbol}")
@limiter.limit("100/minute")
async def stream_predict_signals(request: Request, symbol: str):
    """
    Stream predicted BUY/SELL signals for next trading day.

    Returns SSE stream of signals: {symbol, ts, signal, prob, price}
    - signal: "BUY" or "SELL"
    - prob: Confidence probability (0-1)
    - price: Predicted price at signal time
    """
    symbol = symbol.upper()

    async def generate():
        try:
            signals_file = MODELS_DIR / f"{symbol}_predict_signals.json"

            # Load signals from cache (1-hour TTL)
            signals = get_prediction_file_cached(signals_file)

            if signals is None:
                error_msg = {"error": f"No signals available for {symbol}", "symbol": symbol}
                yield f"data: {json.dumps(error_msg)}\n\n"
                return

            logger.info(f"Streaming {len(signals)} predicted signals for {symbol} (cached)")

            # Stream each signal
            for signal in signals:
                yield f"data: {json.dumps(signal)}\n\n"
                await asyncio.sleep(0.01)  # Small delay for smooth streaming

        except Exception as e:
            logger.error(f"Error streaming signals for {symbol}: {e}")
            error_msg = {"error": str(e), "symbol": symbol}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/sse/multiplex")
@limiter.limit("100/minute")
async def stream_multiplexed(
    request: Request,
    symbols: str,
    types: str,
    interval: float = 1.0
):
    """
    Stream multiple data types for multiple symbols in one SSE connection.

    This endpoint multiplexes all requested streams into a single connection,
    reducing the number of concurrent SSE connections from 18 (6 per stock × 3 stocks)
    to just 1.

    Args:
        symbols: Comma-separated list of symbols (e.g., "TSLA,MSFT,META")
        types: Comma-separated list of data types (e.g., "price,predict_line,predict_signals")
               Valid types: price, predict_line, predict_signals
        interval: Interval in seconds for price updates (default: 1.0)

    Returns:
        SSE stream with events tagged by type and symbol

    Example event format:
        data: {"type": "price", "symbol": "TSLA", "ts": 1234567890, "value": 250.50}
        data: {"type": "predict_line", "symbol": "TSLA", "t": 1234567890, "v": 251.00}
        data: {"type": "predict_signals", "symbol": "TSLA", "action": "buy", "price": 250.00}
    """
    symbol_list = [s.strip().upper() for s in symbols.split(',') if s.strip()]
    type_list = [t.strip().lower() for t in types.split(',') if t.strip()]

    if not symbol_list:
        return JSONResponse({"error": "No symbols provided"}, status_code=400)

    if not type_list:
        return JSONResponse({"error": "No types provided"}, status_code=400)

    # Validate types
    valid_types = {"price", "predict_line", "predict_signals"}
    invalid_types = set(type_list) - valid_types
    if invalid_types:
        return JSONResponse(
            {"error": f"Invalid types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_types)}"},
            status_code=400
        )

    logger.info(f"Starting multiplexed stream for symbols={symbol_list}, types={type_list}")

    async def generate():
        """Generate multiplexed SSE stream."""
        try:
            # For static data (predict_line, predict_signals), send once at start
            # For dynamic data (price), stream continuously

            # First, send all static data
            for symbol in symbol_list:
                for data_type in type_list:
                    if data_type == "predict_line":
                        async for event in _multiplex_predict_line_stream(symbol):
                            yield event
                    elif data_type == "predict_signals":
                        async for event in _multiplex_predict_signals_stream(symbol):
                            yield event

            # Then, if price is requested, stream it continuously
            if "price" in type_list:
                # Stream prices for all symbols in round-robin fashion
                while True:
                    for symbol in symbol_list:
                        async for event in _multiplex_price_stream(symbol, interval):
                            yield event
                            # Only send one price update per symbol per iteration
                            break
                    # Small delay between rounds
                    await asyncio.sleep(interval)
            else:
                # No continuous streaming, just send completion message
                completion_msg = {"type": "complete", "message": "All data sent"}
                yield f"data: {json.dumps(completion_msg)}\n\n"

        except Exception as e:
            logger.error(f"Error in multiplexed stream generator: {e}")
            error_msg = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_msg)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def _multiplex_price_stream(symbol: str, interval: float) -> AsyncGenerator[str, None]:
    """Generate price events for multiplexed stream."""
    async for event_data in _stream_price_data(symbol, interval, send_cache=True):
        # event_data is already formatted as "data: {...}\n\n"
        # We need to parse it and add type field
        if event_data.startswith("data: "):
            try:
                json_str = event_data[6:].strip()
                data = json.loads(json_str)
                data["type"] = "price"
                yield f"data: {json.dumps(data)}\n\n"
            except:
                yield event_data
        else:
            yield event_data


async def _multiplex_predict_line_stream(symbol: str) -> AsyncGenerator[str, None]:
    """Generate predict line events for multiplexed stream."""
    try:
        MODELS_DIR = Path(__file__).parent.parent.parent / "models"
        predict_file = MODELS_DIR / f"{symbol}_predict_line.json"

        # Load predictions from cache (1-hour TTL)
        predictions = get_prediction_file_cached(predict_file)

        if predictions is None:
            error_msg = {"type": "predict_line", "error": f"No predictions available for {symbol}", "symbol": symbol}
            yield f"data: {json.dumps(error_msg)}\n\n"
            return

        logger.info(f"Streaming {len(predictions)} predicted points for {symbol} (cached, multiplexed)")

        # Stream each prediction point
        for point in predictions:
            point["type"] = "predict_line"
            point["symbol"] = symbol
            yield f"data: {json.dumps(point)}\n\n"
            await asyncio.sleep(0.01)  # Small delay for smooth streaming

    except Exception as e:
        logger.error(f"Error streaming predictions for {symbol}: {e}")
        error_msg = {"type": "predict_line", "error": str(e), "symbol": symbol}
        yield f"data: {json.dumps(error_msg)}\n\n"


async def _multiplex_predict_signals_stream(symbol: str) -> AsyncGenerator[str, None]:
    """Generate predict signals events for multiplexed stream."""
    try:
        MODELS_DIR = Path(__file__).parent.parent.parent / "models"
        signals_file = MODELS_DIR / f"{symbol}_predict_signals.json"

        # Load signals from cache (1-hour TTL)
        signals = get_prediction_file_cached(signals_file)

        if signals is None:
            error_msg = {"type": "predict_signals", "error": f"No signals available for {symbol}", "symbol": symbol}
            yield f"data: {json.dumps(error_msg)}\n\n"
            return

        logger.info(f"Streaming {len(signals)} predicted signals for {symbol} (cached, multiplexed)")

        # Stream each signal
        for signal in signals:
            signal["type"] = "predict_signals"
            signal["symbol"] = symbol
            yield f"data: {json.dumps(signal)}\n\n"
            await asyncio.sleep(0.01)  # Small delay for smooth streaming

    except Exception as e:
        logger.error(f"Error streaming signals for {symbol}: {e}")
        error_msg = {"type": "predict_signals", "error": str(e), "symbol": symbol}
        yield f"data: {json.dumps(error_msg)}\n\n"

