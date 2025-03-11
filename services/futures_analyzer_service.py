import json
from datetime import datetime
from typing import List, Dict, Any, Optional, AsyncGenerator
from utils.logger import get_logger
from services.futures_data_provider import FuturesDataProvider
from services.futures_technical_indicator import FuturesTechnicalIndicator
from services.futures_scorer import FuturesScorer
from services.ai_analyzer import AIAnalyzer

# 获取日志器
logger = get_logger()

class FuturesAnalyzerService:
    """
    期货分析服务
    作为门面类协调数据提供、指标计算、评分和AI分析等组件
    """
    
    def __init__(self, custom_api_url=None, custom_api_key=None, custom_api_model=None, custom_api_timeout=None):
        """
        初始化期货分析服务
        
        Args:
            custom_api_url: 自定义API URL
            custom_api_key: 自定义API密钥
            custom_api_model: 自定义API模型
            custom_api_timeout: 自定义API超时时间
        """
        # 初始化各个组件
        self.data_provider = FuturesDataProvider()
        self.indicator = FuturesTechnicalIndicator()
        self.scorer = FuturesScorer()
        self.ai_analyzer = AIAnalyzer(
            custom_api_url=custom_api_url,
            custom_api_key=custom_api_key,
            custom_api_model=custom_api_model,
            custom_api_timeout=custom_api_timeout
        )
        
        logger.info("初始化FuturesAnalyzerService完成")
    
    async def analyze_futures(self, futures_code: str, stream: bool = False) -> AsyncGenerator[str, None]:
        """
        分析单个期货
        
        Args:
            futures_code: 期货代码
            stream: 是否使用流式响应
            
        Returns:
            异步生成器，生成分析结果的JSON字符串
        """
        try:
            logger.info(f"开始分析期货: {futures_code}")
            
            # 获取期货数据
            df = await self.data_provider.get_futures_data(futures_code)
            
            # 检查是否有错误
            if hasattr(df, 'error'):
                error_msg = df.error
                logger.error(f"获取期货数据时出错: {error_msg}")
                yield json.dumps({
                    "futures_code": futures_code,
                    "error": error_msg,
                    "status": "error"
                })
                return
            
            # 检查数据是否为空
            if df.empty:
                error_msg = f"获取到的期货 {futures_code} 数据为空"
                logger.error(error_msg)
                yield json.dumps({
                    "futures_code": futures_code,
                    "error": error_msg,
                    "status": "error"
                })
                return
            
            # 计算技术指标
            df_with_indicators = self.indicator.calculate_futures_indicators(df)
            
            # 计算评分
            score = self.scorer.calculate_score(df_with_indicators)
            recommendation = self.scorer.get_recommendation(score)
            
            # 获取最新数据
            latest_data = df_with_indicators.iloc[-1]
            previous_data = df_with_indicators.iloc[-2] if len(df_with_indicators) > 1 else latest_data
            
            # 价格变动绝对值
            price_change_value = latest_data['Close'] - previous_data['Close']
            
            # 计算涨跌幅
            change_percent = (price_change_value / previous_data['Close']) * 100 if previous_data['Close'] != 0 else 0
            
            # 确定MA趋势
            ma_short = latest_data.get('MA5', 0)
            ma_medium = latest_data.get('MA20', 0)
            ma_long = latest_data.get('MA60', 0)
            
            if ma_short > ma_medium > ma_long:
                ma_trend = "UP"
            elif ma_short < ma_medium < ma_long:
                ma_trend = "DOWN"
            else:
                ma_trend = "FLAT"
                
            # 确定MACD信号
            macd = latest_data.get('MACD', 0)
            signal = latest_data.get('Signal', 0)
            
            if macd > signal:
                macd_signal = "BUY"
            elif macd < signal:
                macd_signal = "SELL"
            else:
                macd_signal = "HOLD"
                
            # 确定成交量状态
            volume = latest_data.get('Volume', 0)
            volume_ma = latest_data.get('Volume_MA', 0)
            
            if volume > volume_ma * 1.5:
                volume_status = "HIGH"
            elif volume < volume_ma * 0.5:
                volume_status = "LOW"
            else:
                volume_status = "NORMAL"
            
            # 确定持仓量状态
            open_interest = latest_data.get('OpenInterest', 0)
            open_interest_ma = latest_data.get('OI_MA', 0)
            
            if open_interest > open_interest_ma * 1.2:
                open_interest_status = "HIGH"
            elif open_interest < open_interest_ma * 0.8:
                open_interest_status = "LOW"
            else:
                open_interest_status = "NORMAL"
                
            # 当前分析日期
            analysis_date = datetime.now().strftime('%Y-%m-%d')
            
            # 生成基本分析结果
            basic_result = {
                "futures_code": futures_code,
                "analysis_date": analysis_date,
                "score": score,
                "price": latest_data['Close'],
                "price_change_value": price_change_value,  # 价格变动绝对值
                "change_percent": change_percent,  # 涨跌幅百分比
                "ma_trend": ma_trend,
                "rsi": latest_data.get('RSI', 0),
                "macd_signal": macd_signal,
                "volume_status": volume_status,
                "open_interest": open_interest,
                "open_interest_status": open_interest_status,
                "volatility": latest_data.get('VolatilityStd', 0),
                "recommendation": recommendation,
                "ai_analysis": ""
            }
            
            # 输出基本分析结果
            logger.info(f"基本分析结果: {json.dumps(basic_result)}")
            yield json.dumps(basic_result)
            
            # 使用AI进行深入分析
            async for analysis_chunk in self.ai_analyzer.get_futures_analysis(df_with_indicators, futures_code, stream):
                yield analysis_chunk
                
            logger.info(f"完成期货分析: {futures_code}")
            
        except Exception as e:
            error_msg = f"分析期货 {futures_code} 时出错: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            yield json.dumps({"error": error_msg})
    
    async def scan_futures(self, futures_codes: List[str], min_score: int = 0, stream: bool = False) -> AsyncGenerator[str, None]:
        """
        批量扫描期货
        
        Args:
            futures_codes: 期货代码列表
            min_score: 最低评分阈值
            stream: 是否使用流式响应
            
        Returns:
            异步生成器，生成扫描结果的JSON字符串
        """
        try:
            logger.info(f"开始批量扫描 {len(futures_codes)} 个期货")
            
            # 输出初始状态 - 发送批量分析初始化消息
            yield json.dumps({
                "stream_type": "batch",
                "futures_codes": futures_codes,
                "min_score": min_score
            })
            
            # 批量获取期货数据
            futures_data_dict = await self.data_provider.get_multiple_futures_data(futures_codes)
            
            # 计算技术指标
            futures_with_indicators = {}
            for code, df in futures_data_dict.items():
                try:
                    futures_with_indicators[code] = self.indicator.calculate_futures_indicators(df)
                except Exception as e:
                    logger.error(f"计算 {code} 技术指标时出错: {str(e)}")
                    # 发送错误状态
                    yield json.dumps({
                        "futures_code": code,
                        "error": f"计算技术指标时出错: {str(e)}",
                        "status": "error"
                    })
            
            # 评分期货
            results = self.scorer.batch_score_futures(futures_with_indicators)
            
            # 过滤低于最低评分的期货
            filtered_results = [r for r in results if r[1] >= min_score]
            
            # 为每个期货发送基本评分和推荐信息
            for code, score, rec in results:
                df = futures_with_indicators.get(code)
                if df is not None and len(df) > 0:
                    # 获取最新数据
                    latest_data = df.iloc[-1]
                    previous_data = df.iloc[-2] if len(df) > 1 else latest_data
                    
                    # 价格变动绝对值
                    price_change_value = latest_data['Close'] - previous_data['Close']
                    
                    # 计算涨跌幅
                    change_percent = (price_change_value / previous_data['Close']) * 100 if previous_data['Close'] != 0 else 0
                    
                    # 发送期货基本信息和评分
                    yield json.dumps({
                        "futures_code": code,
                        "score": score,
                        "recommendation": rec,
                        "price": float(latest_data.get('Close', 0)),
                        "price_change_value": float(price_change_value),  # 价格变动绝对值
                        "change_percent": float(change_percent),  # 涨跌幅百分比
                        "rsi": float(latest_data.get('RSI', 0)) if 'RSI' in latest_data else None,
                        "ma_trend": "UP" if latest_data.get('MA5', 0) > latest_data.get('MA20', 0) else "DOWN",
                        "macd_signal": "BUY" if latest_data.get('MACD', 0) > latest_data.get('Signal', 0) else "SELL",
                        "volume_status": "HIGH" if latest_data.get('Volume', 0) > latest_data.get('Volume_MA', 0) * 1.5 else ("LOW" if latest_data.get('Volume', 0) < latest_data.get('Volume_MA', 0) * 0.5 else "NORMAL"),
                        "open_interest": float(latest_data.get('OpenInterest', 0)) if 'OpenInterest' in latest_data else None,
                        "volatility": float(latest_data.get('VolatilityStd', 0)) if 'VolatilityStd' in latest_data else None,
                        "status": "completed" if score < min_score else "waiting"
                    })
            
            # 如果需要进一步分析，对评分较高的期货进行AI分析
            if stream and filtered_results:
                # 只分析前5个评分最高的期货，避免分析过多导致前端卡顿
                top_futures = filtered_results[:5]
                
                for futures_code, score, _ in top_futures:
                    df = futures_with_indicators.get(futures_code)
                    if df is not None:
                        # 输出正在分析的期货信息
                        yield json.dumps({
                            "futures_code": futures_code,
                            "status": "analyzing"
                        })
                        
                        # AI分析
                        async for analysis_chunk in self.ai_analyzer.get_futures_analysis(df, futures_code, stream):
                            yield analysis_chunk
            
            # 输出扫描完成信息
            yield json.dumps({
                "scan_completed": True,
                "total_scanned": len(results),
                "total_matched": len(filtered_results)
            })
            
            logger.info(f"完成批量扫描 {len(futures_codes)} 个期货, 符合条件: {len(filtered_results)}")
            
        except Exception as e:
            error_msg = f"批量扫描期货时出错: {str(e)}"
            logger.error(error_msg)
            logger.exception(e)
            yield json.dumps({"error": error_msg})