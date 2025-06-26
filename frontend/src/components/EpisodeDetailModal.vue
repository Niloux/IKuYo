<template>
  <div v-if="visible" :class="['modal-overlay', { closing: isClosing }]" @click="handleOverlayClick">
    <div :class="['modal-content', { closing: isClosing }]" @click.stop>
      <!-- 模态框头部 - 固定不滚动 -->
      <div class="modal-header">
        <h2 class="episode-title">{{ episodeData?.title || `第${episodeData?.number}集` }}</h2>
        <button class="close-button" @click="closeModal">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- 可滚动的内容区域 -->
      <div class="modal-body">
        <!-- 集数详细信息 -->
        <div class="episode-details">
        <div class="episode-meta">
          <span v-if="episodeData?.duration" class="meta-item">
            <strong>时长:</strong> {{ episodeData.duration }}
          </span>
          <span v-if="episodeData?.airdate" class="meta-item">
            <strong>首播:</strong> {{ formatDate(episodeData.airdate) }}
          </span>
          <span v-if="episodeData?.comment" class="meta-item">
            <strong>评论:</strong> {{ episodeData.comment }}条
          </span>
        </div>

        <div v-if="episodeData?.subtitle" class="episode-subtitle">
          <strong>原文标题:</strong> {{ episodeData.subtitle }}
        </div>

        <div v-if="episodeData?.desc" class="episode-description">
          <strong>剧情简介:</strong>
          <p :class="{ 'description-collapsed': !descExpanded && isDescLong }">
            {{ episodeData.desc }}
          </p>
          <button 
            v-if="isDescLong" 
            @click="toggleDescription" 
            class="expand-btn"
          >
            {{ descExpanded ? '收起' : '展开' }}
          </button>
        </div>
      </div>

      <!-- 资源列表区域 -->
      <div class="resources-section">
        <h3 class="section-title">资源下载</h3>
        
        <div v-if="episodeData?.available" class="resources-available">
          <div class="resource-stats">
            找到 {{ episodeData.resourceCount }} 个可用资源
          </div>
          
          <!-- 资源列表占位 - 待后续实现 -->
          <div class="resource-list-placeholder">
            <div class="placeholder-item" v-for="i in episodeData.resourceCount" :key="i">
              <div class="resource-item">
                <div class="resource-info">
                  <span class="resource-title">资源 {{ i }} - 字幕组名称</span>
                  <span class="resource-size">1.2GB</span>
                </div>
                <button class="download-button">下载</button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="resources-unavailable">
          <div class="no-resources-message">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="no-resources-icon">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="m9 9 6 6m0-6-6 6" stroke="currentColor" stroke-width="2"/>
            </svg>
            <p>暂无可用资源</p>
            <button class="refresh-resources-btn" @click="refreshResources">刷新资源</button>
          </div>
        </div>
        </div> <!-- 关闭 modal-body -->
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'

// 集数详细信息类型
interface EpisodeDetail {
  number: number
  title: string
  subtitle?: string
  duration?: string
  airdate?: string
  desc?: string
  comment?: number
  available: boolean
  resourceCount: number
  bangumiData?: any
}

// Props定义
interface Props {
  visible: boolean
  episodeData: EpisodeDetail | null
}

const props = defineProps<Props>()

// Emits定义
const emit = defineEmits<{
  close: []
  refreshResources: [episodeNumber: number]
}>()

// 剧情简介展开/收起状态
const descExpanded = ref(false)
const DESC_COLLAPSE_LENGTH = 150 // 收起时显示的字符数

// 关闭动画状态
const isClosing = ref(false)

// 计算属性：判断剧情简介是否足够长需要展开/收起功能
const isDescLong = computed(() => {
  return props.episodeData?.desc && props.episodeData.desc.length > DESC_COLLAPSE_LENGTH
})

// 切换剧情简介展开/收起
const toggleDescription = () => {
  descExpanded.value = !descExpanded.value
}

// 关闭模态框
const closeModal = () => {
  isClosing.value = true
  // 等待关闭动画完成后再真正关闭
  setTimeout(() => {
    isClosing.value = false
    emit('close')
  }, 250) // 与CSS动画时间保持一致
}

// 处理遮罩点击
const handleOverlayClick = () => {
  closeModal()
}

// 刷新资源
const refreshResources = () => {
  if (props.episodeData) {
    emit('refreshResources', props.episodeData.number)
  }
}

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', { 
      year: 'numeric',
      month: 'short', 
      day: 'numeric' 
    })
  } catch {
    return dateStr
  }
}

// 监听ESC键关闭
const handleKeyDown = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && props.visible) {
    closeModal()
  }
}

// 获取滚动条宽度
const getScrollbarWidth = () => {
  const outer = document.createElement('div')
  outer.style.visibility = 'hidden'
  outer.style.overflow = 'scroll'
  // @ts-ignore - IE兼容性属性
  outer.style.msOverflowStyle = 'scrollbar'
  document.body.appendChild(outer)

  const inner = document.createElement('div')
  outer.appendChild(inner)

  const scrollbarWidth = outer.offsetWidth - inner.offsetWidth
  outer.parentNode?.removeChild(outer)

  return scrollbarWidth
}

// 禁用/恢复页面滚动，防止滚动条消失导致的偏移
const disableBodyScroll = () => {
  const scrollbarWidth = getScrollbarWidth()
  document.body.style.overflow = 'hidden'
  document.body.style.paddingRight = `${scrollbarWidth}px`
}

const enableBodyScroll = () => {
  document.body.style.overflow = ''
  document.body.style.paddingRight = ''
}

// 监听visible变化，添加/移除键盘事件
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    document.addEventListener('keydown', handleKeyDown)
    disableBodyScroll() // 禁止背景滚动并补偿偏移
    descExpanded.value = false // 重置展开状态
    isClosing.value = false // 重置关闭状态
  } else {
    document.removeEventListener('keydown', handleKeyDown)
    enableBodyScroll() // 恢复背景滚动
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  opacity: 1;
  animation: fadeIn 0.3s ease-out;
}

.modal-overlay.closing {
  animation: fadeOut 0.25s ease-out forwards;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes fadeOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 95%;
  max-width: 800px;
  max-height: 90vh;
  overflow: hidden; /* 隐藏外层溢出，保持圆角 */
  position: relative;
  transform: scale(1);
  animation: modalSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
  display: flex;
  flex-direction: column;
}

.modal-content.closing {
  animation: modalSlideOut 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
}

@keyframes modalSlideIn {
  0% {
    transform: scale(0.7);
    opacity: 0;
  }
  70% {
    transform: scale(1.05);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes modalSlideOut {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(0.8);
    opacity: 0;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2rem 2rem 1rem 2rem;
  border-bottom: 1px solid #eee;
  flex-shrink: 0; /* 头部不收缩 */
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0; /* 允许flex子项收缩 */
}

/* 自定义滚动条样式 */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: transparent;
}

.modal-body::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background-color: rgba(0, 0, 0, 0.3);
}

.episode-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.close-button {
  background: none;
  border: none;
  padding: 0.5rem;
  cursor: pointer;
  color: #7f8c8d;
  transition: color 0.3s;
  border-radius: 50%;
}

.close-button:hover {
  color: #e74c3c;
  background-color: #f8f9fa;
}

.episode-details {
  padding: 1.5rem 2rem;
}

.episode-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1rem;
}

.meta-item {
  color: #7f8c8d;
  font-size: 0.9rem;
}

.episode-subtitle {
  margin-bottom: 1rem;
  color: #5a6c7d;
  font-size: 0.95rem;
}

.episode-description {
  color: #34495e;
}

.episode-description p {
  margin: 0.5rem 0 0 0;
  line-height: 1.6;
  transition: all 0.3s ease;
  white-space: pre-line; /* 保留换行符和空格，自动换行 */
}

.description-collapsed {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  position: relative;
}

.expand-btn {
  background: none;
  border: none;
  color: #3498db;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 500;
  margin-top: 0.5rem;
  padding: 0;
  transition: color 0.3s;
}

.expand-btn:hover {
  color: #2980b9;
  text-decoration: underline;
}

.resources-section {
  padding: 0 2rem 2rem 2rem;
}

.section-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 1rem;
}

.resource-stats {
  color: #27ae60;
  font-weight: 500;
  margin-bottom: 1rem;
}

.resource-list-placeholder {
  space-y: 0.75rem;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  margin-bottom: 0.75rem;
}

.resource-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.resource-title {
  font-weight: 500;
  color: #2c3e50;
}

.resource-size {
  font-size: 0.85rem;
  color: #7f8c8d;
}

.download-button {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.download-button:hover {
  background-color: #2980b9;
}

.resources-unavailable {
  text-align: center;
  padding: 2rem;
}

.no-resources-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.no-resources-icon {
  color: #e74c3c;
}

.no-resources-message p {
  color: #7f8c8d;
  margin: 0;
  font-size: 1.1rem;
}

.refresh-resources-btn {
  background-color: #f39c12;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.refresh-resources-btn:hover {
  background-color: #e67e22;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .modal-header {
    padding: 1.5rem 1.5rem 1rem 1.5rem;
  }

  .episode-title {
    font-size: 1.25rem;
  }

  .episode-details,
  .resources-section {
    padding-left: 1.5rem;
    padding-right: 1.5rem;
  }

  .episode-meta {
    flex-direction: column;
    gap: 0.5rem;
  }

  .resource-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
}
</style> 