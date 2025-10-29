<template>
    <div class="learning-chain-viewer">
        <!-- Role selector -->
        <div class="role-selector">
            <h2>🎓 学习链分析</h2>
            <p>选择要查看的角色学习进程</p>
            <div class="role-grid">
                <router-link v-for="(role, key) in availableRoles" :key="key" :to="`/learning-chain/${key}`"
                    class="role-card">
                    <span class="role-icon">{{ role.icon }}</span>
                    <span class="role-name">{{ role.name }}</span>
                </router-link>
            </div>
        </div>
    </div>
</template>

<script>
import { computed } from 'vue'
import { getRoleConfig } from '../services/learningChainService'

const roles = ['seer', 'werewolf', 'witch', 'villager', 'guardian', 'hunter']

export default {
    name: 'LearningChainViewer',
    setup() {
        const availableRoles = computed(() => {
            const result = {}
            roles.forEach(role => {
                result[role] = getRoleConfig(role)
            })
            return result
        })

        return {
            availableRoles
        }
    }
}
</script>

<style scoped>
.learning-chain-viewer {
    padding: 20px;
}

.role-selector {
    text-align: center;
    padding: 40px 20px;
}

.role-selector h2 {
    font-size: 28px;
    margin-bottom: 10px;
    color: white;
}

.role-selector p {
    color: rgba(255, 255, 255, 0.7);
    margin-bottom: 30px;
    font-size: 16px;
}

.role-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 16px;
    width: 100%;
    margin: 0 auto;
}

.role-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 20px;
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s ease;
    font-size: 14px;
    color: white;
    text-decoration: none;
}

.role-card:hover {
    border-color: rgba(255, 255, 255, 0.5);
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-4px);
    box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}

.role-icon {
    font-size: 32px;
    margin-bottom: 8px;
    display: block;
}

.role-name {
    font-weight: 600;
}
</style>
