#!/usr/bin/env python3
"""
Script de backtesting simplifié
Utilise les données historiques téléchargées
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings


def load_historical_data(symbol: str, timeframe: str = '1h'):
    """Charger les données historiques depuis CSV"""
    data_dir = Path('data/historical')
    filename = f"{symbol.replace('/', '_')}_{timeframe}.csv"
    filepath = data_dir / filename
    
    if not filepath.exists():
        logger.error(f"Fichier non trouvé: {filepath}")
        return None
    
    df = pd.read_csv(filepath, index_col='datetime', parse_dates=True)
    logger.info(f"✅ Chargé {len(df)} bougies pour {symbol} ({timeframe})")
    return df


def calculate_indicators(df):
    """Calculer des indicateurs techniques simples"""
    # SMA (Simple Moving Average)
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    
    # RSI (Relative Strength Index)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = exp1 - exp2
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Volatilité
    df['returns'] = df['close'].pct_change()
    df['volatility'] = df['returns'].rolling(window=20).std()
    
    return df


def generate_signals(df):
    """Générer des signaux de trading simples"""
    signals = pd.DataFrame(index=df.index)
    signals['position'] = 0
    
    # Stratégie : Croisement SMA 20/50 + RSI
    # Signal ACHAT : SMA 20 croise au-dessus de SMA 50 ET RSI < 70
    buy_signal = (
        (df['sma_20'] > df['sma_50']) &
        (df['sma_20'].shift(1) <= df['sma_50'].shift(1)) &
        (df['rsi'] < 70)
    )
    
    # Signal VENTE : SMA 20 croise en-dessous de SMA 50 OU RSI > 80
    sell_signal = (
        ((df['sma_20'] < df['sma_50']) &
         (df['sma_20'].shift(1) >= df['sma_50'].shift(1))) |
        (df['rsi'] > 80)
    )
    
    signals.loc[buy_signal, 'position'] = 1
    signals.loc[sell_signal, 'position'] = -1
    
    # Forward fill pour maintenir la position
    signals['position'] = signals['position'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    return signals


def backtest_strategy(df, signals, initial_capital=10000, commission=0.0021):
    """Backtester la stratégie"""
    positions = pd.DataFrame(index=signals.index)
    positions['position'] = signals['position']
    
    # Calculer les retours
    positions['returns'] = df['close'].pct_change()
    positions['strategy_returns'] = positions['position'].shift(1) * positions['returns']
    
    # Appliquer les frais de transaction (quand position change)
    position_changes = positions['position'].diff().abs()
    positions['strategy_returns'] = positions['strategy_returns'] - (position_changes * commission)
    
    # Calculer la valeur du portfolio
    positions['equity'] = initial_capital * (1 + positions['strategy_returns']).cumprod()
    
    # Métriques
    total_return = (positions['equity'].iloc[-1] / initial_capital - 1) * 100
    
    # Nombre de trades
    num_trades = (positions['position'].diff() != 0).sum()
    
    # Drawdown maximum
    running_max = positions['equity'].expanding().max()
    drawdown = (positions['equity'] - running_max) / running_max
    max_drawdown = drawdown.min() * 100
    
    # Sharpe ratio (annualisé)
    sharpe_ratio = (positions['strategy_returns'].mean() / positions['strategy_returns'].std()) * np.sqrt(365 * 24)  # pour hourly
    
    # Win rate
    winning_trades = positions[positions['strategy_returns'] > 0]['strategy_returns']
    losing_trades = positions[positions['strategy_returns'] < 0]['strategy_returns']
    win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades)) * 100 if (len(winning_trades) + len(losing_trades)) > 0 else 0
    
    return {
        'initial_capital': initial_capital,
        'final_equity': positions['equity'].iloc[-1],
        'total_return': total_return,
        'num_trades': num_trades,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'win_rate': win_rate,
        'positions': positions
    }


def main():
    """Main function"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("=" * 70)
    logger.info("🔬 BACKTESTING - Stratégie SMA Crossover + RSI")
    logger.info("=" * 70)
    logger.info("")
    
    symbols = settings.trading.assets_list
    timeframe = '1h'
    initial_capital = settings.trading.initial_capital
    commission = settings.trading.simulated_fees
    
    logger.info(f"📊 Paramètres:")
    logger.info(f"   Symboles: {', '.join(symbols)}")
    logger.info(f"   Timeframe: {timeframe}")
    logger.info(f"   Capital initial: {initial_capital:,.0f}€")
    logger.info(f"   Commission: {commission*100:.2f}%")
    logger.info("")
    logger.info("📈 Stratégie:")
    logger.info("   - ACHAT: SMA 20 croise au-dessus SMA 50 ET RSI < 70")
    logger.info("   - VENTE: SMA 20 croise en-dessous SMA 50 OU RSI > 80")
    logger.info("")
    logger.info("=" * 70)
    logger.info("")
    
    all_results = {}
    
    for symbol in symbols:
        logger.info(f"🔍 Backtesting {symbol}...")
        logger.info("-" * 70)
        
        # Charger les données
        df = load_historical_data(symbol, timeframe)
        if df is None or df.empty:
            logger.warning(f"⚠️  Pas de données pour {symbol}, ignoré")
            continue
        
        # Calculer les indicateurs
        logger.info(f"📊 Calcul des indicateurs techniques...")
        df = calculate_indicators(df)
        
        # Générer les signaux
        logger.info(f"🎯 Génération des signaux de trading...")
        signals = generate_signals(df)
        
        # Backtest
        logger.info(f"⚙️  Exécution du backtest...")
        results = backtest_strategy(df, signals, initial_capital, commission)
        all_results[symbol] = results
        
        # Afficher les résultats
        logger.info("")
        logger.info(f"📈 Résultats pour {symbol}:")
        logger.info(f"   Capital initial:    {results['initial_capital']:>12,.2f}€")
        logger.info(f"   Capital final:      {results['final_equity']:>12,.2f}€")
        
        if results['total_return'] >= 0:
            logger.success(f"   Rendement total:    {results['total_return']:>12.2f}%  ✅")
        else:
            logger.error(f"   Rendement total:    {results['total_return']:>12.2f}%  ❌")
        
        logger.info(f"   Nombre de trades:   {results['num_trades']:>12}")
        logger.info(f"   Drawdown max:       {results['max_drawdown']:>12.2f}%")
        logger.info(f"   Sharpe ratio:       {results['sharpe_ratio']:>12.2f}")
        logger.info(f"   Win rate:           {results['win_rate']:>12.2f}%")
        logger.info("")
        logger.info("=" * 70)
        logger.info("")
    
    # Résumé global
    if all_results:
        logger.info("📊 RÉSUMÉ GLOBAL")
        logger.info("=" * 70)
        
        total_initial = initial_capital * len(all_results)
        total_final = sum(r['final_equity'] for r in all_results.values())
        total_return = (total_final / total_initial - 1) * 100
        avg_sharpe = np.mean([r['sharpe_ratio'] for r in all_results.values()])
        total_trades = sum(r['num_trades'] for r in all_results.values())
        
        logger.info(f"Capital total initial:  {total_initial:>12,.2f}€")
        logger.info(f"Capital total final:    {total_final:>12,.2f}€")
        
        if total_return >= 0:
            logger.success(f"Rendement total:        {total_return:>12.2f}%  ✅")
        else:
            logger.error(f"Rendement total:        {total_return:>12.2f}%  ❌")
        
        logger.info(f"Sharpe ratio moyen:     {avg_sharpe:>12.2f}")
        logger.info(f"Total de trades:        {total_trades:>12}")
        logger.info("")
        
        # Recommandation
        logger.info("💡 RECOMMANDATION:")
        if total_return > 0 and avg_sharpe > 1.5:
            logger.success("   ✅ Bons résultats! Stratégie potentiellement viable.")
            logger.info("   👉 Vous pouvez tester en paper trading ou testnet.")
        elif total_return > 0:
            logger.warning("   ⚠️  Résultats positifs mais Sharpe faible.")
            logger.info("   👉 Optimisez la stratégie avant de passer en live.")
        else:
            logger.error("   ❌ Résultats négatifs sur la période.")
            logger.info("   👉 NE PAS trader avec cette stratégie!")
            logger.info("   👉 Testez d'autres paramètres ou stratégies.")
        
        logger.info("")
        logger.info("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

