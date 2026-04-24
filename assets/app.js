// assets/app.js

// Stages: 0: Intro/Login, 1: Video, 2: Simulator, 3: Survey, 4: Outro

const CURRICULUM = [
    { id: 0, title: "✨ 0. ETHOS 소개", items: ["프로그램 소개"], url: 'intro_v2.html' },
    { id: 1, title: "📖 1. AI 윤리 교육 영상", items: ["AI 윤리 개념", "AI 프라이버시", "정보 보호", "할루시네이션", "알고리즘 편향", "AI 사용 명시"], url: 'video_v2.html' },
    { id: 2, title: "💬 2. 시나리오 시뮬레이터", items: ["시나리오 소개", "챗봇 시뮬레이션"], url: 'chatbot_v2.html' },
    { id: 3, title: '만족도 조사', url: 'survey_v2.html', items: ['만족도 테스트'] },
    { id: 4, title: "📄 4. 마치며/안내", items: ["교육 정리 및 수료증"], url: 'outro_v2.html' }
];

const STAGE_PROGRESS = [0, 20, 60, 80, 100];

// State Management
const State = {
    getUser: () => JSON.parse(localStorage.getItem('ethos_user') || 'null'),
    setUser: (userObj) => localStorage.setItem('ethos_user', JSON.stringify(userObj)),
    getStage: () => parseInt(localStorage.getItem('ethos_stage') || '0', 10),
    setStage: (stageNum) => localStorage.setItem('ethos_stage', stageNum.toString()),
    logout: () => {
        localStorage.removeItem('ethos_user');
        localStorage.removeItem('ethos_stage');
        localStorage.removeItem('ethos_video_idx');
        localStorage.removeItem('ethos_video_finished');
        localStorage.removeItem('ethos_sim_started');
        localStorage.removeItem('ethos_active_scenario');
        localStorage.removeItem('ethos_chat_history');
        window.location.href = 'index.html';
    }
};

// UI Components Render
function renderSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    const curStage = State.getStage();
    const curPercent = STAGE_PROGRESS[curStage] || 0;

    // Video specific logic
    const videoIdx = parseInt(localStorage.getItem('ethos_video_idx') || '0', 10);

    let html = `
        <h3>학습 목차</h3>
        <div class="sidebar-sub">순서대로 진행해주세요</div>
        
        <div class="progress-section">
            <div class="progress-header">
                <span>전체 진행률</span>
                <span class="progress-percent">${curPercent}%</span>
            </div>
            <div class="progress-bar-bg">
                <div class="progress-bar-fill" style="width: ${curPercent}%;"></div>
            </div>
        </div>
        
        <div class="tree-nav">
    `;

    const groupIcons = ['auto_awesome', 'menu_book', 'forum', 'edit_document', 'flag'];

    CURRICULUM.forEach((group, i) => {
        let isDone = i < curStage;
        let isActive = i === curStage;
        let isUpcoming = i > curStage;

        // Node Status Styling
        let groupIconClass = '';
        if (isDone) groupIconClass = 'done';
        else if (isActive) groupIconClass = 'active';

        let groupIconStr = groupIcons[i] || 'folder';
        let lastGroupClass = (i === CURRICULUM.length - 1) ? 'last-group' : '';
        let noChildrenClass = (group.items.length === 0) ? 'no-children' : '';

        let titleHtml = group.title;
        if (isDone || isActive) {
            let targetUrl = group.url || '#';
            titleHtml = `<a href="${targetUrl}" style="text-decoration:none; color:inherit; display:block; width:100%;" onclick="if(event.currentTarget.getAttribute('href')==='#') event.preventDefault();">${group.title}</a>`;
        }

        html += `<div class="tree-group">
            <div class="tree-group-header">
                <div class="tree-group-icon ${groupIconClass}">
                    <span class="material-symbols-rounded" style="font-size: 1.2rem;">${groupIconStr}</span>
                </div>
                <div class="tree-group-title" style="color: ${(isActive || isDone) ? 'var(--c-ink-900)' : 'var(--c-ink-500)'}; width:100%; cursor:${(isDone || isActive) ? 'pointer' : 'default'};">
                    ${titleHtml}
                </div>
            </div>
            <div class="tree-children ${lastGroupClass} ${noChildrenClass}">`;

        group.items.forEach((item, j) => {
            let itemStatus = 'upcoming';
            let itemIconStr = 'radio_button_unchecked';
            let itemLinkAble = false;

            if (i < curStage) {
                itemStatus = 'done';
                itemIconStr = 'check_circle';
                itemLinkAble = true;
            } else if (i === curStage) {
                if (i === 1) { // Video stage logic
                    if (j < videoIdx) {
                        itemStatus = 'done'; itemIconStr = 'check_circle'; itemLinkAble = true;
                    }
                    else if (j === videoIdx) {
                        itemStatus = 'active'; itemIconStr = 'radio_button_checked'; itemLinkAble = true;
                    }
                } else {
                    itemStatus = 'active';
                    itemIconStr = 'radio_button_checked';
                    itemLinkAble = true;
                }
            }

            let lastChildClass = (j === group.items.length - 1) ? 'last-child' : '';

            let itemContent = `<span>${item}</span>`;
            if (itemLinkAble) {
                let nodeUrl = group.url || '#';
                // 비디오 탭의 경우 해당 비디오 인덱스로 이동하는 기능이 필요할 경우 여기서 분기 (지금은 페이지 이동만 구현)
                itemContent = `<a href="${nodeUrl}" style="text-decoration:none; color:inherit; display:flex; align-items:center; width:100%; cursor:pointer;" onclick="if('${nodeUrl}'==='#') { event.preventDefault(); return false; } if(${i === 1}){ localStorage.setItem('ethos_video_idx', '${j}'); }">${item}</a>`;
            }

            html += `<div class="tree-child ${itemStatus} ${lastChildClass}">
                <span class="material-symbols-rounded tree-child-icon" style="font-size: 1.1rem;">${itemIconStr}</span>
                ${itemContent}
            </div>`;
        });

        html += `</div></div>`;
    });

    html += `</div>`;
    sidebar.innerHTML = html;
}

function renderTopbar() {
    const topbar = document.getElementById('topbar');
    if (!topbar) return;

    const user = State.getUser();
    if (!user) return;

    topbar.innerHTML = `
        <div class="topbar-left" onclick="window.location.href='intro_v2.html'" style="cursor: pointer;">
            <img src="assets/logo-hor.png" class="logo-icon" alt="ETHOS">
            <div class="topbar-title">
                <h4>AI 윤리 교육 플랫폼</h4>
                <span>${user.name}님 환영합니다</span>
            </div>
        </div>
        <div class="topbar-right">
            ${user.isAdmin
            ? '<button class="btn btn-secondary" onclick="window.location.href=\'intro_v2.html\'">👥 사용자 모드</button>'
            : '<button class="btn btn-secondary" onclick="window.location.href=\'admin_v2.html\'">⚙️ 관리자 페이지</button>'}
            <button class="btn btn-secondary" onclick="State.logout()">🚪 로그아웃</button>
        </div>
    `;
}

// Authentication Check on Page Load
function checkAuth() {
    const user = State.getUser();
    const currentPage = window.location.pathname.split('/').pop() || 'index_v2.html';

    if (!user && currentPage !== 'index_v2.html' && currentPage !== '') {
        window.location.href = 'index_v2.html';
        return false;
    }

    if (user && (currentPage === 'index_v2.html' || currentPage === '')) {
        // Clear all session info when moving to login page
        localStorage.removeItem('ethos_user');
        localStorage.removeItem('ethos_stage');
        localStorage.removeItem('ethos_video_idx');
        localStorage.removeItem('ethos_video_finished');
        localStorage.removeItem('ethos_sim_started');
        localStorage.removeItem('ethos_active_scenario');
        localStorage.removeItem('ethos_chat_history');

        State.setUser(null);
        return false;
    }

    // Render Layout Parts
    renderSidebar();
    renderTopbar();
    return true;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', checkAuth);
