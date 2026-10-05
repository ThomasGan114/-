<template>
  <div class="poll-card" :class="{ 'is-locked': locked }">
    <!-- 顶部：标题 + 右上角参与人数 -->
    <div class="poll-head">
      <p class="poll-title">{{ poll.title }}</p>
      <span class="poll-participants">已有 {{ total }} 人参与</span>
    </div>

    <!-- 中间：红（赞成）/ 蓝（反对）水平进度条，两段本身就是投票按钮 -->
    <div class="poll-bar">
      <button
        type="button"
        class="bar-seg bar-approve"
        :class="{ 'is-chosen': poll.myVote === 'approve' }"
        :style="{ width: approveWidth + '%' }"
        :disabled="locked || pending"
        :aria-label="`赞成 ${approvePct}%`"
        @click="choose('approve')"
      >
        <span v-if="approveInner" class="seg-label">
          <i v-if="poll.myVote === 'approve'" class="bi bi-check-lg"></i>
          赞成 ({{ approvePct }}%)
        </span>
      </button>

      <button
        type="button"
        class="bar-seg bar-oppose"
        :class="{ 'is-chosen': poll.myVote === 'oppose' }"
        :style="{ width: opposeWidth + '%' }"
        :disabled="locked || pending"
        :aria-label="`反对 ${opposePct}%`"
        @click="choose('oppose')"
      >
        <span v-if="opposeInner" class="seg-label">
          反对 ({{ opposePct }}%)
          <i v-if="poll.myVote === 'oppose'" class="bi bi-check-lg"></i>
        </span>
      </button>
    </div>

    <!-- 某一段太窄放不下文字时，把它的百分比放到条外侧，保证始终可读 -->
    <div v-if="!approveInner || !opposeInner" class="bar-outside">
      <span v-if="!approveInner" class="outside-label outside-approve">赞成 {{ approvePct }}%</span>
      <span v-if="!opposeInner" class="outside-label outside-oppose">反对 {{ opposePct }}%</span>
    </div>

    <!-- 底部状态提示 -->
    <div class="poll-foot">
      <span v-if="poll.ended" class="foot-ended">
        <i class="bi bi-lock"></i> 该投票已结束
      </span>
      <span v-else-if="poll.myVote" class="foot-mine">
        <i class="bi bi-check-circle"></i> 你已投「{{ poll.myVote === 'approve' ? '赞成' : '反对' }}」，每台设备只能投一次
      </span>
      <span v-else class="foot-hint">点击左侧红色投赞成，右侧蓝色投反对</span>
      <span v-if="pending" class="foot-pending">提交中…</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  poll: { type: Object, required: true },
  pending: { type: Boolean, default: false }
})

const emit = defineEmits(['vote'])

const total = computed(() => (props.poll.approve || 0) + (props.poll.oppose || 0))
const approvePct = computed(() => (total.value ? Math.round((props.poll.approve / total.value) * 100) : 0))
const opposePct = computed(() => (total.value ? 100 - approvePct.value : 0))

// 还没有人投票时两段各占一半（否则 0% 宽度点不到），标签仍显示 0%
const approveWidth = computed(() => (total.value ? approvePct.value : 50))
const opposeWidth = computed(() => (total.value ? opposePct.value : 50))

// 段宽小于 18% 时条内放不下文字，改到条外显示
const approveInner = computed(() => approveWidth.value >= 18)
const opposeInner = computed(() => opposeWidth.value >= 18)

const locked = computed(() => !!props.poll.myVote || !!props.poll.ended)

const choose = (choice) => {
  if (locked.value || props.pending) return
  emit('vote', props.poll.id, choice)
}
</script>

<style scoped>
.poll-card {
  background: var(--card-bg, #ffffff);
  border: 1px solid var(--border-color, #e0e0e0);
  border-radius: 14px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.06);
  padding: 18px 20px 14px;
  margin-bottom: 18px;
  transition: box-shadow 0.3s, border-color 0.3s;
}

.poll-card:hover {
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
}

/* 顶部 */
.poll-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 14px;
}

.poll-title {
  flex: 1;
  margin: 0;
  font-size: 1.05rem;
  font-weight: 600;
  line-height: 1.6;
  color: var(--text-primary, #333);
  white-space: pre-wrap;
  word-break: break-word;
}

.poll-participants {
  flex: none;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
  color: var(--text-secondary, #666);
  background: var(--hover-bg, rgba(255, 0, 115, 0.05));
  white-space: nowrap;
}

/* 进度条（两段即按钮） */
.poll-bar {
  display: flex;
  width: 100%;
  height: 44px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--card-secondary-bg, #f5f5f5);
}

.bar-seg {
  min-width: 0;
  padding: 0 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  font-size: 0.92rem;
  font-weight: 600;
  color: #ffffff;
  white-space: nowrap;
  overflow: hidden;
  cursor: pointer;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1),
              filter 0.2s,
              opacity 0.3s,
              box-shadow 0.3s;
}

.bar-approve {
  background: #e53935;
}

.bar-oppose {
  background: #1e88e5;
}

.bar-seg:disabled {
  cursor: default;
}

.bar-seg:not(:disabled):hover {
  filter: brightness(1.08);
}

.bar-seg:not(:disabled):active {
  filter: brightness(0.95);
}

/* 已投票 / 已结束：未选中的一侧压暗，选中的一侧加白色描边高亮 */
.is-locked .bar-seg:not(.is-chosen) {
  opacity: 0.78;
}

.bar-seg.is-chosen {
  box-shadow: inset 0 0 0 3px rgba(255, 255, 255, 0.9);
}

.seg-label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

/* 条外侧百分比（段太窄时使用） */
.bar-outside {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 0.85rem;
  font-weight: 600;
}

.outside-approve {
  color: #e53935;
}

.outside-oppose {
  color: #1e88e5;
  margin-left: auto;
}

/* 底部提示 */
.poll-foot {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  font-size: 0.82rem;
  color: var(--text-secondary, #666);
}

.foot-mine {
  color: var(--primary-color, #ff0073);
}

.foot-pending {
  color: var(--text-secondary, #999);
}

@media (prefers-reduced-motion: reduce) {
  .bar-seg {
    transition: none;
  }
}
</style>
