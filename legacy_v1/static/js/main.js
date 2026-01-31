/**
 * 页面初始化与导航逻辑
 */

document.addEventListener('DOMContentLoaded', () => {
    // 导航切换
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => {
            const section = item.dataset.section;
            
            // 移除所有导航的 active 类
            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
            
            // 移除所有内容区域的 active 类
            document.querySelectorAll('.content-section').forEach(content => content.classList.remove('active'));
            
            // 添加当前导航的 active 类
            item.classList.add('active');
            
            // 添加当前内容区域的 active 类
            document.getElementById(section).classList.add('active');
            
            // 根据 section 加载数据
            switch (section) {
                case 'dashboard': loadDashboardData(); break;
                case 'ai-logs': loadAILogs(); break;
                case 'ai-decisions': loadAIDecisions(); break;
                case 'config-changes': loadConfigChanges(); break;
                case 'config': loadConfig(); break;
                case 'config-v2': if (typeof loadConfigV2Page === 'function') loadConfigV2Page(); break;
                case 'personas': loadPersonas(); break;
                case 'memories': loadMemories(); break;
                case 'prompts': loadPrompts(); break;
            }
        });
    });

    // 过滤器功能
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            // 具体的过滤逻辑可以在各自的 JS 中根据 active 按钮状态来处理
        });
    });

    // 初始化 Persona 表单
    if (typeof initPersonaForms === 'function') initPersonaForms();

    // 初始化页面数据
    loadDashboardData();

    // 每 3 秒自动刷新仪表盘
    setInterval(() => {
        const activeSection = document.querySelector('.content-section.active');
        if (activeSection && activeSection.id === 'dashboard') {
            loadDashboardData();
        }
    }, 3000);
});
