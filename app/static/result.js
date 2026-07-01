/**
 * Face2MBTI 任务结果展示页
 * 通过 URL 参数 ?task_id=xxx 自动加载并展示结果
 */

// DOM 元素
const loadingSection = document.getElementById('loadingSection');
const processingSection = document.getElementById('processingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');

const POLL_INTERVAL_MS = 5000; // 轮询间隔 5 秒

// ============ 页面初始化 ============

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    const taskId = params.get('task_id');

    if (!taskId) {
        showError('缺少任务批次号，请通过正确的链接访问');
        return;
    }

    // 启动步骤动画
    startProcessingAnimation();
    // 加载任务结果
    loadTaskResult(taskId);
});

// ============ 加载任务结果 ============

async function loadTaskResult(taskId) {
    try {
        const response = await fetch(`/api/task/${taskId}?t=${Date.now()}`);
        const data = await response.json();

        if (!response.ok) {
            if (response.status === 404) {
                showError('任务不存在，请检查批次号是否正确');
            } else {
                showError(data.detail || '查询任务失败');
            }
            return;
        }

        handleTaskStatus(taskId, data);
    } catch (error) {
        showError('网络错误，请稍后重试');
    }
}

// ============ 处理任务状态 ============

function handleTaskStatus(taskId, data) {
    switch (data.status) {
        case 'COMPLETED':
            if (data.result) {
                data.result.media_url = data.media_url;
                showResult(data.result);
            } else {
                showError('分析完成但未返回结果');
            }
            break;

        case 'FAILED':
            showError(data.error || '分析失败，请重试');
            break;

        case 'PENDING':
        case 'PROCESSING':
            // 继续轮询
            setTimeout(() => loadTaskResult(taskId), POLL_INTERVAL_MS);
            break;

        default:
            showError('未知的任务状态');
    }
}

// ============ 结果展示 ============

function showResult(data) {
    // 校验必要字段
    if (!data || !data.mbti_type) {
        showError('分析结果数据异常');
        return;
    }

    loadingSection.style.display = 'none';
    processingSection.style.display = 'none';
    resultSection.style.display = 'flex';

    // 展示上传的照片或视频
    const photoEl = document.getElementById('resultPhoto');
    const videoEl = document.getElementById('resultVideo');
    const mediaTitleEl = document.getElementById('mediaTitle');

    if (data.media_url) {
        const isVideo = /\.(mp4|webm|mov|avi|mkv)$/i.test(data.media_url);
        if (isVideo) {
            videoEl.src = data.media_url;
            videoEl.style.display = 'block';
            photoEl.style.display = 'none';
            mediaTitleEl.textContent = '你的视频';
        } else {
            photoEl.src = data.media_url;
            photoEl.style.display = 'block';
            videoEl.style.display = 'none';
            mediaTitleEl.textContent = '你的照片';
        }
    } else {
        photoEl.style.display = 'none';
        videoEl.style.display = 'none';
        document.getElementById('mediaModule').style.display = 'none';
    }

    // 填充数据
    document.getElementById('mbtiType').textContent = data.mbti_type;
    document.getElementById('mbtiNickname').textContent = data.nickname || '';
    document.getElementById('resultDescription').textContent = data.description || '';
    document.getElementById('confidenceValue').textContent = (data.confidence ?? 0) + '%';

    // 匹配度进度条动画
    setTimeout(() => {
        document.getElementById('confidenceBar').style.width = (data.confidence ?? 0) + '%';
    }, 100);

    // 渲染四个维度
    renderDimensions(data.dimensions);

    // 渲染面部分析
    renderFaceAnalysis(data.face_analysis);
}

// ============ 渲染四维度分析 ============

function renderDimensions(dimensions) {
    const dimensionsEl = document.getElementById('dimensions');
    dimensionsEl.innerHTML = '';

    const dimensionLabels = {
        'EI': { label: 'E vs I', full: '外向 / 内向' },
        'SN': { label: 'S vs N', full: '感觉 / 直觉' },
        'TF': { label: 'T vs F', full: '思维 / 情感' },
        'JP': { label: 'J vs P', full: '判断 / 感知' },
    };

    if (dimensions) {
        Object.entries(dimensions).forEach(([key, value]) => {
            const config = dimensionLabels[key] || { label: key, full: key };
            const item = document.createElement('div');
            item.className = 'dimension-item';
            item.innerHTML = `
                <div class="dimension-header">
                    <span class="dimension-label">${config.full}</span>
                    <span class="dimension-score">${value.score}%</span>
                </div>
                <div class="dimension-letter">${value.result}</div>
                <div class="dimension-bar">
                    <div class="dimension-bar-fill" style="width: ${value.score}%"></div>
                </div>
                <div class="dimension-reason">${value.reason}</div>
            `;
            dimensionsEl.appendChild(item);
        });
    }
}

// ============ 渲染面部分析（Markdown） ============

function renderFaceAnalysis(analysis) {
    const faceAnalysisEl = document.getElementById('faceAnalysis');
    if (analysis && typeof marked !== 'undefined') {
        faceAnalysisEl.innerHTML = marked.parse(analysis);
    } else {
        faceAnalysisEl.textContent = analysis || '';
    }
}

// ============ 面部分析展开/收起 ============

const analysisToggle = document.getElementById('analysisToggle');
const analysisContent = document.getElementById('analysisContent');

analysisToggle.addEventListener('click', () => {
    const isExpanded = analysisContent.style.display !== 'none';
    analysisContent.style.display = isExpanded ? 'none' : 'block';
    analysisToggle.classList.toggle('expanded', !isExpanded);
    analysisToggle.textContent = isExpanded ? '查看详情 ▾' : '收起详情 ▴';
});

// ============ 错误处理 ============

function showError(message) {
    loadingSection.style.display = 'none';
    processingSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

// ============ 处理中动画 ============

function startProcessingAnimation() {
    const steps = ['pStep1', 'pStep2', 'pStep3', 'pStep4'];
    let current = 0;

    setInterval(() => {
        if (current > 0) {
            document.getElementById(steps[current - 1]).classList.remove('active');
            document.getElementById(steps[current - 1]).classList.add('done');
        }
        if (current < steps.length) {
            document.getElementById(steps[current]).classList.add('active');
            current++;
        }
    }, 5000);
}
