/**
 * 聊天历史管理逻辑
 */

let currentChatHistorySid = '';

async function editChatHistory(sid) {
    currentChatHistorySid = sid;
    document.getElementById('chat-history-sid').textContent = sid;
    const chatData = await API.getChatHistory();
    const messages = chatData[sid] || [];
    const container = document.getElementById('chat-history-items');
    container.innerHTML = '';
    messages.forEach((msg, index) => addChatMessageUI(msg.role, msg.content, msg.time, index, msg.nickname, msg.user_id));
    if (messages.length === 0) container.innerHTML = '<div class="text-center py-8 text-gray-400 italic">暂无历史记录</div>';
    document.getElementById('manage-chat-history-modal').classList.remove('hidden');
}

function addChatMessageUI(role, content, time, index, nickname, sender_id) {
    const container = document.getElementById('chat-history-items');
    if (container.querySelector('.italic')) container.innerHTML = '';
    const item = document.createElement('div');
    item.className = 'bg-white p-5 rounded-xl shadow-sm border border-gray-200 chat-message-item transition-all hover:shadow-md';
    item.innerHTML = `
        <div class="grid grid-cols-12 gap-4">
            <div class="col-span-3 space-y-3 border-r pr-4">
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">角色 (Role)</label>
                    <select class="role-select w-full p-2 border rounded-md text-sm bg-gray-50 focus:ring-2 focus:ring-blue-500">
                        <option value="user" ${role !== 'assistant' && role !== 'system' ? 'selected' : ''}>User (${role})</option>
                        <option value="assistant" ${role === 'assistant' ? 'selected' : ''}>Assistant</option>
                        <option value="system" ${role === 'system' ? 'selected' : ''}>System</option>
                    </select>
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">发送者昵称</label>
                    <input type="text" class="nickname-input w-full p-2 border rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500" value="${nickname || ''}" placeholder="AI 看到的昵称">
                </div>
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">发送者 ID</label>
                    <input type="text" class="sender-id-input w-full p-2 border rounded-md text-sm bg-white focus:ring-2 focus:ring-blue-500 font-mono" value="${sender_id || ''}" placeholder="QQ 号">
                </div>
            </div>
            <div class="col-span-7">
                <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">消息正文 (Content)</label>
                <textarea class="content-textarea w-full p-3 border rounded-md text-sm h-full min-h-[120px] focus:ring-2 focus:ring-blue-500 leading-relaxed">${content || ''}</textarea>
            </div>
            <div class="col-span-2 flex flex-col justify-between pl-4 border-l">
                <div>
                    <label class="block text-[10px] font-bold text-gray-400 uppercase mb-1">发送时间</label>
                    <input type="text" class="time-input w-full p-1 border rounded text-[10px] text-gray-500" value="${time || ''}">
                </div>
                <button class="w-full mt-4 py-2 px-3 bg-red-50 text-red-500 hover:bg-red-500 hover:text-white rounded-lg transition-all flex items-center justify-center group" onclick="this.closest('.chat-message-item').remove()">
                    <i class="fas fa-trash-alt mr-2"></i>
                    <span class="text-xs font-bold">删除该条</span>
                </button>
            </div>
        </div>
    `;
    container.appendChild(item);
}

function addChatMessage() {
    addChatMessageUI('user', '', new Date().toLocaleString(), Date.now());
    const container = document.getElementById('chat-history-items');
    container.scrollTop = container.scrollHeight;
}

async function saveChatHistory() {
    const items = document.querySelectorAll('.chat-message-item');
    const messages = [];
    items.forEach(item => {
        let role = item.querySelector('.role-select').value;
        const select = item.querySelector('.role-select');
        const selectedOptionText = select.options[select.selectedIndex].text;
        if (role === 'user' && selectedOptionText.includes('(')) {
            const match = selectedOptionText.match(/\((.*)\)/);
            if (match) role = match[1];
        }
        messages.push({
            role: role,
            content: item.querySelector('.content-textarea').value,
            time: item.querySelector('.time-input').value,
            nickname: item.querySelector('.nickname-input').value,
            user_id: item.querySelector('.sender-id-input').value
        });
    });
    try {
        const result = await API.updateChatHistory(currentChatHistorySid, messages);
        if (result.success) {
            alert('聊天历史已更新');
            closeManageChatHistoryModal();
            loadMemories();
        } else alert('保存失败: ' + result.message);
    } catch (error) { console.error('Failed to save chat history:', error); }
}

function closeManageChatHistoryModal() {
    document.getElementById('manage-chat-history-modal').classList.add('hidden');
}
