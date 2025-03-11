import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from utils.logger import get_logger

# 获取日志器
logger = get_logger()

class FuturesScorer:
    """
    期货评分系统
    负责根据技术指标评估期货的交易机会
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        初始化期货评分系统
        
        Args:
            weights: 各指标权重配置
        """
        # 默认权重设置
        self.weights = weights or {
            'trend': 0.25,        # 趋势指标权重
            'momentum': 0.20,     # 动量指标权重
            'volatility': 0.15,   # 波动率指标权重
            'volume': 0.15,       # 成交量指标权重
            'open_interest': 0.15, # 持仓量指标权重
            'basis': 0.10         # 基差指标权重
        }
        
        logger.debug(f"初始化FuturesScorer期货评分系统，权重: {self.weights}")
    
    def calculate_score(self, df: pd.DataFrame, basis_df: Optional[pd.DataFrame] = None) -> int:
        """
        计算期货评分
        
        Args:
            df: 包含技术指标的DataFrame
            basis_df: 包含基差数据的DataFrame（可选）
            
        Returns:
            0-100的整数评分
        """
        try:
            # 初始化各部分得分
            trend_score = 0
            momentum_score = 0
            volatility_score = 0
            volume_score = 0
            open_interest_score = 0
            basis_score = 0
            
            # 获取最新数据
            latest_data = df.iloc[-1]
            
            # 1. 趋势评分
            trend_score = self._calculate_trend_score(df)
            
            # 2. 动量评分
            momentum_score = self._calculate_momentum_score(df)
            
            # 3. 波动率评分
            volatility_score = self._calculate_volatility_score(df)
            
            # 4. 成交量评分
            volume_score = self._calculate_volume_score(df)
            
            # 5. 持仓量评分
            if 'OpenInterest' in df.columns:
                open_interest_score = self._calculate_open_interest_score(df)
            
            # 6. 基差评分
            if basis_df is not None and not basis_df.empty:
                basis_score = self._calculate_basis_score(basis_df)
            
            # 计算加权总分
            total_score = (
                trend_score * self.weights['trend'] +
                momentum_score * self.weights['momentum'] +
                volatility_score * self.weights['volatility'] +
                volume_score * self.weights['volume'] +
                open_interest_score * self.weights['open_interest'] +
                basis_score * self.weights['basis']
            )
            
            # 确保分数在0-100范围内
            final_score = max(0, min(100, round(total_score)))
            
            logger.debug(f"期货评分计算完成，总分: {final_score}")
            return final_score
            
        except Exception as e:
            logger.error(f"计算期货评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_trend_score(self, df: pd.DataFrame) -> float:
        """
        计算趋势评分
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            0-100的趋势评分
        """
        try:
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data
            
            score = 50  # 初始中性分数
            
            # 1. MA趋势评分
            if all(col in latest_data for col in ['MA5', 'MA20', 'MA60']):
                # 黄金交叉（短期均线上穿中期均线）
                if latest_data['MA5'] > latest_data['MA20'] and previous_data['MA5'] <= previous_data['MA20']:
                    score += 15
                # 死亡交叉（短期均线下穿中期均线）
                elif latest_data['MA5'] < latest_data['MA20'] and previous_data['MA5'] >= previous_data['MA20']:
                    score -= 15
                
                # 多头排列（短期 > 中期 > 长期）
                if latest_data['MA5'] > latest_data['MA20'] > latest_data['MA60']:
                    score += 10
                # 空头排列（短期 < 中期 < 长期）
                elif latest_data['MA5'] < latest_data['MA20'] < latest_data['MA60']:
                    score -= 10
            
            # 2. 价格与均线关系评分
            if 'MA20' in latest_data:
                # 价格高于中期均线
                if latest_data['Close'] > latest_data['MA20']:
                    score += 5
                # 价格低于中期均线
                else:
                    score -= 5
            
            # 3. MACD评分
            if all(col in latest_data for col in ['MACD', 'Signal']):
                # MACD金叉（MACD上穿信号线）
                if latest_data['MACD'] > latest_data['Signal'] and previous_data['MACD'] <= previous_data['Signal']:
                    score += 10
                # MACD死叉（MACD下穿信号线）
                elif latest_data['MACD'] < latest_data['Signal'] and previous_data['MACD'] >= previous_data['Signal']:
                    score -= 10
                
                # MACD柱状图方向
                if 'Histogram' in latest_data:
                    if latest_data['Histogram'] > 0 and latest_data['Histogram'] > previous_data['Histogram']:
                        score += 5  # 柱状图为正且增加
                    elif latest_data['Histogram'] < 0 and latest_data['Histogram'] < previous_data['Histogram']:
                        score -= 5  # 柱状图为负且减少
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算趋势评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_momentum_score(self, df: pd.DataFrame) -> float:
        """
        计算动量评分
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            0-100的动量评分
        """
        try:
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data
            
            score = 50  # 初始中性分数
            
            # 1. RSI评分
            if 'RSI' in latest_data:
                rsi = latest_data['RSI']
                
                # RSI超买超卖
                if rsi > 70:
                    score -= 10  # 超买
                elif rsi < 30:
                    score += 10  # 超卖
                
                # RSI趋势
                if 'RSI' in previous_data:
                    if rsi > previous_data['RSI'] and rsi < 70:
                        score += 5  # RSI上升但未超买
                    elif rsi < previous_data['RSI'] and rsi > 30:
                        score -= 5  # RSI下降但未超卖
            
            # 2. 动量指标评分
            if 'Momentum' in latest_data:
                momentum = latest_data['Momentum']
                
                if momentum > 0:
                    score += 10  # 正动量
                else:
                    score -= 10  # 负动量
                
                # 动量变化
                if 'Momentum' in previous_data:
                    if momentum > previous_data['Momentum']:
                        score += 5  # 动量增加
                    else:
                        score -= 5  # 动量减少
            
            # 3. 价格变化评分
            if len(df) > 5:
                # 计算过去5天的价格变化
                price_change = (latest_data['Close'] - df.iloc[-6]['Close']) / df.iloc[-6]['Close'] * 100
                
                if price_change > 5:
                    score += 10  # 大幅上涨
                elif price_change > 2:
                    score += 5   # 中等上涨
                elif price_change < -5:
                    score -= 10  # 大幅下跌
                elif price_change < -2:
                    score -= 5   # 中等下跌
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算动量评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_volatility_score(self, df: pd.DataFrame) -> float:
        """
        计算波动率评分
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            0-100的波动率评分
        """
        try:
            latest_data = df.iloc[-1]
            
            score = 50  # 初始中性分数
            
            # 1. 波动率评分
            if 'VolatilityStd' in latest_data:
                volatility = latest_data['VolatilityStd']
                
                # 根据波动率水平调整分数
                if volatility > 0.4:
                    score -= 15  # 极高波动率，风险高
                elif volatility > 0.3:
                    score -= 10  # 高波动率
                elif volatility > 0.2:
                    score -= 5   # 中等波动率
                elif volatility < 0.1:
                    score += 5   # 低波动率，风险低
            
            # 2. 布林带宽度评分
            if all(col in latest_data for col in ['BB_Upper', 'BB_Lower', 'BB_Middle']):
                # 计算布林带宽度
                bandwidth = (latest_data['BB_Upper'] - latest_data['BB_Lower']) / latest_data['BB_Middle']
                
                if bandwidth > 0.1:
                    score -= 10  # 宽布林带，高波动
                else:
                    score += 10  # 窄布林带，低波动
                
                # 价格位置
                if latest_data['Close'] > latest_data['BB_Upper']:
                    score -= 5   # 价格超过上轨，可能超买
                elif latest_data['Close'] < latest_data['BB_Lower']:
                    score += 5   # 价格低于下轨，可能超卖
            
            # 3. ATR评分
            if 'ATR' in latest_data:
                # 计算ATR占价格的百分比
                atr_percent = latest_data['ATR'] / latest_data['Close'] * 100
                
                if atr_percent > 3:
                    score -= 10  # 高ATR，高波动
                elif atr_percent < 1:
                    score += 10  # 低ATR，低波动
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算波动率评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """
        计算成交量评分
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            0-100的成交量评分
        """
        try:
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data
            
            score = 50  # 初始中性分数
            
            # 1. 成交量变化评分
            if 'Volume' in latest_data and 'Volume' in previous_data:
                volume_change = (latest_data['Volume'] - previous_data['Volume']) / previous_data['Volume'] * 100
                
                # 价格与成交量配合
                price_up = latest_data['Close'] > previous_data['Close']
                
                if price_up and volume_change > 20:
                    score += 15  # 价格上涨且成交量大增，强势上涨
                elif price_up and volume_change < -20:
                    score -= 5   # 价格上涨但成交量大减，上涨乏力
                elif not price_up and volume_change > 20:
                    score -= 15  # 价格下跌且成交量大增，强势下跌
                elif not price_up and volume_change < -20:
                    score += 5   # 价格下跌但成交量大减，下跌乏力
            
            # 2. 成交量相对均线评分
            if 'Volume_MA' in latest_data and 'Volume' in latest_data:
                volume_ratio = latest_data['Volume'] / latest_data['Volume_MA']
                
                if volume_ratio > 2:
                    score += 10  # 成交量显著高于均线
                elif volume_ratio > 1.5:
                    score += 5   # 成交量高于均线
                elif volume_ratio < 0.5:
                    score -= 10  # 成交量显著低于均线
                elif volume_ratio < 0.8:
                    score -= 5   # 成交量低于均线
            
            # 3. 价量趋势指标评分
            if 'PVT' in latest_data and 'PVT' in previous_data:
                if latest_data['PVT'] > previous_data['PVT'] and latest_data['Close'] > previous_data['Close']:
                    score += 10  # PVT上升且价格上涨，确认上涨
                elif latest_data['PVT'] < previous_data['PVT'] and latest_data['Close'] < previous_data['Close']:
                    score -= 10  # PVT下降且价格下跌，确认下跌
                elif latest_data['PVT'] > previous_data['PVT'] and latest_data['Close'] < previous_data['Close']:
                    score += 5   # PVT上升但价格下跌，可能反转向上
                elif latest_data['PVT'] < previous_data['PVT'] and latest_data['Close'] > previous_data['Close']:
                    score -= 5   # PVT下降但价格上涨，可能反转向下
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算成交量评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_open_interest_score(self, df: pd.DataFrame) -> float:
        """
        计算持仓量评分
        
        Args:
            df: 包含技术指标的DataFrame
            
        Returns:
            0-100的持仓量评分
        """
        try:
            latest_data = df.iloc[-1]
            previous_data = df.iloc[-2] if len(df) > 1 else latest_data
            
            score = 50  # 初始中性分数
            
            # 1. 持仓量变化评分
            if 'OpenInterest' in latest_data and 'OpenInterest' in previous_data:
                oi_change = (latest_data['OpenInterest'] - previous_data['OpenInterest']) / previous_data['OpenInterest'] * 100
                
                # 价格与持仓量配合
                price_up = latest_data['Close'] > previous_data['Close']
                
                if price_up and oi_change > 5:
                    score += 15  # 价格上涨且持仓量增加，多头进场
                elif price_up and oi_change < -5:
                    score -= 5   # 价格上涨但持仓量减少，空头平仓
                elif not price_up and oi_change > 5:
                    score -= 15  # 价格下跌且持仓量增加，空头进场
                elif not price_up and oi_change < -5:
                    score += 5   # 价格下跌但持仓量减少，多头平仓
            
            # 2. 持仓量相对均线评分
            if 'OI_MA' in latest_data and 'OpenInterest' in latest_data:
                oi_ratio = latest_data['OpenInterest'] / latest_data['OI_MA']
                
                if oi_ratio > 1.2:
                    score += 10  # 持仓量显著高于均线
                elif oi_ratio > 1.1:
                    score += 5   # 持仓量高于均线
                elif oi_ratio < 0.8:
                    score -= 10  # 持仓量显著低于均线
                elif oi_ratio < 0.9:
                    score -= 5   # 持仓量低于均线
            
            # 3. 持仓量/成交量比率评分
            if 'OI_Volume_Ratio' in latest_data:
                oi_vol_ratio = latest_data['OI_Volume_Ratio']
                
                if oi_vol_ratio > 10:
                    score += 5   # 持仓量远大于成交量，市场稳定
                elif oi_vol_ratio < 2:
                    score -= 5   # 持仓量接近成交量，市场活跃
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算持仓量评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def _calculate_basis_score(self, basis_df: pd.DataFrame) -> float:
        """
        计算基差评分
        
        Args:
            basis_df: 包含基差数据的DataFrame
            
        Returns:
            0-100的基差评分
        """
        try:
            latest_data = basis_df.iloc[-1]
            previous_data = basis_df.iloc[-2] if len(basis_df) > 1 else latest_data
            
            score = 50  # 初始中性分数
            
            # 1. 基差方向评分
            if 'Basis' in latest_data:
                basis = latest_data['Basis']
                
                if basis > 0:
                    score += 5   # 正基差（期货升水）
                else:
                    score -= 5   # 负基差（期货贴水）
            
            # 2. 基差变化评分
            if 'Basis' in latest_data and 'Basis' in previous_data:
                basis_change = latest_data['Basis'] - previous_data['Basis']
                
                if basis_change > 0:
                    score += 5   # 基差增加
                else:
                    score -= 5   # 基差减少
            
            # 3. 基差率评分
            if 'BasisRatio' in latest_data:
                basis_ratio = latest_data['BasisRatio']
                
                if basis_ratio > 5:
                    score += 10  # 基差率高，期货大幅升水
                elif basis_ratio < -5:
                    score -= 10  # 基差率低，期货大幅贴水
            
            # 4. 基差Z-Score评分
            if 'SpreadZScore' in latest_data:
                z_score = latest_data['SpreadZScore']
                
                if z_score > 2:
                    score -= 15  # 基差显著高于历史均值，可能回归
                elif z_score < -2:
                    score += 15  # 基差显著低于历史均值，可能回归
            
            # 确保分数在0-100范围内
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"计算基差评分时出错: {str(e)}")
            logger.exception(e)
            return 50  # 出错时返回中性评分
    
    def get_recommendation(self, score: int) -> str:
        """
        根据评分获取交易建议
        
        Args:
            score: 0-100的整数评分
            
        Returns:
            交易建议
        """
        if score >= 80:
            return "强烈买入"
        elif score >= 65:
            return "买入"
        elif score >= 55:
            return "持有"
        elif score >= 45:
            return "观望"
        elif score >= 35:
            return "减持"
        elif score >= 20:
            return "卖出"
        else:
            return "强烈卖出"
    
    def batch_score_futures(self, futures_with_indicators: Dict[str, pd.DataFrame], 
                          basis_data: Optional[Dict[str, pd.DataFrame]] = None) -> List[Tuple[str, int, str]]:
        """
        批量评分多个期货
        
        Args:
            futures_with_indicators: 字典，键为期货代码，值为包含技术指标的DataFrame
            basis_data: 字典，键为期货代码，值为包含基差数据的DataFrame（可选）
            
        Returns:
            列表，每项为(期货代码, 评分, 建议)的元组
        """
        try:
            results = []
            
            for code, df in futures_with_indicators.items():
                # 获取对应的基差数据（如果有）
                basis_df = basis_data.get(code) if basis_data else None
                
                # 计算评分
                score = self.calculate_score(df, basis_df)
                
                # 获取建议
                recommendation = self.get_recommendation(score)
                
                # 添加到结果列表
                results.append((code, score, recommendation))
            
            # 按评分降序排序
            results.sort(key=lambda x: x[1], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"批量评分期货时出错: {str(e)}")
            logger.exception(e)
            return []