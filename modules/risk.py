#!/usr/bin/env python3
"""
Cryptocurrency Trading Risk Management Module 🛡️
风险管理、止损止盈和仓位控制
"""

import os
import yaml
from typing import Dict, List
from datetime import datetime
import numpy as np

class RiskManager:
    """风险管理员 - 监控风险和触发保护机制"""
    
    def __init__(self):
        self.config_path = '/home/tancau/.openclaw/workspace/skills/cryptocurrency-trading/config/preferences.yaml'
        self.load_config()
        
    def load_config(self):
        """加载配置参数"""
        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)
            self.max_daily_loss_pct = config['risk_management']['max_daily_loss_pct']
            self.max_drawdown_pct = config['risk_management']['max_drawdown_pct']
            self.single_coin_max_pct = config['risk_management']['position_limits']['single_coin_max_pct']
            
    def calculate_var(self, portfolio_value: float, confidence_level: float = 95, historical_days: int = 20) -> float:
        """计算在险价值 (VaR)"""
        # 简化实现，实际需要历史数据
        if not hasattr(self, 'price_history'):
            self.price_history = []
            
        if len(self.price_history) < historical_days:
            return None
            
        # 计算收益率分布
        returns = np.diff([h / max(h, 100) for h in self.price_history])
        
        # 简化 VaR 计算（使用标准差）
        std_dev = np.std(returns)
        var_value = portfolio_value * (std_dev * 1.96)  # 95%置信度
        
        return var_value
    
    def check_portfolio_health(self, current_price: float, initial_price: float) -> Dict:
        """检查投资组合健康状态"""
        drawdown_pct = ((initial_price - current_price) / initial_price) * 100
        
        health = {
            'timestamp': datetime.now().isoformat(),
            'drawdown_pct': drawdown_pct,
            'max_drawdown_alert': drawdown_pct > self.max_drawdown_pct,
            'daily_loss_alert': False,  # 需要从日志中检查
            'recommendations': []
        }
        
        if health['max_drawdown_alert']:
            health['recommendations'].append(
                f"⚠️ Drawdown exceeded limit ({drawdown_pct:.2f}% > {self.max_drawdown_pct}%). Consider reducing positions."
            )
        elif drawdown_pct < 0:
            # 盈利状态
            profit_pct = -drawdown_pct
            health['recommendations'].append(
                f"✅ Profit of {profit_pct:.2f}%. Monitor for take profit triggers."
            )
            
        return health
    
    def check_position_limits(self, position_value: float, portfolio_value: float) -> Dict:
        """检查仓位限制"""
        position_pct = (position_value / portfolio_value) * 100
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'position_pct': position_pct,
            'limit_pct': self.single_coin_max_pct,
            'within_limits': position_pct <= self.single_coin_max_pct
        }
        
        if not result['within_limits']:
            excess = position_pct - self.single_coin_max_pct
            result['action_required'] = f"Reduce position by at least {excess:.2f}% to stay within {self.single_coin_max_pct}%"
            
        return result
    
    def generate_risk_report(self, portfolio_stats: Dict) -> str:
        """生成风险报告"""
        report_lines = [
            "╔════════════════════════════════════════════╗",
            "║  🛡️ Risk Management Report ║",
            "╚════════════════════════════════════════════╝",
            "",
            f"Report Time: {portfolio_stats.get('timestamp', 'N/A')}",
            "",
        ]
        
        if 'drawdown_pct' in portfolio_stats:
            report_lines.extend([
                f"Current Drawdown: {portfolio_stats['drawdown_pct']:.2f}%",
                f"Max Drawdown Limit: {self.max_drawdown_pct}%",
                f"Status: {'⚠️ ALERT' if portfolio_stats.get('max_drawdown_alert') else '✅ OK'}",
            ])
        
        report_lines.append("")
        report_lines.append("Position Limits:")
        report_lines.append(f"  • Single Coin Max: {self.single_coin_max_pct}%")
        if 'position_pct' in portfolio_stats:
            report_lines.append(f"  • Current Position: {portfolio_stats['position_pct']:.2f}%")
        
        if portfolio_stats.get('recommendations'):
            report_lines.append("")
            report_lines.append("Recommendations:")
            for rec in portfolio_stats['recommendations']:
                report_lines.append(f"  • {rec}")
                
        return "\n".join(report_lines)


if __name__ == "__main__":
    # 测试模块
    risk_manager = RiskManager()
    
    # 示例数据
    stats = {
        'timestamp': datetime.now().isoformat(),
        'drawdown_pct': -5.2,  # 盈利 5.2%
        'position_pct': 8.5     # 仓位占比 8.5%
    }
    
    report = risk_manager.generate_risk_report(stats)
    print(report)