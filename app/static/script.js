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
const actionButtons = document.getElementById('actionButtons');
const btnUpload = document.getElementById('btnUpload');
const btnCamera = document.getElementById('btnCamera');

// 摄像头相关
const cameraModal = document.getElementById('cameraModal');
const cameraVideo = document.getElementById('cameraVideo');
const cameraCanvas = document.getElementById('cameraCanvas');
const cameraCapture = document.getElementById('cameraCapture');
const cameraSwitch = document.getElementById('cameraSwitch');
const cameraClose = document.getElementById('cameraClose');
const cameraOverlay = document.getElementById('cameraOverlay');
const cameraRetake = document.getElementById('cameraRetake');
const btnRetake = document.getElementById('btnRetake');
const btnUsePhoto = document.getElementById('btnUsePhoto');

let selectedFile = null;
let cameraStream = null;
let facingMode = 'user'; // 'user' = 前置, 'environment' = 后置
let capturedBlob = null;
let uploadedPhotoDataUrl = null; // 存储上传照片的 Data URL
let isSubmitting = false; // 防止重复提交
let loadingStartTime = 0; // loading 开始时间
const MIN_LOADING_MS = 2000; // 最小 loading 展示时间（2秒）

// ============ 上传相关 ============

// 点击上传区显示操作按钮
uploadArea.addEventListener('click', () => {
    actionButtons.style.display = 'flex';
    uploadArea.style.borderColor = 'rgba(255, 255, 255, 0.8)';
});

// 选择照片按钮
btnUpload.addEventListener('click', () => {
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
        uploadedPhotoDataUrl = e.target.result;
        previewImage.src = uploadedPhotoDataUrl;
        uploadArea.style.display = 'none';
        actionButtons.style.display = 'none';
        previewArea.style.display = 'block';
        analyzeBtn.disabled = false;
    };
    reader.readAsDataURL(file);
}

// 更换照片
changeBtn.addEventListener('click', () => {
    resetUpload();
    actionButtons.style.display = 'flex';
});

// ============ 摄像头拍照 ============

// 打开摄像头
btnCamera.addEventListener('click', async () => {
    try {
        await openCamera();
    } catch (err) {
        alert('无法访问摄像头：' + err.message + '\n\n请确保已授权摄像头权限，并使用 HTTPS 或 localhost 访问。');
    }
});

async function openCamera() {
    cameraModal.classList.add('active');
    cameraRetake.style.display = 'none';
    document.querySelector('.camera-controls').style.display = 'flex';
    cameraVideo.style.display = 'block';
    capturedBlob = null;

    const constraints = {
        video: {
            facingMode: facingMode,
            width: { ideal: 1280 },
            height: { ideal: 720 }
        },
        audio: false
    };

    cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
    cameraVideo.srcObject = cameraStream;

    // 检测是否支持切换摄像头（移动端）
    const tracks = cameraStream.getVideoTracks();
    const capabilities = tracks[0]?.getCapabilities?.();
    cameraSwitch.style.display = capabilities?.facingMode ? 'block' : 'none';
}

function closeCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach(track => track.stop());
        cameraStream = null;
    }
    cameraVideo.srcObject = null;
    cameraModal.classList.remove('active');
}

// 拍照
cameraCapture.addEventListener('click', () => {
    const ctx = cameraCanvas.getContext('2d');
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    ctx.drawImage(cameraVideo, 0, 0);

    cameraCanvas.toBlob((blob) => {
        capturedBlob = blob;
        // 显示拍到的画面
        const url = URL.createObjectURL(blob);
        cameraVideo.style.display = 'none';
        
        // 用 video 元素显示拍摄结果
        const img = document.createElement('img');
        img.src = url;
        img.className = 'captured-image';
        img.id = 'capturedPreview';
        
        const viewport = document.querySelector('.camera-viewport');
        const existing = document.getElementById('capturedPreview');
        if (existing) existing.remove();
        viewport.appendChild(img);

        document.querySelector('.camera-controls').style.display = 'none';
        cameraRetake.style.display = 'flex';
    }, 'image/jpeg', 0.92);
});

// 重拍
btnRetake.addEventListener('click', () => {
    const preview = document.getElementById('capturedPreview');
    if (preview) preview.remove();
    cameraVideo.style.display = 'block';
    document.querySelector('.camera-controls').style.display = 'flex';
    cameraRetake.style.display = 'none';
    capturedBlob = null;
});

// 使用此照片
btnUsePhoto.addEventListener('click', () => {
    if (!capturedBlob) return;
    const file = new File([capturedBlob], 'camera_' + Date.now() + '.jpg', { type: 'image/jpeg' });
    closeCamera();
    handleFileSelect(file);
});

// 切换前后摄像头
cameraSwitch.addEventListener('click', async () => {
    facingMode = facingMode === 'user' ? 'environment' : 'user';
    closeCamera();
    try {
        await openCamera();
    } catch (err) {
        alert('切换摄像头失败：' + err.message);
    }
});

// 关闭摄像头
cameraClose.addEventListener('click', closeCamera);
cameraOverlay.addEventListener('click', closeCamera);

// ============ 分析逻辑 ============

analyzeBtn.addEventListener('click', startAnalysis);

async function startAnalysis() {
    if (!selectedFile || isSubmitting) return;

    // 防止重复提交
    isSubmitting = true;
    analyzeBtn.disabled = true;

    // 记录 loading 开始时间
    loadingStartTime = Date.now();

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
            throw new Error(data.detail || '提交失败');
        }

        // 获取 task_id 和轮询间隔
        const { task_id, poll_interval } = data;
        const intervalMs = (poll_interval || 5) * 1000;

        // 开始轮询任务状态
        pollTaskResult(task_id, intervalMs);
    } catch (error) {
        showError(error.message || '网络错误，请重试');
    }
}

// 轮询任务结果
async function pollTaskResult(taskId, intervalMs) {
    async function checkOnce() {
        try {
            const response = await fetch(`/api/task/${taskId}?t=${Date.now()}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.detail || '查询任务失败');
            }

            if (data.status === 'COMPLETED') {
                if (data.result) {
                    data.result.media_url = data.media_url;
                    showResult(data.result);
                } else {
                    showError('分析完成但未返回结果，请重试');
                }
                return true; // 已完成
            } else if (data.status === 'FAILED') {
                showError(data.error || '分析失败，请重试');
                return true; // 已完成
            }
            // PENDING / PROCESSING 继续轮询
            return false;
        } catch (error) {
            showError(error.message || '网络错误，请重试');
            return true; // 出错停止轮询
        }
    }

    // 立即检查一次
    const done = await checkOnce();
    if (done) return;

    // 之后定时轮询
    const poll = setInterval(async () => {
        const finished = await checkOnce();
        if (finished) clearInterval(poll);
    }, intervalMs);

    window._pollInterval = poll;
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
    }, 5000);

    // 存储 interval 以便在结果到来时清除
    window._stepInterval = interval;
}

// ============ 结果展示 ============

function showResult(data) {
    if (window._stepInterval) clearInterval(window._stepInterval);
    if (window._pollInterval) clearInterval(window._pollInterval);

    // 校验必要字段，数据不合法则展示错误
    if (!data || !data.mbti_type) {
        showError('分析结果数据异常，请重试');
        return;
    }

    // 确保 loading 至少展示 MIN_LOADING_MS 毫秒
    const elapsed = Date.now() - loadingStartTime;
    const delay = Math.max(0, MIN_LOADING_MS - elapsed);

    setTimeout(() => {
        loadingSection.style.display = 'none';
        resultSection.style.display = 'flex';

        // 展示上传的照片
        if (data.media_url) {
            document.getElementById('resultPhoto').src = data.media_url;
        } else if (uploadedPhotoDataUrl) {
            document.getElementById('resultPhoto').src = uploadedPhotoDataUrl;
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

        // 重置提交状态
        isSubmitting = false;
    }, delay);
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

analysisToggle.addEventListener('click', () => {
    const isExpanded = analysisContent.style.display !== 'none';
    analysisContent.style.display = isExpanded ? 'none' : 'block';
    analysisToggle.classList.toggle('expanded', !isExpanded);
    analysisToggle.textContent = isExpanded ? '查看详情 ▾' : '收起详情 ▴';
});

// ============ 错误处理 ============

function showError(message) {
    if (window._stepInterval) clearInterval(window._stepInterval);
    if (window._pollInterval) clearInterval(window._pollInterval);

    // 确保 loading 至少展示 MIN_LOADING_MS 毫秒，避免闪退
    const elapsed = Date.now() - loadingStartTime;
    const delay = Math.max(0, MIN_LOADING_MS - elapsed);

    setTimeout(() => {
        loadingSection.style.display = 'none';
        errorSection.style.display = 'block';
        document.getElementById('errorMessage').textContent = message;
        // 重置提交状态
        isSubmitting = false;
    }, delay);
}

// ============ 重试 ============

retryBtn.addEventListener('click', resetAll);
errorRetryBtn.addEventListener('click', resetAll);

function resetAll() {
    if (window._pollInterval) clearInterval(window._pollInterval);
    resultSection.style.display = 'none';
    errorSection.style.display = 'none';
    loadingSection.style.display = 'none';
    uploadSection.style.display = 'flex';
    isSubmitting = false;
    resetUpload();
}

function resetUpload() {
    selectedFile = null;
    uploadedPhotoDataUrl = null;
    fileInput.value = '';
    previewArea.style.display = 'none';
    uploadArea.style.display = 'block';
    actionButtons.style.display = 'none';
    uploadArea.style.borderColor = '';
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
    const toggleBtn = document.getElementById('analysisToggle');
    toggleBtn.classList.remove('expanded');
    toggleBtn.textContent = '查看详情 ▾';
}
