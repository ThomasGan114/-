/**
 * 浏览器录音 → MP3
 *
 * 为什么要在前端编码成 MP3：
 * MediaRecorder 录出来的是 webm/opus（Chrome/安卓）或 mp4/aac（Safari/iOS），
 * 而 webm 在 iOS Safari 上无法播放 —— 校园墙要人人能听，所以录完就地重编码为 MP3
 * （MP3 全平台通吃）。编码库按需动态加载，不录音的访客不会下载它。
 */

/** 允许的最短录音时长（秒） */
export const MIN_DURATION = 0.3
/** 允许的最长录音时长（秒），到点自动停止 */
export const MAX_DURATION = 30

/** 递归顺序：优先体积小、兼容好的组合 */
const PREFERRED_MIME_TYPES = [
  'audio/webm;codecs=opus',
  'audio/webm',
  'audio/ogg;codecs=opus',
  'audio/mp4', // Safari / iOS
  'audio/mpeg'
]

/** 当前浏览器能否录音（需要 HTTPS 或 localhost） */
export const isRecordingSupported = () => {
  return typeof navigator !== 'undefined' &&
    !!navigator.mediaDevices &&
    typeof navigator.mediaDevices.getUserMedia === 'function' &&
    typeof window !== 'undefined' &&
    typeof window.MediaRecorder === 'function'
}

const pickMimeType = () => {
  if (typeof MediaRecorder === 'undefined' || typeof MediaRecorder.isTypeSupported !== 'function') {
    return ''
  }
  for (const type of PREFERRED_MIME_TYPES) {
    if (MediaRecorder.isTypeSupported(type)) return type
  }
  return ''
}

/**
 * 开始录音，返回一个句柄：
 *   handle.elapsed  已录时长（秒，实时）
 *   handle.stop()   停止录音，resolve { blob, duration }（原始格式，未转码）
 *   handle.cancel() 放弃录音并立即释放麦克风
 */
export async function startRecording() {
  if (!isRecordingSupported()) {
    throw new Error('当前浏览器不支持录音，请用最新版 Chrome / Edge / Safari')
  }

  const stream = await navigator.mediaDevices.getUserMedia({
    audio: {
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true
    }
  })

  const mimeType = pickMimeType()
  const recorder = mimeType ? new MediaRecorder(stream, { mimeType }) : new MediaRecorder(stream)
  const chunks = []
  recorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) chunks.push(event.data)
  }
  recorder.start(250) // 每 250ms 交一次数据，停止时不用等太久

  const startedAt = Date.now()
  const releaseStream = () => {
    try {
      stream.getTracks().forEach((track) => track.stop())
    } catch (error) {
      /* 忽略：释放失败不影响主流程 */
    }
  }

  return {
    get elapsed() {
      return (Date.now() - startedAt) / 1000
    },
    stop() {
      return new Promise((resolve) => {
        const finish = () => {
          releaseStream()
          resolve({
            blob: new Blob(chunks, { type: recorder.mimeType || mimeType || 'audio/webm' }),
            duration: (Date.now() - startedAt) / 1000
          })
        }
        if (recorder.state === 'inactive') {
          finish()
          return
        }
        recorder.onstop = finish
        try {
          recorder.stop()
        } catch (error) {
          finish()
        }
      })
    },
    cancel() {
      try {
        if (recorder.state !== 'inactive') {
          recorder.onstop = null
          recorder.stop()
        }
      } catch (error) {
        /* 忽略 */
      }
      releaseStream()
    }
  }
}

/**
 * 把录音（webm / ogg / mp4）解码后重新编码为 MP3
 * @param {Blob} blob 录音原始数据
 * @returns {Promise<Blob>} audio/mpeg
 */
export async function encodeToMp3(blob) {
  const { Mp3Encoder } = await import('@breezystack/lamejs')
  const AudioCtx = window.AudioContext || window.webkitAudioContext
  if (!AudioCtx) {
    throw new Error('当前浏览器无法处理音频')
  }

  const ctx = new AudioCtx()
  try {
    // iOS 上 AudioContext 初始是 suspended，解码前尽量唤醒（失败也不影响 decodeAudioData）
    try {
      if (ctx.state === 'suspended' && typeof ctx.resume === 'function') {
        await ctx.resume()
      }
    } catch (error) {
      /* 忽略：没有用户手势时 resume 可能被拒 */
    }
    const audioBuffer = await ctx.decodeAudioData(await blob.arrayBuffer())
    const { numberOfChannels, length, sampleRate } = audioBuffer

    // 多声道下混为单声道：语音场景足够，文件更小
    const mixed = new Float32Array(length)
    for (let channel = 0; channel < numberOfChannels; channel++) {
      const data = audioBuffer.getChannelData(channel)
      for (let i = 0; i < length; i++) {
        mixed[i] += data[i] / numberOfChannels
      }
    }

    const pcm = new Int16Array(length)
    for (let i = 0; i < length; i++) {
      const sample = Math.max(-1, Math.min(1, mixed[i]))
      pcm[i] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
    }

    const encoder = new Mp3Encoder(1, sampleRate, 128) // 单声道 / 原采样率 / 128kbps
    const parts = []
    const blockSize = 1152
    for (let offset = 0; offset < pcm.length; offset += blockSize) {
      const buffer = encoder.encodeBuffer(pcm.subarray(offset, offset + blockSize))
      if (buffer.length > 0) parts.push(buffer)
    }
    const tail = encoder.flush()
    if (tail.length > 0) parts.push(tail)

    return new Blob(parts, { type: 'audio/mpeg' })
  } finally {
    try {
      ctx.close()
    } catch (error) {
      /* 忽略 */
    }
  }
}

/**
 * 包装成可直接放进上传列表的文件对象
 * 文件名用连字符而不是下划线：后端会存成「uuid_原名」，墙上的文件名展示取
 * 最后一个下划线之后的部分，用连字符才能显示完整名字。
 */
export function buildRecordingFile(mp3Blob, date = new Date()) {
  const pad = (value) => String(value).padStart(2, '0')
  const stamp = `${date.getFullYear()}${pad(date.getMonth() + 1)}${pad(date.getDate())}` +
    `-${pad(date.getHours())}${pad(date.getMinutes())}${pad(date.getSeconds())}`
  return new File([mp3Blob], `录音-${stamp}.mp3`, {
    type: 'audio/mpeg',
    lastModified: Date.now()
  })
}
