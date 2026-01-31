/**
 * 配置管理相关逻辑
 */

// 加载配置
async function loadConfig() {
    try {
        const config = await API.getConfig();
        const container = document.getElementById('current-config');
        if (!container) return;
        
        container.innerHTML = `
            <textarea id="config-editor" class="w-full h-96 font-mono text-sm p-4 bg-gray-900 text-green-400 rounded-lg border-2 border-gray-700 focus:border-blue-500 focus:outline-none shadow-inner">${htmlEscape(JSON.stringify(config, null, 2))}</textarea>
        `;
        
        // 配置说明
        const documentation = document.getElementById('config-documentation');
        if (documentation) {
            documentation.innerHTML = `
                <p><strong>memory:</strong> 内存管理配置</p>
                <ul class="ml-4 mt-1">
                    <li><code>high_watermark</code>: 触发归档的消息数量</li>
                    <li><code>summary_interval</code>: 每次归档并移除的消息数量</li>
                    <li><code>enable_episodic</code>: 是否开启情节记忆</li>
                </ul>
                
                <p class="mt-2"><strong>interaction:</strong> 交互配置</p>
                <ul class="ml-4 mt-1">
                    <li><code>response_wait_time</code>: 响应等待窗口（秒），防抖时间</li>
                    <li><code>group_response_wait_time</code>: 群聊防抖时间</li>
                    <li><code>whitelist</code>: 允许触发 AI 的用户 UID 列表</li>
                    <li><code>group_whitelist</code>: 允许触发 AI 的群号列表</li>
                    <li><code>default_persona</code>: 新用户默认激活的人格名称</li>
                </ul>
                
                <p class="mt-2"><strong>ai:</strong> AI 配置</p>
                <ul class="ml-4 mt-1">
                    <li><code>global_switch</code>: AI 总开关</li>
                    <li><code>mention_mode_only</code>: 是否仅在被 @ 时回复</li>
                    <li><code>enable_group</code>: 群聊开关</li>
                    <li><code>enable_private</code>: 私聊开关</li>
                    <li><code>show_thinking</code>: 是否在回复中显示思考过程</li>
                </ul>
            `;
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
}

// 保存配置
async function saveConfig() {
    try {
        const currentConfig = document.getElementById('config-editor').value;
        const config = JSON.parse(currentConfig);
        const result = await API.saveConfig(config);
        
        if (result.success) {
            alert('配置保存成功');
        } else {
            alert('配置保存失败: ' + result.message);
        }
    } catch (error) {
        console.error('Failed to save config:', error);
        alert('配置保存失败');
    }
}

// 重置配置
async function resetConfig() {
    if (confirm('确定要重置所有配置为默认值吗？')) {
        try {
            const result = await API.resetConfig();
            if (result.success) {
                alert('配置已重置为默认值');
                loadConfig();
            } else {
                alert('配置重置失败: ' + result.message);
            }
        } catch (error) {
            console.error('Failed to reset config:', error);
            alert('配置重置失败');
        }
    }
}
