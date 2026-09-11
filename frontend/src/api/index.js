import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// 后端 sources/adaptations 用 {code,data,msg} 信封；adapt 直出模型。
// 这里统一拆信封：有 code+data 字段就取内层 data，否则原样返回。
const unwrap = (r) => {
  const body = r.data
  if (body && typeof body === 'object' && 'code' in body && 'data' in body) {
    return body.data
  }
  return body
}

export const getSources = () => api.get('/sources').then(unwrap)
export const getSource = (id) => api.get(`/sources/${id}`).then(unwrap)
export const seedSources = () => api.post('/sources/seed').then((r) => r.data)
export const updateSourceCategory = (id, category) =>
  api.patch(`/sources/${id}/category`, { category }).then(unwrap)
export const getAdaptations = () => api.get('/adaptations').then(unwrap)
export const getAdaptation = (id) => api.get(`/adaptations/${id}`).then(unwrap)
export const deleteAdaptation = (id) => api.delete(`/adaptations/${id}`).then(unwrap)
export const extractAdapt = (postId) =>
  api.post('/adapt/extract', { post_id: postId }).then(unwrap)
export const runAdapt = (payload) => api.post('/adapt/run', payload).then(unwrap)
// 复诊：无 user_note → 拿 AI 归因追问；有 user_note → 拿归因结论
export const submitFeedback = (id, payload) =>
  api.post(`/adaptations/${id}/feedback`, payload).then(unwrap)
