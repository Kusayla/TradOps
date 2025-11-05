#!/usr/bin/env python3
"""
Script d'export des données de trading vers le dashboard web.

Ce script lit les données de trading depuis Redis/TimescaleDB et génère
le fichier web/data/latest.json pour le dashboard GitHub Pages.

Usage:
    python scripts/export_dashboard_data.py
    
Peut être appelé automatiquement après chaque cycle de trading ou via cron.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import settings
from src.storage.redis_client import RedisClient
from loguru import logger


class DashboardExporter:
    """Exporte les données de trading vers le format JSON du dashboard."""
    
    def __init__(self):
        self.redis_client = RedisClient()
        self.output_path = Path(__file__).parent.parent / "docs" / "data" / "latest.json"
    
    def get_equity_series(self, days: int = 60) -> List[Dict[str, Any]]:
        """
        Récupère la série temporelle d'équité depuis Redis.
        
        Args:
            days: Nombre de jours d'historique à récupérer
            
        Returns:
            Liste de points {ts, equity}
        """
        try:
            # Clé pour l'historique du solde dans Redis
            balance_key = f"{settings.redis.key_prefix}:balance_history"
            
            # Récupérer l'historique du solde depuis Redis (sorted set)
            balance_history = self.redis_client.client.zrange(
                balance_key,
                0, -1,
                withscores=True
            )
            
            if not balance_history:
                logger.warning("Aucun historique de balance trouvé, utilisation du solde actuel")
                # Récupérer le solde actuel
                try:
                    current_balance = float(self.redis_client.get("balance_USD") or settings.trading.initial_capital)
                except:
                    current_balance = settings.trading.initial_capital
                
                return [{
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "equity": current_balance
                }]
            
            # Convertir en format attendu
            series = []
            for balance_json, timestamp in balance_history:
                try:
                    # Le balance_json peut être soit un JSON, soit un nombre direct
                    if isinstance(balance_json, (int, float)):
                        equity = float(balance_json)
                    elif isinstance(balance_json, bytes):
                        balance_json = balance_json.decode('utf-8')
                        try:
                            balance_data = json.loads(balance_json)
                            equity = float(balance_data.get("total", balance_data.get("equity", 0)))
                        except json.JSONDecodeError:
                            equity = float(balance_json)
                    else:
                        balance_data = json.loads(str(balance_json))
                        equity = float(balance_data.get("total", balance_data.get("equity", 0)))
                    
                    series.append({
                        "ts": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                        "equity": equity
                    })
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Erreur de parsing pour un point de balance: {e}")
                    continue
            
            # Limiter aux N derniers jours si nécessaire
            if len(series) > days:
                series = series[-days:]
            
            # Si toujours pas de données, utiliser le solde actuel
            if not series:
                try:
                    current_balance = float(self.redis_client.get("balance_USD") or settings.trading.initial_capital)
                except:
                    current_balance = settings.trading.initial_capital
                    
                series = [{
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "equity": current_balance
                }]
            
            return series
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la série d'équité: {e}")
            # Fallback: retourner le capital initial comme point unique
            return [{
                "ts": datetime.now(timezone.utc).isoformat(),
                "equity": settings.trading.initial_capital
            }]
    
    def get_trades_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des trades depuis Redis.
        
        Args:
            limit: Nombre maximum de trades à récupérer
            
        Returns:
            Liste de trades formatés pour le dashboard
        """
        try:
            # Récupérer les trades depuis Redis
            # Format attendu: liste avec les trades les plus récents
            trades_keys = self.redis_client.client.lrange(
                f"{settings.redis.key_prefix}:trades_history",
                0, limit - 1
            )
            
            if not trades_keys:
                logger.warning("Aucun trade trouvé dans l'historique")
                return []
            
            trades = []
            for trade_json in trades_keys:
                try:
                    trade = json.loads(trade_json)
                    
                    # Convertir au format attendu par le dashboard
                    formatted_trade = {
                        "enter_ts": trade.get("entry_time", datetime.now(timezone.utc).isoformat()),
                        "exit_ts": trade.get("exit_time", datetime.now(timezone.utc).isoformat()),
                        "symbol": trade.get("symbol", "UNKNOWN"),
                        "side": trade.get("side", "long").lower(),
                        "size": float(trade.get("size", 0)),
                        "entry": float(trade.get("entry_price", 0)),
                        "exit": float(trade.get("exit_price", 0)),
                        "pnl": float(trade.get("pnl", 0)),
                        "tags": trade.get("tags", [])
                    }
                    
                    trades.append(formatted_trade)
                    
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Erreur de parsing pour un trade: {e}")
                    continue
            
            # Trier par date d'entrée (plus récent en premier)
            trades.sort(key=lambda x: x["enter_ts"], reverse=True)
            
            return trades
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des trades: {e}")
            return []
    
    def export(self):
        """Exporte les données vers le fichier JSON."""
        try:
            logger.info("Début de l'export des données dashboard...")
            
            # Récupérer les données
            series = self.get_equity_series(days=60)
            trades = self.get_trades_history(limit=100)
            
            # Créer la structure JSON
            data = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "series": series,
                "trades": trades
            }
            
            # Créer le répertoire si nécessaire
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le fichier
            with open(self.output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.success(
                f"✅ Dashboard exporté: {len(series)} points série, "
                f"{len(trades)} trades → {self.output_path}"
            )
            
            # Afficher quelques stats
            if series:
                first_equity = series[0]["equity"]
                last_equity = series[-1]["equity"]
                pnl = last_equity - first_equity
                logger.info(f"   Capital: ${first_equity:.2f} → ${last_equity:.2f} (PnL: ${pnl:+.2f})")
            
            if trades:
                winning_trades = sum(1 for t in trades if t["pnl"] > 0)
                winrate = (winning_trades / len(trades)) * 100 if trades else 0
                logger.info(f"   Trades: {len(trades)} total, {winning_trades} gagnants ({winrate:.1f}%)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'export dashboard: {e}")
            return False


def main():
    """Point d'entrée principal."""
    logger.info("🚀 Export Dashboard - Début")
    
    try:
        exporter = DashboardExporter()
        success = exporter.export()
        
        if success:
            logger.success("✅ Export terminé avec succès")
            sys.exit(0)
        else:
            logger.error("❌ Export échoué")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("⚠️ Export interrompu par l'utilisateur")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Erreur fatale: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

