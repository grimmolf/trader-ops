"""
BacktestService - Integration with Kairos for strategy backtesting.

Manages the execution of Pine Script strategies through the Kairos automation engine,
providing a REST API interface for backtest submission, progress tracking, and results retrieval.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

from pydantic import BaseModel, Field
from fastapi import BackgroundTasks


logger = logging.getLogger(__name__)


class BacktestStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BacktestRequest(BaseModel):
    """Backtest request model"""
    pine_script: str = Field(..., description="Pine Script strategy code")
    symbols: List[str] = Field(..., description="List of symbols to test")
    timeframes: List[str] = Field(default=["1h"], description="Timeframes to test")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    initial_capital: float = Field(default=10000.0, description="Initial capital for backtest")
    commission: float = Field(default=0.01, description="Commission per trade")
    slippage: float = Field(default=0.0, description="Slippage in percentage")


class BacktestResult(BaseModel):
    """Backtest result model"""
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profit_factor: float
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    equity_curve: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]


class BacktestJob(BaseModel):
    """Backtest job tracking model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: BacktestStatus = BacktestStatus.QUEUED
    request: BacktestRequest
    result: Optional[BacktestResult] = None
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = Field(default=0, description="Progress percentage")


class BacktestService:
    """Service for managing strategy backtesting through Kairos"""
    
    def __init__(self, kairos_path: Path, max_concurrent: int = 3):
        self.kairos_path = kairos_path
        self.max_concurrent = max_concurrent
        self.active_jobs: Dict[str, BacktestJob] = {}
        self.running_jobs: Dict[str, asyncio.Task] = {}
        
        # Ensure Kairos is available
        if not self.kairos_path.exists():
            logger.warning(f"Kairos path not found: {kairos_path}")
        
    async def submit_backtest(
        self, 
        request: BacktestRequest, 
        background_tasks: BackgroundTasks
    ) -> str:
        """Submit a new backtest job"""
        
        # Create job
        job = BacktestJob(request=request)
        self.active_jobs[job.id] = job
        
        logger.info(f"Submitted backtest job {job.id} for symbols: {request.symbols}")
        
        # Schedule execution
        background_tasks.add_task(self._execute_backtest, job.id)
        
        return job.id
    
    async def get_backtest_status(self, job_id: str) -> Optional[BacktestJob]:
        """Get backtest job status"""
        return self.active_jobs.get(job_id)
    
    async def get_backtest_result(self, job_id: str) -> Optional[BacktestResult]:
        """Get backtest results"""
        job = self.active_jobs.get(job_id)
        if job and job.status == BacktestStatus.COMPLETED:
            return job.result
        return None
    
    async def cancel_backtest(self, job_id: str) -> bool:
        """Cancel a running backtest"""
        job = self.active_jobs.get(job_id)
        if not job:
            return False
            
        if job.status in [BacktestStatus.QUEUED, BacktestStatus.RUNNING]:
            job.status = BacktestStatus.CANCELLED
            
            # Cancel running task if exists
            if job_id in self.running_jobs:
                self.running_jobs[job_id].cancel()
                del self.running_jobs[job_id]
            
            logger.info(f"Cancelled backtest job {job_id}")
            return True
        
        return False
    
    async def list_backtests(self, limit: int = 50) -> List[BacktestJob]:
        """List backtest jobs"""
        jobs = list(self.active_jobs.values())
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]
    
    async def _execute_backtest(self, job_id: str):
        """Execute backtest in background"""
        job = self.active_jobs.get(job_id)
        if not job:
            return
        
        try:
            # Check concurrent limit
            while len(self.running_jobs) >= self.max_concurrent:
                await asyncio.sleep(1)
            
            # Start job
            task = asyncio.create_task(self._run_backtest(job))
            self.running_jobs[job_id] = task
            
            await task
            
        except asyncio.CancelledError:
            job.status = BacktestStatus.CANCELLED
            logger.info(f"Backtest job {job_id} was cancelled")
        except Exception as e:
            job.status = BacktestStatus.FAILED
            job.error_message = str(e)
            logger.error(f"Backtest job {job_id} failed: {e}")
        finally:
            if job_id in self.running_jobs:
                del self.running_jobs[job_id]
    
    async def _run_backtest(self, job: BacktestJob):
        """Run the actual backtest using Kairos"""
        job.status = BacktestStatus.RUNNING
        job.started_at = datetime.now()
        job.progress = 10
        
        logger.info(f"Starting backtest execution for job {job.id}")
        
        try:
            # Create temporary strategy file
            strategy_file = await self._create_strategy_file(job)
            job.progress = 20
            
            # Execute backtest for each symbol
            all_results = []
            total_symbols = len(job.request.symbols)
            
            for i, symbol in enumerate(job.request.symbols):
                if job.status == BacktestStatus.CANCELLED:
                    return
                
                logger.info(f"Running backtest for {symbol} ({i+1}/{total_symbols})")
                
                symbol_result = await self._run_symbol_backtest(
                    strategy_file, symbol, job.request
                )
                all_results.append(symbol_result)
                
                # Update progress
                job.progress = 20 + int(70 * (i + 1) / total_symbols)
            
            # Aggregate results
            job.result = await self._aggregate_results(all_results, job.request)
            job.progress = 100
            job.status = BacktestStatus.COMPLETED
            job.completed_at = datetime.now()
            
            logger.info(f"Backtest job {job.id} completed successfully")
            
        except Exception as e:
            job.status = BacktestStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now()
            logger.error(f"Backtest execution failed for job {job.id}: {e}")
        
        finally:
            # Cleanup temporary files
            await self._cleanup_temp_files(job.id)
    
    async def _create_strategy_file(self, job: BacktestJob) -> Path:
        """Create temporary Pine Script strategy file"""
        temp_dir = Path("/tmp") / "kairos_backtests" / job.id
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        strategy_file = temp_dir / "strategy.pine"
        
        # Write Pine Script to file
        with open(strategy_file, "w") as f:
            f.write(job.request.pine_script)
        
        logger.debug(f"Created strategy file: {strategy_file}")
        return strategy_file
    
    async def _run_symbol_backtest(
        self, 
        strategy_file: Path, 
        symbol: str, 
        request: BacktestRequest
    ) -> Dict[str, Any]:
        """Run backtest for a single symbol using Kairos"""
        
        try:
            # Create Kairos configuration for this backtest
            kairos_config = {
                "strategy_file": str(strategy_file),
                "symbol": symbol,
                "timeframe": request.timeframes[0],  # Use first timeframe
                "start_date": request.start_date,
                "end_date": request.end_date,
                "initial_capital": request.initial_capital,
                "commission": request.commission,
                "slippage": request.slippage
            }
            
            # Use mock backtest execution for now
            # In a real implementation, this would call Kairos
            result = await self._mock_kairos_execution(symbol, kairos_config)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to run backtest for {symbol}: {e}")
            raise
    
    async def _mock_kairos_execution(self, symbol: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Kairos execution for development"""
        
        # Simulate backtest execution time
        await asyncio.sleep(2)
        
        # Generate mock results based on symbol hash for consistency
        symbol_hash = hash(symbol) % 10000
        
        # Generate mock equity curve
        days = 252  # One year of trading days
        equity_curve = []
        equity = config["initial_capital"]
        
        for i in range(days):
            # Simulate daily returns
            daily_return = (symbol_hash % 100 - 45) / 10000  # -0.45% to +0.55%
            equity *= (1 + daily_return)
            
            equity_curve.append({
                "date": (datetime.now() - timedelta(days=days-i)).strftime("%Y-%m-%d"),
                "equity": round(equity, 2)
            })
        
        # Generate mock trades
        num_trades = abs(symbol_hash % 50) + 10
        trades = []
        
        for i in range(num_trades):
            entry_price = 100 + (symbol_hash % 100)
            exit_price = entry_price * (1 + ((symbol_hash + i) % 20 - 10) / 100)
            
            trades.append({
                "entry_date": (datetime.now() - timedelta(days=days-i*5)).strftime("%Y-%m-%d"),
                "exit_date": (datetime.now() - timedelta(days=days-i*5-2)).strftime("%Y-%m-%d"),
                "side": "long" if i % 2 == 0 else "short",
                "entry_price": round(entry_price, 2),
                "exit_price": round(exit_price, 2),
                "quantity": 100,
                "pnl": round((exit_price - entry_price) * 100, 2)
            })
        
        # Calculate metrics
        final_equity = equity_curve[-1]["equity"]
        total_return = (final_equity - config["initial_capital"]) / config["initial_capital"]
        
        winning_trades = [t for t in trades if t["pnl"] > 0]
        losing_trades = [t for t in trades if t["pnl"] < 0]
        
        win_rate = len(winning_trades) / len(trades) if trades else 0
        avg_win = sum(t["pnl"] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t["pnl"] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        return {
            "symbol": symbol,
            "total_return": total_return,
            "final_equity": final_equity,
            "max_drawdown": abs(symbol_hash % 15) / 100,  # Mock drawdown
            "sharpe_ratio": (symbol_hash % 300) / 100,    # Mock Sharpe ratio
            "win_rate": win_rate,
            "total_trades": len(trades),
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "equity_curve": equity_curve,
            "trades": trades
        }
    
    async def _aggregate_results(
        self, 
        symbol_results: List[Dict[str, Any]], 
        request: BacktestRequest
    ) -> BacktestResult:
        """Aggregate results from multiple symbols"""
        
        if not symbol_results:
            raise ValueError("No results to aggregate")
        
        # Calculate portfolio-level metrics
        total_capital = request.initial_capital * len(symbol_results)
        total_final_equity = sum(r["final_equity"] for r in symbol_results)
        total_return = (total_final_equity - total_capital) / total_capital
        
        # Aggregate trades
        all_trades = []
        for result in symbol_results:
            all_trades.extend(result["trades"])
        
        # Calculate aggregated metrics
        winning_trades = [t for t in all_trades if t["pnl"] > 0]
        losing_trades = [t for t in all_trades if t["pnl"] < 0]
        
        total_pnl = sum(t["pnl"] for t in all_trades)
        gross_profit = sum(t["pnl"] for t in winning_trades) if winning_trades else 0
        gross_loss = abs(sum(t["pnl"] for t in losing_trades)) if losing_trades else 1
        
        # Create combined equity curve
        combined_equity_curve = []
        if symbol_results:
            dates = symbol_results[0]["equity_curve"]
            for i, date_point in enumerate(dates):
                total_equity = sum(
                    result["equity_curve"][i]["equity"] 
                    for result in symbol_results
                )
                combined_equity_curve.append({
                    "date": date_point["date"],
                    "equity": round(total_equity, 2)
                })
        
        return BacktestResult(
            total_return=total_return,
            max_drawdown=max(r["max_drawdown"] for r in symbol_results),
            sharpe_ratio=sum(r["sharpe_ratio"] for r in symbol_results) / len(symbol_results),
            win_rate=len(winning_trades) / len(all_trades) if all_trades else 0,
            total_trades=len(all_trades),
            profit_factor=gross_profit / gross_loss if gross_loss > 0 else 0,
            avg_win=gross_profit / len(winning_trades) if winning_trades else 0,
            avg_loss=gross_loss / len(losing_trades) if losing_trades else 0,
            largest_win=max((t["pnl"] for t in winning_trades), default=0),
            largest_loss=min((t["pnl"] for t in losing_trades), default=0),
            equity_curve=combined_equity_curve,
            trades=all_trades
        )
    
    async def _cleanup_temp_files(self, job_id: str):
        """Clean up temporary files created for the job"""
        temp_dir = Path("/tmp") / "kairos_backtests" / job_id
        
        try:
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temp directory: {temp_dir}")
        except Exception as e:
            logger.warning(f"Failed to cleanup temp files for job {job_id}: {e}")


# Global instance
backtest_service: Optional[BacktestService] = None


def get_backtest_service() -> BacktestService:
    """Get the global backtest service instance"""
    global backtest_service
    
    if backtest_service is None:
        kairos_path = Path(os.getenv("KAIROS_PATH", "/opt/grimm-kairos"))
        backtest_service = BacktestService(kairos_path=kairos_path)
    
    return backtest_service