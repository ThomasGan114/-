/**
 * 投票数据层（预留接口）
 *
 * 后端目前还没有投票接口，所以数据先存在浏览器 localStorage 里：
 *   poll_items  已发起的投票列表（用户发起，本地持久化）
 *   poll_votes  本设备投过的票（pollId -> 'approve' | 'oppose'）
 *   voter_id    设备级匿名标识，将来作为 voter_id / creator_id 提交给后端
 *
 * 页面组件只依赖本文件的 fetchPolls / createPoll / submitVote。
 * 后端就绪后按下面的约定实现接口，再把 USE_REMOTE_API 改成 true 即可，页面代码无需改动：
 *   GET  /api/polls            -> { success: true, polls: [{ id, title, approve, oppose, createdAt, ended }] }
 *   POST /api/polls            -> { success: true, poll: { ...同上... } }   请求体 { title, creator_id }
 *   POST /api/polls/{id}/vote  -> { success: true, poll: { ...同上... } }   请求体 { choice, voter_id }
 */
import api from './api'

const USE_REMOTE_API = false

const LIST_KEY = 'poll_items'
const VOTER_KEY = 'voter_id'
const VOTES_KEY = 'poll_votes'

/** 投票内容长度上限（纯文本） */
export const TITLE_MAX_LENGTH = 200

const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const readJSON = (key, fallback) => {
  try {
    const value = JSON.parse(localStorage.getItem(key))
    return value === null || value === undefined ? fallback : value
  } catch (e) {
    return fallback
  }
}

const writeJSON = (key, value) => {
  localStorage.setItem(key, JSON.stringify(value))
}

const randomId = () => ((window.crypto && window.crypto.randomUUID)
  ? window.crypto.randomUUID()
  : `id-${Date.now()}-${Math.random().toString(16).slice(2)}`)

const formatNow = () => {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} `
    + `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

/** 设备级匿名身份：将来作为 voter_id / creator_id 提交给后端做防重复 */
export const getVoterId = () => {
  let id = localStorage.getItem(VOTER_KEY)
  if (!id) {
    id = randomId()
    localStorage.setItem(VOTER_KEY, id)
  }
  return id
}

const readPolls = () => {
  const list = readJSON(LIST_KEY, [])
  return Array.isArray(list) ? list : []
}

const writePolls = (list) => writeJSON(LIST_KEY, list)

const readVotes = () => readJSON(VOTES_KEY, {}) || {}

const writeVotes = (votes) => writeJSON(VOTES_KEY, votes)

/**
 * 把本地那一票叠加到票数上。
 * 幂等：刷新页面不会重复累加，因为叠加的是「本地记录的那一票」而不是每次都 +1。
 */
const attachMyVote = (poll, myVote) => ({
  id: poll.id,
  title: poll.title,
  approve: (poll.approve || 0) + (myVote === 'approve' ? 1 : 0),
  oppose: (poll.oppose || 0) + (myVote === 'oppose' ? 1 : 0),
  createdAt: poll.createdAt || '',
  ended: !!poll.ended,
  myVote: myVote || null
})

/** 拉取投票列表（含当前设备的投票状态） */
export async function fetchPolls() {
  const votes = readVotes()

  if (USE_REMOTE_API) {
    const res = await api.getPolls()
    const list = (res.data && res.data.polls) || []
    return list.map((poll) => attachMyVote(poll, votes[poll.id]))
  }

  await delay(150)
  return readPolls().map((poll) => attachMyVote(poll, votes[poll.id]))
}

/** 发起投票：纯文本内容，票数从 0 开始；成功返回新建的投票对象 */
export async function createPoll(title) {
  const text = (title || '').trim()
  if (!text) {
    throw new Error('请输入投票内容')
  }
  if (text.length > TITLE_MAX_LENGTH) {
    throw new Error(`投票内容不能超过 ${TITLE_MAX_LENGTH} 字`)
  }

  let created
  if (USE_REMOTE_API) {
    const res = await api.createPoll({ title: text, creator_id: getVoterId() })
    created = (res.data && res.data.poll) || null
    if (!created) {
      throw new Error('发起投票失败，请稍后重试')
    }
  } else {
    await delay(150)
    created = {
      id: randomId(),
      title: text,
      approve: 0,
      oppose: 0,
      createdAt: formatNow(),
      ended: false
    }
  }

  const list = readPolls()
  list.unshift(created)
  writePolls(list)
  return attachMyVote(created, null)
}

/** 提交一票，成功返回更新后的投票对象，失败抛出可直接展示的错误信息 */
export async function submitVote(pollId, choice) {
  if (choice !== 'approve' && choice !== 'oppose') {
    throw new Error('无效的投票选项')
  }

  const votes = readVotes()
  if (votes[pollId]) {
    throw new Error('你已经投过票了')
  }

  const list = readPolls()
  const poll = list.find((item) => item.id === pollId)
  if (!poll) {
    throw new Error('投票不存在')
  }

  let updated = poll
  if (USE_REMOTE_API) {
    const res = await api.submitVote(pollId, { choice, voter_id: getVoterId() })
    updated = (res.data && res.data.poll) || poll
  } else {
    await delay(150)
    if (poll.ended) {
      throw new Error('该投票已结束')
    }
  }

  votes[pollId] = choice
  writeVotes(votes)
  return attachMyVote(updated, choice)
}
