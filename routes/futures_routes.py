from fastapi import APIRouter, Request, Response, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generator
from services.futures_analyzer_service import FuturesAnalyzerService
from services.futures_service_async import FuturesServiceAsync
from utils.logger import get_logger
from web_server import verify_token  # 导入验证令牌函数
import json

# 获取日志器
logger = get_logger()

# 创建路由器
router = APIRouter(prefix="/api/futures", tags=["futures"])

# 初始化异步服务
futures_service = FuturesServiceAsync()

# 定义请求和响应模型
class AnalyzeFuturesRequest(BaseModel):
    futures_codes: List[str]
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_model: Optional[str] = None
    api_timeout: Optional[str] = None

# 搜索期货代码
@router.get("/search")
async def search_futures(keyword: str = "", username: str = Depends(verify_token)):
    try:
        if not keyword:
            raise HTTPException(status_code=400, detail="请输入搜索关键词")
        
        # 直接使用异步服务的异步方法
        results = await futures_service.search_futures(keyword)
        return {"results": results}
        
    except Exception as e:
        logger.error(f"搜索期货代码时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取期货详情
@router.get("/detail/{symbol}")
async def get_futures_detail(symbol: str, username: str = Depends(verify_token)):
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="请提供期货代码")
        
        # 使用异步服务获取详情
        detail = await futures_service.get_futures_detail(symbol)
        return detail
        
    except Exception as e:
        logger.error(f"获取期货详情时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 获取主力合约列表
@router.get("/main_contracts")
async def get_main_contracts(username: str = Depends(verify_token)):
    try:
        # 使用异步服务获取主力合约列表
        contracts = await futures_service.get_main_contract_list()
        return {"contracts": contracts}
        
    except Exception as e:
        logger.error(f"获取主力合约列表时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# AI分析期货
@router.post("/analyze")
async def analyze_futures(request: AnalyzeFuturesRequest, username: str = Depends(verify_token)):
    try:
        logger.info("开始处理期货分析请求")
        futures_codes = request.futures_codes
        
        # 后端再次去重，确保安全
        original_count = len(futures_codes)
        futures_codes = list(dict.fromkeys(futures_codes))  # 保持原有顺序的去重方法
        if len(futures_codes) < original_count:
            logger.info(f"后端去重: 从{original_count}个代码中移除了{original_count - len(futures_codes)}个重复项")
        
        logger.debug(f"接收到期货分析请求: futures_codes={futures_codes}")
        
        # 获取自定义API配置
        custom_api_url = request.api_url
        custom_api_key = request.api_key
        custom_api_model = request.api_model
        custom_api_timeout = request.api_timeout
        
        logger.debug(f"自定义API配置: URL={custom_api_url}, 模型={custom_api_model}, API Key={'已提供' if custom_api_key else '未提供'}, Timeout={custom_api_timeout}")
        
        # 创建新的分析器实例，使用自定义配置
        custom_analyzer = FuturesAnalyzerService(
            custom_api_url=custom_api_url,
            custom_api_key=custom_api_key,
            custom_api_model=custom_api_model,
            custom_api_timeout=custom_api_timeout
        )
        
        if not futures_codes:
            logger.warning("未提供期货代码")
            raise HTTPException(status_code=400, detail="请输入代码")
        
        # 定义流式生成器
        async def generate_stream():
            if len(futures_codes) == 1:
                # 单个期货分析流式处理
                futures_code = futures_codes[0].strip()
                logger.info(f"开始单个期货流式分析: {futures_code}")
                
                futures_code_json = json.dumps(futures_code)
                init_message = f'{{"stream_type": "single", "futures_code": {futures_code_json}}}\n'
                yield init_message
                
                logger.debug(f"开始处理期货 {futures_code} 的流式响应")
                chunk_count = 0
                
                # 使用异步生成器
                async for chunk in custom_analyzer.analyze_futures(futures_code, stream=True):
                    chunk_count += 1
                    yield chunk + '\n'
                
                logger.info(f"期货 {futures_code} 流式分析完成，共发送 {chunk_count} 个块")
            else:
                # 批量分析流式处理
                logger.info(f"开始批量流式分析期货: {futures_codes}")
                
                futures_codes_json = json.dumps(futures_codes)
                init_message = f'{{"stream_type": "batch", "futures_codes": {futures_codes_json}}}\n'
                yield init_message
                
                logger.debug(f"开始处理批量期货的流式响应")
                chunk_count = 0
                
                # 使用异步生成器
                async for chunk in custom_analyzer.scan_futures(
                    [code.strip() for code in futures_codes], 
                    min_score=0, 
                    stream=True
                ):
                    chunk_count += 1
                    yield chunk + '\n'
                
                logger.info(f"批量流式分析期货完成，共发送 {chunk_count} 个块")
        
        logger.info("成功创建期货流式响应生成器")
        return StreamingResponse(generate_stream(), media_type='application/json')
            
    except Exception as e:
        error_msg = f"分析期货时出错: {str(e)}"
        logger.error(error_msg)
        logger.exception(e)
        raise HTTPException(status_code=500, detail=error_msg)