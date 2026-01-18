/**
 * HTML 转义函数
 */
function htmlEscape(text) {
    if (typeof text !== 'string') return text;
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

/**
 * 显示详细信息模态框
 */
function showDetail(title, content) {
    document.getElementById('modal-title').textContent = title;
    const modalContent = document.getElementById('modal-content');
    
    try {
        // 如果 content 是字符串且看起来像 JSON，尝试解析它
        let displayContent = content;
        if (typeof content === 'string' && (content.startsWith('{') || content.startsWith('['))) {
            try {
                const parsed = JSON.parse(content);
                displayContent = JSON.stringify(parsed, null, 2);
            } catch (e) {
                // 解析失败，保持原样
            }
        } else if (typeof content === 'object') {
            displayContent = JSON.stringify(content, null, 2);
        }
        
        modalContent.textContent = displayContent;
    } catch (error) {
        modalContent.textContent = content;
    }
    
    document.getElementById('detail-modal').classList.remove('hidden');
}

/**
 * 关闭模态框
 */
function closeModal() {
    document.getElementById('detail-modal').classList.add('hidden');
}
