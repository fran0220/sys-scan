import pandas as pd
from datetime import datetime, timedelta
import asyncio
from typing import Dict, List, Optional, Tuple, Any
from utils.logger import get_logger

# 获取日志器
logger = get_logger()

class FuturesDataProvider:
    """
    异步期货数据提供服务
    负责获取期货产品的历史数据
    """
    
    def __init__(self):
        """初始化数据提供者服务"""
        logger.debug("初始化FuturesDataProvider")
    
    async def get_futures_data(self, futures_code: str, 
                              start_date: Optional[str] = None, 
                              end_date: Optional[str] = None) -> pd.DataFrame:
        """
        异步获取期货数据
        
        Args:
            futures_code: 期货代码
            start_date: 开始日期，格式YYYYMMDD，默认为一年前
            end_date: 结束日期，格式YYYYMMDD，默认为今天
            
        Returns:
            包含历史数据的DataFrame
        """
        # 使用线程池执行同步的akshare调用
        return await asyncio.to_thread(
            self._get_futures_data_sync, 
            futures_code, 
            start_date, 
            end_date
        )
    
    def _get_futures_data_sync(self, futures_code: str, 
                             start_date: Optional[str] = None, 
                             end_date: Optional[str] = None) -> pd.DataFrame:
        """
        同步获取期货数据的实现
        将被异步方法调用
        """
        import akshare as ak
        
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
            
        # 确保日期格式统一（移除可能的'-'符号）
        if isinstance(start_date, str) and '-' in start_date:
            start_date = start_date.replace('-', '')
        if isinstance(end_date, str) and '-' in end_date:
            end_date = end_date.replace('-', '')
            
        try:
            logger.debug(f"获取期货数据: {futures_code}")
            
            # 判断是否是主力合约
            is_main_contract = False
            if futures_code.endswith('88') or futures_code.endswith('99'):
                is_main_contract = True
                
            # 判断交易所
            exchange = self._determine_exchange(futures_code)
            
            if is_main_contract:
                # 获取主力连续合约
                logger.debug(f"获取主力连续合约数据: {futures_code}")
                try:
                    # 尝试使用新浪财经API获取主力连续合约数据
                    df = ak.futures_main_sina(symbol=futures_code[:-2], start_date=start_date, end_date=end_date)
                except Exception as e:
                    logger.warning(f"使用新浪财经API获取主力连续合约数据失败: {str(e)}，尝试使用其他API")
                    # 尝试使用其他API
                    df = ak.futures_zh_daily(symbol=futures_code)
            else:
                # 获取普通合约
                logger.debug(f"获取普通合约数据: {futures_code}, 交易所: {exchange}")
                
                if exchange == "SHFE":  # 上海期货交易所
                    df = ak.futures_zh_daily(symbol=futures_code)
                elif exchange == "DCE":  # 大连商品交易所
                    df = ak.futures_zh_daily(symbol=futures_code)
                elif exchange == "CZCE":  # 郑州商品交易所
                    df = ak.futures_zh_daily(symbol=futures_code)
                elif exchange == "CFFEX":  # 中国金融期货交易所
                    df = ak.futures_zh_daily(symbol=futures_code)
                else:
                    # 默认使用通用API
                    df = ak.futures_zh_daily(symbol=futures_code)
            
            # 标准化列名
            # 根据实际数据结构调整列名映射
            if 'date' in df.columns:
                df = df.rename(columns={
                    "date": "Date",
                    "open": "Open",
                    "high": "High",
                    "low": "Low",
                    "close": "Close",
                    "volume": "Volume",
                    "open_interest": "OpenInterest",
                    "turnover": "Amount"
                })
            else:
                # 尝试根据常见列名模式进行映射
                columns_mapping = {
                    "日期": "Date",
                    "开盘价": "Open",
                    "最高价": "High",
                    "最低价": "Low",
                    "收盘价": "Close",
                    "成交量": "Volume",
                    "持仓量": "OpenInterest",
                    "成交额": "Amount"
                }
                
                # 创建新的DataFrame以确保列顺序和存在性
                new_df = pd.DataFrame(index=df.index)
                
                # 遍历映射，填充新DataFrame
                for orig_col, new_col in columns_mapping.items():
                    if orig_col in df.columns:
                        new_df[new_col] = df[orig_col]
                
                # 如果映射后的DataFrame为空，则使用原始DataFrame
                if new_df.empty:
                    logger.warning(f"无法映射期货数据列名，使用原始列名")
                    # 尝试将所有列名转为首字母大写
                    df.columns = [col.capitalize() for col in df.columns]
                else:
                    df = new_df
            
            # 确保日期列是日期类型
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df.set_index('Date', inplace=True)
            
            # 确保按日期升序排序
            df.sort_index(inplace=True)
            
            # 过滤日期范围
            try:
                start_date_dt = pd.to_datetime(start_date, format='%Y%m%d')
                end_date_dt = pd.to_datetime(end_date, format='%Y%m%d')
                df = df[(df.index >= start_date_dt) & (df.index <= end_date_dt)]
                logger.debug(f"日期过滤后数据点数: {len(df)}")
            except Exception as e:
                logger.warning(f"日期过滤出错: {str(e)}，返回原始数据")
            
            # 确保必要的列存在
            required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            for col in required_columns:
                if col not in df.columns:
                    logger.warning(f"数据中缺少{col}列，使用0值填充")
                    df[col] = 0.0
            
            # 添加OpenInterest列（如果不存在）
            if 'OpenInterest' not in df.columns:
                logger.warning(f"数据中缺少OpenInterest列，使用0值填充")
                df['OpenInterest'] = 0.0
            
            # 添加Amount列（如果不存在）
            if 'Amount' not in df.columns:
                logger.warning(f"数据中缺少Amount列，使用0值填充")
                df['Amount'] = 0.0
            
            logger.info(f"成功获取期货数据 {futures_code}, 数据点数: {len(df)}")
            return df
            
        except Exception as e:
            error_msg = f"获取期货数据失败 {futures_code}: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            # 使用空的DataFrame并添加错误信息，而不是抛出异常
            df = pd.DataFrame()
            df.error = error_msg  # 添加错误属性
            return df
    
    def _determine_exchange(self, futures_code: str) -> str:
        """
        根据期货代码判断交易所
        
        Args:
            futures_code: 期货代码
            
        Returns:
            交易所代码: SHFE(上期所), DCE(大商所), CZCE(郑商所), CFFEX(中金所)
        """
        # 移除可能的主力合约后缀
        if futures_code.endswith('88') or futures_code.endswith('99'):
            code = futures_code[:-2]
        else:
            code = futures_code
        
        # 提取代码前缀（通常是字母部分）
        prefix = ''.join([c for c in code if c.isalpha()]).upper()
        
        # 根据前缀判断交易所
        if prefix in ['IF', 'IC', 'IH', 'IM', 'TS', 'TF', 'T']:
            return "CFFEX"  # 中金所
        elif prefix in ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SS', 'BU', 'RU', 'FU', 'SP']:
            return "SHFE"   # 上期所
        elif prefix in ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD', 'RR', 'L', 'V', 'PP', 'J', 'JM', 'I', 'EG', 'EB']:
            return "DCE"    # 大商所
        elif prefix in ['SR', 'CF', 'CY', 'ZC', 'FG', 'TA', 'MA', 'RM', 'OI', 'WH', 'PM', 'RI', 'SF', 'SM', 'AP', 'CJ', 'UR']:
            return "CZCE"   # 郑商所
        else:
            logger.warning(f"无法确定期货代码 {futures_code} 的交易所，默认使用通用API")
            return "UNKNOWN"
    
    async def get_multiple_futures_data(self, futures_codes: List[str], 
                                      start_date: Optional[str] = None, 
                                      end_date: Optional[str] = None,
                                      max_concurrency: int = 5) -> Dict[str, pd.DataFrame]:
        """
        异步批量获取多个期货数据
        
        Args:
            futures_codes: 期货代码列表
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            max_concurrency: 最大并发数，默认为5
            
        Returns:
            字典，键为期货代码，值为对应的DataFrame
        """
        # 使用信号量控制并发数
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def get_with_semaphore(code):
            async with semaphore:
                try:
                    return code, await self.get_futures_data(code, start_date, end_date)
                except Exception as e:
                    logger.error(f"获取期货 {code} 数据时出错: {str(e)}")
                    return code, None
        
        # 创建异步任务
        tasks = [get_with_semaphore(code) for code in futures_codes]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 构建结果字典，过滤掉失败的请求
        return {code: df for code, df in results if df is not None}
    
    async def get_basis_data(self, futures_code: str, spot_code: str, 
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取期货与现货的基差数据
        
        Args:
            futures_code: 期货代码
            spot_code: 现货代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            包含基差数据的DataFrame
        """
        try:
            logger.info(f"获取基差数据: 期货={futures_code}, 现货={spot_code}")
            
            # 获取期货数据
            futures_df = await self.get_futures_data(futures_code, start_date, end_date)
            
            # 检查期货数据是否有错误
            if hasattr(futures_df, 'error'):
                error_msg = f"获取期货数据失败: {futures_df.error}"
                logger.error(error_msg)
                df = pd.DataFrame()
                df.error = error_msg
                return df
            
            # 获取现货数据
            # 这里假设现货代码是A股代码，实际使用时可能需要根据不同的现货类型调用不同的API
            import akshare as ak
            
            # 使用线程池执行同步的akshare调用
            spot_df = await asyncio.to_thread(
                self._get_spot_data_sync, 
                spot_code, 
                start_date, 
                end_date
            )
            
            # 检查现货数据是否有错误
            if hasattr(spot_df, 'error'):
                error_msg = f"获取现货数据失败: {spot_df.error}"
                logger.error(error_msg)
                df = pd.DataFrame()
                df.error = error_msg
                return df
            
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
            merged_df['Basis'] = merged_df['Close_futures'] - merged_df['Close_spot']
            
            # 计算基差率
            merged_df['BasisRatio'] = (merged_df['Basis'] / merged_df['Close_spot']) * 100
            
            logger.info(f"成功获取基差数据: 期货={futures_code}, 现货={spot_code}, 数据点数: {len(merged_df)}")
            return merged_df
            
        except Exception as e:
            error_msg = f"获取基差数据失败: 期货={futures_code}, 现货={spot_code}: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            df = pd.DataFrame()
            df.error = error_msg
            return df
    
    def _get_spot_data_sync(self, spot_code: str, 
                          start_date: Optional[str] = None, 
                          end_date: Optional[str] = None) -> pd.DataFrame:
        """
        同步获取现货数据的实现
        将被异步方法调用
        
        Args:
            spot_code: 现货代码
            start_date: 开始日期，格式YYYYMMDD
            end_date: 结束日期，格式YYYYMMDD
            
        Returns:
            包含现货数据的DataFrame
        """
        import akshare as ak
        
        try:
            logger.debug(f"获取现货数据: {spot_code}")
            
            # 这里假设现货代码是A股代码，实际使用时可能需要根据不同的现货类型调用不同的API
            df = ak.stock_zh_a_hist(
                symbol=spot_code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            # 标准化列名
            df.columns = ['Date', 'Code', 'Open', 'Close', 'High', 'Low', 'Volume', 'Amount', 'Amplitude', 'Change_pct', 'Change', 'Turnover']
            
            # 确保日期列是日期类型
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            # 确保按日期升序排序
            df.sort_index(inplace=True)
            
            logger.info(f"成功获取现货数据 {spot_code}, 数据点数: {len(df)}")
            return df
            
        except Exception as e:
            error_msg = f"获取现货数据失败 {spot_code}: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            df = pd.DataFrame()
            df.error = error_msg
            return df