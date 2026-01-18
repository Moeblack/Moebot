/**
 * 人格主管理逻辑
 */

let currentBasePersonas = {};
let currentInitialTraits = {};

async function loadPersonas() {
    try {
        currentBasePersonas = await API.getBasePersonas();
        const activePersonasData = await API.getActivePersonas();
        currentInitialTraits = await API.getInitialTraits();
        const runtimePersonas = await API.getPersonas();
        
        renderBasePersonas();
        renderActivePersonas(activePersonasData, runtimePersonas);
        renderInitialTraits();
    } catch (error) {
        console.error('Failed to load personas:', error);
    }
}

function renderBasePersonas() {
    const container = document.getElementById('base-personas');
    if (!container) return;
    container.innerHTML = Object.entries(currentBasePersonas).map(([name, description]) => `
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 persona-card relative group cursor-pointer hover:border-blue-400 transition-all" onclick="editPersona('${name}')">
            <div class="flex justify-between items-start mb-2">
                <div class="font-bold text-gray-800 text-lg">${name}</div>
                <div class="flex space-x-1">
                    <button class="p-1.5 text-blue-500 hover:bg-blue-50 rounded-md transition-all active:scale-90" onclick="event.stopPropagation(); editPersona('${name}')">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="p-1.5 text-red-500 hover:bg-red-50 rounded-md transition-all active:scale-90" onclick="event.stopPropagation(); deletePersona('${name}')">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
            <div class="text-sm text-gray-600 whitespace-pre-wrap leading-relaxed bg-gray-50 p-3 rounded-md border border-gray-100 group-hover:bg-blue-50 transition-colors">${description}</div>
        </div>
    `).join('');
}

function renderActivePersonas(activeData, runtimeData) {
    const container = document.getElementById('active-personas');
    if (!container) return;
    container.innerHTML = Object.entries(activeData).length > 0 ? Object.entries(activeData).map(([user, persona]) => {
        const sid = `${user}:${persona}`;
        const traits = runtimeData[sid] || [];
        return `
            <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors group" onclick="editActiveTraits('${user}', '${persona}')">
                <div class="flex items-center justify-between">
                    <div>
                        <div class="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">USER / GROUP</div>
                        <div class="font-medium text-gray-800">${user}</div>
                    </div>
                    <div class="text-right">
                        <div class="text-xs text-gray-400 font-bold uppercase tracking-wider mb-1">ACTIVE</div>
                        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">${persona}</span>
                    </div>
                </div>
                <div class="mt-2 text-[10px] text-gray-400 truncate opacity-0 group-hover:opacity-100 transition-opacity">
                    <i class="fas fa-magic mr-1"></i>点击编辑当前特质 (${traits.length})
                </div>
            </div>
        `;
    }).join('') : '<div class="text-center py-4 text-gray-400 text-sm italic">暂无活跃会话记录</div>';
}

function renderInitialTraits() {
    const container = document.getElementById('initial-traits');
    if (!container) return;
    container.innerHTML = Object.entries(currentInitialTraits).map(([persona, traits]) => `
        <div class="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <div class="flex items-center justify-between mb-3">
                <div class="font-bold text-gray-800">${persona}</div>
                <button class="text-xs px-2 py-1 bg-purple-50 text-purple-600 border border-purple-200 rounded hover:bg-purple-100 transition-colors" onclick="showAddTraitModal('${persona}')">
                    <i class="fas fa-plus mr-1"></i>添加
                </button>
            </div>
            <div class="text-sm text-gray-600">
                <ul class="space-y-2">
                    ${traits.map(trait => `
                        <li class="flex items-start justify-between group p-2 hover:bg-gray-50 rounded transition-colors border-l-2 border-purple-300">
                            <span class="flex-1 mr-2 leading-snug">${trait}</span>
                            <button class="text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity" onclick="removeTrait('${persona}', '${trait.replace(/'/g, "\\'")}')">
                                <i class="fas fa-times-circle"></i>
                            </button>
                        </li>
                    `).join('')}
                    ${traits.length === 0 ? '<li class="text-gray-400 italic text-xs">暂无初始特质</li>' : ''}
                </ul>
            </div>
        </div>
    `).join('');
}

function showAddPersonaModal() {
    document.getElementById('add-persona-modal').classList.remove('hidden');
    document.getElementById('add-persona-form').reset();
}

function closeAddPersonaModal() { document.getElementById('add-persona-modal').classList.add('hidden'); }

function editPersona(name) {
    const description = currentBasePersonas[name] || '';
    document.getElementById('edit-persona-name').value = name;
    document.getElementById('edit-persona-description').value = description;
    document.getElementById('edit-persona-modal').classList.remove('hidden');
}

function closeEditPersonaModal() { document.getElementById('edit-persona-modal').classList.add('hidden'); }

function initPersonaForms() {
    document.getElementById('add-persona-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const result = await API.addBasePersona(document.getElementById('persona-name').value, document.getElementById('persona-description').value);
        if (result.success) { alert('添加成功'); closeAddPersonaModal(); loadPersonas(); }
    });
    document.getElementById('edit-persona-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const result = await API.updateBasePersona(document.getElementById('edit-persona-name').value, document.getElementById('edit-persona-description').value);
        if (result.success) { alert('更新成功'); closeEditPersonaModal(); loadPersonas(); }
    });
    document.getElementById('add-trait-form')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const result = await API.addInitialTrait(document.getElementById('trait-persona-name').value, document.getElementById('trait-content').value);
        if (result.success) { closeAddTraitModal(); loadPersonas(); }
    });
}

async function deletePersona(name) {
    if (confirm(`确定删除 "${name}"？`)) {
        const result = await API.deleteBasePersona(name);
        if (result.success) { alert('删除成功'); loadPersonas(); }
    }
}
