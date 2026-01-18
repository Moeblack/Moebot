/**
 * 人格特质管理逻辑
 */

// 特质管理
function showAddTraitModal(personaName) {
    document.getElementById('trait-persona-name').value = personaName;
    document.getElementById('trait-content').value = '';
    document.getElementById('add-trait-modal').classList.remove('hidden');
}

function closeAddTraitModal() {
    document.getElementById('add-trait-modal').classList.add('hidden');
}

async function removeTrait(personaName, trait) {
    if (confirm(`确定要移除此特质吗？\n"${trait}"`)) {
        try {
            const result = await API.removeInitialTrait(personaName, trait);
            if (result.success) loadPersonas();
            else alert('移除失败: ' + result.message);
        } catch (error) { console.error('Failed to remove trait:', error); }
    }
}

// 编辑运行时特质
async function editActiveTraits(user, persona) {
    const sid = `${user}:${persona}`;
    const allPersonas = await API.getPersonas();
    const currentTraits = allPersonas[sid] || [];
    const newTraits = prompt(`正在编辑 ${user} (${persona}) 的运行时特质：\n(用分号“；”分隔多个特质)`, currentTraits.join('；'));
    if (newTraits !== null) {
        try {
            const result = await API.updateActivePersonaTraits(sid, newTraits);
            if (result.success) {
                alert('运行时特质已更新');
                loadPersonas();
            }
        } catch (error) { console.error('Failed to update active traits:', error); }
    }
}
