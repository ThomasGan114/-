<template>
  <Teleport to="body">
    <div
      v-if="visible"
      ref="overlayRef"
      class="fv-overlay"
      @click.self="onOverlayClick"
    >
      <div
        ref="shellRef"
        class="fv-shell"
        :class="{ 'is-resizing': resizing, 'is-fullscreen': isFullscreen }"
        :style="shellStyle"
        @touchstart.passive="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
        @touchcancel="onTouchEnd"
      >
        <!-- 媒体窗口本体 -->
        <div class="fv-window">
          <!-- 顶栏：半透明磨砂 -->
          <div class="fv-bar fv-topbar">
            <div class="fv-bar-group">
              <button
                v-if="files.length > 1"
                class="fv-btn"
                :class="{ disabled: currentIndex === 0 }"
                title="上一个 (←)"
                @click="prevFile"
              >
                <i class="bi bi-chevron-left"></i>
              </button>
              <button
                v-if="files.length > 1"
                class="fv-btn"
                :class="{ disabled: currentIndex >= files.length - 1 }"
                title="下一个 (→)"
                @click="nextFile"
              >
                <i class="bi bi-chevron-right"></i>
              </button>
            </div>

            <div class="fv-bar-group">
              <button
                v-if="currentFileType === 'video' && canPictureInPicture"
                class="fv-btn"
                :class="{ active: isPip }"
                title="画中画"
                @click="togglePictureInPicture"
              >
                <i class="bi bi-pip"></i>
              </button>
              <button class="fv-btn" title="下载" @click="downloadFile">
                <i class="bi bi-download"></i>
              </button>
              <button class="fv-btn fv-btn-close" title="关闭 (Esc)" @click="close">
                <i class="bi bi-x-lg"></i>
              </button>
            </div>
          </div>

          <!-- 内容区 -->
          <div ref="stageRef" class="fv-stage" :class="'type-' + currentFileType">
            <img
              v-if="currentFileType === 'image'"
              :src="currentFileUrl"
              :alt="currentFileName"
              class="fv-image"
              draggable="false"
            >

            <video
              v-else-if="currentFileType === 'video'"
              ref="videoRef"
              class="fv-video"
              :src="currentFileUrl"
              playsinline
              preload="metadata"
              @loadedmetadata="onLoadedMetadata"
              @timeupdate="onTimeUpdate"
              @progress="onProgress"
              @play="isPlaying = true"
              @pause="isPlaying = false"
              @ended="onEnded"
              @volumechange="onVolumeChange"
              @click="togglePlay"
              @dblclick="toggleFullscreen"
            ></video>

            <div v-else-if="currentFileType === 'audio'" class="fv-audio-box">
              <i class="bi bi-music-note-beamed fv-audio-icon"></i>
              <audio
                ref="audioRef"
                :src="currentFileUrl"
                class="fv-audio"
                controls
              ></audio>
            </div>

            <iframe
              v-else-if="currentFileType === 'pdf'"
              :src="currentFileUrl"
              class="fv-frame"
              type="application/pdf"
            ></iframe>

            <iframe
              v-else-if="currentFileType === 'office'"
              :src="getOfficeViewerUrl(currentFileUrl)"
              class="fv-frame"
            ></iframe>

            <div v-else class="fv-other">
              <i :class="getFileIcon(currentFile)" class="fv-other-icon"></i>
              <p class="fv-other-name">{{ currentFileName }}</p>
              <button class="fv-primary-btn" @click="downloadFile">
                <i class="bi bi-download me-2"></i>下载文件
              </button>
            </div>
          </div>

          <!-- 底栏：半透明磨砂（视频控制条 / 图片信息） -->
          <div class="fv-bar fv-bottombar">
            <template v-if="currentFileType === 'video'">
              <button class="fv-btn" :title="isPlaying ? '暂停 (空格)' : '播放 (空格)'" @click="togglePlay">
                <i :class="isPlaying ? 'bi bi-pause-fill' : 'bi bi-play-fill'"></i>
              </button>
              <span class="fv-time">{{ formatTime(currentTime) }}/{{ formatTime(duration) }}</span>
              <input
                class="fv-seek"
                type="range"
                min="0"
                :max="duration || 0"
                step="0.01"
                :value="currentTime"
                :style="seekStyle"
                aria-label="播放进度"
                @input="onSeekInput"
              >
              <button class="fv-btn" :title="muted ? '取消静音' : '静音'" @click="toggleMute">
                <i :class="muted ? 'bi bi-volume-mute-fill' : 'bi bi-volume-up-fill'"></i>
              </button>
              <input
                class="fv-volume"
                type="range"
                min="0"
                max="1"
                step="0.02"
                :value="muted ? 0 : volume"
                aria-label="音量"
                @input="onVolumeInput"
              >
              <button class="fv-btn" :title="isFullscreen ? '退出全屏' : '全屏'" @click="toggleFullscreen">
                <i :class="isFullscreen ? 'bi bi-fullscreen-exit' : 'bi bi-arrows-fullscreen'"></i>
              </button>
              <button class="fv-btn" title="更多" @click.stop="toggleMenu()">
                <i class="bi bi-three-dots-vertical"></i>
              </button>
            </template>

            <template v-else>
              <span class="fv-name">{{ currentFileName }}</span>
              <span v-if="files.length > 1" class="fv-counter">{{ currentIndex + 1 }} / {{ files.length }}</span>
            </template>
          </div>

          <!-- 更多菜单 -->
          <div v-if="menuOpen" class="fv-menu" @click.stop>
            <button class="fv-menu-item" @click="downloadFile(); menuOpen = false">
              <i class="bi bi-download"></i> 下载
            </button>
            <button class="fv-menu-item" @click="toggleLoop()">
              <i :class="loop ? 'bi bi-check2-square' : 'bi bi-square'"></i> 循环播放
            </button>
            <button
              v-if="canPictureInPicture"
              class="fv-menu-item"
              @click="togglePictureInPicture(); menuOpen = false"
            >
              <i class="bi bi-pip"></i> 画中画
            </button>
          </div>
        </div>

        <!-- 八个方向的缩放手柄（电脑端鼠标拖动） -->
        <span
          v-for="handle in RESIZE_HANDLES"
          :key="handle"
          class="fv-handle"
          :class="'handle-' + handle"
          :title="handle === 'se' ? '拖动调整窗口大小' : ''"
          @pointerdown.prevent="startResize($event, handle)"
        ></span>

        <!-- 右下角视觉提示 -->
        <i class="bi bi-arrows-angle-expand fv-resize-hint" aria-hidden="true"></i>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch, nextTick } from 'vue'

const props = defineProps({
  files: { type: Array, default: () => [] },
  initialIndex: { type: Number, default: 0 }
})

const emit = defineEmits(['close'])

const staticUrl = import.meta.env.VITE_STATIC_URL || '/static/'

const visible = ref(false)
const currentIndex = ref(0)
const menuOpen = ref(false)
const resizing = ref(false)

const overlayRef = ref(null)
const shellRef = ref(null)
const stageRef = ref(null)
const videoRef = ref(null)
const audioRef = ref(null)

// ---------- 视频状态 ----------
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const buffered = ref(0)
const volume = ref(1)
const muted = ref(false)
const loop = ref(false)
const isFullscreen = ref(false)
const isPip = ref(false)
const canPictureInPicture = ref(false)

// ---------- 尺寸（可自由缩放，记住上次大小） ----------
const MIN_WIDTH = 320
const MIN_HEIGHT = 220
const EDGE_GAP = 8
const SIZE_KEY = 'filePreviewSize'
const shellWidth = ref(900)
const shellHeight = ref(600)
const posX = ref(0)
const posY = ref(0)

const RESIZE_HANDLES = ['n', 's', 'w', 'e', 'nw', 'ne', 'sw', 'se']

const shellStyle = computed(() => ({
  left: `${Math.round(posX.value)}px`,
  top: `${Math.round(posY.value)}px`,
  width: `${Math.round(shellWidth.value)}px`,
  height: `${Math.round(shellHeight.value)}px`
}))

const seekStyle = computed(() => {
  const played = duration.value > 0 ? (currentTime.value / duration.value) * 100 : 0
  const loaded = duration.value > 0 ? (buffered.value / duration.value) * 100 : 0
  const p = Math.max(0, Math.min(100, played))
  const l = Math.max(p, Math.min(100, loaded))
  return {
    background: `linear-gradient(to right, var(--primary-color) 0%, var(--primary-color) ${p}%, rgba(255,255,255,0.45) ${p}%, rgba(255,255,255,0.45) ${l}%, rgba(255,255,255,0.16) ${l}%, rgba(255,255,255,0.16) 100%)`
  }
})

// ---------- 文件信息 ----------
const currentFile = computed(() => props.files[currentIndex.value] || '')
const currentFileName = computed(() => {
  const name = currentFile.value.split('_').pop() || ''
  return name || '未命名文件'
})
const currentFileUrl = computed(() => `${staticUrl}uploads/${currentFile.value}`)
const currentFileType = computed(() => getFileType(currentFile.value))

// ---------- 尺寸工具 ----------
const viewportLimit = () => ({
  maxWidth: Math.max(MIN_WIDTH, window.innerWidth - 32),
  maxHeight: Math.max(MIN_HEIGHT, window.innerHeight - 32)
})

const clampSize = (width, height) => {
  const { maxWidth, maxHeight } = viewportLimit()
  return {
    width: Math.min(Math.max(width, MIN_WIDTH), maxWidth),
    height: Math.min(Math.max(height, MIN_HEIGHT), maxHeight)
  }
}

/** 把窗口摆在可视区域中间 */
const centerWindow = (width = shellWidth.value, height = shellHeight.value) => {
  const next = clampSize(width, height)
  shellWidth.value = next.width
  shellHeight.value = next.height
  posX.value = Math.max(EDGE_GAP, (window.innerWidth - next.width) / 2)
  posY.value = Math.max(EDGE_GAP, (window.innerHeight - next.height) / 2)
}

/** 只改尺寸、保持中心点不动（双指缩放用，视觉上更自然） */
const resizeAroundCenter = (width, height) => {
  const centerX = posX.value + shellWidth.value / 2
  const centerY = posY.value + shellHeight.value / 2
  const next = clampSize(width, height)
  shellWidth.value = next.width
  shellHeight.value = next.height
  clampPosition(centerX - next.width / 2, centerY - next.height / 2)
}

/** 把位置收敛进可视范围，避免窗口被拖出屏幕 */
const clampPosition = (x, y) => {
  const maxX = Math.max(EDGE_GAP, window.innerWidth - shellWidth.value - EDGE_GAP)
  const maxY = Math.max(EDGE_GAP, window.innerHeight - shellHeight.value - EDGE_GAP)
  posX.value = Math.min(Math.max(x, EDGE_GAP), maxX)
  posY.value = Math.min(Math.max(y, EDGE_GAP), maxY)
}

const loadSavedSize = () => {
  const fallbackWidth = Math.min(1000, Math.max(MIN_WIDTH, window.innerWidth - 160))
  const fallbackHeight = Math.min(700, Math.max(MIN_HEIGHT, window.innerHeight - 140))
  let width = fallbackWidth
  let height = fallbackHeight
  try {
    const raw = localStorage.getItem(SIZE_KEY)
    if (raw) {
      const saved = JSON.parse(raw)
      if (typeof saved.width === 'number' && typeof saved.height === 'number') {
        width = saved.width
        height = saved.height
      }
    }
  } catch (error) {
    /* 忽略损坏的缓存 */
  }
  centerWindow(width, height)
}

const saveSize = () => {
  try {
    localStorage.setItem(SIZE_KEY, JSON.stringify({
      width: Math.round(shellWidth.value),
      height: Math.round(shellHeight.value)
    }))
  } catch (error) {
    /* 隐私模式写不了，忽略 */
  }
}

// ---------- 桌面端：拖动边缘缩放 ----------
let resizeState = null

const startResize = (event, handle) => {
  if (!shellRef.value) return
  resizeState = {
    handle,
    startX: event.clientX,
    startY: event.clientY,
    width: shellWidth.value,
    height: shellHeight.value,
    left: posX.value,
    top: posY.value
  }
  resizing.value = true
  window.addEventListener('pointermove', onResizeMove)
  window.addEventListener('pointerup', onResizeEnd)
  window.addEventListener('pointercancel', onResizeEnd)
  document.body.classList.add('fv-resizing')
}

const onResizeMove = (event) => {
  if (!resizeState) return
  const { handle, startX, startY, width, height, left, top } = resizeState
  const dx = event.clientX - startX
  const dy = event.clientY - startY
  let nextWidth = width
  let nextHeight = height
  let nextX = left
  let nextY = top
  if (handle.includes('e')) nextWidth = width + dx
  if (handle.includes('w')) nextWidth = width - dx
  if (handle.includes('s')) nextHeight = height + dy
  if (handle.includes('n')) nextHeight = height - dy

  const clamped = clampSize(nextWidth, nextHeight)
  // 拖左边/上边时，位置跟着尺寸收敛量一起修正 —— 这样被拖的角始终跟手
  if (handle.includes('w')) nextX = left + (width - clamped.width)
  if (handle.includes('n')) nextY = top + (height - clamped.height)

  shellWidth.value = clamped.width
  shellHeight.value = clamped.height
  clampPosition(nextX, nextY)
}

const onResizeEnd = () => {
  if (!resizeState) return
  resizeState = null
  resizing.value = false
  window.removeEventListener('pointermove', onResizeMove)
  window.removeEventListener('pointerup', onResizeEnd)
  window.removeEventListener('pointercancel', onResizeEnd)
  document.body.classList.remove('fv-resizing')
  saveSize()
}

// ---------- 移动端：双指开合缩放 ----------
let pinchState = null

const touchDistance = (touches) => {
  const [a, b] = touches
  return Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY)
}

const onTouchStart = (event) => {
  if (event.touches.length !== 2) return
  pinchState = {
    distance: touchDistance(event.touches) || 1,
    width: shellWidth.value,
    height: shellHeight.value
  }
}

const onTouchMove = (event) => {
  if (!pinchState || event.touches.length !== 2) return
  if (event.cancelable) event.preventDefault() // 阻止浏览器整页缩放
  const ratio = touchDistance(event.touches) / pinchState.distance
  resizeAroundCenter(pinchState.width * ratio, pinchState.height * ratio)
}

const onTouchEnd = (event) => {
  if (event.touches && event.touches.length >= 2) return
  if (!pinchState) return
  pinchState = null
  saveSize()
}

// ---------- 视频控制 ----------
const formatTime = (seconds) => {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00'
  const total = Math.floor(seconds)
  const minutes = Math.floor(total / 60)
  const rest = total % 60
  return `${minutes}:${String(rest).padStart(2, '0')}`
}

const togglePlay = () => {
  const video = videoRef.value
  if (!video) return
  if (video.paused) video.play().catch(() => {})
  else video.pause()
}

const onLoadedMetadata = () => {
  const video = videoRef.value
  if (!video) return
  duration.value = Number.isFinite(video.duration) ? video.duration : 0
  volume.value = video.volume
  muted.value = video.muted
  video.loop = loop.value
  checkPictureInPicture()
}

const onTimeUpdate = () => {
  const video = videoRef.value
  if (!video) return
  currentTime.value = video.currentTime
  if (Number.isFinite(video.duration)) duration.value = video.duration
}

const onProgress = () => {
  const video = videoRef.value
  if (!video || !video.buffered || video.buffered.length === 0) return
  try {
    buffered.value = video.buffered.end(video.buffered.length - 1)
  } catch (error) {
    /* 忽略 */
  }
}

const onEnded = () => {
  isPlaying.value = false
  if (loop.value) {
    const video = videoRef.value
    if (video) {
      video.currentTime = 0
      video.play().catch(() => {})
    }
  }
}

const onSeekInput = (event) => {
  const video = videoRef.value
  if (!video) return
  const value = Number(event.target.value)
  currentTime.value = value
  video.currentTime = value
}

const onVolumeInput = (event) => {
  const video = videoRef.value
  if (!video) return
  const value = Number(event.target.value)
  video.volume = value
  video.muted = value === 0
}

const onVolumeChange = () => {
  const video = videoRef.value
  if (!video) return
  volume.value = video.volume
  muted.value = video.muted
}

const toggleMute = () => {
  const video = videoRef.value
  if (!video) return
  video.muted = !video.muted
}

const toggleLoop = () => {
  loop.value = !loop.value
  const video = videoRef.value
  if (video) video.loop = loop.value
}

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

// ---------- 画中画 ----------
const checkPictureInPicture = () => {
  const video = videoRef.value
  const standard = !!(document.pictureInPictureEnabled && video && typeof video.requestPictureInPicture === 'function')
  const webkit = !!(video && typeof video.webkitSetPresentationMode === 'function')
  canPictureInPicture.value = standard || webkit
}

const togglePictureInPicture = async () => {
  const video = videoRef.value
  if (!video) return
  try {
    if (document.pictureInPictureElement) {
      await document.exitPictureInPicture()
      isPip.value = false
      return
    }
    if (typeof video.requestPictureInPicture === 'function') {
      await video.requestPictureInPicture()
      isPip.value = true
    } else if (typeof video.webkitSetPresentationMode === 'function') {
      const next = video.webkitPresentationMode === 'picture-in-picture' ? 'inline' : 'picture-in-picture'
      video.webkitSetPresentationMode(next)
      isPip.value = next === 'picture-in-picture'
    }
  } catch (error) {
    /* 用户取消/不支持，忽略 */
  }
}

// ---------- 全屏 ----------
const toggleFullscreen = () => {
  const target = shellRef.value
  if (!target) return
  const active = document.fullscreenElement || document.webkitFullscreenElement
  if (active) {
    const exit = document.exitFullscreen || document.webkitExitFullscreen
    if (exit) exit.call(document).catch?.(() => {})
    return
  }
  const request = target.requestFullscreen || target.webkitRequestFullscreen
  if (request) request.call(target).catch?.(() => {})
}

const onFullscreenChange = () => {
  isFullscreen.value = !!(document.fullscreenElement || document.webkitFullscreenElement)
  if (!isFullscreen.value) centerWindow()
}

// ---------- 文件类型 ----------
const getFileType = (file) => {
  if (!file) return 'other'
  const ext = file.split('.').pop().toLowerCase()
  if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'avif'].includes(ext)) return 'image'
  if (['mp4', 'webm', 'mov', 'avi', 'mkv', 'flv', 'm4v'].includes(ext)) return 'video'
  if (['mp3', 'wav', 'm4a', 'aac', 'flac', 'ogg', 'oga', 'opus', 'wma', 'amr'].includes(ext)) return 'audio'
  if (ext === 'pdf') return 'pdf'
  if (['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx'].includes(ext)) return 'office'
  return 'other'
}

const getOfficeViewerUrl = (fileUrl) => `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(fileUrl)}`

const getFileIcon = (file) => {
  if (!file) return 'bi bi-file-earmark'
  const ext = file.split('.').pop().toLowerCase()
  const map = {
    pdf: 'bi bi-file-earmark-pdf',
    doc: 'bi bi-file-earmark-word',
    docx: 'bi bi-file-earmark-word',
    xls: 'bi bi-file-earmark-excel',
    xlsx: 'bi bi-file-earmark-excel',
    ppt: 'bi bi-file-earmark-ppt',
    pptx: 'bi bi-file-earmark-ppt',
    zip: 'bi bi-file-earmark-zip',
    rar: 'bi bi-file-earmark-zip',
    '7z': 'bi bi-file-earmark-zip'
  }
  return map[ext] || 'bi bi-file-earmark'
}

// ---------- 打开 / 关闭 / 翻页 ----------
const pauseMedia = () => {
  if (videoRef.value) videoRef.value.pause()
  if (audioRef.value) audioRef.value.pause()
}

const resetMediaState = () => {
  isPlaying.value = false
  currentTime.value = 0
  duration.value = 0
  buffered.value = 0
  menuOpen.value = false
}

const startPlayback = () => {
  nextTick(() => {
    checkPictureInPicture()
    const video = videoRef.value
    if (video) video.play().catch(() => {})
  })
}

const open = () => {
  const lastIndex = Math.max((props.files?.length || 1) - 1, 0)
  currentIndex.value = Math.min(Math.max(props.initialIndex || 0, 0), lastIndex)
  loadSavedSize()
  resetMediaState()
  visible.value = true
  document.body.style.overflow = 'hidden'
  startPlayback()
}

const close = () => {
  if (!visible.value) return
  pauseMedia()
  visible.value = false
  document.body.style.overflow = ''
  if (document.pictureInPictureElement) document.exitPictureInPicture().catch(() => {})
  isPip.value = false
  emit('close')
}

const onOverlayClick = () => close()

const stepTo = (index) => {
  if (index < 0 || index > props.files.length - 1 || index === currentIndex.value) return
  pauseMedia()
  currentIndex.value = index
  resetMediaState()
  startPlayback()
}

const prevFile = () => stepTo(currentIndex.value - 1)
const nextFile = () => stepTo(currentIndex.value + 1)

const downloadFile = () => {
  if (!currentFile.value) return
  const link = document.createElement('a')
  link.href = currentFileUrl.value
  link.download = currentFileName.value
  link.target = '_blank'
  link.rel = 'noopener'
  link.click()
}

// ---------- 键盘 ----------
const onKeyDown = (event) => {
  if (!visible.value) return
  switch (event.key) {
    case 'Escape':
      event.preventDefault()
      close()
      break
    case 'ArrowLeft':
      event.preventDefault()
      prevFile()
      break
    case 'ArrowRight':
      event.preventDefault()
      nextFile()
      break
    case ' ':
      if (currentFileType.value === 'video') {
        event.preventDefault()
        togglePlay()
      }
      break
    case 'f':
    case 'F':
      if (currentFileType.value === 'video') {
        event.preventDefault()
        toggleFullscreen()
      }
      break
    default:
      break
  }
}

// ---------- 视口变化收敛尺寸 ----------
const onViewportResize = () => {
  if (isFullscreen.value) return
  const clamped = clampSize(shellWidth.value, shellHeight.value)
  shellWidth.value = clamped.width
  shellHeight.value = clamped.height
  clampPosition(posX.value, posY.value)
}

const onDocumentClick = () => {
  if (menuOpen.value) menuOpen.value = false
}

// ---------- 生命周期 ----------
watch(() => props.files, () => {
  if (!visible.value) return
  const lastIndex = Math.max(props.files.length - 1, 0)
  if (currentIndex.value > lastIndex) currentIndex.value = lastIndex
})

onMounted(() => {
  document.addEventListener('keydown', onKeyDown)
  document.addEventListener('fullscreenchange', onFullscreenChange)
  document.addEventListener('webkitfullscreenchange', onFullscreenChange)
  document.addEventListener('click', onDocumentClick, true)
  window.addEventListener('resize', onViewportResize)
  window.addEventListener('orientationchange', onViewportResize)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('fullscreenchange', onFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
  document.removeEventListener('click', onDocumentClick, true)
  window.removeEventListener('resize', onViewportResize)
  window.removeEventListener('orientationchange', onViewportResize)
  onResizeEnd()
  document.body.style.overflow = ''
  document.body.classList.remove('fv-resizing')
})

defineExpose({ open, close })
</script>

<style scoped>
.fv-overlay {
  position: fixed;
  inset: 0;
  z-index: 100000;
  padding: 16px;
  background: rgba(0, 0, 0, 0.74);
}

.fv-shell {
  position: absolute;
  color: #fff;
  touch-action: pan-y;
}

.fv-window {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 14px;
  background: #000;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6);
}

/* ==================== 磨砂玻璃条 ==================== */
.fv-bar {
  position: absolute;
  left: 0;
  right: 0;
  z-index: 6;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  background: rgba(18, 18, 22, 0.55);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  backdrop-filter: blur(18px) saturate(160%);
}

.fv-topbar {
  top: 0;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.14);
}

.fv-bottombar {
  bottom: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.14);
}

.fv-bar-group {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ==================== 按钮 ==================== */
.fv-btn {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #fff;
  font-size: 1rem;
  line-height: 1;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
}

.fv-btn:hover {
  background: rgba(255, 255, 255, 0.16);
}

.fv-btn:active {
  background: rgba(255, 255, 255, 0.24);
}

.fv-btn.active {
  background: var(--primary-color);
}

.fv-btn.disabled,
.fv-btn:disabled {
  opacity: 0.28;
  pointer-events: none;
}

.fv-btn-close:hover {
  background: #e53935;
}

/* ==================== 内容区 ==================== */
.fv-stage {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #000;
}

.fv-image {
  max-width: 100%;
  max-height: 100%;
  width: auto;
  height: auto;
  object-fit: contain;
  display: block;
  user-select: none;
}

.fv-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
  display: block;
  cursor: pointer;
}

.fv-frame {
  width: 100%;
  height: 100%;
  border: none;
  display: block;
  background: #fff;
}

.fv-audio-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 22px;
  padding: 24px;
}

.fv-audio-icon {
  font-size: 4rem;
  opacity: 0.9;
}

.fv-audio {
  width: min(460px, 100%);
  height: 42px;
}

.fv-other {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 28px;
  text-align: center;
}

.fv-other-icon {
  font-size: 5rem;
  opacity: 0.85;
}

.fv-other-name {
  max-width: 90%;
  margin: 0;
  font-size: 1.05rem;
  word-break: break-all;
}

.fv-primary-btn {
  padding: 10px 22px;
  border: none;
  border-radius: 10px;
  background: var(--primary-color);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

/* ==================== 进度条 / 音量 ==================== */
.fv-time {
  flex: 0 0 auto;
  min-width: 74px;
  text-align: center;
  font-size: 0.8rem;
  font-variant-numeric: tabular-nums;
  opacity: 0.9;
}

.fv-seek {
  flex: 1 1 auto;
  min-width: 60px;
  height: 4px;
  margin: 0 4px;
  appearance: none;
  -webkit-appearance: none;
  border-radius: 999px;
  outline: none;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.16);
}

.fv-seek::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.35);
  cursor: pointer;
}

.fv-seek::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border: none;
  border-radius: 50%;
  background: #fff;
  cursor: pointer;
}

.fv-volume {
  flex: 0 0 auto;
  width: 64px;
  height: 4px;
  appearance: none;
  -webkit-appearance: none;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.28);
  outline: none;
  cursor: pointer;
}

.fv-volume::-webkit-slider-thumb {
  appearance: none;
  -webkit-appearance: none;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
}

.fv-volume::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border: none;
  border-radius: 50%;
  background: #fff;
}

.fv-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.86rem;
}

.fv-counter {
  flex: 0 0 auto;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 0.78rem;
}

/* ==================== 更多菜单 ==================== */
.fv-menu {
  position: absolute;
  right: 10px;
  bottom: 52px;
  z-index: 8;
  min-width: 140px;
  padding: 6px;
  border-radius: 10px;
  background: rgba(24, 24, 28, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.14);
  -webkit-backdrop-filter: blur(14px);
  backdrop-filter: blur(14px);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.45);
}

.fv-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border: none;
  border-radius: 7px;
  background: transparent;
  color: #fff;
  font-size: 0.86rem;
  text-align: left;
  cursor: pointer;
}

.fv-menu-item:hover {
  background: rgba(255, 255, 255, 0.14);
}

/* ==================== 缩放手柄 ==================== */
.fv-handle {
  position: absolute;
  z-index: 20;
  touch-action: none;
}

.handle-n { top: 0; left: 14px; right: 14px; height: 8px; cursor: ns-resize; }
.handle-s { bottom: 0; left: 14px; right: 14px; height: 8px; cursor: ns-resize; }
.handle-w { left: 0; top: 14px; bottom: 14px; width: 8px; cursor: ew-resize; }
.handle-e { right: 0; top: 14px; bottom: 14px; width: 8px; cursor: ew-resize; }
.handle-nw { top: 0; left: 0; width: 16px; height: 16px; cursor: nwse-resize; }
.handle-ne { top: 0; right: 0; width: 16px; height: 16px; cursor: nesw-resize; }
.handle-sw { bottom: 0; left: 0; width: 16px; height: 16px; cursor: nesw-resize; }
.handle-se {
  bottom: 0;
  right: 0;
  width: 22px;
  height: 22px;
  cursor: nwse-resize;
  background: linear-gradient(135deg, transparent 46%, rgba(255, 255, 255, 0.55) 47%, rgba(255, 255, 255, 0.55) 55%, transparent 56%);
}

.fv-resize-hint {
  position: absolute;
  right: 3px;
  bottom: 3px;
  z-index: 19;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  pointer-events: none;
}

/* 拖动缩放时禁止选中文本 */
:global(.fv-resizing) {
  user-select: none;
}

.is-fullscreen {
  left: 0 !important;
  top: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  max-width: none;
  max-height: none;
}

.is-fullscreen .fv-window {
  border-radius: 0;
}

/* ==================== 全屏/小屏适配 ==================== */
@media (max-width: 640px) {
  .fv-overlay { padding: 0; }
  .fv-volume { display: none; }
  .fv-time { min-width: 62px; font-size: 0.74rem; }
  .fv-btn { width: 30px; height: 30px; }
  .fv-handle { display: none; } /* 手机上用手势缩放，只留右下角 */
  .handle-se { display: block; }
}

@media (max-height: 480px) {
  .fv-bar { padding: 4px 8px; }
  .fv-btn { width: 28px; height: 28px; }
}
</style>
