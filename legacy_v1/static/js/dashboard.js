/**
 * 仪表盘相关逻辑
 */

// 渲染最近 AI 交互
function renderRecentAILogs(logs) {
    const container = document.getElementById('recent-ai-logs');
    if (!container) return;
    container.innerHTML = logs.map(log => `
        <div class="border-l-4 border-blue-500 pl-4 py-3 bg-white rounded-lg shadow-sm">
            <div class="text-sm font-medium text-gray-800">${log.timestamp}</div>
            <div class="text-xs text-gray-600">${log.model} - ${log.duration.toFixed(2)}s</div>
        </div>
    `).join('');
}

// 渲染最近 AI 决策
function renderRecentAIDecisions(decisions) {
    const container = document.getElementById('recent-ai-decisions');
    if (!container) return;
    container.innerHTML = decisions.map(decision => {
        let decisionTypeText = '';
        switch (decision.decision_type) {
            case 'entry': decisionTypeText = '准入决策'; break;
            case 'micro': decisionTypeText = '微观决策'; break;
            case 'macro': decisionTypeText = '宏观决策'; break;
        }
        
        return `
            <div class="border-l-4 border-green-500 pl-4 py-3 bg-white rounded-lg shadow-sm">
                <div class="text-sm font-medium text-gray-800">${decision.timestamp}</div>
                <div class="text-xs text-gray-600">${decisionTypeText} - ${decision.duration.toFixed(2)}s</div>
            </div>
        `;
    }).join('');
}

// 渲染用户活跃度
function renderUserActivity(activity) {
    const container = document.getElementById('user-activity-list');
    if (!container) return;
    
    if (activity.length === 0) {
        container.innerHTML = '<div class="py-4 text-center text-gray-400">暂无活跃用户数据</div>';
        return;
    }
    
    container.innerHTML = activity.map((user, index) => {
        const medalColors = ['text-yellow-500', 'text-gray-400', 'text-amber-600'];
        const medalIcon = index < 3 ? `<i class="fas fa-medal ${medalColors[index]} mr-2"></i>` : `<span class="inline-block w-6 text-center mr-2 text-gray-400 font-bold">${index + 1}</span>`;
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                <div class="flex items-center space-x-3 overflow-hidden">
                    ${medalIcon}
                    <div class="overflow-hidden">
                        <p class="text-sm font-bold text-gray-800 truncate">${user.nickname}</p>
                        <p class="text-[10px] text-gray-500 truncate">ID: ${user.user_id} | Session: ${user.session_id}</p>
                    </div>
                </div>
                <div class="text-right flex-shrink-0 ml-4">
                    <p class="text-sm font-bold text-purple-600">${user.message_count} 消息</p>
                    <p class="text-[10px] text-gray-400">最后活跃: ${user.last_message_time.split(' ')[1]}</p>
                </div>
            </div>
        `;
    }).join('');
}

// 渲染最近配置变更
function renderRecentConfigChanges(changes) {
    const container = document.getElementById('recent-config-changes');
    if (!container) return;
    container.innerHTML = changes.map(change => `
        <div class="border-l-4 border-yellow-500 pl-4 py-3 bg-white rounded-lg shadow-sm">
            <div class="text-sm font-medium text-gray-800">${change.timestamp}</div>
            <div class="text-xs text-gray-600">${change.config_section}.${change.config_key}: ${change.old_value} -> ${change.new_value}</div>
        </div>
    `).join('');
}

// 加载活跃任务
async function loadActiveTasks() {
    try {
        const tasks = await API.getActiveTasks();
        const container = document.getElementById('active-tasks-container');
        const countBadge = document.getElementById('active-tasks-count');
        
        if (countBadge) countBadge.textContent = `活跃: ${tasks.length}`;
        if (!container) return;
        
        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="col-span-full py-8 text-center bg-white rounded-xl shadow-inner border-2 border-dashed border-gray-200 text-gray-400">
                    <i class="fas fa-ghost mb-2 text-4xl block"></i>
                    暂无活跃处理任务
                </div>
            `;
            return;
        }
        
        container.innerHTML = tasks.map(task => {
            let statusColor = 'blue';
            let icon = 'fa-spinner fa-spin';
            let isPulsing = true;
            
            if (task.status.includes('等待')) {
                statusColor = 'yellow';
                icon = 'fa-clock';
            } else if (task.status.includes('决策')) {
                statusColor = 'purple';
                icon = 'fa-brain';
            } else if (task.status.includes('生成') || task.status.includes('思考')) {
                statusColor = 'green';
                icon = 'fa-magic';
            } else if (task.status.includes('专注模式')) {
                statusColor = 'indigo';
                icon = 'fa-eye';
                if (task.status.includes('空闲')) isPulsing = false;
            }
            
            return `
                <div class="bg-white p-5 rounded-xl shadow-md border-l-4 border-${statusColor}-500 flex items-center space-x-4 ${isPulsing ? 'animate-pulse' : ''}">
                    <div class="bg-${statusColor}-100 p-3 rounded-full">
                        <i class="fas ${icon} text-${statusColor}-600 text-xl"></i>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center justify-between">
                            <p class="text-sm font-bold text-gray-800 truncate">会话: ${task.session_id}</p>
                            ${task.status.includes('专注') ? '<span class="text-[10px] bg-indigo-100 text-indigo-600 px-1.5 py-0.5 rounded font-bold">FOCUS</span>' : ''}
                        </div>
                        <p class="text-xs text-gray-600 mt-1">${task.status}</p>
                        <div class="flex items-center mt-2">
                            <span class="text-[10px] bg-gray-100 text-gray-500 px-2 py-0.5 rounded">消息堆积: ${task.message_count}</span>
                            <span class="text-[10px] text-gray-400 ml-auto">${task.last_update.split(' ')[1]}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (error) {
        console.error('Failed to load active tasks:', error);
    }
}

// 仪表盘数据加载
async function loadDashboardData() {
    try {
        await loadActiveTasks();

        const logs = await API.getAILogs(5);
        const decisions = await API.getAIDecisions(5);
        const configChanges = await API.getConfigChanges(5);
        const activity = await API.getUserActivity(null, 5);
        
        document.getElementById('ai-logs-count').textContent = logs.length >= 50 ? '50+' : logs.length;
        document.getElementById('ai-decisions-count').textContent = decisions.length >= 50 ? '50+' : decisions.length;
        document.getElementById('config-changes-count').textContent = configChanges.length >= 50 ? '50+' : configChanges.length;
        
        renderRecentAILogs(logs);
        renderRecentAIDecisions(decisions);
        renderUserActivity(activity);
        renderRecentConfigChanges(configChanges);
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}
