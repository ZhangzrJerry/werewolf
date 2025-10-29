// Service for fetching learning chain data
export async function getLearningChainData(role) {
    try {
        const response = await fetch(`/public/.training/learning-chain/${role}.json`)
        if (!response.ok) {
            throw new Error(`Failed to fetch learning chain data for ${role}`)
        }
        return await response.json()
    } catch (error) {
        console.error('Error fetching learning chain data:', error)
        return { sessions: [], total_sessions: 0, total_reviews: 0, total_strategies: 0 }
    }
}

// Get role configuration
export function getRoleConfig(role) {
    const configs = {
        'seer': { name: '预言家', icon: '🔮', color: '#ffc107' },
        'werewolf': { name: '狼人', icon: '🐺', color: '#6f42c1' },
        'witch': { name: '女巫', icon: '🧙‍♀️', color: '#e91e63' },
        'villager': { name: '村民', icon: '👨‍🌾', color: '#10b981' },
        'guardian': { name: '守卫', icon: '🛡️', color: '#00bcd4' },
        'hunter': { name: '猎人', icon: '🏹', color: '#ff6b6b' }
    }
    return configs[role] || { name: role, icon: '❓', color: '#999' }
}
