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
        
        <!-- 加载状态 -->
        <div v-if="resourcesLoading" class="resources-loading">
          <div class="loading-spinner"></div>
          <p>正在加载资源列表...</p>
        </div>

        <!-- 加载错误 -->
        <div v-else-if="resourcesError" class="resources-error">
          <div class="error-message">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" class="error-icon">
              <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
              <path d="m15 9-6 6m0-6 6 6" stroke="currentColor" stroke-width="2"/>
            </svg>
            <p>{{ resourcesError }}</p>
            <button class="retry-btn" @click="loadEpisodeResources">重试</button>
          </div>
        </div>
        
        <!-- 有资源数据 -->
        <div v-else-if="resourcesData && resourcesData.subtitle_groups.length > 0" class="resources-available">
          <div class="resource-stats">
            找到 {{ resourcesData.total_resources }} 个可用资源，来自 {{ resourcesData.subtitle_groups.length }} 个字幕组
          </div>
          
          <!-- 按字幕组分类的资源列表 -->
          <div class="subtitle-groups">
            <div 
              v-for="group in resourcesData.subtitle_groups" 
              :key="group.id" 
              class="subtitle-group"
            >
              <div class="group-header">
                <h4 class="group-name">{{ group.name }}</h4>
                <span class="group-count">{{ group.resource_count }} 个资源</span>
              </div>
              
              <div class="group-resources">
                <div 
                  v-for="resource in group.resources" 
                  :key="resource.id" 
                  class="resource-item"
                >
                  <div class="resource-info">
                    <div class="resource-title">{{ resource.title }}</div>
                    <div class="resource-meta">
                      <span v-if="resource.resolution" class="meta-tag resolution">{{ resource.resolution }}</span>
                      <span v-if="resource.subtitle_type" class="meta-tag subtitle">{{ resource.subtitle_type }}</span>
                      <span v-if="resource.file_size" class="meta-tag size">{{ resource.file_size }}</span>
                    </div>
                  </div>
                  
                  <div class="resource-actions">
                    <button 
                      v-if="resource.magnet_url" 
                      @click="downloadResource(resource.magnet_url, 'magnet')"
                      class="download-btn magnet-btn"
                      title="磁力链接下载"
                    >
                      磁力
                    </button>
                    <button 
                      v-if="resource.torrent_url" 
                      @click="downloadResource(resource.torrent_url, 'torrent')"
                      class="download-btn torrent-btn"
                      title="种子文件下载"
                    >
                      种子
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 无资源状态 -->
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
import BangumiApiService, { type EpisodeResourcesData, type SubtitleGroupData } from '../services/api'

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
  bangumiId?: number
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

// 资源数据状态
const resourcesData = ref<EpisodeResourcesData | null>(null)
const resourcesLoading = ref(false)
const resourcesError = ref<string | null>(null)

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

// 加载资源数据
const loadEpisodeResources = async () => {
  if (!props.bangumiId || !props.episodeData?.number) {
    return
  }

  try {
    resourcesLoading.value = true
    resourcesError.value = null
    resourcesData.value = null

    const data = await BangumiApiService.getEpisodeResources(
      props.bangumiId,
      props.episodeData.number
    )
    resourcesData.value = data
    console.log('✅ 资源数据加载成功:', data)

  } catch (err: any) {
    console.error('❌ 加载资源数据失败:', err)
    resourcesError.value = err.response?.data?.message || '加载资源数据失败'
  } finally {
    resourcesLoading.value = false
  }
}

// 刷新资源
const refreshResources = () => {
  if (props.episodeData) {
    loadEpisodeResources()
    emit('refreshResources', props.episodeData.number)
  }
}

// 下载资源
const downloadResource = (url: string, type: 'magnet' | 'torrent') => {
  if (!url) return
  
  try {
    if (type === 'magnet') {
      // 磁力链接可以直接在浏览器中打开
      window.location.href = url
    } else if (type === 'torrent') {
      // 种子文件需要下载
      const link = document.createElement('a')
      link.href = url
      link.download = '' // 让浏览器决定文件名
      link.target = '_blank'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
    
    console.log(`🔗 ${type === 'magnet' ? '磁力链接' : '种子文件'}下载触发:`, url)
  } catch (err) {
    console.error('下载失败:', err)
    alert('下载失败，请检查链接或重试')
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
    loadEpisodeResources() // 加载资源数据
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

/* 资源统计信息 */
.resource-stats {
  color: #27ae60;
  font-weight: 500;
  margin-bottom: 1.5rem;
  padding: 0.75rem;
  background-color: #f8fff8;
  border-radius: 6px;
  border-left: 4px solid #27ae60;
}

/* 加载状态 */
.resources-loading {
  text-align: center;
  padding: 2rem;
  color: #7f8c8d;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #3498db;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 错误状态 */
.resources-error {
  text-align: center;
  padding: 2rem;
}

.error-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.error-icon {
  color: #e74c3c;
}

.retry-btn {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.3s;
}

.retry-btn:hover {
  background-color: #c0392b;
}

/* 字幕组列表 */
.subtitle-groups {
  space-y: 1.5rem;
}

.subtitle-group {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background-color: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
}

.group-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.group-count {
  font-size: 0.85rem;
  color: #7f8c8d;
  background-color: #e9ecef;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
}

.group-resources {
  padding: 0.5rem;
}

.resource-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 1rem;
  margin-bottom: 0.5rem;
  background-color: white;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.resource-item:hover {
  border-color: #3498db;
  box-shadow: 0 2px 8px rgba(52, 152, 219, 0.1);
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-info {
  flex: 1;
  margin-right: 1rem;
}

.resource-title {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.resource-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.meta-tag {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-weight: 500;
}

.meta-tag.resolution {
  background-color: #e3f2fd;
  color: #1976d2;
}

.meta-tag.subtitle {
  background-color: #f3e5f5;
  color: #7b1fa2;
}

.meta-tag.size {
  background-color: #e8f5e8;
  color: #388e3c;
}

.resource-actions {
  display: flex;
  gap: 0.5rem;
}

.download-btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.85rem;
  transition: all 0.3s;
  min-width: 60px;
}

.magnet-btn {
  background-color: #e74c3c;
  color: white;
}

.magnet-btn:hover {
  background-color: #c0392b;
  transform: translateY(-1px);
}

.torrent-btn {
  background-color: #3498db;
  color: white;
}

.torrent-btn:hover {
  background-color: #2980b9;
  transform: translateY(-1px);
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