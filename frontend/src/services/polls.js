/**
 * 投票数据层（对接后端 /api/polls）
 *
 * 数据存在服务器上（backend/polls.json），所有访客看到同一份投票与票数。
 * 防重复：前端在 localStorage 里保存一个设备级匿名标识 voter_id，随请求提交，
 * 后端按 voter_id 去重 —— 同一设备同一投票只能投一次。
 *
 * 接口：
 *   GET  /api/polls?voter_id=xxx        列表（含该设备投过什么）
 *   POST /api/polls                     发起投票  body: { title, creator_id }
 *   POST /api/polls/{id}/vote           投票      body: { choice, voter_id }
 */
import api from './api'

const VOTER_KEY = 'voter_id'

/** 投票内容长度上限（纯文本，与后端保持一致） */
export const TITLE_MAX_LENGTH = 200

const randomId = () => ((window.crypto && window.crypto.randomUUID)
  ? window.crypto.randomUUID()
  : `id-${Date.now()}-${Math.random().toString(16).slice(2)}`)

/** 设备级匿名身份：后端据此判断「这台设备是否已投过」 */
export const getVoterId = () => {
  let id = localStorage.getItem(VOTER_KEY)
  if (!id) {
    id = randomId()
    localStorage.setItem(VOTER_KEY, id)
  }
  return id
}

/** 统一整理后端返回的投票对象 */
const normalize = (poll) => ({
  id: poll.id,
  title: poll.title,
  approve: poll.approve || 0,
  oppose: poll.oppose || 0,
  createdAt: poll.createdAt || '',
  ended: !!poll.ended,
  myVote: poll.myVote || null
})

const pickPoll = (data) => {
  if (!data || !data.success || !data.poll) {
    throw new Error((data && data.error) || '操作失败，请稍后重试')
  }
  return normalize(data.poll)
}

/** 拉取投票列表 */
export async function fetchPolls() {
  const res = await api.getPolls(getVoterId())
  const list = (res.data && res.data.polls) || []
  return list.map(normalize)
}

/** 发起投票：纯文本内容，票数从 0 开始 */
export async function createPoll(title) {
  const text = (title || '').trim()
  if (!text) {
    throw new Error('请输入投票内容')
  }
  if (text.length > TITLE_MAX_LENGTH) {
    throw new Error(`投票内容不能超过 ${TITLE_MAX_LENGTH} 字`)
  }
  const res = await api.createPoll({ title: text, creator_id: getVoterId() })
  return pickPoll(res.data)
}

/** 提交一票，成功返回更新后的投票对象 */
export async function submitVote(pollId, choice) {
  if (choice !== 'approve' && choice !== 'oppose') {
    throw new Error('无效的投票选项')
  }
  const res = await api.submitVote(pollId, { choice, voter_id: getVoterId() })
  return pickPoll(res.data)
}
