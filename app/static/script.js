/**
 * Face2MBTI 前端交互逻辑
 */

// DOM 元素
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewArea = document.getElementById('previewArea');
const previewImage = document.getElementById('previewImage');
const changeBtn = document.getElementById('changeBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const uploadSection = document.getElementById('uploadSection');
const loadingSection = document.getElementById('loadingSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const retryBtn = document.getElementById('retryBtn');
const errorRetryBtn = document.getElementById('errorRetryBtn');

let selectedFile = null;

// ============ 上传相关 ============

// 点击上传区域触发文件选择
uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// 文件选择变化
fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleFileSelect(file);
});

// 拖拽上传
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFileSelect(file);
    }
});

// 处理文件选择
function handleFileSelect(file) {
    if (!file.type.startsWith('image/')) {
        alert('请选择图片文件');
        return;
    }
    if (file.size > 10 * 1024 * 1024) {
        alert('图片文件过大，请选择小于 10MB 的图片');
        return;
    }

    selectedFile = file;

    // 显示预览
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImage.src = e.target.result;
        uploadArea.style.display = 'none';
        previewArea.style.display = 'block';
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

// 更换照片
changeBtn.addEventListener('click', () => {
    resetUpload();
    fileInput.click();
});

// ============ 分析逻辑 ============

analyzeBtn.addEventListener('click', startAnalysis);

async function startAnalysis() {
    if (!selectedFile) return;

    // 显示加载状态
    uploadSection.style.display = 'none';
    loadingSection.style.display = 'block';
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';

    // 模拟步骤进度
    simulateSteps();

    // 发送请求
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '分析失败');
        }

        if (data.error) {
            showError(data.message || '分析失败，请重试');
        } else {
            showResult(data);
        }
    } catch (error) {
        showError(error.message || '网络错误，请重试');
    }
}

// 模拟步骤进度动画
function simulateSteps() {
    const steps = ['step1', 'step2', 'step3', 'step4'];
    let current = 0;

    const interval = setInterval(() => {
        if (current > 0) {
            document.getElementById(steps[current - 1]).classList.remove('active');
            document.getElementById(steps[current - 1]).classList.add('done');
        }
        if (current < steps.length) {
            document.getElementById(steps[current]).classList.add('active');
            current++;
        } else {
            clearInterval(interval);
        }
    }, 3000);

    // 存储 interval 以便在结果到来时清除
    window._stepInterval = interval;
}

// ============ 结果展示 ============

function showResult(data) {
    if (window._stepInterval) clearInterval(window._stepInterval);

    loadingSection.style.display = 'none';
    resultSection.style.display = 'flex';

    // 填充数据
    document.getElementById('mbtiType').textContent = data.mbti_type;
    document.getElementById('mbtiNickname').textContent = data.nickname;
    document.getElementById('resultDescription').textContent = data.description;
    document.getElementById('confidenceValue').textContent = data.confidence + '%';

    // 匹配度进度条动画
    setTimeout(() => {
        document.getElementById('confidenceBar').style.width = data.confidence + '%';
    }, 100);

    // 渲染四个维度
    renderDimensions(data.dimensions);

    // 渲染面部分析（使用 Markdown）
    renderFaceAnalysis(data.face_analysis);
}

// 渲染四维度分析
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

// 渲染面部分析（Markdown）
function renderFaceAnalysis(analysis) {
    const faceAnalysisEl = document.getElementById('faceAnalysis');
    if (analysis && typeof marked !== 'undefined') {
        // 使用 marked.js 渲染 Markdown
        faceAnalysisEl.innerHTML = marked.parse(analysis);
    } else {
        // 降级为纯文本
        faceAnalysisEl.textContent = analysis || '';
    }
}

// 面部分析展开/收起
const analysisToggle = document.getElementById('analysisToggle');
const analysisContent = document.getElementById('analysisContent');
const toggleArrow = document.getElementById('toggleArrow');

analysisToggle.addEventListener('click', () => {
    const isExpanded = analysisContent.style.display !== 'none';
    analysisContent.style.display = isExpanded ? 'none' : 'block';
    toggleArrow.classList.toggle('expanded', !isExpanded);
});

// ============ 错误处理 ============

function showError(message) {
    if (window._stepInterval) clearInterval(window._stepInterval);

    loadingSection.style.display = 'none';
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
}

// ============ 重试 ============

retryBtn.addEventListener('click', resetAll);
errorRetryBtn.addEventListener('click', resetAll);

function resetAll() {
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    loadingSection.style.display = 'none';
    uploadSection.style.display = 'flex';
    resetUpload();
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    previewArea.style.display = 'none';
    uploadArea.style.display = 'block';
    analyzeBtn.disabled = true;

    // 重置步骤状态
    ['step1', 'step2', 'step3', 'step4'].forEach(id => {
        const el = document.getElementById(id);
        el.classList.remove('active', 'done');
    });
    document.getElementById('step1').classList.add('active');
    document.getElementById('confidenceBar').style.width = '0%';
    
    // 重置面部分析收起状态
    document.getElementById('analysisContent').style.display = 'none';
    document.getElementById('toggleArrow').classList.remove('expanded');
}
