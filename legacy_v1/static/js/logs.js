/**
 * 日志相关逻辑
 */

let allAILogs = [];
let allAIDecisions = [];

// 加载 AI 交互记录
async function loadAILogs() {
    try {
        allAILogs = await API.getAILogs();
        const tbody = document.getElementById('ai-logs-body');
        if (!tbody) return;
        
        tbody.innerHTML = allAILogs.map((log, index) => `
            <tr class="border-b hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-sm text-gray-600">${log.timestamp}</td>
                <td class="px-6 py-4 text-sm text-blue-600 font-medium">${log.model}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${log.duration.toFixed(2)}s</td>
                <td class="px-6 py-4">
                    <button class="text-blue-500 hover:text-blue-700" onclick="showAILogDetail(${index}, 'request')">
                        <i class="fas fa-eye mr-1"></i>查看
                    </button>
                </td>
                <td class="px-6 py-4">
                    <button class="text-blue-500 hover:text-blue-700" onclick="showAILogDetail(${index}, 'response')">
                        <i class="fas fa-eye mr-1"></i>查看
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load AI logs:', error);
    }
}

// 加载 AI 决策记录
async function loadAIDecisions() {
    try {
        allAIDecisions = await API.getAIDecisions();
        const tbody = document.getElementById('ai-decisions-body');
        if (!tbody) return;
        
        tbody.innerHTML = allAIDecisions.map((decision, index) => {
            let decisionTypeText = '';
            switch (decision.decision_type) {
                case 'entry': decisionTypeText = '准入决策'; break;
                case 'micro': decisionTypeText = '微观决策'; break;
                case 'macro': decisionTypeText = '宏观决策'; break;
            }
            
            return `
                <tr class="border-b hover:bg-gray-50 transition-colors">
                    <td class="px-6 py-4 text-sm text-gray-600">${decision.timestamp}</td>
                    <td class="px-6 py-4 text-sm text-green-600 font-medium">${decisionTypeText}</td>
                    <td class="px-6 py-4 text-sm text-gray-800">${decision.session_id}</td>
                    <td class="px-6 py-4">
                        <button class="text-blue-500 hover:text-blue-700" onclick="showAIDecisionDetail(${index})">
                            <i class="fas fa-eye mr-1"></i>查看
                        </button>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-600">${decision.reason}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">${decision.duration.toFixed(2)}s</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load AI decisions:', error);
    }
}

// 加载配置变更记录
async function loadConfigChanges() {
    try {
        const changes = await API.getConfigChanges();
        const tbody = document.getElementById('config-changes-body');
        if (!tbody) return;
        
        tbody.innerHTML = changes.map(change => `
            <tr class="border-b hover:bg-gray-50 transition-colors">
                <td class="px-6 py-4 text-sm text-gray-600">${change.timestamp}</td>
                <td class="px-6 py-4 text-sm text-gray-800">${change.config_section}</td>
                <td class="px-6 py-4 text-sm text-gray-800">${change.config_key}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${htmlEscape(change.old_value)}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${htmlEscape(change.new_value)}</td>
                <td class="px-6 py-4 text-sm text-gray-600">${change.change_source}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Failed to load config changes:', error);
    }
}

// 显示 AI 日志详情
function showAILogDetail(index, type) {
    const log = allAILogs[index];
    if (!log) return;
    const title = type === 'request' ? '请求详情' : '响应详情';
    const content = type === 'request' ? log.request_payload : log.response_body;
    showDetail(title, content);
}

// 显示 AI 决策详情
function showAIDecisionDetail(index) {
    const decision = allAIDecisions[index];
    if (!decision) return;
    showDetail('决策结果详情', decision.decision_result);
}

// 清除日志
async function clearLogs(logType) {
    if (confirm(`确定要清除${logType === 'all' ? '所有' : logType}日志吗？`)) {
        try {
            const result = await API.clearLogs(logType);
            if (result.success) {
                alert('日志已清除');
                if (logType === 'ai_logs') loadAILogs();
                else if (logType === 'ai_decisions') loadAIDecisions();
                else if (logType === 'config_changes') loadConfigChanges();
                else if (logType === 'all') {
                    loadDashboardData();
                    loadAILogs();
                    loadAIDecisions();
                    loadConfigChanges();
                }
            } else {
                alert('日志清除失败: ' + result.message);
            }
        } catch (error) {
            console.error('Failed to clear logs:', error);
            alert('日志清除失败');
        }
    }
}
