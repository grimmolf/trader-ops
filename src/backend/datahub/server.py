"""
DataHub FastAPI Server - Core trading data aggregation and distribution.

Implements:
- TradingView UDF protocol for charts (/udf/*)
- Real-time WebSocket streaming (/stream)
- REST API for quotes, history, symbols (/api/v1/*)
- TradingView webhook endpoints (/webhook/tradingview)
- Alert management and Chronos integration

Compatible with Tradier, CCXT, and future data sources.
"""

import asyncio
import json
import logging
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings

from ..models.market_data import (
    Candle, Quote, Symbol, HistoryRequest, HistoryResponse, TimeFrame
)
from ..models.alerts import Alert, AlertEvent, AlertStatus
from ..models.execution import Order, Execution, Position, Account
from ..feeds.tradier import TradierConnector
from ..feeds.tradovate.manager import TradovateManager
from ..feeds.tradovate.auth import TradovateCredentials
from ..services.backtest_service import (
    BacktestService, BacktestRequest, BacktestJob, BacktestStatus, get_backtest_service
)
from ..webhooks import tradingview_router
from ..webhooks.tradingview_receiver import set_global_instances


# Configuration
class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Server configuration
    host: str = "localhost"
    port: int = 8080
    debug: bool = True
    
    # Data sources
    tradier_api_key: Optional[str] = None
    tradier_account_id: Optional[str] = None
    tradier_base_url: str = "https://api.tradier.com"
    tradier_ws_url: str = "wss://ws.tradier.com"
    
    # TradingView configuration
    tradingview_webhook_secret: Optional[str] = None
    
    # Tradovate configuration
    tradovate_username: Optional[str] = None
    tradovate_password: Optional[str] = None
    tradovate_app_id: Optional[str] = None
    tradovate_demo: bool = True
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Alert system
    chronos_webhook_url: str = "http://localhost:5000/webhook"
    
    class Config:
        env_file = ".env"


# Global state
settings = Settings()
logger = logging.getLogger(__name__)

# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time data streaming"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, symbols: List[str]):
        """Subscribe connection to symbols"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].update(symbols)
            await websocket.send_text(json.dumps({
                "type": "subscription_confirmed",
                "symbols": list(self.subscriptions[websocket])
            }))
    
    async def unsubscribe(self, websocket: WebSocket, symbols: List[str]):
        """Unsubscribe connection from symbols"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].difference_update(symbols)
    
    async def broadcast_quote(self, quote: Quote):
        """Broadcast quote to subscribed connections"""
        if not self.active_connections:
            return
            
        message = {
            "type": "quote",
            "data": quote.dict()
        }
        
        disconnected = []
        for websocket in self.active_connections:
            if quote.symbol in self.subscriptions.get(websocket, set()):
                try:
                    await websocket.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Error sending to WebSocket: {e}")
                    disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        message_str = json.dumps(message)
        disconnected = []
        
        for websocket in self.active_connections:
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.warning(f"Failed to send to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def broadcast_account_update(self, account_data: dict):
        """Broadcast account update to all connections"""
        await self.broadcast_to_all({
            "type": "account",
            "data": account_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    async def broadcast_positions_update(self, positions_data: list):
        """Broadcast positions update to all connections"""
        await self.broadcast_to_all({
            "type": "positions", 
            "data": positions_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })


# Global instances
connection_manager = ConnectionManager()
tradier_connector: Optional[TradierConnector] = None
tradovate_manager: Optional[TradovateManager] = None
active_alerts: Dict[str, Alert] = {}


async def broadcast_mock_data():
    """Periodically broadcast mock data updates"""
    import random
    
    while True:
        try:
            await asyncio.sleep(5)  # Update every 5 seconds
            
            if connection_manager.active_connections:
                # Update account P&L with small random changes
                mock_account.day_pnl += random.uniform(-50, 50)
                mock_account.total_pnl += random.uniform(-25, 25)
                
                # Update position P&L
                for position in mock_positions:
                    position.day_pnl += random.uniform(-10, 10)
                    position.total_pnl += random.uniform(-5, 5)
                
                # Broadcast updates
                await connection_manager.broadcast_account_update(mock_account.dict())
                await connection_manager.broadcast_positions_update([pos.dict() for pos in mock_positions])
                
                # Send mock quotes for watchlist symbols
                watchlist_symbols = ['MNQ1!', 'ES1!', 'NQ1!', 'RTY1!', 'YM1!']
                quotes = []
                for symbol in watchlist_symbols:
                    base_price = 17900.0 if 'MNQ' in symbol else 4750.0 if 'ES' in symbol else 18500.0
                    price = base_price + random.uniform(-50, 50)
                    change = random.uniform(-25, 25)
                    change_percent = (change / base_price) * 100
                    
                    quote = Quote(
                        symbol=symbol,
                        price=price,
                        change=change,
                        change_percent=change_percent,
                        volume=random.randint(1000, 10000),
                        timestamp=int(time.time())
                    )
                    quotes.append(quote.dict())
                
                # Broadcast quotes
                await connection_manager.broadcast_to_all({
                    "type": "quotes",
                    "data": quotes,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error in mock data broadcast: {e}")
            await asyncio.sleep(1)

# Application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown"""
    global tradier_connector, tradovate_manager
    
    # Startup
    logger.info("Starting DataHub server...")
    
    # Initialize Tradier connector
    if settings.tradier_api_key:
        tradier_connector = TradierConnector(
            api_key=settings.tradier_api_key,
            account_id=settings.tradier_account_id,
            base_url=settings.tradier_base_url,
            ws_url=settings.tradier_ws_url
        )
        logger.info("Tradier connector initialized")
    else:
        logger.warning("Tradier API key not provided - using mock data")
    
    # Initialize Tradovate manager
    if settings.tradovate_username and settings.tradovate_password and settings.tradovate_app_id:
        try:
            tradovate_credentials = TradovateCredentials(
                username=settings.tradovate_username,
                password=settings.tradovate_password,
                app_id=settings.tradovate_app_id,
                demo=settings.tradovate_demo
            )
            tradovate_manager = TradovateManager(tradovate_credentials)
            await tradovate_manager.initialize()
            logger.info(f"Tradovate manager initialized in {'demo' if settings.tradovate_demo else 'live'} mode")
        except Exception as e:
            logger.error(f"Failed to initialize Tradovate manager: {e}")
            tradovate_manager = None
    else:
        logger.warning("Tradovate credentials not provided - futures trading unavailable")
    
    # Set global instances for webhook processor
    set_global_instances(settings, tradovate_manager, connection_manager)
    logger.info("Webhook processor configured with global instances")
    
    # Start mock data broadcasting task
    mock_data_task = asyncio.create_task(broadcast_mock_data())
    logger.info("Mock data broadcasting started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down DataHub server...")
    mock_data_task.cancel()
    if tradier_connector:
        await tradier_connector.close()
    if tradovate_manager:
        # TradovateManager doesn't have a close method, but auth tokens will expire
        logger.info("Tradovate manager shutdown")


# FastAPI app
app = FastAPI(
    title="Trader Dashboard DataHub",
    description="Real-time trading data aggregation and distribution service",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include webhook router
app.include_router(tradingview_router)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "version": "1.0.0",
        "tradier_connected": tradier_connector is not None,
        "tradovate_connected": tradovate_manager is not None,
        "active_connections": len(connection_manager.active_connections)
    }


# ============================================================================
# TradingView UDF Protocol Implementation
# ============================================================================

@app.get("/udf/config")
async def udf_config():
    """TradingView UDF configuration endpoint"""
    return {
        "supported_resolutions": ["1", "5", "15", "30", "60", "240", "D", "W"],
        "supports_group_request": False,
        "supports_marks": False,
        "supports_search": True,
        "supports_timescale_marks": False,
        "exchanges": [
            {"value": "NASDAQ", "name": "NASDAQ", "desc": "NASDAQ"},
            {"value": "NYSE", "name": "NYSE", "desc": "New York Stock Exchange"},
            {"value": "CRYPTO", "name": "CRYPTO", "desc": "Cryptocurrency"}
        ],
        "symbols_types": [
            {"name": "All types", "value": ""},
            {"name": "Stock", "value": "stock"},
            {"name": "Index", "value": "index"},
            {"name": "Forex", "value": "forex"},
            {"name": "Bitcoin", "value": "bitcoin"}
        ],
        "currency_codes": ["USD", "EUR", "GBP", "JPY"]
    }


@app.get("/udf/symbols")
async def udf_symbols(symbol: str):
    """TradingView UDF symbol info endpoint"""
    try:
        # Get symbol metadata
        if tradier_connector:
            symbol_info = await tradier_connector.get_symbol_info(symbol)
        else:
            # Mock data for development
            symbol_info = Symbol.from_tradier_symbol(symbol, f"{symbol} Corp")
        
        return {
            "name": symbol_info.symbol,
            "full_name": symbol_info.full_name,
            "description": symbol_info.description,
            "exchange": symbol_info.exchange,
            "type": symbol_info.type,
            "session": symbol_info.session,
            "timezone": symbol_info.timezone,
            "minmov": symbol_info.minmov,
            "pricescale": symbol_info.pricescale,
            "has_intraday": symbol_info.has_intraday,
            "has_weekly_and_monthly": symbol_info.has_weekly,
            "supported_resolutions": symbol_info.supported_resolutions,
            "volume_precision": 0,
            "data_status": "streaming"
        }
    except Exception as e:
        logger.error(f"Error getting symbol info for {symbol}: {e}")
        raise HTTPException(status_code=404, detail="Symbol not found")


@app.get("/udf/history")
async def udf_history(
    symbol: str,
    resolution: str,
    from_ts: int = 0,  # from parameter (renamed to avoid Python keyword)
    to: int = 0,
    countback: Optional[int] = None
):
    """TradingView UDF historical data endpoint"""
    try:
        # Create history request
        request = HistoryRequest(
            symbol=symbol,
            resolution=resolution,
            from_ts=from_ts,
            to_ts=to,
            countback=countback
        )
        
        # Get historical data
        if tradier_connector:
            history = await tradier_connector.get_history(request)
        else:
            # Mock data for development
            history = _generate_mock_history(request)
        
        return history.to_udf_format()
        
    except ValidationError as e:
        logger.error(f"Invalid history request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting history for {symbol}: {e}")
        return {"s": "error", "errmsg": str(e)}


@app.get("/udf/search")
async def udf_search(query: str, type: str = "", exchange: str = "", limit: int = 50):
    """TradingView UDF symbol search endpoint"""
    try:
        if tradier_connector:
            results = await tradier_connector.search_symbols(query, limit=limit)
        else:
            # Mock search results
            results = _generate_mock_search(query, limit)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching symbols for '{query}': {e}")
        return []


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.get("/api/v1/quotes")
async def get_quotes(symbols: str):
    """Get current quotes for symbols"""
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    try:
        if tradier_connector:
            quotes = await tradier_connector.get_quotes(symbol_list)
        else:
            # Mock quotes
            quotes = [_generate_mock_quote(symbol) for symbol in symbol_list]
        
        return {"quotes": [quote.dict() for quote in quotes]}
        
    except Exception as e:
        logger.error(f"Error getting quotes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/symbols/search")
async def search_symbols(q: str, limit: int = 20):
    """Search for trading symbols"""
    try:
        if tradier_connector:
            results = await tradier_connector.search_symbols(q, limit=limit)
        else:
            results = _generate_mock_search(q, limit)
        
        return {"symbols": results}
        
    except Exception as e:
        logger.error(f"Error searching symbols: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WebSocket Real-time Streaming
# ============================================================================

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming"""
    await connection_manager.connect(websocket)
    
    try:
        while True:
            # Receive subscription messages
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                if message.get("action") == "subscribe":
                    symbols = message.get("symbols", [])
                    await connection_manager.subscribe(websocket, symbols)
                    logger.info(f"WebSocket subscribed to: {symbols}")
                
                elif message.get("action") == "unsubscribe":
                    symbols = message.get("symbols", [])
                    await connection_manager.unsubscribe(websocket, symbols)
                    logger.info(f"WebSocket unsubscribed from: {symbols}")
                
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message"
                }))
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


# ============================================================================
# TradingView Webhook Endpoints - Now handled by enhanced webhook module
# ============================================================================
# Webhook endpoints moved to ../webhooks/tradingview_receiver.py for improved
# security, validation, and processing capabilities.


# ============================================================================
# Alert Management
# ============================================================================

@app.post("/api/v1/alerts")
async def create_alert(alert: Alert):
    """Create a new alert"""
    try:
        active_alerts[alert.id] = alert
        logger.info(f"Created alert: {alert.id} for {alert.symbol}")
        return {"status": "created", "alert_id": alert.id}
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/alerts")
async def get_alerts():
    """Get all active alerts"""
    return {"alerts": [alert.dict() for alert in active_alerts.values()]}


@app.delete("/api/v1/alerts/{alert_id}")
async def delete_alert(alert_id: str):
    """Delete an alert"""
    if alert_id in active_alerts:
        del active_alerts[alert_id]
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Alert not found")


# ============================================================================
# Trading API Endpoints
# ============================================================================

# Mock data stores for development
mock_account = Account(
    account_id="test_account_001",
    broker="tradier",
    account_type="margin",
    total_equity=50000.0,
    cash_balance=25000.0,
    buying_power=100000.0,
    day_trade_buying_power=75000.0,
    day_pnl=1250.0,
    total_pnl=8750.0,
    is_active=True,
    pattern_day_trader=False
)

mock_positions = [
    Position(
        symbol="MNQ1!",
        account_id="test_account_001",
        quantity=2.0,
        avg_price=17850.0,
        market_value=35800.0,
        day_pnl=150.0,
        total_pnl=300.0
    ),
    Position(
        symbol="ES1!",
        account_id="test_account_001",
        quantity=-1.0,
        avg_price=4750.0,
        market_value=4725.0,
        day_pnl=-25.0,
        total_pnl=25.0
    )
]

mock_orders = [
    Order(
        id="order_001",
        broker_order_id="TRAD_12345",
        symbol="NQ1!",
        order_type="limit",
        side="buy",
        quantity=1.0,
        price=17900.0,
        status="pending",
        account_id="test_account_001"
    ),
    Order(
        id="order_002",
        broker_order_id="TRAD_12346",
        symbol="ES1!",
        order_type="market",
        side="sell",
        quantity=1.0,
        status="filled",
        filled_quantity=1.0,
        avg_fill_price=4752.0,
        account_id="test_account_001"
    )
]

@app.get("/api/account")
async def get_account():
    """Get account information"""
    try:
        # For now, return mock data. In production, this would fetch from broker
        return mock_account.dict()
    except Exception as e:
        logger.error(f"Error fetching account: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/positions")
async def get_positions():
    """Get current positions"""
    try:
        # For now, return mock data. In production, this would fetch from broker
        return [pos.dict() for pos in mock_positions]
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/orders")
async def get_orders(limit: int = 50):
    """Get recent orders"""
    try:
        # For now, return mock data. In production, this would fetch from broker
        orders = mock_orders[:limit]
        return [order.dict() for order in orders]
    except Exception as e:
        logger.error(f"Error fetching orders: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/orders")
async def submit_order(order_request: dict):
    """Submit a new order"""
    try:
        # Create order from request
        order = Order(
            symbol=order_request.get('symbol'),
            order_type=order_request.get('type', 'market'),
            side=order_request.get('side'),
            quantity=order_request.get('quantity'),
            price=order_request.get('price'),
            account_id="test_account_001"
        )
        
        # Add to mock orders (in production, submit to broker)
        mock_orders.insert(0, order)
        
        logger.info(f"Order submitted: {order.symbol} {order.side} {order.quantity}")
        
        return {
            "order_id": order.id,
            "status": "submitted",
            "message": "Order submitted successfully"
        }
    except Exception as e:
        logger.error(f"Error submitting order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/status")
async def get_market_status():
    """Get current market status"""
    try:
        # Simple market hours check (9:30 AM - 4:00 PM ET)
        from datetime import datetime, time
        import pytz
        
        et = pytz.timezone('US/Eastern')
        now = datetime.now(et)
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        is_weekday = now.weekday() < 5  # Monday=0, Sunday=6
        is_market_hours = market_open <= now.time() <= market_close
        is_open = is_weekday and is_market_hours
        
        return {
            "isOpen": is_open,
            "session": "regular" if is_open else "closed",
            "next_open": "2025-01-20 09:30:00 ET" if not is_open else None,
            "timezone": "US/Eastern"
        }
    except Exception as e:
        logger.error(f"Error getting market status: {e}")
        raise HTTPException(status_code=500, detail={"isOpen": False, "session": "unknown"})


# ============================================================================
# Backtesting API Endpoints
# ============================================================================

@app.post("/api/backtest/strategy")
async def submit_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks
):
    """Submit a new strategy backtest"""
    try:
        backtest_service = get_backtest_service()
        backtest_id = await backtest_service.submit_backtest(request, background_tasks)
        
        logger.info(f"Backtest submitted: {backtest_id}")
        
        return {
            "backtest_id": backtest_id,
            "status": "queued",
            "message": "Backtest submitted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error submitting backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{backtest_id}/status")
async def get_backtest_status(backtest_id: str):
    """Check backtest progress and status"""
    try:
        backtest_service = get_backtest_service()
        job = await backtest_service.get_backtest_status(backtest_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return {
            "backtest_id": job.id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest/{backtest_id}/results")
async def get_backtest_results(backtest_id: str):
    """Retrieve backtest results"""
    try:
        backtest_service = get_backtest_service()
        job = await backtest_service.get_backtest_status(backtest_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        if job.status != BacktestStatus.COMPLETED:
            raise HTTPException(
                status_code=400, 
                detail=f"Backtest not completed. Current status: {job.status}"
            )
        
        return {
            "backtest_id": job.id,
            "status": job.status,
            "request": job.request.dict(),
            "results": job.result.dict() if job.result else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/backtest/{backtest_id}")
async def cancel_backtest(backtest_id: str):
    """Cancel a running backtest"""
    try:
        backtest_service = get_backtest_service()
        cancelled = await backtest_service.cancel_backtest(backtest_id)
        
        if not cancelled:
            raise HTTPException(
                status_code=400, 
                detail="Backtest cannot be cancelled or does not exist"
            )
        
        return {
            "backtest_id": backtest_id,
            "status": "cancelled",
            "message": "Backtest cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/backtest")
async def list_backtests(limit: int = 20):
    """List recent backtests"""
    try:
        backtest_service = get_backtest_service()
        jobs = await backtest_service.list_backtests(limit=limit)
        
        return {
            "backtests": [
                {
                    "backtest_id": job.id,
                    "status": job.status,
                    "progress": job.progress,
                    "symbols": job.request.symbols,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        }
        
    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/api/backtest/{backtest_id}/progress")
async def backtest_progress_websocket(websocket: WebSocket, backtest_id: str):
    """WebSocket endpoint for real-time backtest progress updates"""
    await websocket.accept()
    
    try:
        backtest_service = get_backtest_service()
        
        # Send initial status
        job = await backtest_service.get_backtest_status(backtest_id)
        if not job:
            await websocket.send_text(json.dumps({
                "type": "error",
                "message": "Backtest not found"
            }))
            return
        
        # Send progress updates every second until completion
        while job.status in [BacktestStatus.QUEUED, BacktestStatus.RUNNING]:
            await websocket.send_text(json.dumps({
                "type": "progress",
                "backtest_id": job.id,
                "status": job.status,
                "progress": job.progress
            }))
            
            await asyncio.sleep(1)
            job = await backtest_service.get_backtest_status(backtest_id)
            
            if not job:
                break
        
        # Send final status
        if job:
            await websocket.send_text(json.dumps({
                "type": "completed",
                "backtest_id": job.id,
                "status": job.status,
                "progress": job.progress,
                "error_message": job.error_message
            }))
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for backtest {backtest_id}")
    except Exception as e:
        logger.error(f"WebSocket error for backtest {backtest_id}: {e}")


# ============================================================================
# Mock Data Functions (for development)
# ============================================================================

def _generate_mock_history(request: HistoryRequest) -> HistoryResponse:
    """Generate mock historical data for development"""
    bars = []
    current_time = request.from_ts
    base_price = 150.0
    
    while current_time <= request.to_ts:
        # Generate realistic OHLCV data
        open_price = base_price + (hash(str(current_time)) % 100 - 50) / 100
        high_price = open_price + abs(hash(str(current_time + 1)) % 50) / 100
        low_price = open_price - abs(hash(str(current_time + 2)) % 50) / 100
        close_price = low_price + (high_price - low_price) * 0.6
        volume = abs(hash(str(current_time + 3)) % 1000000)
        
        bars.append(Candle(
            ts=current_time,
            o=open_price,
            h=high_price,
            l=low_price,
            c=close_price,
            v=volume
        ))
        
        # Increment time based on resolution
        if request.resolution == "D":
            current_time += 86400  # 1 day
        elif request.resolution == "60":
            current_time += 3600   # 1 hour
        else:
            current_time += 300    # 5 minutes
    
    return HistoryResponse(
        symbol=request.symbol,
        resolution=request.resolution,
        bars=bars
    )


def _generate_mock_quote(symbol: str) -> Quote:
    """Generate mock quote for development"""
    base_price = 150.0 + (hash(symbol) % 1000) / 10
    return Quote(
        symbol=symbol,
        timestamp=int(time.time()),
        bid=base_price - 0.01,
        ask=base_price + 0.01,
        last=base_price,
        volume=hash(symbol) % 1000000,
        change=(hash(symbol) % 200 - 100) / 100,
        change_percent=(hash(symbol) % 200 - 100) / 1000
    )


def _generate_mock_search(query: str, limit: int) -> List[Dict[str, Any]]:
    """Generate mock search results"""
    mock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "META", "NVDA", "AMD"]
    results = []
    
    for symbol in mock_symbols:
        if query.upper() in symbol or len(results) < limit // 2:
            results.append({
                "symbol": symbol,
                "full_name": f"{symbol} Inc",
                "description": f"{symbol} Common Stock",
                "exchange": "NASDAQ",
                "type": "stock"
            })
    
    return results[:limit]


# ============================================================================
# Development Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )