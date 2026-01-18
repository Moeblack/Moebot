/**
 * 情节记忆管理逻辑
 */

let currentEpisodicSid = '';

async function editEpisodic(sid) {
    currentEpisodicSid = sid;
    document.getElementById('episodic-sid').textContent = sid;
    const episodicData = await API.getEpisodicMemory();
    const memories = episodicData[sid] || [];
    const container = document.getElementById('episodic-items');
    container.innerHTML = '';
    memories.forEach((mem, index) => addEpisodicUI(mem.summary, mem.time, index));
    if (memories.length === 0) container.innerHTML = '<div class="text-center py-8 text-gray-400 italic">暂无记忆记录</div>';
    document.getElementById('manage-episodic-modal').classList.remove('hidden');
}

function addEpisodicUI(summary, time, index) {
    const container = document.getElementById('episodic-items');
    if (container.querySelector('.italic')) container.innerHTML = '';
    const item = document.createElement('div');
    item.className = 'relative pl-8 pb-8 episodic-item group';
    item.innerHTML = `
        <div class="absolute left-3 top-0 bottom-0 w-0.5 bg-purple-200 group-last:bg-transparent"></div>
        <div class="absolute left-0 top-1 w-6.5 h-6.5 rounded-full bg-white border-2 border-purple-500 flex items-center justify-center z-10">
            <i class="fas fa-bookmark text-[10px] text-purple-500"></i>
        </div>
        <div class="bg-white p-5 rounded-xl shadow-sm border border-gray-200 transition-all hover:shadow-md hover:border-purple-300">
            <div class="flex flex-col md:flex-row md:items-start md:space-x-4">
                <div class="flex-1">
                    <label class="block text-[10px] font-bold text-gray-400 uppercase mb-2">情节摘要 (Summary)</label>
                    <textarea class="summary-textarea w-full p-3 border border-gray-100 rounded-lg text-sm h-28 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all leading-relaxed">${summary || ''}</textarea>
                </div>
                <div class="md:w-64 mt-4 md:mt-0 flex flex-col justify-between">
                    <div>
                        <label class="block text-[10px] font-bold text-gray-400 uppercase mb-2">发生时间范围</label>
                        <div class="relative">
                            <i class="fas fa-clock absolute left-3 top-2.5 text-gray-300 text-xs"></i>
                            <input type="text" class="time-input w-full pl-8 pr-3 py-2 border border-gray-100 rounded-lg text-[11px] text-gray-600 focus:ring-2 focus:ring-purple-500" value="${time || ''}" placeholder="YYYY-MM-DD HH:MM">
                        </div>
                    </div>
                    <div class="flex items-center justify-end space-x-2 mt-4">
                        <button class="text-xs px-3 py-1.5 text-red-500 hover:bg-red-50 rounded-md transition-colors flex items-center" onclick="this.closest('.episodic-item').remove()">
                            <i class="fas fa-trash-alt mr-1.5"></i>删除
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    container.appendChild(item);
}

function addEpisodicItem() {
    addEpisodicUI('', new Date().toLocaleString(), Date.now());
    const container = document.getElementById('episodic-items');
    container.scrollTop = container.scrollHeight;
}

async function saveEpisodicHistory() {
    const items = document.querySelectorAll('.episodic-item');
    const memories = [];
    items.forEach(item => {
        memories.push({
            summary: item.querySelector('.summary-textarea').value,
            time: item.querySelector('.time-input').value
        });
    });
    try {
        const result = await API.updateEpisodicMemory(currentEpisodicSid, memories);
        if (result.success) {
            alert('情节记忆已更新');
            closeManageEpisodicModal();
            loadMemories();
        } else alert('保存失败: ' + result.message);
    } catch (error) { console.error('Failed to save episodic history:', error); }
}

function closeManageEpisodicModal() {
    document.getElementById('manage-episodic-modal').classList.add('hidden');
}
