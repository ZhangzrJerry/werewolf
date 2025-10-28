import api from './index'

export const learningApi = {
  // 获取角色学习链数据 - 对应 Flask 的 /learning-chain/<role> 路由
  getLearningData(role) {
    // 注意：这个是页面路由，不是API路由
    // 实际的学习数据可能需要从其他API获取
    return api.get(`/learning-chain/${role}`)
  },

  // 获取角色学习数据（基于复盘数据）
  getRoleLearningData(role) {
    // 这个需要根据实际的Flask后端实现来调整
    // 可能需要调用多个API来组合数据
    return api.get(`/role-learning/${role}`)
  }
}