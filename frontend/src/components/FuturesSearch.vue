<template>
  <div class="futures-search">
    <n-input-group>
      <n-input
        v-model:value="keyword"
        placeholder="输入期货代码或名称搜索"
        @keydown.enter="searchFutures"
      />
      <n-button type="primary" @click="searchFutures" :loading="isSearching">
        搜索
      </n-button>
    </n-input-group>

    <div v-if="isSearching" class="search-loading">
      <n-spin size="small" />
      <span class="loading-text">搜索中...</span>
    </div>

    <div v-else-if="searchResults.length > 0" class="search-results">
      <n-list hoverable clickable>
        <n-list-item
          v-for="(item, index) in searchResults"
          :key="index"
          @click="selectFutures(item.symbol)"
        >
          <n-thing :title="item.symbol" :description="item.name">
            <template #avatar>
              <n-tag :type="getExchangeTagType(item.exchange)">
                {{ item.exchange || '未知' }}
              </n-tag>
            </template>
            <template #description>
              <div class="futures-info">
                <span>{{ item.name }}</span>
                <span class="futures-price">
                  {{ item.price ? item.price.toFixed(2) : '--' }}
                </span>
              </div>
            </template>
          </n-thing>
        </n-list-item>
      </n-list>
    </div>

    <div v-else-if="hasSearched" class="no-results">
      <n-empty description="未找到匹配的期货" size="small">
        <template #icon>
          <n-icon>
            <SearchIcon />
          </n-icon>
        </template>
      </n-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, defineEmits } from 'vue';
import { 
  NInputGroup, 
  NInput, 
  NButton, 
  NSpin, 
  NList, 
  NListItem, 
  NThing, 
  NTag, 
  NEmpty, 
  NIcon,
  useMessage
} from 'naive-ui';
import { SearchOutline as SearchIcon } from '@vicons/ionicons5';
import { apiService } from '../services/api'; 
import logger from '../utils/logger'; 

// 定义事件
const emit = defineEmits(['select']);

// 使用Naive UI的消息组件
const message = useMessage();

// 搜索状态
const keyword = ref('');
const searchResults = ref<any[]>([]);
const isSearching = ref(false);
const hasSearched = ref(false);

// 搜索期货
async function searchFutures() {
  if (!keyword.value.trim()) {
    message.warning('请输入搜索关键词');
    return;
  }
  
  isSearching.value = true;
  searchResults.value = [];
  
  try {
    logger.debug(`开始搜索期货: ${keyword.value}`);
    
    // 使用API服务搜索期货
    searchResults.value = await apiService.searchFutures(keyword.value);
    
    if (searchResults.value.length === 0) {
      message.info('未找到匹配的期货');
    } else {
      message.success(`找到 ${searchResults.value.length} 个匹配的期货`);
    }
  } catch (error) {
    logger.error('搜索期货时出错:', error);
    message.error(`搜索失败: ${error instanceof Error ? error.message : '未知错误'}`);
  } finally {
    isSearching.value = false;
  }
}

// 选择期货
function selectFutures(symbol: string) {
  emit('select', symbol);
  // 清空搜索结果
  searchResults.value = [];
  keyword.value = '';
}

// 根据交易所获取标签类型
function getExchangeTagType(exchange: string): 'default' | 'info' | 'success' | 'warning' | 'error' {
  if (!exchange) return 'default';
  
  const exchangeMap: Record<string, 'default' | 'info' | 'success' | 'warning' | 'error'> = {
    '上期所': 'info',
    '大商所': 'success',
    '郑商所': 'warning',
    '中金所': 'error'
  };
  
  return exchangeMap[exchange] || 'default';
}
</script>

<style scoped>
.futures-search {
  width: 100%;
}

.search-loading {
  display: flex;
  align-items: center;
  margin-top: 8px;
  color: #666;
}

.loading-text {
  margin-left: 8px;
}

.search-results {
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #eee;
  border-radius: 4px;
}

.no-results {
  margin-top: 16px;
  padding: 16px;
  text-align: center;
  color: #999;
}

.futures-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.futures-price {
  font-weight: bold;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .search-results {
    max-height: 200px;
  }
}
</style>