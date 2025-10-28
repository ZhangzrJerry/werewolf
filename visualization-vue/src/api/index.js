import axios from 'axios'

// 创建 axios 实例
const api = axios.create({
    baseURL: '/api',
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json'
    }
})

// 请求拦截器
api.interceptors.request.use(
    (config) => {
        // 可以在这里添加认证 token 等
        return config
    },
    (error) => {
        return Promise.reject(error)
    }
)

// 响应拦截器
api.interceptors.response.use(
    (response) => {
        return response
    },
    (error) => {
        console.error('API 请求错误:', error)

        if (error.response) {
            // 服务器返回错误状态码
            const message = error.response.data?.message || error.response.statusText
            throw new Error(`${error.response.status}: ${message}`)
        } else if (error.request) {
            // 请求发出但没有收到响应
            throw new Error('网络连接失败，请检查网络状态')
        } else {
            // 其他错误
            throw new Error(error.message || '未知错误')
        }
    }
)

export default api