"""
TopstepX Integration Manager

High-level manager that coordinates all TopstepX operations including
authentication, funded account monitoring, risk management, and integration
with TraderTerminal webhook system.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .auth import TopstepXAuth, TopstepXCredentials
from .connector import TopstepXConnector
from .models import (
    TopstepAccount, FundedAccountRules, AccountMetrics, RuleViolation,
    AccountStatus, TradingPhase, RuleViolationType
)

logger = logging.getLogger(__name__)


class TopstepXManager:
    """
    High-level manager for all TopstepX operations.
    
    Provides a unified interface for:
    - Authentication and connection management
    - Funded account monitoring and rule enforcement
    - Risk management for funded traders
    - Integration with TradingView alerts
    - Real-time account performance tracking
    """
    
    def __init__(self, credentials: TopstepXCredentials):
        self.credentials = credentials
        
        # Initialize core components
        self.connector = TopstepXConnector(credentials)
        
        # State management
        self._initialized = False
        self._accounts: List[TopstepAccount] = []
        self._default_account_id: Optional[str] = None
        self._monitoring_active = False
        
        logger.info(f"Initialized TopstepX manager for {credentials.environment} environment")
    
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the TopstepX connection and verify setup.
        
        Returns:
            Dict[str, Any]: Initialization results
        """
        if self._initialized:
            logger.warning("TopstepX manager already initialized")
            return {"status": "already_initialized"}
        
        logger.info("Initializing TopstepX connection...")
        
        try:
            # For development/demo mode, use mock authentication
            if self.credentials.environment == "demo":
                logger.info("Using TopstepX mock mode for development")
                
                # Step 1: Mock authentication
                auth_result = {"status": "success", "message": "Mock authentication successful"}
                
                # Step 2: Load mock accounts from connector
                self._accounts = await self.connector.get_accounts()
                
                # Step 3: Set default account (first active account)
                for account in self._accounts:
                    if account.status == AccountStatus.ACTIVE:
                        self._default_account_id = account.account_id
                        break
                
                # Step 4: Mock monitoring (always successful)
                self._monitoring_active = True
                
            else:
                # Real API mode (for production)
                # Step 1: Test authentication
                auth_test = await self.connector.test_connection()
                if auth_test.get("status") != "success":
                    return {
                        "status": "failed",
                        "step": "authentication", 
                        "error": auth_test.get("message", "Authentication failed")
                    }
                
                # Step 2: Load funded accounts
                self._accounts = await self.connector.get_accounts()
                if not self._accounts:
                    logger.warning("No TopstepX accounts found - this may be expected for new users")
                    self._accounts = []
                
                # Step 3: Set default account (first active account)
                for account in self._accounts:
                    if account.status == AccountStatus.ACTIVE:
                        self._default_account_id = account.account_id
                        break
                
                # Step 4: Initialize real-time monitoring for active accounts
                if self._accounts:
                    try:
                        monitoring_started = await self._start_account_monitoring()
                        self._monitoring_active = monitoring_started
                    except Exception as e:
                        logger.warning(f"Failed to start account monitoring: {e}")
                        self._monitoring_active = False
            
            self._initialized = True
            
            return {
                "status": "success",
                "environment": self.credentials.environment,
                "account_count": len(self._accounts),
                "default_account_id": self._default_account_id,
                "monitoring_active": self._monitoring_active,
                "accounts": [
                    {
                        "id": acc.account_id,
                        "name": acc.account_name,
                        "status": acc.status.value,
                        "phase": acc.phase.value,
                        "balance": acc.current_balance,
                        "violations": len(acc.active_violations)
                    }
                    for acc in self._accounts
                ]
            }
            
        except Exception as e:
            logger.error(f"Error initializing TopstepX: {e}")
            return {
                "status": "failed",
                "step": "initialization",
                "error": str(e)
            }
    
    async def execute_alert(self, alert: Any) -> Dict[str, Any]:
        """
        Execute a TradingView alert with TopstepX funded account validation.
        
        This method:
        1. Validates the alert against funded account rules
        2. Delegates actual execution to Tradovate (TopstepX doesn't execute trades)
        3. Reports trade execution back to TopstepX for monitoring
        
        Args:
            alert: TradingViewAlert object or dict with alert data
            
        Returns:
            Dict[str, Any]: Execution result with TopstepX validation
        """
        if not self._initialized:
            return {
                "status": "error",
                "message": "TopstepX manager not initialized"
            }
        
        try:
            logger.info(f"Validating TopstepX rules for alert: {alert}")
            
            # Handle both TradingViewAlert objects and dictionaries
            if hasattr(alert, 'symbol'):
                # TradingViewAlert object
                symbol = alert.symbol.upper()
                action = alert.action.lower()
                quantity = alert.quantity
                account_group = getattr(alert, 'account_group', 'topstep')
                alert_data = {
                    'symbol': symbol,
                    'action': action,
                    'quantity': quantity,
                    'account_group': account_group,
                    'order_type': getattr(alert, 'order_type', 'market'),
                    'price': getattr(alert, 'price', None),
                    'strategy': getattr(alert, 'strategy', None)
                }
            else:
                # Dictionary format
                alert_data = alert
                symbol = alert_data.get("symbol", "").upper()
                action = alert_data.get("action", "").lower()
                quantity = alert_data.get("quantity", 1)
                account_group = alert_data.get("account_group", "topstep")
            
            # Validate parameters
            if not symbol or not action:
                return {
                    "status": "rejected",
                    "message": "Missing required parameters: symbol and action"
                }
            
            if action not in ["buy", "sell", "close"]:
                return {
                    "status": "rejected",
                    "message": f"Invalid action: {action}. Must be buy, sell, or close"
                }
            
            # Find matching TopstepX account
            target_account = await self._get_target_account(account_group)
            if not target_account:
                return {
                    "status": "rejected",
                    "message": f"No TopstepX account found for group: {account_group}"
                }
            
            # Check funded account rules
            risk_check = await self._check_funded_account_rules(target_account, alert_data)
            if not risk_check.get("allowed"):
                return {
                    "status": "rejected",
                    "message": f"TopstepX risk check failed: {risk_check.get('reason')}",
                    "account_id": target_account.account_id,
                    "current_metrics": risk_check.get("current_metrics")
                }
            
            # Rules passed - indicate that execution can proceed
            # Note: TopstepX doesn't execute trades directly, Tradovate does
            # This manager validates rules and reports back to TopstepX
            return {
                "status": "rules_validated",
                "message": "TopstepX funded account rules validated successfully",
                "account_id": target_account.account_id,
                "account_name": target_account.account_name,
                "current_metrics": risk_check.get("current_metrics"),
                "remaining_buffers": {
                    "loss_buffer": target_account.rules.account_rules.get_remaining_loss_buffer(),
                    "drawdown_buffer": target_account.rules.account_rules.get_remaining_drawdown_buffer()
                }
            }
                
        except Exception as e:
            logger.error(f"Error validating TopstepX rules: {e}")
            return {
                "status": "error",
                "message": f"TopstepX validation error: {str(e)}"
            }
    
    async def report_trade_execution(
        self,
        account_group: str,
        symbol: str,
        action: str,
        quantity: int,
        price: float,
        execution_result: Dict[str, Any]
    ) -> bool:
        """
        Report completed trade execution to TopstepX for monitoring.
        
        This should be called after Tradovate successfully executes a trade
        to update TopstepX account metrics and check for rule violations.
        
        Args:
            account_group: TopstepX account group
            symbol: Trading symbol
            action: Buy/sell action
            quantity: Number of contracts
            price: Execution price
            execution_result: Result from Tradovate execution
            
        Returns:
            bool: True if successfully reported
        """
        try:
            # Find matching account
            target_account = await self._get_target_account(account_group)
            if not target_account:
                logger.warning(f"No TopstepX account found for trade reporting: {account_group}")
                return False
            
            # Report to TopstepX
            success = await self.connector.report_trade_execution(
                target_account.account_id,
                symbol,
                quantity,
                price,
                action
            )
            
            if success:
                logger.info(f"Trade reported to TopstepX: {symbol} {action} {quantity} @ {price}")
                
                # Check for new violations after trade
                await self._check_account_violations(target_account.account_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Error reporting trade to TopstepX: {e}")
            return False
    
    async def _get_target_account(self, account_group: str) -> Optional[TopstepAccount]:
        """Find TopstepX account based on account group"""
        if not self._accounts:
            return None
        
        # For funded accounts, match by account type/group
        group_lower = account_group.lower()
        
        # Try to find account by group name
        for account in self._accounts:
            if group_lower in account.account_name.lower() or group_lower in account.account_id.lower():
                return account
        
        # Fallback to first active account
        for account in self._accounts:
            if account.status == AccountStatus.ACTIVE:
                logger.info(f"Using default TopstepX account for group: {account_group}")
                return account
        
        return None
    
    async def _check_funded_account_rules(
        self, 
        account: TopstepAccount, 
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check funded account rules before allowing trade execution.
        
        Args:
            account: TopstepX funded account
            alert_data: Alert data for validation
            
        Returns:
            Dict[str, Any]: Validation result
        """
        try:
            # Check if account is eligible for trading
            trading_allowed, reason = account.is_trading_allowed()
            if not trading_allowed:
                return {
                    "allowed": False,
                    "reason": reason,
                    "account_id": account.account_id
                }
            
            # Check specific trade against account rules
            quantity = alert_data.get("quantity", 1)
            symbol = alert_data.get("symbol", "")
            
            can_trade, trade_reason = account.rules.account_rules.can_trade(quantity, symbol)
            if not can_trade:
                return {
                    "allowed": False,
                    "reason": trade_reason,
                    "account_id": account.account_id
                }
            
            # Get current account metrics
            current_metrics = {
                "daily_pnl": account.current_metrics.daily_pnl,
                "current_drawdown": account.current_metrics.current_drawdown,
                "total_contracts": account.current_metrics.total_contracts,
                "open_positions": account.current_metrics.open_positions,
                "win_rate": account.current_metrics.win_rate,
                "profit_factor": account.current_metrics.profit_factor
            }
            
            return {
                "allowed": True,
                "account_id": account.account_id,
                "account_name": account.account_name,
                "current_metrics": current_metrics
            }
            
        except Exception as e:
            logger.error(f"Error checking funded account rules: {e}")
            return {
                "allowed": False,
                "reason": f"Rule check error: {str(e)}",
                "account_id": account.account_id
            }
    
    async def _start_account_monitoring(self) -> bool:
        """Start real-time monitoring for all active accounts"""
        try:
            monitoring_tasks = []
            
            for account in self._accounts:
                if account.status == AccountStatus.ACTIVE:
                    # Start monitoring task for each account
                    task = asyncio.create_task(
                        self.connector.start_realtime_monitoring(
                            account.account_id, 
                            self._handle_account_violation
                        )
                    )
                    monitoring_tasks.append(task)
            
            # Wait for all monitoring tasks to start
            if monitoring_tasks:
                results = await asyncio.gather(*monitoring_tasks, return_exceptions=True)
                success_count = sum(1 for r in results if r is True)
                logger.info(f"Started monitoring for {success_count}/{len(monitoring_tasks)} TopstepX accounts")
                return success_count > 0
            
            return True  # No accounts to monitor is considered success
            
        except Exception as e:
            logger.error(f"Error starting account monitoring: {e}")
            return False
    
    async def _handle_account_violation(self, violation_data: Dict[str, Any]):
        """Handle account rule violation callback"""
        try:
            account_id = violation_data.get("account_id")
            violation_type = violation_data.get("violation_type")
            
            logger.warning(f"TopstepX account violation: {account_id} - {violation_type}")
            
            # Emergency actions for severe violations
            if violation_type in ["daily_loss_limit", "trailing_drawdown"]:
                logger.error(f"CRITICAL VIOLATION: Emergency flattening account {account_id}")
                
                # Flatten all positions immediately
                flatten_result = await self.connector.emergency_flatten_positions(account_id)
                if flatten_result.get("success"):
                    logger.info(f"Emergency position flattening completed for {account_id}")
                else:
                    logger.error(f"Emergency flattening failed for {account_id}: {flatten_result.get('message')}")
            
        except Exception as e:
            logger.error(f"Error handling account violation: {e}")
    
    async def _check_account_violations(self, account_id: str):
        """Check for new rule violations after trade execution"""
        try:
            violations = await self.connector.get_rule_violations(account_id)
            
            if violations:
                for violation in violations:
                    await self._handle_account_violation({
                        "account_id": account_id,
                        "violation_type": violation.violation_type.value,
                        "violation": violation
                    })
        
        except Exception as e:
            logger.error(f"Error checking account violations: {e}")
    
    async def get_account_summary(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive TopstepX account summary.
        
        Args:
            account_id: Account ID (uses default if None)
            
        Returns:
            Dict[str, Any]: Account summary
        """
        if not account_id:
            account_id = self._default_account_id
        
        if not account_id:
            return {"error": "No TopstepX account ID specified"}
        
        try:
            # Get account info from connector
            account = await self.connector.get_account_info(account_id)
            if not account:
                return {"error": f"TopstepX account {account_id} not found"}
            
            # Get additional metrics
            violations = await self.connector.get_rule_violations(account_id)
            
            return {
                "account_info": {
                    "id": account.account_id,
                    "name": account.account_name,
                    "status": account.status.value,
                    "phase": account.phase.value,
                    "balance": account.current_balance,
                    "account_size": account.account_size
                },
                "current_metrics": {
                    "daily_pnl": account.current_metrics.daily_pnl,
                    "total_pnl": account.current_metrics.total_pnl,
                    "current_drawdown": account.current_metrics.current_drawdown,
                    "max_drawdown": account.current_metrics.max_drawdown,
                    "win_rate": account.current_metrics.win_rate,
                    "profit_factor": account.current_metrics.profit_factor,
                    "total_trades": account.current_metrics.total_trades,
                    "open_positions": account.current_metrics.open_positions
                },
                "rules": {
                    "max_daily_loss": account.rules.account_rules.max_daily_loss,
                    "trailing_drawdown": account.rules.account_rules.trailing_drawdown,
                    "max_contracts": account.rules.account_rules.max_contracts,
                    "profit_target": account.rules.account_rules.profit_target,
                    "remaining_loss_buffer": account.rules.account_rules.get_remaining_loss_buffer(),
                    "remaining_drawdown_buffer": account.rules.account_rules.get_remaining_drawdown_buffer()
                },
                "violations": [
                    {
                        "type": v.violation_type.value,
                        "message": v.message,
                        "triggered_at": v.triggered_at.isoformat(),
                        "resolved": v.resolved
                    }
                    for v in violations
                ],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting TopstepX account summary: {e}")
            return {"error": str(e)}
    
    async def get_all_accounts_summary(self) -> Dict[str, Any]:
        """Get summary of all TopstepX accounts"""
        try:
            summaries = []
            
            for account in self._accounts:
                summary = await self.get_account_summary(account.account_id)
                if "error" not in summary:
                    summaries.append(summary)
            
            return {
                "account_count": len(self._accounts),
                "active_accounts": len([a for a in self._accounts if a.status == AccountStatus.ACTIVE]),
                "total_violations": sum(len(a.active_violations) for a in self._accounts),
                "accounts": summaries,
                "monitoring_active": self._monitoring_active,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting all accounts summary: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close all connections and cleanup"""
        try:
            self._monitoring_active = False
            await self.connector.close()
            logger.info("TopstepX manager closed")
            
        except Exception as e:
            logger.error(f"Error closing TopstepX manager: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of TopstepX manager"""
        return {
            "initialized": self._initialized,
            "environment": self.credentials.environment,
            "account_count": len(self._accounts),
            "default_account_id": self._default_account_id,
            "monitoring_active": self._monitoring_active,
            "active_accounts": len([a for a in self._accounts if a.status == AccountStatus.ACTIVE]),
            "total_violations": sum(len(a.active_violations) for a in self._accounts)
        }
    
    def __repr__(self) -> str:
        env = self.credentials.environment
        status = "initialized" if self._initialized else "not_initialized"
        return f"TopstepXManager(env={env}, status={status}, accounts={len(self._accounts)})"