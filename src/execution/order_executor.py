"""Order execution with exchange connectivity"""
import asyncio
from typing import Dict, Optional, List
from datetime import datetime
import ccxt.async_support as ccxt
from loguru import logger

from src.config import settings
from src.storage.redis_client import RedisClient
from src.data_ingestion.streaming_producer import StreamingProducer


class OrderExecutor:
    """
    Execute orders on exchanges
    Supports:
    - Market orders
    - Limit orders
    - Stop loss / Take profit orders
    - Order status tracking
    """
    
    def __init__(self, 
                 exchange_id: str = None,
                 redis_client: RedisClient = None,
                 streaming_producer: StreamingProducer = None):
        self.exchange_id = exchange_id or settings.exchange.default_exchange
        self.exchange = None
        self.redis = redis_client
        self.streaming_producer = streaming_producer
        self.paper_trading = settings.trading.trading_mode == 'paper'
        
        # Track orders
        self.pending_orders = {}
        self.executed_orders = {}
    
    async def initialize(self):
        """Initialize exchange connection"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            config = {
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            }
            
            if not self.paper_trading:
                if self.exchange_id == 'binance':
                    config['apiKey'] = settings.exchange.binance_api_key
                    config['secret'] = settings.exchange.binance_api_secret
                    if settings.exchange.binance_testnet:
                        config['urls'] = {
                            'api': {
                                'public': 'https://testnet.binance.vision/api',
                                'private': 'https://testnet.binance.vision/api',
                            }
                        }
                elif self.exchange_id == 'coinbase':
                    config['apiKey'] = settings.exchange.coinbase_api_key
                    config['secret'] = settings.exchange.coinbase_api_secret
            
            self.exchange = exchange_class(config)
            await self.exchange.load_markets()
            
            logger.info(f"Initialized {self.exchange_id} executor "
                       f"(mode: {'paper' if self.paper_trading else 'live'})")
            
        except Exception as e:
            logger.error(f"Failed to initialize executor: {e}")
            raise
    
    async def execute_order(self, decision: Dict) -> Optional[Dict]:
        """
        Execute a trading decision
        Returns: order result or None
        """
        try:
            symbol = decision['symbol']
            side = decision['side'].lower()
            size = decision['size']
            
            logger.info(f"Executing {side.upper()} order for {symbol}: {size} units")
            
            if self.paper_trading:
                # Simulate order execution
                result = await self._execute_paper_order(decision)
            else:
                # Real order execution
                result = await self._execute_live_order(decision)
            
            if result:
                # Update position in Redis
                self._update_position(decision, result)
                
                # Send to Kafka
                if self.streaming_producer:
                    self.streaming_producer.send_trade(result)
                
                # Store executed order
                self.executed_orders[result['id']] = result
                
                logger.info(f"Order executed: {result['id']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return None
    
    async def _execute_paper_order(self, decision: Dict) -> Dict:
        """Simulate order execution for paper trading"""
        try:
            # Simulate slight slippage
            import random
            slippage = random.uniform(-0.001, 0.001)  # 0.1% slippage
            
            execution_price = decision['price'] * (1 + slippage)
            
            # Simulate fees (0.1%)
            fee_rate = 0.001
            cost = decision['size'] * execution_price
            fee = cost * fee_rate
            
            order_id = f"paper_{decision['symbol']}_{int(datetime.now().timestamp() * 1000)}"
            
            result = {
                'id': order_id,
                'symbol': decision['symbol'],
                'side': decision['side'],
                'type': 'market',
                'price': execution_price,
                'amount': decision['size'],
                'cost': cost,
                'fee': fee,
                'timestamp': datetime.now().isoformat(),
                'status': 'closed',
                'paper_trade': True,
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit'),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in paper order execution: {e}")
            return None
    
    async def _execute_live_order(self, decision: Dict) -> Optional[Dict]:
        """Execute real order on exchange"""
        try:
            symbol = decision['symbol']
            side = decision['side'].lower()
            amount = decision['size']
            
            # Create market order
            order = await self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side,
                amount=amount
            )
            
            # Wait for order to fill
            await asyncio.sleep(1)
            
            # Fetch order status
            order_status = await self.exchange.fetch_order(order['id'], symbol)
            
            # Create stop loss order if specified
            if decision.get('stop_loss') and self.exchange.has.get('createStopLossOrder'):
                try:
                    stop_order = await self.exchange.create_order(
                        symbol=symbol,
                        type='stop_loss',
                        side='sell' if side == 'buy' else 'buy',
                        amount=amount,
                        params={'stopPrice': decision['stop_loss']}
                    )
                    logger.info(f"Stop loss order created: {stop_order['id']}")
                except Exception as e:
                    logger.warning(f"Failed to create stop loss: {e}")
            
            # Create take profit order if specified
            if decision.get('take_profit') and self.exchange.has.get('createTakeProfitOrder'):
                try:
                    tp_order = await self.exchange.create_order(
                        symbol=symbol,
                        type='take_profit',
                        side='sell' if side == 'buy' else 'buy',
                        amount=amount,
                        params={'stopPrice': decision['take_profit']}
                    )
                    logger.info(f"Take profit order created: {tp_order['id']}")
                except Exception as e:
                    logger.warning(f"Failed to create take profit: {e}")
            
            result = {
                'id': order_status['id'],
                'symbol': order_status['symbol'],
                'side': order_status['side'],
                'type': order_status['type'],
                'price': order_status.get('average') or order_status.get('price'),
                'amount': order_status['filled'],
                'cost': order_status['cost'],
                'fee': order_status.get('fee', {}).get('cost', 0),
                'timestamp': datetime.fromtimestamp(order_status['timestamp'] / 1000).isoformat(),
                'status': order_status['status'],
                'paper_trade': False,
                'stop_loss': decision.get('stop_loss'),
                'take_profit': decision.get('take_profit'),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing live order: {e}")
            return None
    
    def _update_position(self, decision: Dict, result: Dict):
        """Update position in Redis after order execution"""
        if not self.redis:
            return
        
        symbol = decision['symbol']
        action = decision['action']
        
        if action == 'CLOSE':
            # Close position
            position = self.redis.get_position(symbol)
            if position:
                # Calculate PnL
                entry_price = float(position.get('entry_price', 0))
                exit_price = result['price']
                size = result['amount']
                
                if position.get('side') == 'BUY':
                    pnl = (exit_price - entry_price) * size
                else:
                    pnl = (entry_price - exit_price) * size
                
                pnl -= result['fee']  # Subtract fees
                
                logger.info(f"Position closed for {symbol}. PnL: ${pnl:.2f}")
                
                # Clear position
                self.redis.delete(f"position:{symbol}")
        else:
            # Open or add to position
            existing = self.redis.get_position(symbol)
            
            if existing and existing.get('size'):
                # Add to existing position (average price)
                old_size = float(existing['size'])
                old_price = float(existing['entry_price'])
                new_size = result['amount']
                new_price = result['price']
                
                total_size = old_size + new_size
                avg_price = (old_size * old_price + new_size * new_price) / total_size
                
                position = {
                    'symbol': symbol,
                    'side': decision['side'],
                    'size': total_size,
                    'entry_price': avg_price,
                    'stop_loss': decision.get('stop_loss'),
                    'take_profit': decision.get('take_profit'),
                    'timestamp': result['timestamp']
                }
            else:
                # New position
                position = {
                    'symbol': symbol,
                    'side': decision['side'],
                    'size': result['amount'],
                    'entry_price': result['price'],
                    'stop_loss': decision.get('stop_loss'),
                    'take_profit': decision.get('take_profit'),
                    'timestamp': result['timestamp']
                }
            
            self.redis.set_position(symbol, position)
            logger.info(f"Position updated for {symbol}: {position}")
    
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an order"""
        try:
            if self.paper_trading:
                logger.info(f"Paper trade: cancelled order {order_id}")
                return True
            
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Cancelled order {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
    
    async def get_order_status(self, order_id: str, symbol: str) -> Optional[Dict]:
        """Get order status"""
        try:
            if self.paper_trading:
                return self.executed_orders.get(order_id)
            
            order = await self.exchange.fetch_order(order_id, symbol)
            return order
            
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
    
    async def get_balance(self, currency: str = 'USDT') -> float:
        """Get account balance"""
        try:
            if self.paper_trading:
                # Return simulated balance from Redis
                balance = self.redis.get(f"balance:{currency}")
                return float(balance) if balance else 100000.0
            
            balance = await self.exchange.fetch_balance()
            return balance.get(currency, {}).get('free', 0)
            
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            return 0.0
    
    async def close(self):
        """Close exchange connection"""
        if self.exchange:
            await self.exchange.close()
            logger.info("Closed order executor")
