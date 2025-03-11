import pandas as pd
import numpy as np
from typing import Dict, Optional, Any, Tuple
from utils.logger import get_logger
from services.technical_indicator import TechnicalIndicator

# 获取日志器
logger = get_logger()

class FuturesTechnicalIndicator(TechnicalIndicator):
    """
    期货技术指标计算服务
    继承自基础技术指标计算服务，并添加期货特有指标
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        初始化期货技术指标计算服务
        
        Args:
            params: 技术指标参数配置
        """
        # 调用父类初始化方法
        super().__init__(params)
        
        # 期货特有参数设置
        self.futures_params = params or {
            'basis_ma_period': 20,
            'open_interest_ma_period': 14,
            'momentum_period': 10,
            'volatility_period': 20
        }
        
        logger.debug(f"初始化FuturesTechnicalIndicator期货技术指标计算服务，参数: {self.futures_params}")
    
    def calculate_basis(self, futures_df: pd.DataFrame, spot_df: pd.DataFrame) -> pd.Series:
        """
        计算基差(期货价格-现货价格)
        
        Args:
            futures_df: 期货价格DataFrame
            spot_df: 现货价格DataFrame
            
        Returns:
            基差序列
        """
        try:
            # 确保两个DataFrame的索引是日期类型
            if not isinstance(futures_df.index, pd.DatetimeIndex):
                futures_df.index = pd.to_datetime(futures_df.index)
            
            if not isinstance(spot_df.index, pd.DatetimeIndex):
                spot_df.index = pd.to_datetime(spot_df.index)
            
            # 合并数据
            merged_df = pd.merge(
                futures_df[['Close']], 
                spot_df[['Close']], 
                left_index=True, 
                right_index=True,
                how='inner',
                suffixes=('_futures', '_spot')
            )
            
            # 计算基差
            basis = merged_df['Close_futures'] - merged_df['Close_spot']
            
            return basis
        except Exception as e:
            logger.error(f"计算基差时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_basis_ratio(self, futures_df: pd.DataFrame, spot_df: pd.DataFrame) -> pd.Series:
        """
        计算基差率((期货价格-现货价格)/现货价格)
        
        Args:
            futures_df: 期货价格DataFrame
            spot_df: 现货价格DataFrame
            
        Returns:
            基差率序列
        """
        try:
            # 确保两个DataFrame的索引是日期类型
            if not isinstance(futures_df.index, pd.DatetimeIndex):
                futures_df.index = pd.to_datetime(futures_df.index)
            
            if not isinstance(spot_df.index, pd.DatetimeIndex):
                spot_df.index = pd.to_datetime(spot_df.index)
            
            # 合并数据
            merged_df = pd.merge(
                futures_df[['Close']], 
                spot_df[['Close']], 
                left_index=True, 
                right_index=True,
                how='inner',
                suffixes=('_futures', '_spot')
            )
            
            # 计算基差率
            basis_ratio = (merged_df['Close_futures'] - merged_df['Close_spot']) / merged_df['Close_spot'] * 100
            
            return basis_ratio
        except Exception as e:
            logger.error(f"计算基差率时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_open_interest_change(self, df: pd.DataFrame) -> pd.Series:
        """
        计算持仓量变化率
        
        Args:
            df: 包含OpenInterest列的DataFrame
            
        Returns:
            持仓量变化率序列
        """
        try:
            if 'OpenInterest' not in df.columns:
                logger.warning("数据中缺少OpenInterest列，无法计算持仓量变化率")
                return pd.Series(index=df.index)
            
            # 计算持仓量变化率
            open_interest_change = df['OpenInterest'].pct_change() * 100
            
            return open_interest_change
        except Exception as e:
            logger.error(f"计算持仓量变化率时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_open_interest_ma(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算持仓量移动平均
        
        Args:
            df: 包含OpenInterest列的DataFrame
            period: 周期
            
        Returns:
            持仓量移动平均序列
        """
        try:
            if 'OpenInterest' not in df.columns:
                logger.warning("数据中缺少OpenInterest列，无法计算持仓量移动平均")
                return pd.Series(index=df.index)
            
            # 计算持仓量移动平均
            open_interest_ma = df['OpenInterest'].rolling(window=period).mean()
            
            return open_interest_ma
        except Exception as e:
            logger.error(f"计算持仓量移动平均时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_momentum(self, series: pd.Series, period: int = 10) -> pd.Series:
        """
        计算动量指标
        
        Args:
            series: 价格序列
            period: 周期
            
        Returns:
            动量指标序列
        """
        try:
            # 计算动量指标
            momentum = series.diff(period)
            
            return momentum
        except Exception as e:
            logger.error(f"计算动量指标时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_price_volume_trend(self, df: pd.DataFrame) -> pd.Series:
        """
        计算价量趋势指标(PVT)
        
        Args:
            df: 包含Close和Volume列的DataFrame
            
        Returns:
            价量趋势指标序列
        """
        try:
            if 'Close' not in df.columns or 'Volume' not in df.columns:
                logger.warning("数据中缺少Close或Volume列，无法计算价量趋势指标")
                return pd.Series(index=df.index)
            
            # 计算价格变化率
            price_change_rate = df['Close'].pct_change()
            
            # 计算PVT
            pvt = (price_change_rate * df['Volume']).cumsum()
            
            return pvt
        except Exception as e:
            logger.error(f"计算价量趋势指标时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_open_interest_volume_ratio(self, df: pd.DataFrame) -> pd.Series:
        """
        计算持仓量/成交量比率
        
        Args:
            df: 包含OpenInterest和Volume列的DataFrame
            
        Returns:
            持仓量/成交量比率序列
        """
        try:
            if 'OpenInterest' not in df.columns or 'Volume' not in df.columns:
                logger.warning("数据中缺少OpenInterest或Volume列，无法计算持仓量/成交量比率")
                return pd.Series(index=df.index)
            
            # 避免除以零
            volume_non_zero = df['Volume'].replace(0, np.nan)
            
            # 计算持仓量/成交量比率
            oi_volume_ratio = df['OpenInterest'] / volume_non_zero
            
            return oi_volume_ratio
        except Exception as e:
            logger.error(f"计算持仓量/成交量比率时出错: {str(e)}")
            logger.exception(e)
            return pd.Series()
    
    def calculate_futures_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有期货技术指标
        
        Args:
            df: 原始价格数据，包含Open, High, Low, Close, Volume, OpenInterest列
            
        Returns:
            添加了技术指标的DataFrame
        """
        try:
            # 首先计算基础技术指标
            result_df = self.calculate_indicators(df)
            
            # 计算期货特有指标
            
            # 持仓量变化率
            if 'OpenInterest' in df.columns:
                result_df['OI_Change'] = self.calculate_open_interest_change(df)
                
                # 持仓量移动平均
                result_df['OI_MA'] = self.calculate_open_interest_ma(
                    df, 
                    self.futures_params['open_interest_ma_period']
                )
                
                # 持仓量/成交量比率
                result_df['OI_Volume_Ratio'] = self.calculate_open_interest_volume_ratio(df)
            
            # 动量指标
            result_df['Momentum'] = self.calculate_momentum(
                df['Close'], 
                self.futures_params['momentum_period']
            )
            
            # 价量趋势指标
            result_df['PVT'] = self.calculate_price_volume_trend(df)
            
            # 计算期货特有的波动率指标
            # 使用对数收益率计算波动率
            log_returns = np.log(df['Close'] / df['Close'].shift(1))
            result_df['LogReturns'] = log_returns
            
            # 计算波动率（标准差）
            result_df['VolatilityStd'] = log_returns.rolling(
                window=self.futures_params['volatility_period']
            ).std() * np.sqrt(252)  # 年化波动率
            
            return result_df
            
        except Exception as e:
            logger.error(f"计算期货技术指标时出错: {str(e)}")
            logger.exception(e)
            raise
    
    def calculate_term_structure(self, near_contract_df: pd.DataFrame, far_contract_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算期限结构指标
        
        Args:
            near_contract_df: 近期合约DataFrame
            far_contract_df: 远期合约DataFrame
            
        Returns:
            包含期限结构指标的DataFrame
        """
        try:
            # 确保两个DataFrame的索引是日期类型
            if not isinstance(near_contract_df.index, pd.DatetimeIndex):
                near_contract_df.index = pd.to_datetime(near_contract_df.index)
            
            if not isinstance(far_contract_df.index, pd.DatetimeIndex):
                far_contract_df.index = pd.to_datetime(far_contract_df.index)
            
            # 合并数据
            merged_df = pd.merge(
                near_contract_df[['Close']], 
                far_contract_df[['Close']], 
                left_index=True, 
                right_index=True,
                how='inner',
                suffixes=('_near', '_far')
            )
            
            # 计算期限结构指标
            # 1. 价差
            merged_df['Spread'] = merged_df['Close_far'] - merged_df['Close_near']
            
            # 2. 价差率
            merged_df['SpreadRatio'] = (merged_df['Close_far'] - merged_df['Close_near']) / merged_df['Close_near'] * 100
            
            # 3. 价差移动平均
            merged_df['SpreadMA'] = merged_df['Spread'].rolling(window=20).mean()
            
            # 4. 价差标准差
            merged_df['SpreadStd'] = merged_df['Spread'].rolling(window=20).std()
            
            # 5. 价差Z-Score
            merged_df['SpreadZScore'] = (merged_df['Spread'] - merged_df['SpreadMA']) / merged_df['SpreadStd']
            
            return merged_df
        except Exception as e:
            logger.error(f"计算期限结构指标时出错: {str(e)}")
            logger.exception(e)
            return pd.DataFrame()