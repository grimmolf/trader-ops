"""
TradeNote Integration for TraderTerminal

Provides automated trade logging to TradeNote journal system via REST API.
Supports both live and paper trading data with rich analytics integration.
"""

from .client import TradeNoteClient
from .models import TradeNoteTradeData, TradeNoteConfig, TradeNoteResponse
from .service import TradeNoteService
from .hooks import TradeNoteIntegration, load_tradenote_config_from_env

__all__ = [
    'TradeNoteClient',
    'TradeNoteTradeData', 
    'TradeNoteConfig',
    'TradeNoteResponse',
    'TradeNoteService',
    'TradeNoteIntegration',
    'load_tradenote_config_from_env'
]