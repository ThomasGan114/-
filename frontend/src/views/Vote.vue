<template>
  <div class="vote-page">
    <div class="container mt-4">
      <h1 class="page-title">投票</h1>
      <p class="page-desc">点击卡片上的红色（赞成）或蓝色（反对）即可投票；每个投票每台设备只能投一次。</p>

      <div v-if="loading" class="text-center py-5">
        <div class="spinner-border" role="status">
          <span class="visually-hidden">加载中...</span>
        </div>
      </div>

      <div v-else-if="loadError" class="alert alert-danger">{{ loadError }}</div>

      <div v-else-if="polls.length === 0" class="empty-box">
        <i class="bi bi-bar-chart"></i>
        <p>还没有投票，点右下角的「发起投票」发起第一个吧</p>
      </div>

      <div v-else class="poll-list">
        <PollCard
          v-for="poll in polls"
          :key="poll.id"
          :poll="poll"
          :pending="pendingId === poll.id"
          @vote="handleVote"
        />
      </div>

      <div v-if="actionError" class="alert alert-warning mt-3 mb-0">{{ actionError }}</div>
    </div>

    <!-- 右下角：发起投票 -->
    <button class="fab" type="button" @click="openCreate">
      <i class="bi bi-plus-lg"></i>
      <span>发起投票</span>
    </button>

    <!-- 发起投票小窗 -->
    <Modal
      :visible="showCreateModal"
      :show-close="false"
      :show-footer="true"
      @close="closeCreate"
      @update:visible="handleCreateModalUpdate"
    >
      <template #default>
        <div class="create-modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              <i class="bi bi-bar-chart me-2"></i>发起投票
            </h5>
          </div>
          <div class="modal-body">
            <textarea
              ref="titleInput"
              v-model="newTitle"
              class="poll-textarea"
              rows="4"
              :maxlength="TITLE_MAX_LENGTH"
              placeholder="输入投票内容（纯文本），例如：食堂是否应该延长晚餐供应时间？"
              @input="createError = ''"
              @keydown.ctrl.enter="handleCreate"
            ></textarea>
            <div class="counter">
              <span :class="{ 'near-limit': newTitle.length >= TITLE_MAX_LENGTH - 20 }">
                {{ newTitle.length }}/{{ TITLE_MAX_LENGTH }}
              </span>
            </div>
            <div v-if="createError" class="alert alert-danger mt-2 mb-0 py-2">{{ createError }}</div>
          </div>
        </div>
      </template>
      <template #footer>
        <button type="button" class="btn btn-secondary" @click="closeCreate">取消</button>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="creating || !newTitle.trim()"
          @click="handleCreate"
        >
          <span v-if="creating" class="spinner-border spinner-border-sm me-2"></span>
          {{ creating ? '发布中…' : '发布' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import PollCard from '../components/PollCard.vue'
import Modal from '../components/Modal.vue'
import { fetchPolls, createPoll, submitVote, TITLE_MAX_LENGTH } from '../services/polls'

const polls = ref([])
const loading = ref(true)
const loadError = ref('')
const actionError = ref('')
const pendingId = ref('')
let errorTimer = null

// 发起投票
const showCreateModal = ref(false)
const newTitle = ref('')
const createError = ref('')
const creating = ref(false)
const titleInput = ref(null)

const loadPolls = async () => {
  loading.value = true
  loadError.value = ''
  try {
    polls.value = await fetchPolls()
  } catch (error) {
    loadError.value = error.message || '加载投票失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const showActionError = (message) => {
  actionError.value = message
  if (errorTimer) clearTimeout(errorTimer)
  errorTimer = setTimeout(() => {
    actionError.value = ''
  }, 3000)
}

const handleVote = async (pollId, choice) => {
  if (pendingId.value) return
  pendingId.value = pollId
  actionError.value = ''
  try {
    const updated = await submitVote(pollId, choice)
    // 只替换这一条数据，不整页刷新
    polls.value = polls.value.map((poll) => (poll.id === pollId ? updated : poll))
  } catch (error) {
    showActionError(error.message || '投票失败，请稍后重试')
  } finally {
    pendingId.value = ''
  }
}

const openCreate = async () => {
  newTitle.value = ''
  createError.value = ''
  showCreateModal.value = true
  await nextTick()
  if (titleInput.value) {
    titleInput.value.focus()
  }
}

const closeCreate = () => {
  if (creating.value) return
  showCreateModal.value = false
}

const handleCreateModalUpdate = (value) => {
  showCreateModal.value = value
}

const handleCreate = async () => {
  if (creating.value) return
  const text = newTitle.value.trim()
  if (!text) {
    createError.value = '请输入投票内容'
    return
  }
  creating.value = true
  createError.value = ''
  try {
    const poll = await createPoll(text)
    polls.value = [poll, ...polls.value]
    showCreateModal.value = false
    newTitle.value = ''
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch (error) {
    createError.value = error.message || '发起投票失败，请稍后重试'
  } finally {
    creating.value = false
  }
}

onMounted(loadPolls)

onUnmounted(() => {
  if (errorTimer) clearTimeout(errorTimer)
})
</script>

<style scoped>
.vote-page {
  width: 100%;
  /* 给右下角的悬浮按钮留出空间 */
  padding-bottom: 96px;
}

.page-title {
  font-size: 1.6rem;
  font-weight: 700;
  margin-bottom: 6px;
  color: var(--text-primary, #333);
}

.page-desc {
  font-size: 0.9rem;
  margin-bottom: 20px;
  color: var(--text-secondary, #666);
}

.poll-list {
  display: flex;
  flex-direction: column;
}

/* 空状态 */
.empty-box {
  padding: 48px 20px;
  text-align: center;
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  color: var(--text-secondary, #666);
}

.empty-box i {
  display: block;
  margin-bottom: 12px;
  font-size: 2.4rem;
  color: var(--primary-color, #ff0073);
}

.empty-box p {
  margin: 0;
  font-size: 0.95rem;
}

/* 右下角悬浮按钮（与校园墙页面的 FAB 同款配色/阴影） */
.fab {
  position: fixed;
  right: 20px;
  bottom: 20px;
  z-index: 1000;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 56px;
  padding: 0 22px;
  border: none;
  border-radius: 28px;
  background: var(--primary-color, #ff0073);
  color: #ffffff;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(255, 0, 115, 0.4);
  transition: background-color 0.3s, transform 0.3s, box-shadow 0.3s;
}

.fab i {
  font-size: 1.15rem;
}

.fab:hover {
  background: var(--primary-dark, #cc005c);
  transform: translateY(-3px) scale(1.03);
  box-shadow: 0 6px 25px rgba(255, 0, 115, 0.5);
}

.fab:active {
  transform: translateY(-1px) scale(1);
}

/* 发起投票弹窗 */
.create-modal-content {
  display: flex;
  flex-direction: column;
  border-radius: 16px;
}

.create-modal-content .modal-header {
  background: var(--card-bg, white);
  padding: 16px 20px;
}

.create-modal-content .modal-title {
  margin: 0;
  color: var(--primary-color);
  font-weight: 600;
  font-size: 1.2rem;
}

.create-modal-content .modal-body {
  background: var(--card-bg, white);
  padding: 20px;
}

.poll-textarea {
  width: 100%;
  padding: 16px;
  border: 2px solid var(--border-color, #e0e0e0);
  border-radius: 10px;
  font-size: 1rem;
  line-height: 1.6;
  resize: none;
  background: var(--input-bg, #f5f5f5);
  color: var(--text-primary, #333);
  transition: border-color 0.3s;
}

.poll-textarea:focus {
  outline: none;
  border-color: var(--primary-color);
}

.counter {
  margin-top: 6px;
  text-align: right;
  font-size: 0.8rem;
  color: var(--text-secondary, #999);
}

.counter .near-limit {
  color: #e53935;
}

.btn-primary {
  background: var(--primary-color);
  border-color: var(--primary-color);
}

.btn-primary:hover {
  background: var(--primary-dark);
  border-color: var(--primary-dark);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

@media (max-width: 576px) {
  .fab {
    width: 56px;
    padding: 0;
    justify-content: center;
    border-radius: 50%;
  }

  .fab span {
    display: none;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fab {
    transition: none;
  }
}
</style>
