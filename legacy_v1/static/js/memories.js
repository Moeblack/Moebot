/**
 * 印象管理与主记忆加载逻辑
 */

let currentImpressionsSid = '';

// 加载记忆数据
async function loadMemories() {
    try {
        const impressionsData = await API.getImpressions();
        const chatHistoryData = await API.getChatHistory();
        const episodicMemoryData = await API.getEpisodicMemory();
        
        renderImpressions(impressionsData);
        renderChatHistory(chatHistoryData);
        renderEpisodicMemory(episodicMemoryData);
    } catch (error) {
        console.error('Failed to load memories:', error);
    }
}

function renderImpressions(data) {
    const container = document.getElementById('impressions');
    if (!container) return;
    container.innerHTML = Object.entries(data).length > 0 ? Object.entries(data).map(([sid, impressions]) => `
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors group" onclick="editImpression('${sid}', '${impressions.join('；')}')">
            <div class="flex justify-between items-start mb-2">
                <div class="font-medium text-gray-800 truncate flex-1 mr-2">${sid}</div>
                <button class="text-pink-500 opacity-0 group-hover:opacity-100 transition-opacity">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
            <div class="text-xs text-gray-500">印象条数: <span class="font-bold text-pink-600">${impressions.length}</span></div>
        </div>
    `).join('') : '<div class="text-center py-8 text-gray-400 italic">暂无印象记录</div>';
}

function renderChatHistory(data) {
    const container = document.getElementById('chat-history');
    if (!container) return;
    container.innerHTML = Object.entries(data).length > 0 ? Object.entries(data).map(([sid, messages]) => `
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors group" onclick="editChatHistory('${sid}')">
            <div class="flex justify-between items-start mb-2">
                <div class="font-medium text-gray-800 truncate flex-1 mr-2">${sid}</div>
                <button class="text-blue-500 opacity-0 group-hover:opacity-100 transition-opacity">
                    <i class="fas fa-edit"></i>
                </button>
            </div>
            <div class="text-xs text-gray-500">消息总数: <span class="font-bold text-blue-600">${messages.length}</span></div>
            ${messages.length > 0 ? `<div class="mt-2 text-[10px] text-gray-400 truncate">${htmlEscape(messages[messages.length-1].content)}</div>` : ''}
        </div>
    `).join('') : '<div class="text-center py-8 text-gray-400 italic">暂无历史记录</div>';
}

function renderEpisodicMemory(data) {
    const container = document.getElementById('episodic-memory');
    if (!container) return;
    container.innerHTML = Object.entries(data).length > 0 ? Object.entries(data).map(([sid, memories]) => `
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors group" onclick="editEpisodic('${sid}')">
            <div class="flex justify-between items-start mb-2">
                <div class="font-medium text-gray-800 truncate flex-1 mr-2">${sid}</div>
                <button class="text-purple-500 opacity-0 group-hover:opacity-100 transition-opacity">
                    <i class="fas fa-history"></i>
                </button>
            </div>
            <div class="text-xs text-gray-500">情节片段: <span class="font-bold text-purple-600">${memories.length}</span></div>
            ${memories.length > 0 ? `<div class="mt-2 text-[10px] text-gray-400 italic truncate">${htmlEscape(memories[memories.length-1].summary)}</div>` : ''}
        </div>
    `).join('') : '<div class="text-center py-8 text-gray-400 italic">暂无记忆记录</div>';
}

// 记忆过滤功能
function filterMemories(type) {
    const query = document.getElementById(`${type}-search`).value.toLowerCase();
    const containerId = type === 'chat' ? 'chat-history' : (type === 'episodic' ? 'episodic-memory' : 'impressions');
    const container = document.getElementById(containerId);
    if (!container) return;
    for (let item of container.children) {
        item.style.display = item.innerText.toLowerCase().includes(query) ? '' : 'none';
    }
}

// --- 印象管理 ---
async function editImpression(sid, currentImpression) {
    currentImpressionsSid = sid;
    document.getElementById('impressions-sid').textContent = sid;
    const impressions = typeof currentImpression === 'string' ? currentImpression.split(/[；;]/).filter(i => i.trim()) : [];
    const container = document.getElementById('impressions-items');
    container.innerHTML = '';
    impressions.forEach((imp, index) => addImpressionUI(imp, index));
    if (impressions.length === 0) container.innerHTML = '<div class="text-center py-8 text-gray-400 italic">暂无印象记录</div>';
    document.getElementById('manage-impressions-modal').classList.remove('hidden');
}

function addImpressionUI(content, index) {
    const container = document.getElementById('impressions-items');
    if (container.querySelector('.italic')) container.innerHTML = '';
    const item = document.createElement('div');
    item.className = 'bg-white p-3 rounded-lg shadow-sm border border-gray-200 impression-item flex items-center space-x-3 transition-all hover:border-pink-300';
    item.innerHTML = `
        <div class="flex-1">
            <input type="text" class="impression-input w-full p-2 border rounded-md text-sm focus:ring-2 focus:ring-pink-500" value="${content || ''}" placeholder="输入印象描述...">
        </div>
        <button class="text-red-400 hover:text-red-600 p-2 transition-colors" onclick="this.closest('.impression-item').remove()">
            <i class="fas fa-times-circle"></i>
        </button>
    `;
    container.appendChild(item);
}

function addImpressionItem() {
    addImpressionUI('', Date.now());
    const container = document.getElementById('impressions-items');
    container.scrollTop = container.scrollHeight;
}

async function saveImpressions() {
    const inputs = document.querySelectorAll('.impression-input');
    const impressions = [];
    inputs.forEach(input => { if (input.value.trim()) impressions.push(input.value.trim()); });
    try {
        const result = await API.updateImpressions(currentImpressionsSid, impressions);
        if (result.success) {
            alert('印象已更新');
            closeManageImpressionsModal();
            loadMemories();
        } else alert('保存失败: ' + result.message);
    } catch (error) { console.error('Failed to save impressions:', error); }
}

function closeManageImpressionsModal() {
    document.getElementById('manage-impressions-modal').classList.add('hidden');
}
