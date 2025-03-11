import asyncio
import pandas as pd
from typing import List, Dict, Any, Optional
from utils.logger import get_logger

# 获取日志器
logger = get_logger()

class FuturesServiceAsync:
    """
    期货服务
    提供期货数据的搜索和获取功能
    """
    
    def __init__(self):
        """初始化期货服务"""
        logger.debug("初始化FuturesServiceAsync")
        
        # 可选：添加缓存以减少频繁请求
        self._cache = None
        self._cache_timestamp = None
    
    async def search_futures(self, keyword: str) -> List[Dict[str, Any]]:
        """
        异步搜索期货代码
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配的期货列表
        """
        try:
            logger.info(f"异步搜索期货: {keyword}")
            
            # 使用线程池执行同步的akshare调用
            df = await asyncio.to_thread(self._get_futures_list)
            
            # 模糊匹配搜索
            mask = df['name'].str.contains(keyword, case=False, na=False) | df['symbol'].str.contains(keyword, case=False, na=False)
            results = df[mask]
            
            # 格式化返回结果并处理 NaN 值
            formatted_results = []
            for _, row in results.iterrows():
                formatted_results.append({
                    'name': row['name'] if pd.notna(row['name']) else '',
                    'symbol': str(row['symbol']) if pd.notna(row['symbol']) else '',
                    'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                    'exchange': str(row['exchange']) if pd.notna(row['exchange']) else '',
                    'type': str(row['type']) if pd.notna(row['type']) else ''
                })
                # 限制只返回前10个结果
                if len(formatted_results) >= 10:
                    break
            
            logger.info(f"期货搜索完成，找到 {len(formatted_results)} 个匹配项（限制显示前10个）")
            return formatted_results
            
        except Exception as e:
            error_msg = f"搜索期货代码失败: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            raise Exception(error_msg)
    
    def _get_futures_list(self) -> pd.DataFrame:
        """
        获取期货列表（同步方法，将被异步方法调用）
        
        Returns:
            包含期货列表的DataFrame
        """
        import akshare as ak
        
        try:
            # 获取期货合约信息
            # 分别获取各交易所的期货合约
            dfs = []
            
            # 上海期货交易所
            try:
                shfe_df = ak.futures_zh_spot("shfe")
                shfe_df['exchange'] = '上期所'
                shfe_df['type'] = '商品期货'
                dfs.append(shfe_df)
            except Exception as e:
                logger.warning(f"获取上期所期货列表失败: {str(e)}")
            
            # 大连商品交易所
            try:
                dce_df = ak.futures_zh_spot("dce")
                dce_df['exchange'] = '大商所'
                dce_df['type'] = '商品期货'
                dfs.append(dce_df)
            except Exception as e:
                logger.warning(f"获取大商所期货列表失败: {str(e)}")
            
            # 郑州商品交易所
            try:
                czce_df = ak.futures_zh_spot("czce")
                czce_df['exchange'] = '郑商所'
                czce_df['type'] = '商品期货'
                dfs.append(czce_df)
            except Exception as e:
                logger.warning(f"获取郑商所期货列表失败: {str(e)}")
            
            # 中国金融期货交易所
            try:
                cffex_df = ak.futures_zh_spot("cffex")
                cffex_df['exchange'] = '中金所'
                cffex_df['type'] = '金融期货'
                dfs.append(cffex_df)
            except Exception as e:
                logger.warning(f"获取中金所期货列表失败: {str(e)}")
            
            # 合并所有交易所的数据
            if not dfs:
                raise Exception("未能获取任何交易所的期货列表")
                
            df = pd.concat(dfs, ignore_index=True)
            
            # 转换列名
            df = df.rename(columns={
                "代码": "symbol",
                "名称": "name",
                "最新价": "price",
                "涨跌额": "price_change",
                "涨跌幅": "price_change_percent",
                "成交量": "volume",
                "成交额": "turnover",
                "持仓量": "open_interest",
                "开盘价": "open",
                "最高价": "high",
                "最低价": "low",
                "昨收价": "pre_close",
                "昨结算": "pre_settlement",
                "今结算": "settlement"
            })
            
            return df
            
        except Exception as e:
            logger.error(f"获取期货列表失败: {str(e)}")
            logger.exception(e)
            raise Exception(f"获取期货列表失败: {str(e)}")
            
    async def get_futures_detail(self, symbol: str) -> Dict[str, Any]:
        """
        异步获取单个期货详细信息
        
        Args:
            symbol: 期货代码
            
        Returns:
            期货详细信息
        """
        try:
            logger.info(f"获取期货详情: {symbol}")
            
            # 使用线程池执行同步的akshare调用
            df = await asyncio.to_thread(self._get_futures_list)
            
            # 精确匹配期货代码
            result = df[df['symbol'] == symbol]
            
            if len(result) == 0:
                raise Exception(f"未找到期货代码: {symbol}")
            
            # 获取第一行数据
            row = result.iloc[0]
            
            # 格式化为字典
            futures_detail = {
                'name': row['name'] if pd.notna(row['name']) else '',
                'symbol': str(row['symbol']) if pd.notna(row['symbol']) else '',
                'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                'price_change': float(row['price_change']) if pd.notna(row['price_change']) else 0.0,
                'price_change_percent': float(row['price_change_percent'].strip('%'))/100 if pd.notna(row['price_change_percent']) else 0.0,
                'open': float(row['open']) if pd.notna(row['open']) else 0.0,
                'high': float(row['high']) if pd.notna(row['high']) else 0.0,
                'low': float(row['low']) if pd.notna(row['low']) else 0.0,
                'pre_close': float(row['pre_close']) if pd.notna(row['pre_close']) else 0.0,
                'volume': float(row['volume']) if pd.notna(row['volume']) else 0.0,
                'turnover': float(row['turnover']) if pd.notna(row['turnover']) else 0.0,
                'open_interest': float(row['open_interest']) if pd.notna(row['open_interest']) else 0.0,
                'exchange': str(row['exchange']) if pd.notna(row['exchange']) else '',
                'type': str(row['type']) if pd.notna(row['type']) else ''
            }
            
            # 如果有结算价，也添加
            if 'settlement' in row and pd.notna(row['settlement']):
                futures_detail['settlement'] = float(row['settlement'])
            
            logger.info(f"获取期货详情成功: {symbol}")
            return futures_detail
            
        except Exception as e:
            error_msg = f"获取期货详情失败: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            raise Exception(error_msg)
    
    async def get_main_contract_list(self) -> List[Dict[str, Any]]:
        """
        获取主力合约列表
        
        Returns:
            主力合约列表
        """
        try:
            logger.info("获取主力合约列表")
            
            # 使用线程池执行同步的akshare调用
            df = await asyncio.to_thread(self._get_main_contract_list)
            
            # 格式化返回结果
            formatted_results = []
            for _, row in df.iterrows():
                formatted_results.append({
                    'name': row['name'] if pd.notna(row['name']) else '',
                    'symbol': str(row['symbol']) if pd.notna(row['symbol']) else '',
                    'price': float(row['price']) if pd.notna(row['price']) else 0.0,
                    'exchange': str(row['exchange']) if pd.notna(row['exchange']) else '',
                    'type': str(row['type']) if pd.notna(row['type']) else ''
                })
            
            logger.info(f"获取主力合约列表成功，共 {len(formatted_results)} 个合约")
            return formatted_results
            
        except Exception as e:
            error_msg = f"获取主力合约列表失败: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            raise Exception(error_msg)
    
    def _get_main_contract_list(self) -> pd.DataFrame:
        """
        获取主力合约列表（同步方法，将被异步方法调用）
        
        Returns:
            包含主力合约列表的DataFrame
        """
        import akshare as ak
        
        try:
            # 获取主力合约信息
            df = ak.futures_main_sina()
            
            # 添加交易所和类型信息
            df['exchange'] = ''
            df['type'] = ''
            
            # 根据合约代码前缀判断交易所和类型
            for idx, row in df.iterrows():
                symbol = str(row['symbol'])
                prefix = symbol[:2]  # 取前两个字符作为前缀
                
                # 根据前缀判断交易所和类型
                if prefix in ['IF', 'IC', 'IH', 'IM', 'TS', 'TF', 'T']:
                    df.at[idx, 'exchange'] = '中金所'
                    df.at[idx, 'type'] = '金融期货'
                elif prefix in ['cu', 'al', 'zn', 'pb', 'ni', 'sn', 'au', 'ag', 'rb', 'wr', 'hc', 'ss', 'bu', 'ru', 'fu', 'sp']:
                    df.at[idx, 'exchange'] = '上期所'
                    df.at[idx, 'type'] = '商品期货'
                elif prefix in ['c', 'cs', 'a', 'b', 'm', 'y', 'p', 'fb', 'bb', 'jd', 'rr', 'l', 'v', 'pp', 'j', 'jm', 'i', 'eg', 'eb']:
                    df.at[idx, 'exchange'] = '大商所'
                    df.at[idx, 'type'] = '商品期货'
                elif prefix in ['SR', 'CF', 'CY', 'ZC', 'FG', 'TA', 'MA', 'RM', 'OI', 'WH', 'PM', 'RI', 'SF', 'SM', 'AP', 'CJ', 'UR']:
                    df.at[idx, 'exchange'] = '郑商所'
                    df.at[idx, 'type'] = '商品期货'
                else:
                    df.at[idx, 'exchange'] = '未知'
                    df.at[idx, 'type'] = '未知'
            
            return df
            
        except Exception as e:
            logger.error(f"获取主力合约列表失败: {str(e)}")
            logger.exception(e)
            raise Exception(f"获取主力合约列表失败: {str(e)}")