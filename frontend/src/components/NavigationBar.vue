<template>
  <div class="nav-container">
    <n-menu
      v-model:value="activeKey"
      mode="horizontal"
      :options="menuOptions"
      @update:value="handleMenuUpdate"
    />
  </div>
</template>

<script setup lang="ts">
import { h, ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { NMenu, NIcon } from 'naive-ui';
import { 
  BarChartOutline as ChartIcon,
  TrendingUpOutline as TrendingUpIcon
} from '@vicons/ionicons5';

const router = useRouter();
const route = useRoute();

// 根据当前路由设置活动菜单项
const activeKey = computed(() => {
  const path = route.path;
  if (path === '/futures') return 'futures';
  return 'stocks';
});

// 菜单选项
const menuOptions = [
  {
    label: () => h(
      'div',
      {
        style: 'display: flex; align-items: center;'
      },
      [
        h(
          NIcon,
          {
            style: 'margin-right: 4px;'
          },
          { default: () => h(ChartIcon) }
        ),
        '股票分析'
      ]
    ),
    key: 'stocks',
    disabled: false
  },
  {
    label: () => h(
      'div',
      {
        style: 'display: flex; align-items: center;'
      },
      [
        h(
          NIcon,
          {
            style: 'margin-right: 4px;'
          },
          { default: () => h(TrendingUpIcon) }
        ),
        '期货分析'
      ]
    ),
    key: 'futures',
    disabled: false
  }
];

// 处理菜单项更新
const handleMenuUpdate = (key: string) => {
  switch (key) {
    case 'stocks':
      router.push('/');
      break;
    case 'futures':
      router.push('/futures');
      break;
  }
};
</script>

<style scoped>
.nav-container {
  margin-bottom: 16px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* 移动端适配 */
@media (max-width: 768px) {
  .nav-container {
    margin-bottom: 12px;
  }
}
</style>