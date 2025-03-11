<template>
  <n-card class="futures-card" :bordered="false" size="small">
    <template #header>
      <div class="futures-header">
        <div class="futures-title">
          <span class="futures-code">{{ futures.code }}</span>
          <span class="futures-name" v-if="futures.name">{{ futures.name }}</span>
        </div>
        <div class="futures-status">
          <n-tag :type="getStatusType(futures.analysisStatus)" size="small">
            {{ getStatusText(futures.analysisStatus) }}
          </n-tag>
        </div>
      </div>
    </template>

    <!-- 错误状态显示 -->
    <template v-if="futures.analysisStatus === 'error'">
      <div class="error-container">
        <n-alert type="error" :title="'分析出错'" :closable="false">
          {{ futures.error || '未知错误' }}
        </n-alert>
      </div>
    </template>

    <!-- 等待分析状态 -->
    <template v-else-if="futures.analysisStatus === 'waiting'">
      <div class="waiting-container">
        <n-spin size="small" />
        <span class="waiting-text">等待分析...</span>
      </div>
    </template>

    <!-- 分析中状态 -->
    <template v-else-if="futures.analysisStatus === 'analyzing'">
      <div class="analyzing-container">
        <n-spin size="small" />
        <span class="analyzing-text">分析中...</span>
        <div class="analysis-preview" v-if="futures.analysis">
          <n-ellipsis :line-clamp="3" expand-trigger="click">
            {{ futures.analysis }}
          </n-ellipsis>
        </div>
      </div>
    </template>

    <!-- 分析完成状态 -->
    <template v-else>
      <n-descriptions :column="2" size="small" class="futures-info">
        <n-descriptions-item label="价格">
          {{ futures.price ? futures.price.toFixed(2) : '--' }}
        </n-descriptions-item>
        <n-descriptions-item label="涨跌幅">
          <span :class="getPriceChangeClass(futures.changePercent)">
            {{ formatPriceChange(futures.changePercent) }}
          </span>
        </n-descriptions-item>
        <n-descriptions-item label="RSI">
          {{ futures.rsi ? futures.rsi.toFixed(2) : '--' }}
        </n-descriptions-item>
        <n-descriptions-item label="均线趋势">
          <n-tag :type="getTrendTagType(futures.ma_trend)" size="small">
            {{ getTrendText(futures.ma_trend) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="MACD信号">
          <n-tag :type="getMacdTagType(futures.macd_signal)" size="small">
            {{ getMacdText(futures.macd_signal) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="成交量">
          <n-tag :type="getVolumeTagType(futures.volume_status)" size="small">
            {{ getVolumeText(futures.volume_status) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="持仓量" v-if="futures.open_interest !== undefined">
          {{ futures.open_interest.toLocaleString() }}
        </n-descriptions-item>
        <n-descriptions-item label="持仓状态" v-if="futures.open_interest_status">
          <n-tag :type="getOpenInterestTagType(futures.open_interest_status)" size="small">
            {{ getOpenInterestText(futures.open_interest_status) }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="波动率" v-if="futures.volatility !== undefined">
          {{ futures.volatility.toFixed(2) }}%
        </n-descriptions-item>
        <n-descriptions-item label="评分">
          <n-progress
            type="line"
            :percentage="futures.score || 0"
            :color="getScoreColor(futures.score)"
            :height="12"
            :border-radius="4"
            :show-indicator="false"
          />
          <span class="score-text">{{ futures.score || 0 }}</span>
        </n-descriptions-item>
        <n-descriptions-item label="推荐" :span="2">
          <n-tag :type="getRecommendationType(futures.recommendation)" size="small">
            {{ futures.recommendation || '观望' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="分析日期" :span="2" v-if="futures.analysis_date">
          {{ formatDate(futures.analysis_date) }}
        </n-descriptions-item>
      </n-descriptions>

      <div class="analysis-content" v-if="futures.analysis">
        <n-divider />
        <n-collapse>
          <n-collapse-item title="分析结果" name="1">
            <div class="analysis-text">
              <pre>{{ futures.analysis }}</pre>
            </div>
          </n-collapse-item>
        </n-collapse>
      </div>
    </template>
  </n-card>
</template>

<script setup lang="ts">
import { defineProps } from 'vue';
import { 
  NCard, 
  NTag, 
  NDescriptions, 
  NDescriptionsItem, 
  NDivider, 
  NCollapse, 
  NCollapseItem, 
  NSpin, 
  NAlert, 
  NProgress,
  NEllipsis
} from 'naive-ui';

// 定义属性
const props = defineProps({
  futures: {
    type: Object,
    required: true
  }
});

// 格式化价格变化
function formatPriceChange(change?: number): string {
  if (change === undefined) return '--';
  const sign = change > 0 ? '+' : '';
  return `${sign}${change.toFixed(2)}%`;
}

// 获取价格变化的CSS类
function getPriceChangeClass(change?: number): string {
  if (change === undefined) return '';
  return change > 0 ? 'price-up' : (change < 0 ? 'price-down' : '');
}

// 获取状态类型
function getStatusType(status: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  const statusMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    'waiting': 'default',
    'analyzing': 'info',
    'completed': 'success',
    'error': 'error'
  };
  return statusMap[status] || 'default';
}

// 获取状态文本
function getStatusText(status: string): string {
  const statusMap: Record<string, string> = {
    'waiting': '等待分析',
    'analyzing': '分析中',
    'completed': '已完成',
    'error': '出错'
  };
  return statusMap[status] || status;
}

// 获取趋势标签类型
function getTrendTagType(trend?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!trend) return 'default';
  const trendMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    'UP': 'success',
    'DOWN': 'error',
    'FLAT': 'info',
    'NEUTRAL': 'info'
  };
  return trendMap[trend] || 'default';
}

// 获取趋势文本
function getTrendText(trend?: string): string {
  if (!trend) return '--';
  const trendMap: Record<string, string> = {
    'UP': '上升',
    'DOWN': '下降',
    'FLAT': '平稳',
    'NEUTRAL': '平稳'
  };
  return trendMap[trend] || trend;
}

// 获取MACD标签类型
function getMacdTagType(signal?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!signal) return 'default';
  const signalMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    'BUY': 'success',
    'SELL': 'error',
    'HOLD': 'info',
    'NEUTRAL': 'default'
  };
  return signalMap[signal] || 'default';
}

// 获取MACD文本
function getMacdText(signal?: string): string {
  if (!signal) return '--';
  const signalMap: Record<string, string> = {
    'BUY': '买入',
    'SELL': '卖出',
    'HOLD': '持有',
    'NEUTRAL': '中性'
  };
  return signalMap[signal] || signal;
}

// 获取成交量标签类型
function getVolumeTagType(status?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!status) return 'default';
  const statusMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    'HIGH': 'success',
    'LOW': 'warning',
    'NORMAL': 'info'
  };
  return statusMap[status] || 'default';
}

// 获取成交量文本
function getVolumeText(status?: string): string {
  if (!status) return '--';
  const statusMap: Record<string, string> = {
    'HIGH': '放量',
    'LOW': '缩量',
    'NORMAL': '正常'
  };
  return statusMap[status] || status;
}

// 获取持仓量标签类型
function getOpenInterestTagType(status?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!status) return 'default';
  const statusMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    'HIGH': 'success',
    'LOW': 'warning',
    'NORMAL': 'info'
  };
  return statusMap[status] || 'default';
}

// 获取持仓量文本
function getOpenInterestText(status?: string): string {
  if (!status) return '--';
  const statusMap: Record<string, string> = {
    'HIGH': '增加',
    'LOW': '减少',
    'NORMAL': '正常'
  };
  return statusMap[status] || status;
}

// 获取推荐类型
function getRecommendationType(recommendation?: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!recommendation) return 'default';
  const recommendationMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    '强烈买入': 'success',
    '买入': 'success',
    '持有': 'info',
    '观望': 'default',
    '减持': 'warning',
    '卖出': 'error',
    '强烈卖出': 'error',
    '做多': 'success',
    '做空': 'error'
  };
  return recommendationMap[recommendation] || 'default';
}

// 获取评分颜色
function getScoreColor(score?: number): string {
  if (score === undefined) return '#d9d9d9';
  if (score >= 80) return '#18a058';
  if (score >= 60) return '#2080f0';
  if (score >= 40) return '#f0a020';
  return '#d03050';
}

// 格式化日期
function formatDate(dateStr?: string): string {
  if (!dateStr) return '--';
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      return dateStr;
    }
    return date.toISOString().split('T')[0];
  } catch (e) {
    return dateStr;
  }
}
</script>

<style scoped>
.futures-card {
  margin-bottom: 16px;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.futures-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
}

.futures-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.futures-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.futures-code {
  font-weight: bold;
  font-size: 1.1em;
}

.futures-name {
  color: #666;
  font-size: 0.9em;
}

.futures-info {
  margin-top: 8px;
}

.price-up {
  color: #18a058;
}

.price-down {
  color: #d03050;
}

.score-text {
  margin-left: 8px;
  font-size: 0.9em;
  color: #666;
}

.analysis-content {
  margin-top: 8px;
}

.analysis-text {
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 0.9em;
  line-height: 1.5;
  color: #333;
  max-height: 300px;
  overflow-y: auto;
}

.analysis-text pre {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
}

.error-container {
  padding: 8px 0;
}

.waiting-container, .analyzing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 16px 0;
  gap: 8px;
}

.waiting-text, .analyzing-text {
  color: #666;
  font-size: 0.9em;
}

.analysis-preview {
  margin-top: 8px;
  width: 100%;
  color: #666;
  font-size: 0.85em;
  line-height: 1.4;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .futures-card {
    margin-bottom: 12px;
  }
  
  .futures-code {
    font-size: 1em;
  }
  
  .futures-name {
    font-size: 0.85em;
  }
  
  .analysis-text {
    max-height: 200px;
    font-size: 0.85em;
  }
}
</style>