// Service for fetching learning chain data
export async function getLearningChainData(role) {
    try {
        // First, get the list of session directories
        const sessionsResponse = await fetch('/.training/sessions.json')
        if (!sessionsResponse.ok) {
            console.warn('Could not fetch sessions.json, trying direct access')
            return getEmptyData()
        }

        const sessionsData = await sessionsResponse.json()
        const sessionIds = Object.keys(sessionsData).sort().reverse() // Most recent first

        const sessions = []
        let totalReviews = 0
        let totalStrategies = 0

        // Fetch data for each session
        for (const sessionId of sessionIds) {
            try {
                // Try to get full_analysis.json
                const analysisResponse = await fetch(
                    `/.training/reviews/${sessionId}/full_analysis.json`
                )

                if (analysisResponse.ok) {
                    const analysisData = await analysisResponse.json()

                    // Parse timestamp
                    const dateStr = sessionId.substring(0, 8) // YYYYMMDD
                    const timeStr = sessionId.substring(9, 15) // HHMMSS
                    const formattedDate = `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
                    const formattedTime = `${timeStr.substring(0, 2)}:${timeStr.substring(2, 4)}:${timeStr.substring(4, 6)}`

                    // Extract reviews for this role
                    const sessionReviews = []
                    const perPlayer = analysisData.per_player || {}

                    for (const [player, review] of Object.entries(perPlayer)) {
                        if (isRoleRelevantReview(review, role)) {
                            sessionReviews.push({
                                player,
                                content: review
                            })
                        }
                    }

                    // Extract strategies for this role
                    let sessionStrategies = []
                    const lessons = analysisData.lessons || {}
                    const roleKey = capitalizeFirstLetter(role)

                    if (lessons[roleKey]) {
                        sessionStrategies = lessons[roleKey].slice(0, 5) // Top 5 strategies
                    }

                    totalReviews += sessionReviews.length
                    totalStrategies = Math.max(totalStrategies, sessionStrategies.length)

                    // Only add session if it has relevant data
                    if (sessionReviews.length > 0 || sessionStrategies.length > 0) {
                        sessions.push({
                            date: formattedDate,
                            time: formattedTime,
                            timestamp: sessionId,
                            reviews: sessionReviews,
                            strategies: sessionStrategies
                        })
                    }
                }
            } catch (error) {
                console.warn(`Error loading session ${sessionId}:`, error)
                // Continue with next session
            }
        }

        return {
            sessions,
            total_sessions: sessions.length,
            total_reviews: totalReviews,
            total_strategies: totalStrategies
        }
    } catch (error) {
        console.error('Error fetching learning chain data:', error)
        return getEmptyData()
    }
}

function getEmptyData() {
    return {
        sessions: [],
        total_sessions: 0,
        total_reviews: 0,
        total_strategies: 0
    }
}

function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1)
}

function isRoleRelevantReview(content, role) {
    const roleKeywords = {
        seer: ['预言家', 'seer', '查验', '验人', '警徽'],
        werewolf: ['狼人', 'werewolf', '刀人', '狼队'],
        witch: ['女巫', 'witch', '毒药', '解药'],
        villager: ['村民', 'villager', '票型', '发言'],
        guardian: ['守卫', 'guardian', '守护', '撞刀'],
        hunter: ['猎人', 'hunter', '开枪', '带走']
    }

    const keywords = roleKeywords[role] || []
    const lowerContent = content.toLowerCase()

    return keywords.some(keyword =>
        lowerContent.includes(keyword.toLowerCase())
    )
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
