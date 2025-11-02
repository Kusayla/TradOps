"""Alerting system for critical events"""
import httpx
from typing import Dict, Optional
from datetime import datetime
from loguru import logger

from src.config import settings


class AlertManager:
    """
    Send alerts via multiple channels:
    - Slack
    - Telegram
    """
    
    def __init__(self):
        self.slack_webhook = settings.monitoring.slack_webhook_url
        self.telegram_token = settings.monitoring.telegram_bot_token
        self.telegram_chat_id = settings.monitoring.telegram_chat_id
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send_alert(self, 
                        message: str, 
                        level: str = 'INFO',
                        data: Optional[Dict] = None):
        """
        Send alert to all configured channels
        
        Args:
            message: Alert message
            level: Alert level (INFO, WARNING, ERROR, CRITICAL)
            data: Additional data to include
        """
        # Format message
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{level}] {timestamp}\n{message}"
        
        if data:
            formatted_message += f"\n\nDetails:\n{self._format_data(data)}"
        
        # Send to all channels
        await self._send_slack(formatted_message, level)
        await self._send_telegram(formatted_message, level)
    
    async def _send_slack(self, message: str, level: str):
        """Send alert to Slack"""
        if not self.slack_webhook:
            return
        
        try:
            # Color based on level
            color_map = {
                'INFO': '#36a64f',
                'WARNING': '#ff9800',
                'ERROR': '#ff5722',
                'CRITICAL': '#d32f2f'
            }
            
            payload = {
                'attachments': [{
                    'color': color_map.get(level, '#808080'),
                    'text': message,
                    'mrkdwn_in': ['text']
                }]
            }
            
            response = await self.client.post(self.slack_webhook, json=payload)
            response.raise_for_status()
            
            logger.debug("Alert sent to Slack")
            
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
    
    async def _send_telegram(self, message: str, level: str):
        """Send alert to Telegram"""
        if not self.telegram_token or not self.telegram_chat_id:
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            
            # Add emoji based on level
            emoji_map = {
                'INFO': '??',
                'WARNING': '??',
                'ERROR': '?',
                'CRITICAL': '??'
            }
            
            formatted_message = f"{emoji_map.get(level, '??')} {message}"
            
            payload = {
                'chat_id': self.telegram_chat_id,
                'text': formatted_message,
                'parse_mode': 'Markdown'
            }
            
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            
            logger.debug("Alert sent to Telegram")
            
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")
    
    def _format_data(self, data: Dict) -> str:
        """Format data dictionary for display"""
        lines = []
        for key, value in data.items():
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.4f}")
            else:
                lines.append(f"  {key}: {value}")
        return '\n'.join(lines)
    
    # Predefined alert types
    async def alert_trade_executed(self, trade: Dict):
        """Alert when a trade is executed"""
        message = (f"?? Trade Executed\n"
                  f"Symbol: {trade['symbol']}\n"
                  f"Side: {trade['side']}\n"
                  f"Size: {trade['amount']:.4f}\n"
                  f"Price: {trade['price']:.2f}\n"
                  f"Cost: ${trade['cost']:.2f}")
        
        await self.send_alert(message, level='INFO')
    
    async def alert_position_closed(self, symbol: str, pnl: float):
        """Alert when a position is closed"""
        level = 'INFO' if pnl > 0 else 'WARNING'
        emoji = '?' if pnl > 0 else '?'
        
        message = (f"{emoji} Position Closed\n"
                  f"Symbol: {symbol}\n"
                  f"PnL: ${pnl:.2f}")
        
        await self.send_alert(message, level=level)
    
    async def alert_stop_loss_hit(self, symbol: str, price: float, loss: float):
        """Alert when stop loss is hit"""
        message = (f"?? Stop Loss Hit\n"
                  f"Symbol: {symbol}\n"
                  f"Price: {price:.2f}\n"
                  f"Loss: ${loss:.2f}")
        
        await self.send_alert(message, level='WARNING')
    
    async def alert_take_profit_hit(self, symbol: str, price: float, profit: float):
        """Alert when take profit is hit"""
        message = (f"?? Take Profit Hit\n"
                  f"Symbol: {symbol}\n"
                  f"Price: {price:.2f}\n"
                  f"Profit: ${profit:.2f}")
        
        await self.send_alert(message, level='INFO')
    
    async def alert_risk_limit_reached(self, check_type: str, details: Dict):
        """Alert when a risk limit is reached"""
        message = f"?? Risk Limit Reached: {check_type}"
        await self.send_alert(message, level='WARNING', data=details)
    
    async def alert_circuit_breaker(self, reason: str):
        """Alert when circuit breaker is activated"""
        message = (f"?? CIRCUIT BREAKER ACTIVATED\n"
                  f"Reason: {reason}\n"
                  f"Trading has been paused")
        
        await self.send_alert(message, level='CRITICAL')
    
    async def alert_max_drawdown(self, current_dd: float, max_dd: float):
        """Alert when max drawdown is approached"""
        message = (f"?? Drawdown Warning\n"
                  f"Current: {current_dd:.2%}\n"
                  f"Limit: {max_dd:.2%}")
        
        await self.send_alert(message, level='ERROR')
    
    async def alert_api_error(self, service: str, error: str):
        """Alert on API errors"""
        message = (f"? API Error\n"
                  f"Service: {service}\n"
                  f"Error: {error}")
        
        await self.send_alert(message, level='ERROR')
    
    async def alert_strong_signal(self, symbol: str, signal: Dict):
        """Alert on strong trading signals"""
        message = (f"?? Strong Signal Detected\n"
                  f"Symbol: {symbol}\n"
                  f"Type: {signal['signal_type']}\n"
                  f"Strength: {signal['strength']:.2f}\n"
                  f"Strategy: {signal['strategy']}")
        
        if signal.get('reasons'):
            message += f"\nReasons: {', '.join(signal['reasons'])}"
        
        await self.send_alert(message, level='INFO')
    
    async def alert_daily_summary(self, summary: Dict):
        """Send daily summary alert"""
        message = (f"?? Daily Summary\n"
                  f"Trades: {summary['total_trades']}\n"
                  f"PnL: ${summary['daily_pnl']:.2f}\n"
                  f"Win Rate: {summary['win_rate']:.1%}\n"
                  f"Portfolio Value: ${summary['portfolio_value']:.2f}")
        
        await self.send_alert(message, level='INFO')
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global alert manager instance
alert_manager = AlertManager()
