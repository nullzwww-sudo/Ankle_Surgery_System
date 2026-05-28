import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: 'http://127.0.0.1:8000', // 你的 FastAPI 本地地址
  timeout: 60000 // AI 运算比较慢，超时设为 60 秒
})

// 响应拦截器：统一处理报错
service.interceptors.response.use(
  response => {
    const res = response.data
    if (res.code !== 200) {
      ElMessage.error(res.message || 'Error')
      return Promise.reject(new Error(res.message || 'Error'))
    } else {
      return res.data
    }
  },
  error => {
    ElMessage.error('服务器连接失败或算法报错: ' + error.message)
    return Promise.reject(error)
  }
)

export default service