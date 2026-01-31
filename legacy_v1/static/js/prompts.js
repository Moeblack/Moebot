/**
 * 提示词管理相关逻辑
 */

async function loadPrompts() {
    try {
        const prompts = await API.getPrompts();
        const container = document.getElementById('prompts-editor-container');
        if (!container) return;
        
        container.innerHTML = Object.entries(prompts).map(([category, value]) => {
            const categoryTitle = {
                'templates': '基础模板 (Templates)',
                'summaries': '三大总结 (Summaries)',
                'decisions': '多种决策 (Decisions)'
            }[category] || category;

            return `
                <div class="border-b pb-6 last:border-0">
                    <h4 class="text-xl font-bold text-gray-800 mb-4 border-l-4 border-blue-600 pl-3">${categoryTitle}</h4>
                    <div class="grid grid-cols-1 gap-6">
                        ${Object.entries(value).map(([key, content]) => `
                            <div class="bg-gray-50 p-4 rounded-xl border border-gray-200">
                                <label class="block text-sm font-bold text-gray-600 mb-2 uppercase tracking-wide">
                                    <i class="fas fa-code mr-1"></i>${key.replace(/_/g, ' ')}
                                </label>
                                <textarea data-category="${category}" data-key="${key}" class="prompt-input w-full p-4 bg-white border border-gray-300 rounded-lg font-mono text-sm h-64 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all shadow-inner">${htmlEscape(content)}</textarea>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load prompts:', error);
    }
}

async function savePrompts() {
    const inputs = document.querySelectorAll('.prompt-input');
    const data = {};
    inputs.forEach(input => {
        const category = input.dataset.category;
        const key = input.dataset.key;
        if (!data[category]) data[category] = {};
        data[category][key] = input.value;
    });
    try {
        const result = await API.savePrompts(data);
        if (result.success) {
            alert('提示词配置更新成功');
            loadPrompts();
        } else alert('更新失败: ' + result.message);
    } catch (error) { console.error('Failed to save prompts:', error); }
}
