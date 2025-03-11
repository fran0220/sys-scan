<template>
  <div class="app-container mobile-bottom-extend">
    <!-- 公告横幅 -->
    <AnnouncementBanner
      v-if="announcement && showAnnouncementBanner"
      :content="announcement"
      :auto-close-time="5"
      @close="handleAnnouncementClose"
    />
    
    <n-layout class="main-layout">
      <n-layout-content class="main-content mobile-content-container">
        
        <!-- 导航栏 -->
        <NavigationBar />
        
        <!-- 市场时间显示 -->
        <MarketTimeDisplay :is-mobile="isMobile" />
        
        <!-- API配置面板 -->
        <ApiConfigPanel
          :default-api-url="defaultApiUrl"
          :default-api-model="defaultApiModel"
          :default-api-timeout="defaultApiTimeout"
          @update:api-config="updateApiConfig"
        />
        
        <!-- 主要内容 -->
        <n-card class="analysis-container mobile-card mobile-card-spacing mobile-shadow">
          <n-tabs type="line" animated>
            <n-tab-pane name="futures" tab="期货分析">
              <n-grid cols="1 xl:24" :x-gap="16" :y-gap="16" responsive="screen">
                <!-- 左侧配置区域 -->
                <n-grid-item span="1 xl:8">
                  <div class="config-section">
                    <n-form-item label="期货搜索">
                      <FuturesSearch @select="addSelectedFutures" />
                    </n-form-item>
                    
                    <n-form-item label="输入代码">
                      <n-input
                        v-model:value="futuresCodes"
                        type="textarea"
                        placeholder="输入期货代码，多个代码用逗号、空格或换行分隔"
                        :autosize="{ minRows: 3, maxRows: 6 }"
                      />
                    </n-form-item>
                    
                    <div class="action-buttons">
                      <n-button
                        type="primary"
                        :loading="isAnalyzing"
                        :disabled="!futuresCodes.trim()"
                        @click="analyzeFutures"
                      >
                        {{ isAnalyzing ? '分析中...' : '开始分析' }}
                      </n-button>
                      
                      <n-button
                        :disabled="analyzedFutures.length === 0"
                        @click="copyAnalysisResults"
                      >
                        复制结果
                      </n-button>
                    </div>
                  </div>
                </n-grid-item>
                
                <!-- 右侧结果区域 -->
                <n-grid-item span="1 xl:16">
                  <div class="results-section">
                    <div class="results-header">
                      <n-space align="center" justify="space-between">
                        <n-text>分析结果 ({{ analyzedFutures.length }})</n-text>
                        <n-space>
                          <n-select 
                            v-model:value="displayMode" 
                            size="small" 
                            style="width: 120px"
                            :options="[
                              { label: '卡片视图', value: 'card' },
                              { label: '表格视图', value: 'table' }
                            ]"
                          />
                          <n-button 
                            size="small" 
                            :disabled="analyzedFutures.length === 0"
                            @click="copyAnalysisResults"
                          >
                            复制结果
                          </n-button>
                          <n-dropdown 
                            trigger="click" 
                            :disabled="analyzedFutures.length === 0"
                            :options="exportOptions"
                            @select="handleExportSelect"
                          >
                            <n-button size="small" :disabled="analyzedFutures.length === 0">
                              导出
                              <template #icon>
                                <n-icon>
                                  <DownloadIcon />
                                </n-icon>
                              </template>
                            </n-button>
                          </n-dropdown>
                        </n-space>
                      </n-space>
                    </div>
                    
                    <template v-if="analyzedFutures.length === 0 && !isAnalyzing">
                      <n-empty description="尚未分析期货" size="large">
                        <template #icon>
                          <n-icon :component="DocumentTextIcon" />
                        </template>
                      </n-empty>
                    </template>
                    
                    <template v-else-if="displayMode === 'card'">
                      <n-grid cols="1" :x-gap="8" :y-gap="8" responsive="screen">
                        <n-grid-item v-for="futures in analyzedFutures" :key="futures.code">
                          <FuturesCard :futures="futures" />
                        </n-grid-item>
                      </n-grid>
                    </template>
                    
                    <template v-else>
                      <div class="table-container">
                        <n-data-table
                          :columns="futuresTableColumns"
                          :data="analyzedFutures"
                          :pagination="{ pageSize: 10 }"
                          :row-key="(row: FuturesInfo) => row.code"
                          :bordered="false"
                          :single-line="false"
                          striped
                          :scroll-x="1200"
                        />
                      </div>
                    </template>
                  </div>
                </n-grid-item>
              </n-grid>
            </n-tab-pane>
            
            <n-tab-pane name="main-contracts" tab="主力合约">
              <div class="main-contracts-section">
                <div class="main-contracts-header">
                  <n-space align="center" justify="space-between">
                    <n-text>主力合约列表</n-text>
                    <n-button 
                      size="small" 
                      :loading="isLoadingMainContracts"
                      @click="loadMainContracts"
                    >
                      刷新
                    </n-button>
                  </n-space>
                </div>
                
                <template v-if="isLoadingMainContracts">
                  <div class="loading-container">
                    <n-spin size="medium" />
                    <span class="loading-text">加载中...</span>
                  </div>
                </template>
                
                <template v-else-if="mainContracts.length === 0">
                  <n-empty description="暂无主力合约数据" size="large">
                    <template #icon>
                      <n-icon :component="DocumentTextIcon" />
                    </template>
                  </n-empty>
                </template>
                
                <template v-else>
                  <div class="table-container">
                    <n-data-table
                      :columns="mainContractsColumns"
                      :data="mainContracts"
                      :pagination="{ pageSize: 10 }"
                      :row-key="(row: any) => row.symbol"
                      :bordered="false"
                      :single-line="false"
                      striped
                      :scroll-x="1200"
                    />
                  </div>
                </template>
              </div>
            </n-tab-pane>
          </n-tabs>
        </n-card>

      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue';
import {
  NCard,
  NSpace,
  NInput,
  NButton,
  NGrid,
  NGridItem,
  NTabs,
  NTabPane,
  NDataTable,
  NTag,
  NInputGroup,
  NSpin,
  useMessage,
  NModal,
  NForm,
  NFormItem,
  NSelect,
  NSwitch,
  NCheckbox,
  NInputNumber,
  NCollapse,
  NCollapseItem,
  NPopover,
  NText,
  NIcon,
  NTooltip,
  NDivider,
  NEmpty
} from 'naive-ui';
import { apiService } from '../services/api';
import logger from '../utils/logger';
import { loadApiConfig } from '../utils';
import { useClipboard } from '@vueuse/core'
import { 
  DocumentTextOutline as DocumentTextIcon,
  DownloadOutline as DownloadIcon,
} from '@vicons/ionicons5';

import MarketTimeDisplay from './MarketTimeDisplay.vue';
import ApiConfigPanel from './ApiConfigPanel.vue';
import FuturesSearch from './FuturesSearch.vue';
import FuturesCard from './FuturesCard.vue';
import AnnouncementBanner from './AnnouncementBanner.vue';

import type { ApiConfig } from '@/types';

// 期货信息接口
interface FuturesInfo {
  code: string;
  name?: string;
  price?: number;
  price_change?: number;
  changePercent?: number;
  rsi?: number;
  ma_trend?: string;
  macd_signal?: string;
  volume_status?: string;
  open_interest?: number;
  open_interest_status?: string;
  volatility?: number;
  score?: number;
  recommendation?: string;
  analysis?: string;
  analysis_date?: string;
  analysisStatus: 'waiting' | 'analyzing' | 'completed' | 'error';
  error?: string;
}

// 使用Naive UI的组件API
const message = useMessage();
const { copy } = useClipboard();

// 从环境变量获取的默认配置
const defaultApiUrl = ref('');
const defaultApiModel = ref('');
const defaultApiTimeout = ref('60');
const announcement = ref('');
const showAnnouncementBanner = ref(true);

// 期货分析配置
const futuresCodes = ref('');
const isAnalyzing = ref(false);
const analyzedFutures = ref<FuturesInfo[]>([]);
const displayMode = ref<'card' | 'table'>('card');

// 主力合约
const mainContracts = ref<any[]>([]);
const isLoadingMainContracts = ref(false);

// API配置
const apiConfig = ref<ApiConfig>({
  apiUrl: '',
  apiKey: '',
  apiModel: '',
  apiTimeout: '60',
  saveApiConfig: false
});

// 移动端检测
const isMobile = computed(() => {
  return window.innerWidth <= 768;
});

// 监听窗口大小变化
function handleResize() {
  // 窗口大小变化时，isMobile计算属性会自动更新
}

// 显示系统公告
const showAnnouncement = (content: string) => {
  if (!content) return;
  
  // 使用AnnouncementBanner组件显示公告
  announcement.value = content;
  showAnnouncementBanner.value = true;
};

// 表格列定义 - 期货
const futuresTableColumns = ref([
  {
    title: '代码',
    key: 'code',
    width: 100,
    fixed: 'left'
  },
  {
    title: '状态',
    key: 'analysisStatus',
    width: 100,
    render(row: FuturesInfo) {
      const statusMap = {
        'waiting': '等待分析',
        'analyzing': '分析中',
        'completed': '已完成',
        'error': '出错'
      };
      return statusMap[row.analysisStatus] || row.analysisStatus;
    }
  },
  {
    title: '价格',
    key: 'price',
    width: 100,
    render(row: FuturesInfo) {
      return row.price !== undefined ? row.price.toFixed(2) : '--';
    }
  },
  {
    title: '涨跌额',
    key: 'price_change',
    width: 100,
    render(row: FuturesInfo) {
      if (row.price_change === undefined) return '--';
      const sign = row.price_change > 0 ? '+' : '';
      return `${sign}${row.price_change.toFixed(2)}`;
    }
  },
  {
    title: '涨跌幅',
    key: 'changePercent',
    width: 100,
    render(row: FuturesInfo) {
      if (row.changePercent === undefined) {
        return '--';
      }
      const sign = row.changePercent > 0 ? '+' : '';
      return `${sign}${row.changePercent.toFixed(2)}%`;
    }
  },
  {
    title: 'RSI',
    key: 'rsi',
    width: 80,
    render(row: FuturesInfo) {
      return row.rsi !== undefined ? row.rsi.toFixed(2) : '--';
    }
  },
  {
    title: '均线趋势',
    key: 'ma_trend',
    width: 100,
    render(row: FuturesInfo) {
      const trendMap: Record<string, string> = {
        'UP': '上升',
        'DOWN': '下降',
        'NEUTRAL': '平稳'
      };
      return row.ma_trend ? trendMap[row.ma_trend] || row.ma_trend : '--';
    }
  },
  {
    title: 'MACD信号',
    key: 'macd_signal',
    width: 100,
    render(row: FuturesInfo) {
      const signalMap: Record<string, string> = {
        'BUY': '买入',
        'SELL': '卖出',
        'HOLD': '持有',
        'NEUTRAL': '中性'
      };
      return row.macd_signal ? signalMap[row.macd_signal] || row.macd_signal : '--';
    }
  },
  {
    title: '持仓量',
    key: 'open_interest',
    width: 100,
    render(row: FuturesInfo) {
      return row.open_interest !== undefined ? row.open_interest.toLocaleString() : '--';
    }
  },
  {
    title: '波动率',
    key: 'volatility',
    width: 100,
    render(row: FuturesInfo) {
      return row.volatility !== undefined ? `${row.volatility.toFixed(2)}%` : '--';
    }
  },
  {
    title: '评分',
    key: 'score',
    width: 80,
    render(row: FuturesInfo) {
      return row.score !== undefined ? row.score : '--';
    }
  },
  {
    title: '推荐',
    key: 'recommendation',
    width: 100
  },
  {
    title: '分析日期',
    key: 'analysis_date',
    width: 120,
    render(row: FuturesInfo) {
      if (!row.analysis_date) return '--';
      try {
        const date = new Date(row.analysis_date);
        if (isNaN(date.getTime())) {
          return row.analysis_date;
        }
        return date.toISOString().split('T')[0];
      } catch (e) {
        return row.analysis_date;
      }
    }
  },
  {
    title: '分析结果',
    key: 'analysis',
    ellipsis: {
      tooltip: true
    },
    width: 300,
    className: 'analysis-cell'
  }
]);

// 表格列定义 - 主力合约
const mainContractsColumns = ref([
  {
    title: '代码',
    key: 'symbol',
    width: 100,
    fixed: 'left'
  },
  {
    title: '名称',
    key: 'name',
    width: 150
  },
  {
    title: '价格',
    key: 'price',
    width: 100,
    render(row: any) {
      return row.price !== undefined ? row.price.toFixed(2) : '--';
    }
  },
  {
    title: '交易所',
    key: 'exchange',
    width: 100
  },
  {
    title: '类型',
    key: 'type',
    width: 100
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    render(row: any) {
      return h(
        NButton,
        {
          size: 'small',
          onClick: () => addSelectedFutures(row.symbol)
        },
        { default: () => '添加到分析' }
      );
    }
  }
]);

// 导出选项
const exportOptions = [
  {
    label: '导出为CSV',
    key: 'csv'
  },
  {
    label: '导出为Excel',
    key: 'excel'
  },
  {
    label: '导出为PDF',
    key: 'pdf'
  }
];

// 更新API配置
function updateApiConfig(config: ApiConfig) {
  apiConfig.value = { ...config };
}

// 添加选择的期货
function addSelectedFutures(symbol: string) {
  // 确保symbol不包含序号或其他不需要的信息
  const cleanSymbol = symbol.trim().replace(/^\d+\.\s*/, '');
  
  if (futuresCodes.value) {
    futuresCodes.value += ', ' + cleanSymbol;
  } else {
    futuresCodes.value = cleanSymbol;
  }
}

// 处理流式响应数据
function processStreamData(data: string) {
  try {
    const jsonData = JSON.parse(data);
    
    // 处理初始化消息
    if (jsonData.stream_type) {
      logger.debug('收到流初始化消息:', jsonData);
      return;
    }
    
    // 处理期货分析更新
    if (jsonData.futures_code) {
      const futuresCode = jsonData.futures_code;
      const index = analyzedFutures.value.findIndex(f => f.code === futuresCode);
      
      if (index !== -1) {
        // 更新现有期货信息
        const updatedFutures = {
          ...analyzedFutures.value[index],
          name: jsonData.name || analyzedFutures.value[index].name,
          price: jsonData.price,
          changePercent: jsonData.change_percent,
          analysisStatus: jsonData.status,
          error: jsonData.error,
          score: jsonData.score,
          recommendation: jsonData.recommendation,
          price_change: jsonData.price_change,
          rsi: jsonData.rsi,
          ma_trend: jsonData.ma_trend,
          macd_signal: jsonData.macd_signal,
          volume_status: jsonData.volume_status,
          open_interest: jsonData.open_interest,
          open_interest_status: jsonData.open_interest_status,
          volatility: jsonData.volatility,
          analysis_date: jsonData.analysis_date,
          exchange: jsonData.exchange,
          type: jsonData.type
        };
        
        // 处理AI分析块
        if (jsonData.ai_analysis_chunk) {
          updatedFutures.analysis = (updatedFutures.analysis || '') + jsonData.ai_analysis_chunk;
        }
        
        // 更新分析结果
        analyzedFutures.value[index] = updatedFutures;
      } else {
        // 添加新的期货信息
        analyzedFutures.value.push({
          code: futuresCode,
          name: jsonData.name || '',
          price: jsonData.price,
          changePercent: jsonData.change_percent,
          analysisStatus: jsonData.status,
          error: jsonData.error,
          score: jsonData.score,
          recommendation: jsonData.recommendation,
          price_change: jsonData.price_change,
          rsi: jsonData.rsi,
          ma_trend: jsonData.ma_trend,
          macd_signal: jsonData.macd_signal,
          volume_status: jsonData.volume_status,
          open_interest: jsonData.open_interest,
          open_interest_status: jsonData.open_interest_status,
          volatility: jsonData.volatility,
          analysis_date: jsonData.analysis_date,
          exchange: jsonData.exchange,
          type: jsonData.type,
          analysis: jsonData.ai_analysis_chunk || ''
        });
      }
    }
  } catch (error) {
    logger.error('解析流数据时出错:', error);
    message.error(`解析数据时出错: ${error instanceof Error ? error.message : '未知错误'}`);
  }
}

// 分析期货
async function analyzeFutures() {
  if (!futuresCodes.value.trim()) {
    message.warning('请输入期货代码');
    return;
  }
  
  isAnalyzing.value = true;
  
  try {
    // 解析输入的期货代码
    const codes = futuresCodes.value
      .split(/[\s,，、;；]+/)
      .map(code => code.trim())
      .filter(code => code);
    
    // 去重
    const uniqueCodes = [...new Set(codes)];
    
    if (uniqueCodes.length === 0) {
      message.warning('请输入有效的期货代码');
      isAnalyzing.value = false;
      return;
    }
    
    logger.debug(`开始分析期货: ${uniqueCodes.join(', ')}`);
    
    // 初始化分析状态
    analyzedFutures.value = uniqueCodes.map(code => ({
      code,
      name: '',
      analysisStatus: 'waiting',
      analysis: ''
    }));
    
    // 准备API请求
    const request = {
      futures_codes: uniqueCodes,
      api_url: apiConfig.value.apiUrl,
      api_key: apiConfig.value.apiKey,
      api_model: apiConfig.value.apiModel,
      api_timeout: parseInt(apiConfig.value.apiTimeout)
    };
    
    // 发送分析请求
    const response = await apiService.analyzeFutures(request);
    
    if (!response.data) {
      throw new Error('分析请求失败，未收到响应数据');
    }
    
    // 处理流式响应
    const reader = response.data.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    
    while (true) {
      const { done, value } = await reader.read();
      
      if (done) {
        // 处理缓冲区中剩余的数据
        if (buffer.trim()) {
          processStreamData(buffer);
        }
        break;
      }
      
      // 解码并处理数据
      const text = decoder.decode(value, { stream: true });
      buffer += text;
      
      // 按行分割并处理
      const lines = buffer.split('\n');
      
      // 保留最后一行（可能不完整）
      buffer = lines.pop() || '';
      
      // 处理完整的行
      for (const line of lines) {
        if (line.trim()) {
          processStreamData(line);
        }
      }
    }
    
    logger.debug('期货分析完成');
    
  } catch (error) {
    logger.error('分析期货时出错:', error);
    message.error(`分析失败: ${error instanceof Error ? error.message : '未知错误'}`);
    
    // 更新所有等待中的期货状态为错误
    analyzedFutures.value = analyzedFutures.value.map(futures => {
      if (futures.analysisStatus === 'waiting') {
        return {
          ...futures,
          analysisStatus: 'error',
          error: '分析请求失败'
        };
      }
      return futures;
    });
    
  } finally {
    isAnalyzing.value = false;
  }
}

// 加载主力合约
async function loadMainContracts() {
  isLoadingMainContracts.value = true;
  
  try {
    logger.debug('开始加载主力合约列表');
    
    // 使用API服务获取主力合约
    mainContracts.value = await apiService.getMainContracts();
    
    if (mainContracts.value.length === 0) {
      message.warning('未找到主力合约');
    } else {
      message.success(`成功加载 ${mainContracts.value.length} 个主力合约`);
    }
  } catch (error) {
    message.error(`加载主力合约失败: ${error instanceof Error ? error.message : '未知错误'}`);
    logger.error('加载主力合约时出错:', error);
  } finally {
    isLoadingMainContracts.value = false;
  }
}

// 复制分析结果
async function copyAnalysisResults() {
  if (analyzedFutures.value.length === 0) {
    message.warning('没有可复制的分析结果');
    return;
  }
  
  try {
    // 格式化分析结果
    const formattedResults = analyzedFutures.value
      .filter((futures: FuturesInfo) => futures.analysisStatus === 'completed')
      .map((futures: FuturesInfo) => {
        let result = `【${futures.code} ${futures.name || ''}】\n`;
        
        // 添加分析日期
        if (futures.analysis_date) {
          try {
            const date = new Date(futures.analysis_date);
            if (!isNaN(date.getTime())) {
              result += `分析日期: ${date.toISOString().split('T')[0]}\n`;
            } else {
              result += `分析日期: ${futures.analysis_date}\n`;
            }
          } catch (e) {
            result += `分析日期: ${futures.analysis_date}\n`;
          }
        }
        
        // 添加评分和推荐信息
        if (futures.score !== undefined) {
          result += `评分: ${futures.score}\n`;
        }
        
        if (futures.recommendation) {
          result += `推荐: ${futures.recommendation}\n`;
        }
        
        // 添加技术指标信息
        if (futures.rsi !== undefined) {
          result += `RSI: ${futures.rsi.toFixed(2)}\n`;
        }
        
        if (futures.price_change !== undefined) {
          const sign = futures.price_change > 0 ? '+' : '';
          result += `涨跌额: ${sign}${futures.price_change.toFixed(2)}\n`;
        }
        
        if (futures.ma_trend) {
          const trendMap: Record<string, string> = {
            'UP': '上升',
            'DOWN': '下降',
            'NEUTRAL': '平稳'
          };
          const trend = trendMap[futures.ma_trend] || futures.ma_trend;
          result += `均线趋势: ${trend}\n`;
        }
        
        if (futures.macd_signal) {
          const signalMap: Record<string, string> = {
            'BUY': '买入',
            'SELL': '卖出',
            'HOLD': '持有',
            'NEUTRAL': '中性'
          };
          const signal = signalMap[futures.macd_signal] || futures.macd_signal;
          result += `MACD信号: ${signal}\n`;
        }
        
        if (futures.open_interest !== undefined) {
          result += `持仓量: ${futures.open_interest.toLocaleString()}\n`;
        }
        
        if (futures.volatility !== undefined) {
          result += `波动率: ${futures.volatility.toFixed(2)}%\n`;
        }
        
        // 添加分析结果
        result += `\n${futures.analysis || '无分析结果'}\n`;
        
        return result;
      })
      .join('\n');
    
    if (!formattedResults) {
      message.warning('没有已完成的分析结果可复制');
      return;
    }
    
    // 复制到剪贴板
    await copy(formattedResults);
    message.success('已复制分析结果到剪贴板');
  } catch (error) {
    message.error('复制失败，请手动复制');
    console.error('复制分析结果时出错:', error);
  }
}

// 处理导出选择
function handleExportSelect(key: string) {
  switch (key) {
    case 'csv':
      exportToCSV();
      break;
    case 'excel':
      message.info('Excel导出功能即将推出');
      break;
    case 'pdf':
      message.info('PDF导出功能即将推出');
      break;
  }
}

// 导出为CSV
function exportToCSV() {
  if (analyzedFutures.value.length === 0) {
    message.warning('没有可导出的分析结果');
    return;
  }
  
  try {
    // 创建CSV内容
    const headers = ['代码', '名称', '价格', '涨跌幅', 'RSI', '均线趋势', 'MACD信号', '成交量状态', '持仓量', '波动率', '评分', '推荐', '分析日期'];
    let csvContent = headers.join(',') + '\n';
    
    // 添加数据行
    analyzedFutures.value.forEach(futures => {
      const row = [
        `"${futures.code}"`,
        `"${futures.name || ''}"`,
        futures.price !== undefined ? futures.price.toFixed(2) : '',
        futures.changePercent !== undefined ? `${futures.changePercent > 0 ? '+' : ''}${futures.changePercent.toFixed(2)}%` : '',
        futures.rsi !== undefined ? futures.rsi.toFixed(2) : '',
        futures.ma_trend ? getChineseTrend(futures.ma_trend) : '',
        futures.macd_signal ? getChineseSignal(futures.macd_signal) : '',
        futures.volume_status ? getChineseVolumeStatus(futures.volume_status) : '',
        futures.open_interest !== undefined ? futures.open_interest.toLocaleString() : '',
        futures.volatility !== undefined ? `${futures.volatility.toFixed(2)}%` : '',
        futures.score !== undefined ? futures.score : '',
        `"${futures.recommendation || ''}"`,
        futures.analysis_date || ''
      ];
      
      csvContent += row.join(',') + '\n';
    });
    
    // 创建Blob对象
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    
    // 创建下载链接
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `期货分析结果_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    
    // 添加到文档并触发点击
    document.body.appendChild(link);
    link.click();
    
    // 清理
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    message.success('已导出CSV文件');
  } catch (error) {
    message.error('导出失败');
    console.error('导出CSV时出错:', error);
  }
}

// 辅助函数：获取中文趋势描述
function getChineseTrend(trend: string): string {
  const trendMap: Record<string, string> = {
    'UP': '上升',
    'DOWN': '下降',
    'NEUTRAL': '平稳'
  };
  return trendMap[trend] || trend;
}

// 辅助函数：获取中文信号描述
function getChineseSignal(signal: string): string {
  const signalMap: Record<string, string> = {
    'BUY': '买入',
    'SELL': '卖出',
    'HOLD': '持有',
    'NEUTRAL': '中性'
  };
  return signalMap[signal] || signal;
}

// 辅助函数：获取中文成交量状态描述
function getChineseVolumeStatus(status: string): string {
  const statusMap: Record<string, string> = {
    'HIGH': '放量',
    'LOW': '缩量',
    'NORMAL': '正常'
  };
  return statusMap[status] || status;
}

// 页面加载时获取默认配置和公告
onMounted(async () => {
  try {
    // 添加窗口大小变化监听
    window.addEventListener('resize', handleResize);
    
    // 从API获取配置信息
    const config = await apiService.getConfig();
    
    if (config.default_api_url) {
      defaultApiUrl.value = config.default_api_url;
    }
    
    if (config.default_api_model) {
      defaultApiModel.value = config.default_api_model;
    }
    
    if (config.default_api_timeout) {
      defaultApiTimeout.value = config.default_api_timeout;
    }
    
    if (config.announcement) {
      announcement.value = config.announcement;
      // 使用通知显示公告
      showAnnouncement(config.announcement);
    }
    
    // 初始化后恢复本地保存的配置
    const savedConfig = loadApiConfig();
    if (savedConfig && savedConfig.saveApiConfig) {
      apiConfig.value = {
        apiUrl: savedConfig.apiUrl || '',
        apiKey: savedConfig.apiKey || '',
        apiModel: savedConfig.apiModel || defaultApiModel.value,
        apiTimeout: savedConfig.apiTimeout || defaultApiTimeout.value,
        saveApiConfig: savedConfig.saveApiConfig
      };
    }
    
    // 加载主力合约
    await loadMainContracts();
  } catch (error) {
    console.error('获取默认配置时出错:', error);
  }
});

// 组件销毁前移除事件监听
onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize);
});

// 处理公告关闭事件
function handleAnnouncementClose() {
  showAnnouncementBanner.value = false;
}
</script>

<style scoped>
.app-container {
  min-height: 100vh;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
  padding-bottom: 20px; /* 增加底部内边距 */
  box-sizing: border-box;
}

.main-layout {
  background-color: #f6f6f6;
  width: 100%;
  max-width: 100vw;
  overflow-x: hidden;
  min-height: calc(100vh - 20px); /* 确保至少占满视口高度减去底部空间 */
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 1rem;
  width: 100%;
  box-sizing: border-box;
}

.analysis-container {
  margin-bottom: 1rem;
}

/* 修改卡片内容区域的内边距 */
.analysis-container :deep(.n-card__content) {
  padding: 16px;
}

.config-section {
  padding: 0.5rem;
}

.action-buttons {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.results-section, .main-contracts-section {
  padding: 0.5rem;
  min-height: 200px;
}

.results-header, .main-contracts-header {
  margin-bottom: 1rem;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  gap: 1rem;
}

.loading-text {
  color: #666;
}

.n-data-table .analysis-cell {
  max-width: 300px;
  white-space: normal;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-word;
}

/* 表格容器基础样式 */
.table-container {
  width: 100%;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch; /* 支持iOS的滚动惯性 */
  position: relative;
  border-radius: 0.5rem;
}

/* 表格横向滚动指示器 */
.table-container::after {
  content: '←→';
  position: absolute;
  bottom: 10px;
  right: 10px;
  color: rgba(32, 128, 240, 0.6);
  font-size: 14px;
  pointer-events: none;
  z-index: 2;
  animation: fadeInOut 2s infinite;
  display: none; /* 默认隐藏，只在移动端显示 */
}

/* 移动端适配的媒体查询 */
@media (max-width: 768px) {
  .main-content {
    padding: 0.5rem;
    max-width: 100%;
    width: 100%;
  }
  
  /* 显示滚动指示器 */
  .table-container::after {
    display: block;
  }
  
  /* 减少移动端卡片内容区域的内边距 */
  .analysis-container :deep(.n-card__content) {
    padding: 12px 8px;
  }
  
  /* 使用更精确的选择器确保覆盖 */
  :deep(.n-card) > :deep(.n-card__content),
  :deep(.n-card-header) {
    padding: 12px 8px !important;
  }
  
  /* 减少网格间距到最小 */
  :deep(.n-grid[cols="1 l\\:2"]) {
    gap: 4px !important;
  }
  
  .results-section, .main-contracts-section {
    padding: 0.25rem 0.125rem;
  }
  
  .results-header, .main-contracts-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  :deep(.n-space) {
    flex-wrap: wrap;
    width: 100%;
    justify-content: space-between;
  }
  
  :deep(.n-space .n-button) {
    margin-right: 0 !important;
  }
  
  .analysis-container {
    border-radius: 0.75rem;
    margin-bottom: 0.5rem;
  }
  
  /* 移动端表格样式优化 */
  .table-container {
    margin: 0 -4px; /* 抵消父容器的padding */
    padding: 0 4px;
  }

  /* 表格组件移动端优化 */
  :deep(.n-data-table-wrapper) {
    border-radius: 0.5rem;
  }

  :deep(.n-data-table-base-table-header, .n-data-table-base-table-body) {
    min-width: 100%;
  }

  :deep(.n-pagination) {
    flex-wrap: wrap;
    justify-content: center;
    margin-top: 8px;
  }
  
  /* 保留原有移动端优化样式 */
  :deep(.n-form-item) {
    margin-bottom: 0.75rem;
  }

  :deep(.n-grid) {
    width: 100% !important;
  }

  :deep(.n-grid-item) {
    width: 100% !important;
    max-width: 100% !important;
  }

  :deep(.n-grid[cols="1 m\\:24"]) {
    gap: 8px !important;
  }

  :deep(.n-grid[cols="1 l\\:2"]) {
    gap: 6px !important;
  }

  :deep(.n-grid-item) > * {
    margin-bottom: 8px;
  }

  :deep(.n-dropdown-menu) {
    max-width: 90vw;
  }
  
  .app-container {
    padding-bottom: 30px; /* 增加移动端底部内边距 */
  }
}

/* 小屏幕手机适配 */
@media (max-width: 480px) {
  .main-content {
    padding: 0.25rem;
  }
  
  /* 进一步减少小屏幕卡片内容区域的内边距 */
  .analysis-container :deep(.n-card__content) {
    padding: 6px 4px;
  }
  
  /* 使用更精确的选择器确保覆盖 */
  :deep(.n-card) > :deep(.n-card__content),
  :deep(.n-card-header) {
    padding: 6px 4px !important;
  }
  
  /* 减少网格间距到最小 */
  :deep(.n-grid[cols="1 l\\:2"]) {
    gap: 4px !important;
  }
  
  .results-section, .main-contracts-section {
    padding: 0.15rem 0.05rem;
  }
  
  .results-header, .main-contracts-header {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }
  
  :deep(.n-space) {
    flex-wrap: wrap;
    width: 100%;
    justify-content: space-between;
  }
  
  :deep(.n-space .n-button) {
    margin-right: 0 !important;
  }
  
  .analysis-container {
    border-radius: 0.625rem;
    margin-bottom: 0.5rem;
  }
  
  /* 小屏幕下进一步优化n-grid */
  :deep(.n-grid) {
    gap: 4px !important;
  }
  
  :deep(.n-grid-item) {
    padding: 0 !important;
  }
  
  /* 确保n-grid-item内容在小屏幕下有更紧凑的间距 */
  :deep(.n-grid-item) > * {
    margin-bottom: 4px;
  }
  
  /* 小屏幕表格样式调整 */
  .table-container {
    margin: 0 -2px;
    padding: 0 2px;
  }
  
  /* 小屏幕分页控件优化 */
  :deep(.n-pagination .n-pagination-item) {
    margin: 0 2px;
  }
  
  .app-container {
    padding-bottom: 40px; /* 增加小屏幕底部内边距 */
  }
}
</style>