/**
 * API 调用封装
 */
const API = {
    async getAILogs(limit = 50) {
        const response = await fetch(`/api/ai-logs?limit=${limit}`);
        return await response.json();
    },
    async getAIDecisions(limit = 50) {
        const response = await fetch(`/api/ai-decisions?limit=${limit}`);
        return await response.json();
    },
    async getActiveTasks() {
        const response = await fetch('/api/active-tasks');
        return await response.json();
    },
    async getUserActivity(sessionId = null, limit = 20) {
        let url = `/api/user-activity?limit=${limit}`;
        if (sessionId) url += `&session_id=${sessionId}`;
        const response = await fetch(url);
        return await response.json();
    },
    async getConfigChanges(limit = 50) {
        const response = await fetch(`/api/config-changes?limit=${limit}`);
        return await response.json();
    },
    async getConfig() {
        const response = await fetch('/api/config');
        return await response.json();
    },
    async saveConfig(config) {
        const response = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        return await response.json();
    },
    async resetConfig() {
        const response = await fetch('/api/config/reset', { method: 'POST' });
        return await response.json();
    },
    async clearLogs(logType) {
        const response = await fetch('/api/logs/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `log_type=${logType}`
        });
        return await response.json();
    },
    async getBasePersonas() {
        const response = await fetch('/api/base-personas');
        return await response.json();
    },
    async getActivePersonas() {
        const response = await fetch('/api/active-personas');
        return await response.json();
    },
    async getInitialTraits() {
        const response = await fetch('/api/initial-traits');
        return await response.json();
    },
    async getPersonas() {
        const response = await fetch('/api/personas');
        return await response.json();
    },
    async addBasePersona(name, description) {
        const response = await fetch('/api/base-personas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return await response.json();
    },
    async updateBasePersona(name, description) {
        const response = await fetch('/api/base-personas', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return await response.json();
    },
    async deleteBasePersona(name) {
        const response = await fetch('/api/base-personas', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name })
        });
        return await response.json();
    },
    async addInitialTrait(personaName, trait) {
        const response = await fetch('/api/initial-traits', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona_name: personaName, trait: trait })
        });
        return await response.json();
    },
    async removeInitialTrait(personaName, trait) {
        const response = await fetch('/api/initial-traits', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ persona_name: personaName, trait: trait })
        });
        return await response.json();
    },
    async updateActivePersonaTraits(sid, traits) {
        const response = await fetch('/api/active-personas/traits', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sid, traits: traits })
        });
        return await response.json();
    },
    async getImpressions() {
        const response = await fetch('/api/impressions');
        return await response.json();
    },
    async updateImpressions(sid, impressions) {
        const response = await fetch('/api/impressions', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sid, impressions: impressions })
        });
        return await response.json();
    },
    async getChatHistory() {
        const response = await fetch('/api/chat-history');
        return await response.json();
    },
    async updateChatHistory(sid, messages) {
        const response = await fetch('/api/chat-history', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sid, messages: messages })
        });
        return await response.json();
    },
    async getEpisodicMemory() {
        const response = await fetch('/api/episodic-memory');
        return await response.json();
    },
    async updateEpisodicMemory(sid, memories) {
        const response = await fetch('/api/episodic-memory', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sid, memories: memories })
        });
        return await response.json();
    },
    async getPrompts() {
        const response = await fetch('/api/prompts');
        return await response.json();
    },
    async savePrompts(data) {
        const response = await fetch('/api/prompts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    },

    // ----------------------------
    // V2 Config API
    // ----------------------------
    async getConfigV2(masked = true) {
        const response = await fetch(`/api/v2/config?masked=${masked ? 'true' : 'false'}`);
        return await response.json();
    },
    async getConfigV2Schema() {
        const response = await fetch('/api/v2/config/schema');
        return await response.json();
    },
    async getConfigV2Section(section) {
        const response = await fetch(`/api/v2/config/${encodeURIComponent(section)}`);
        return await response.json();
    },
    async patchConfigV2Section(section, data) {
        const response = await fetch(`/api/v2/config/${encodeURIComponent(section)}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data || {})
        });
        return await response.json();
    },
    async testConfigV2(section) {
        const response = await fetch(`/api/v2/config/test/${encodeURIComponent(section)}`, { method: 'POST' });
        return await response.json();
    },
    async exportConfigV2() {
        const response = await fetch('/api/v2/config/export');
        return await response.json();
    },
    async importConfigV2(config) {
        const response = await fetch('/api/v2/config/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config })
        });
        return await response.json();
    },
};
