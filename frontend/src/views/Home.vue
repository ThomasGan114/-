<template>
  <div class="home-page">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-text">
          <h1 class="hero-title">欢迎来到</h1>
          <h2 class="hero-subtitle">深圳市高级中学高中园</h2>
          <h3 class="hero-subtitle-light">校园墙</h3>
          <div class="run-time">
            <span class="run-time-label">本站已运行</span>
            <span class="run-time-value">{{ runTime.days }}</span>天
            <span class="run-time-value">{{ runTime.hours }}</span>小时
            <span class="run-time-value">{{ runTime.minutes }}</span>分钟
            <span class="run-time-value">{{ runTime.seconds }}</span>秒
          </div>
          <router-link to="/wall" class="hero-button">
            <i class="bi bi-arrow-right-circle me-2"></i>
            前往深高园校园墙
          </router-link>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2>功能特色</h2>
        <p>让校园墙再次伟大!</p>
      </div>
      <div class="features-grid g-4">

          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-speedometer2"></i>
            </div>
            <h3>即刻发表</h3>
            <p>只需一步，轻松完成发言！无需等待，快速分享你的心声。</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-heart-fill"></i>
            </div>
            <h3>互动交流</h3>
            <p>点赞、评论、分享，与同学们实时互动，畅所欲言。</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-cloud-upload"></i>
            </div>
            <h3>多媒体支持</h3>
            <p>支持图片、视频、音频等多种格式，让你的表达更生动。</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">
              <i class="bi bi-shield-check"></i>
            </div>
            <h3>安全可靠</h3>
            <p>完善的管理系统，确保平台安全，营造良好的交流环境。</p>
          </div>
        </div>
    </section>

    <!-- Quick Post Section -->
    <section class="quick-post-section">
      <div class="section-header">
        <h2>快速留言</h2>
        <p>发出你的第一条消息</p>
      </div>
      <div class="quick-post-card">
        <form @submit.prevent="handleQuickSubmit">
          <textarea
            v-model="quickText"
            class="quick-post-input"
            placeholder="想说什么就说什么..."
            rows="4"
          ></textarea>
          <button type="submit" class="btn-submit">
            <i class="bi bi-send me-2"></i>
            发布留言
          </button>
        </form>
      </div>
    </section>

    <!-- Hot Messages Section -->
    <section class="hot-messages-section">
      <div class="section-header">
        <h2>热门留言</h2>
        <p>看看大家在讨论什么</p>
      </div>
      <div v-if="loading" class="loading-state">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
      </div>
      <div v-else-if="hotMessages.length === 0" class="empty-state">
        <i class="bi bi-inbox"></i>
        <p>暂无热门留言</p>
      </div>
      <div v-else class="hot-messages-grid">
        <div v-for="message in hotMessages" :key="message.id" class="message-card">
          <router-link :to="`/wall/message/${message.id}`" class="message-link">
            <p class="message-text">{{ message.text }}</p>
            <div class="message-footer">
              <span class="message-time">{{ formatTime(message.timestamp) }}</span>
              <div class="message-stats">
                <span><i class="bi bi-hand-thumbs-up"></i> {{ message.likes }}</span>
                <span><i class="bi bi-chat"></i> {{ message.comments?.length || 0 }}</span>
              </div>
            </div>
          </router-link>
        </div>
      </div>
    </section>

    <!-- About Section -->
    <section class="about-section">
      <div class="about-content">
        <h2>关于本站</h2>
        <p>本站由龙高一名学生编写 深高园一名学生搭建，旨在为同学们提供一个快捷自由表达的平台。</p>
        <div class="about-links">
          <a href="https://github.com/renzhen666666/campusWall" target="_blank" rel="noopener">
            <i class="bi bi-github"></i>
            GitHub
          </a>
          <button
            type="button"
            class="contact-btn"
            :class="{ 'is-open': showEmail }"
            :style="contactWidth ? { width: contactWidth } : null"
            :aria-expanded="showEmail ? 'true' : 'false'"
            aria-label="联系站长"
            :title="showEmail ? '再点一下收起' : '点击显示站长邮箱'"
            ref="contactBtn"
            @click="toggleContact"
          >
            <span class="contact-face contact-face-label" ref="contactLabel">
              <i class="bi bi-envelope"></i>
              <span>联系站长</span>
            </span>
            <span class="contact-face contact-face-email" ref="contactEmailEl">
              <i class="bi bi-envelope-open"></i>
              <span>{{ contactEmail }}</span>
            </span>
          </button>
        </div>
      </div>
    </section>

    <!-- 免责声明 -->
    <section class="disclaimer-section">
      <div class="disclaimer-content">
        <h2>免责声明</h2>
        <p class="disclaimer-intro">
          欢迎使用本校园墙网站（以下简称“本站”）。为保障平台正常运行并明确各方权利义务，请您在使用前仔细阅读以下免责声明。使用本站即视为您已充分理解并同意本声明全部内容。
        </p>

        <h3>一、平台性质</h3>
        <p>本站仅作为校园信息交流与分享的中立平台，提供匿名或实名发布、浏览、互动等技术服务。本站不对用户发布的任何内容进行实质性审核或背书，也不对内容的真实性、准确性、完整性、合法性承担任何保证或连带责任。</p>

        <h3>二、用户责任</h3>
        <p>用户应对其发布的所有内容（包括但不限于文字、图片、链接、评论等）独立承担全部法律责任。</p>
        <p>用户不得发布违反国家法律法规、公序良俗、校园规章制度的内容，包括但不限于：</p>
        <ul>
          <li>危害国家安全、煽动颠覆国家政权、宣扬恐怖主义、极端主义的信息；</li>
          <li>侮辱、诽谤、造谣、侵犯他人名誉权、肖像权、隐私权、知识产权等合法权益的内容；</li>
          <li>色情、暴力、赌博、毒品、诈骗等违法违规信息；</li>
          <li>涉及人身攻击、恶意举报、散布谣言、扰乱校园秩序的内容。</li>
        </ul>
        <p>因用户发布内容引发的任何纠纷、投诉、诉讼或损失，均由发布者自行承担，本站不承担任何责任。</p>

        <h3>三、内容管理与处理</h3>
        <p>本站有权（但无义务）对涉嫌违规的内容进行删除、屏蔽、限制展示或封禁账号等处理，且无需事先通知。</p>
        <p>本站不对内容删除后的任何后果（包括数据丢失、影响等）承担责任。</p>
        <p>用户发现侵权或违规内容，可通过本站「联系站长」入口反馈，本站将在合理范围内予以处理，但不保证处理结果或时效。</p>

        <h3>四、知识产权与授权</h3>
        <p>用户发布内容即视为授予本站在全球范围内、免费、非独家、可转授权的使用权（包括展示、存储、复制、传播等），用于平台运营及必要的推广。</p>
        <p>用户应保证其发布内容不侵犯第三方知识产权，否则由此产生的全部责任由用户自行承担。</p>

        <h3>五、隐私与匿名</h3>
        <p>本站尽力保护用户隐私，但因技术限制、系统故障、第三方攻击或用户自身操作等原因导致的信息泄露，本站不承担责任。</p>
        <p>匿名发布并不意味着绝对匿名。在配合有权机关依法调查或处理严重违规行为时，本站可能依法提供必要信息。</p>

        <h3>六、服务可用性与免责</h3>
        <p>本站不保证服务的持续、稳定、无中断运行，因系统维护、升级、不可抗力、网络故障等原因导致的服务中断或数据丢失，本站不承担责任。</p>
        <p>本站不对通过本站获取的任何信息、建议、链接等内容的适用性或后果承担责任。用户应自行判断并承担使用风险。</p>
        <p>在法律允许的最大范围内，本站对因使用或无法使用本站服务而产生的任何直接、间接、附带、惩罚性损失不承担责任。</p>

        <h3>七、其他</h3>
        <p>本声明的解释权、修改权归本站所有。本站有权根据法律法规变化或运营需要随时更新本声明，更新后将在本站公示，继续使用即视为接受更新内容。</p>
        <p>本声明未尽事宜，适用中华人民共和国相关法律法规。因本声明或本站服务产生的争议，由本站所在地有管辖权的人民法院管辖。</p>
        <p>如本声明任何条款被认定为无效或不可执行，不影响其他条款的效力。</p>

        <p class="disclaimer-note">
          特别提示：请理性发言、文明互动，共同维护健康的校园交流环境。若您不同意本声明任何内容，请立即停止使用本站服务。
        </p>
      </div>
    </section>

    <!-- Notice Modal -->
    <div class="modal fade" id="noticeModal" tabindex="-1" aria-labelledby="noticeModalLabel" aria-hidden="true" ref="noticeModal">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="noticeModalLabel">
              <i class="bi bi-megaphone me-2"></i>公告
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            <div v-if="noticeContent" v-html="noticeContent"></div>
            <div v-else class="text-muted">暂无公告</div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-primary" data-bs-dismiss="modal">知道了</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Modal } from 'bootstrap'
import api from '../services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

const runTime = ref({
  days: 0,
  hours: 0,
  minutes: 0,
  seconds: 0
})

const hotMessages = ref([])
const loading = ref(true)
const quickText = ref('')
const noticeContent = ref('')
const noticeModal = ref(null)

let runTimeInterval = null

const updateRunTime = () => {
  // 计时起点（2026-10-04 22:48:39 重置，从零开始）
  const startDate = new Date(2026,9,4,22,48,39);
  const now = new Date()
  const diff = now - startDate
  runTime.value.days = Math.floor(diff / (1000 * 60 * 60 * 24))
  runTime.value.hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  runTime.value.minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  runTime.value.seconds = Math.floor((diff % (1000 * 60)) / 1000)
}

const loadHotMessages = async () => {
  try {
    const response = await api.getHotMessages()
    if (response.data.success) {
      hotMessages.value = response.data.messages || []
    }
  } catch (error) {
    console.error('加载热门留言失败:', error)
  } finally {
    loading.value = false
  }
}

const handleQuickSubmit = async () => {
  if (!quickText.value.trim()) {
    alert('请输入内容')
    return
  }
  try {
    await api.submitMessage({
      text: quickText.value,
      tags: [],
      filenames: []
    })
    quickText.value = ''
    alert('提交成功!')
    loadHotMessages()
  } catch (error) {
    console.error('提交失败:', error)
    alert('提交失败: ' + (error.response?.data?.error || '未知错误'))
  }
}

const loadNotice = async () => {
  try {
    const response = await api.getNotice()
    if (response.data.success) {
      noticeContent.value = response.data.content
    }
  } catch (error) {
    console.error('加载公告失败:', error)
  }
}

const showNoticeModal = () => {
  const today = new Date()
  const month = today.getFullYear() + '-' + (today.getMonth() + 1)
  const hasVisited = localStorage.getItem('hasVisitedWall' + month)
  if (!hasVisited && noticeContent.value && noticeModal.value) {
    const modal = new Modal(noticeModal.value)
    modal.show()
    localStorage.setItem('hasVisitedWall' + month, 'true')
  }
}

const formatTime = (time) => {
  return dayjs(time).fromNow()
}

// 「联系站长」：点一下展开邮箱，再点还原；按钮宽度随文案平滑拉伸
const contactEmail = ref('thomasgan@126.com')
const showEmail = ref(false)
const contactWidth = ref('')
const contactBtn = ref(null)
const contactLabel = ref(null)
const contactEmailEl = ref(null)

const measureContactWidth = () => {
  if (!contactBtn.value || !contactLabel.value || !contactEmailEl.value) return
  const styles = getComputedStyle(contactBtn.value)
  const padding = (parseFloat(styles.paddingLeft) || 0) + (parseFloat(styles.paddingRight) || 0)
  const target = showEmail.value ? contactEmailEl.value : contactLabel.value
  contactWidth.value = `${Math.ceil(target.getBoundingClientRect().width + padding)}px`
}

const toggleContact = () => {
  showEmail.value = !showEmail.value
  measureContactWidth()
}

onMounted(() => {
  updateRunTime()
  runTimeInterval = setInterval(updateRunTime, 1000)
  loadHotMessages()
  loadNotice()
  showNoticeModal()

  measureContactWidth()
  window.addEventListener('resize', measureContactWidth)
  if (document.fonts && document.fonts.ready) {
    document.fonts.ready.then(measureContactWidth)
  }
})

onUnmounted(() => {
  if (runTimeInterval) {
    clearInterval(runTimeInterval)
  }
  window.removeEventListener('resize', measureContactWidth)
})
</script>

<style scoped>
.home-page {
  width: 100%;
  gap:10px;
}

:root {
  --primary-color: #FF0073;
  --primary-light: rgba(255, 0, 115, 0.1);
  --primary-dark: #CC005C;
}

/* Hero Section */
.hero-section {
  background: linear-gradient(45deg, var(--primary-color),var(--primary-dark));
  padding: 80px 0;
  text-align: center;
  color: white;

  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-text {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.hero-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.hero-subtitle {
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.hero-subtitle-light {
  font-size: 1.75rem;
  font-weight: 400;
  margin-bottom: 2rem;
}

.run-time {
  font-size: 1.1rem;
  margin-bottom: 2rem;
  padding: 15px 25px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50px;
  display: inline-block;
  backdrop-filter: blur(10px);
}

.run-time-label {
  margin-right: 10px;
}

.run-time-value {
  font-weight: 700;
  color: #ffd700;
  margin: 0 5px;
}

.hero-button {
  display: inline-flex;
  align-items: center;
  padding: 15px 40px;
  background: white;
  color: var(--primary-color);
  text-decoration: none;
  border-radius: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  transition: all 0.3s;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.hero-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
}

/* Sections */
section {
  padding: 60px 0;
  border-radius: 16px;
}

.section-header {
  text-align: center;
  margin-bottom: 40px;
}

.section-header h2 {
  font-size: 2rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.section-header p {
  color: #666;
  font-size: 1.1rem;
}

/* Features Section */
.features-section {
  background: transparent;
}

.features-grid {
  display:flex;
  flex-wrap: wrap;
  justify-content: space-between;

  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}


.feature-card {
  background: var(--card-bg);
  border-radius: 15px;
  text-align: center;
  transition: all 0.3s;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);

  padding: 15px 5px;
  max-width: 200px;
}


.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(255, 0, 115, 0.15);
}

.feature-icon {
  width: 80px;
  height: 80px;
  margin: 0 auto 10px;
  background: var(--primary-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  color: var(--primary-color);
}

.feature-card h3 {
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 15px;
  color: var(--text-primary);
}

.feature-card p {
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Quick Post Section */
.quick-post-section {
  background: transparent;
}

.quick-post-card {
  max-width: 800px;
  margin: 0 auto;
  background: var(--card-bg, #f5f5f5);
  padding: 40px;
  border-radius: 15px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.quick-post-input {
  width: 100%;
  padding: 15px;
  border: 2px solid var(--border-color, #e0e0e0);
  border-radius: 10px;
  font-size: 1rem;
  resize: none;
  margin-bottom: 20px;
  transition: border-color 0.3s;
}

.quick-post-input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.btn-submit {
  width: 100%;
  padding: 15px;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-submit:hover {
  background: var(--primary-dark);
  transform: translateY(-2px);
}

/* Hot Messages Section */
.hot-messages-section {
  background: var(--bg-color, #f5f5f5);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #999;
}

.empty-state i {
  font-size: 4rem;
  display: block;
  margin-bottom: 20px;
}

.hot-messages-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.message-card {
  background: var(--card-bg);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
}

.message-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.message-link {
  display: block;
  padding: 20px;
  text-decoration: none;
  color: inherit;
}

.message-text {
  margin: 0 0 15px;
  color: var(--text-primary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.message-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.message-time {
  font-size: 0.875rem;
  color: #999;
}

.message-stats {
  display: flex;
  gap: 15px;
  font-size: 0.875rem;
  color: #666;
}

.message-stats i {
  margin-right: 5px;
}

/* About Section */
.about-section {
  background: var(--primary-color);
  color: white;
  text-align: center;
}

.about-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px;
}

.about-content h2 {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 20px;
}

.about-content > p {
  font-size: 1.1rem;
  line-height: 1.8;
  margin-bottom: 30px;
}

.about-links {
  display: flex;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
}

.about-links a,
.contact-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 25px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  text-decoration: none;
  border-radius: 50px;
  backdrop-filter: blur(10px);
  transition: background-color 0.3s, transform 0.3s;
}

.about-links a:hover,
.contact-btn:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

/* 免责声明 */
.disclaimer-section {
  background: #ffffff;
}

.disclaimer-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 20px;
  color: #444444;
  font-size: 0.95rem;
  line-height: 1.9;
  text-align: left;
}

.disclaimer-content h2 {
  margin-bottom: 16px;
  font-size: 1.75rem;
  font-weight: 700;
  color: #333333;
  text-align: center;
}

.disclaimer-intro {
  color: #555555;
}

.disclaimer-content h3 {
  margin: 22px 0 8px;
  font-size: 1.05rem;
  font-weight: 600;
  color: #333333;
}

.disclaimer-content p {
  margin: 0 0 8px;
}

.disclaimer-content ul {
  margin: 0 0 8px;
  padding-left: 22px;
}

.disclaimer-content li {
  margin-bottom: 4px;
}

.disclaimer-content p.disclaimer-note {
  margin: 22px 0 0;
  padding: 12px 16px;
  border-left: 4px solid var(--primary-color, #ff0073);
  border-radius: 8px;
  background: rgba(255, 0, 115, 0.06);
  color: #333333;
  font-weight: 500;
}

/* 「联系站长」按钮：点击展开邮箱，宽度随文案平滑拉伸 */
.contact-btn {
  position: relative;
  justify-content: center;
  overflow: hidden;
  white-space: nowrap;
  border: none;
  font: inherit;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: width 0.42s cubic-bezier(0.4, 0, 0.2, 1),
              background-color 0.3s,
              transform 0.3s;
}

.contact-face {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  flex: none;
  white-space: nowrap;
  transition: opacity 0.28s ease, transform 0.42s cubic-bezier(0.4, 0, 0.2, 1);
}

.contact-face-label {
  opacity: 1;
  transform: translateX(0);
}

.contact-face-email {
  position: absolute;
  left: 50%;
  top: 50%;
  opacity: 0;
  transform: translate(-50%, -50%) translateX(-16px);
}

.contact-btn.is-open .contact-face-label {
  opacity: 0;
  transform: translateX(16px);
}

.contact-btn.is-open .contact-face-email {
  opacity: 1;
  transform: translate(-50%, -50%) translateX(0);
}

@media (prefers-reduced-motion: reduce) {
  .contact-btn,
  .contact-face {
    transition-duration: 0.01ms;
  }
}

/* Modal */
.modal-content {
  border-radius: 15px;
  border: none;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  background: var(--primary-light);
  border-bottom: 1px solid rgba(255, 0, 115, 0.1);
}

.modal-title {
  color: var(--primary-color);
  font-weight: 600;
}

.btn-primary {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.btn-primary:hover {
  background: var(--primary-dark);
  border-color: var(--primary-dark);
}

/* Responsive */
@media (max-width: 400px) {
  section {
    border-radius: 25px;
  }
  .hero-section {
    height: auto;
    padding-top: 50px;
    padding-bottom: 50px;
  }
  .hero-content {
    row-gap: 15px;
  }
  .hero-text {
    row-gap: 5px;
  }
  .features-grid {
    row-gap: 10px;
    padding: 0 10px;
  }
  .feature-card {
    width: 45%;
  }
}


@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }

  .hero-subtitle {
    font-size: 1.5rem;
  }

  .hero-subtitle-light {
    font-size: 1.25rem;
  }

  .run-time {
    font-size: 0.9rem;
    padding: 10px 15px;
  }

  .hero-button {
    padding: 12px 30px;
    font-size: 1rem;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .hot-messages-grid {
    grid-template-columns: 1fr;
  }

  .about-links {
    flex-direction: column;
    align-items: center;
  }
  .feature-card {
    width: 45%;
  }
}




@media (min-width: 993px) {
  section {
    border-radius: 16px;
  }
}
</style>