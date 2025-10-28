const BASE = '/werewolf'

export const learningApi = {
  async getLearningData(role) {
    const r = await fetch(`${BASE}/learning-chain/${role}.json`)
    if (!r.ok) throw new Error('学习链数据未找到')
    return { data: await r.json() }
  },

  async getRoleLearningData(role) {
    // Role learning data should be exported into werewolf/learning/<role>.json
    const r = await fetch(`${BASE}/learning/${role}.json`)
    if (!r.ok) throw new Error('角色学习数据未找到')
    return { data: await r.json() }
  }
}