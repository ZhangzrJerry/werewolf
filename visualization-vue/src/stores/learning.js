import { defineStore } from 'pinia'
import { ref } from 'vue'
import { learningApi } from '../api/learning'

export const useLearningStore = defineStore('learning', () => {
    // State
    const learningData = ref({})
    const currentRole = ref(null)
    const loading = ref(false)
    const error = ref(null)

    // Actions
    async function fetchLearningData(role) {
        try {
            loading.value = true
            error.value = null
            currentRole.value = role

            // 调用角色学习数据 API
            const response = await learningApi.getRoleLearningData(role)
            learningData.value[role] = response.data
        } catch (err) {
            error.value = err.message || '获取学习数据失败'
            console.error('获取学习数据失败:', err)
        } finally {
            loading.value = false
        }
    }

    function getLearningDataForRole(role) {
        return learningData.value[role] || null
    }

    return {
        // State
        learningData,
        currentRole,
        loading,
        error,

        // Actions
        fetchLearningData,
        getLearningDataForRole
    }
})