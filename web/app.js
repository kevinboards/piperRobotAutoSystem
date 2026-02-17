// ============================================================
// Piper Automation System - Web UI
// Adapted from NodeEditor dual-robot timeline system
// ============================================================

// Application State
const state = {
    // WebSocket
    ws: null,
    wsConnected: false,

    // Robot
    robotConnected: false,
    robotEnabled: false,
    isRecording: false,
    isPlaying: false,
    isPaused: false,

    // Recordings library
    recordings: [],

    // Node editor
    nodes: [],
    connections: [],
    selectedNode: null,
    isDragging: false,
    dragOffset: { x: 0, y: 0 },
    isConnecting: false,
    connectionStart: null,

    // Canvas transform
    panOffset: { x: 0, y: 0 },
    scale: 1,
    isPanning: false,
    lastPanPoint: { x: 0, y: 0 },

    // Timer
    timerStart: null,
    timerInterval: null
};

let nodeIdCounter = 0;

// DOM Elements
const el = {
    connIndicator: document.getElementById('conn-indicator'),
    connLabel: document.getElementById('conn-label'),
    robotConnected: document.getElementById('robot-connected'),
    robotEnabled: document.getElementById('robot-enabled'),
    robotState: document.getElementById('robot-state'),
    recordBtn: document.getElementById('record-btn'),
    recordingStatus: document.getElementById('recording-status'),
    recInfo: document.getElementById('rec-info'),
    refreshRecordingsBtn: document.getElementById('refresh-recordings-btn'),
    recordingsList: document.getElementById('recordings-list'),
    playBtn: document.getElementById('play-btn'),
    stopBtn: document.getElementById('stop-btn'),
    pauseBtn: document.getElementById('pause-btn'),
    executionStatus: document.getElementById('execution-status'),
    timer: document.getElementById('timer'),
    loopCheckbox: document.getElementById('loop-checkbox'),
    loopDelay: document.getElementById('loop-delay'),
    globalSpeed: document.getElementById('global-speed'),
    saveBtn: document.getElementById('save-btn'),
    loadBtn: document.getElementById('load-btn'),
    clearBtn: document.getElementById('clear-btn'),
    zoomInBtn: document.getElementById('zoom-in-btn'),
    zoomOutBtn: document.getElementById('zoom-out-btn'),
    zoomResetBtn: document.getElementById('zoom-reset-btn'),
    zoomLevel: document.getElementById('zoom-level'),
    nodeEditor: document.getElementById('node-editor'),
    logOutput: document.getElementById('log-output'),
    timelinesModal: document.getElementById('timelines-modal'),
    timelinesList: document.getElementById('timelines-list'),
    modalCloseBtn: document.getElementById('modal-close-btn'),
    resetRobotBtn: document.getElementById('reset-robot-btn'),
    resetModal: document.getElementById('reset-modal'),
    resetConfirmBtn: document.getElementById('reset-confirm-btn'),
    resetCancelBtn: document.getElementById('reset-cancel-btn')
};

// ============================================================
// Logging
// ============================================================
function log(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const timestamp = new Date().toLocaleTimeString();
    entry.textContent = `[${timestamp}] ${message}`;
    el.logOutput.appendChild(entry);
    el.logOutput.scrollTop = el.logOutput.scrollHeight;

    // Keep log from growing unbounded
    while (el.logOutput.children.length > 500) {
        el.logOutput.removeChild(el.logOutput.firstChild);
    }
}

// ============================================================
// WebSocket Connection
// ============================================================
function connectWebSocket() {
    const wsUrl = `ws://${window.location.hostname || 'localhost'}:8080`;
    log(`Connecting to ${wsUrl}...`);

    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
        state.wsConnected = true;
        el.connIndicator.classList.add('connected');
        el.connLabel.textContent = 'CAN Bus: Connected';
        log('WebSocket connected', 'success');

        // Request initial data
        wsSend({ type: 'get_status' });
        wsSend({ type: 'get_recordings' });
    };

    state.ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleServerMessage(data);
        } catch (err) {
            log(`Error parsing message: ${err.message}`, 'error');
        }
    };

    state.ws.onerror = () => {
        log('WebSocket error', 'error');
    };

    state.ws.onclose = () => {
        state.wsConnected = false;
        el.connIndicator.classList.remove('connected');
        el.connLabel.textContent = 'CAN Bus: Disconnected';
        log('Disconnected. Reconnecting in 3s...', 'warning');
        setTimeout(connectWebSocket, 3000);
    };
}

function wsSend(msg) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        state.ws.send(JSON.stringify(msg));
    }
}

// ============================================================
// Server Message Handling
// ============================================================
function handleServerMessage(data) {
    switch (data.type) {
        case 'status':
            handleStatus(data);
            break;
        case 'recordings_list':
            handleRecordingsList(data);
            break;
        case 'recording_progress':
            handleRecordingProgress(data);
            break;
        case 'playback_progress':
            handlePlaybackProgress(data);
            break;
        case 'timeline_complete':
            handleTimelineComplete();
            break;
        case 'timelines_list':
            handleTimelinesList(data);
            break;
        case 'timeline_loaded':
            handleTimelineLoaded(data);
            break;
        case 'reset_complete':
            handleResetComplete(data);
            break;
        case 'error':
            log(`Server error: ${data.message}`, 'error');
            break;
        case 'log':
            log(data.message, data.level || 'info');
            break;
        default:
            log(`Unknown message: ${data.type}`, 'warning');
    }
}

function handleStatus(data) {
    state.robotConnected = data.connected;
    state.robotEnabled = data.enabled || data.sdk_available || false;

    // Update robot info display
    const connEl = el.robotConnected;
    connEl.textContent = data.connected ? 'Yes' : 'No';
    connEl.className = 'info-value ' + (data.connected ? 'yes' : 'no');

    const enEl = el.robotEnabled;
    const enabledVal = data.enabled || data.sdk_available || false;
    enEl.textContent = enabledVal ? 'Yes' : 'No';
    enEl.className = 'info-value ' + (enabledVal ? 'yes' : 'no');

    // State text
    let stateText = 'Idle';
    if (data.recording) stateText = 'Recording';
    else if (data.playing) stateText = 'Playing';
    el.robotState.textContent = stateText;

    // Update recording/playing state from server
    state.isRecording = data.recording || false;
    state.isPlaying = data.playing || false;

    // Joint angles
    if (data.joints && data.joints.length === 6) {
        for (let i = 0; i < 6; i++) {
            const jel = document.getElementById(`j${i}`);
            if (jel) jel.textContent = data.joints[i].toFixed(1);
        }
    }

    // Update button states based on connection
    if (data.connected) {
        el.recordBtn.disabled = false;
        if (state.nodes.length > 0) el.playBtn.disabled = false;
    }
}

function handleRecordingsList(data) {
    state.recordings = data.recordings || [];
    renderRecordingsList();
}

function handleRecordingProgress(data) {
    el.recInfo.textContent = `${data.samples} samples, ${data.duration.toFixed(1)}s, ${data.rate.toFixed(0)} Hz`;
}

function handlePlaybackProgress(data) {
    // Update progress display
    updateExecutionStatus(
        data.status || 'Playing',
        data.status === 'paused' ? '#b08800' : '#FFC107'
    );

    // Highlight current node
    if (data.current_node) {
        state.nodes.forEach(n => highlightNode(n.id, n.id === data.current_node));
    }

    // Update timer from progress
    if (typeof data.progress === 'number') {
        // progress is 0-100
    }
}

function handleTimelineComplete() {
    log('Timeline playback completed', 'success');
    updateExecutionStatus('Complete', '#4CAF50');
    stopTimer();
    state.isPlaying = false;
    state.isPaused = false;
    el.playBtn.disabled = false;
    el.stopBtn.disabled = true;
    el.pauseBtn.disabled = true;
    el.pauseBtn.innerHTML = '<span>&#10074;&#10074;</span> Pause';
    state.nodes.forEach(n => highlightNode(n.id, false));
}

function handleTimelinesList(data) {
    const list = data.timelines || [];
    el.timelinesList.innerHTML = '';

    if (list.length === 0) {
        el.timelinesList.innerHTML = '<p class="waiting-message">No saved timelines</p>';
        return;
    }

    list.forEach(tl => {
        // Backend may return strings or objects
        const name = typeof tl === 'string' ? tl : tl.name;
        const created = typeof tl === 'object' ? (tl.created || '') : '';

        const item = document.createElement('div');
        item.className = 'timeline-item';
        item.innerHTML = `
            <div class="tl-name">${escapeHtml(name)}</div>
            <div class="tl-meta">${escapeHtml(created)}</div>
        `;
        item.addEventListener('click', () => {
            wsSend({ type: 'load_timeline', name: name });
            el.timelinesModal.style.display = 'none';
            log(`Loading timeline: ${name}`, 'info');
        });
        el.timelinesList.appendChild(item);
    });
}

function handleTimelineLoaded(data) {
    if (data.data) {
        loadTimelineData(data.data);
        log(`Timeline "${data.name}" loaded from server`, 'success');
    }
}

// ============================================================
// Recordings Library
// ============================================================
function renderRecordingsList() {
    el.recordingsList.innerHTML = '';

    if (state.recordings.length === 0) {
        el.recordingsList.innerHTML = '<p class="waiting-message">No recordings found</p>';
        return;
    }

    // Sort alphabetically
    const sorted = [...state.recordings].sort((a, b) =>
        (a.name || '').localeCompare(b.name || '', undefined, { numeric: true, sensitivity: 'base' })
    );

    sorted.forEach(rec => {
        const item = document.createElement('div');
        item.className = 'recording-item';
        item.draggable = true;

        const dur = rec.duration_sec ?? rec.duration ?? null;
        const samp = rec.sample_count ?? rec.samples ?? null;
        const durationStr = dur != null ? `${dur.toFixed(1)}s` : '?';
        const samplesStr = samp != null ? `${samp} samples` : '';

        item.innerHTML = `
            <div class="rec-name">${escapeHtml(rec.name)}</div>
            <div class="rec-meta">${durationStr} ${samplesStr}</div>
        `;

        item.addEventListener('dragstart', (e) => {
            e.dataTransfer.setData('application/json', JSON.stringify({
                type: 'recording',
                name: rec.name,
                duration_sec: dur || 0,
                sample_count: samp || 0
            }));
        });

        el.recordingsList.appendChild(item);
    });
}

// ============================================================
// Recording Controls
// ============================================================
el.recordBtn.addEventListener('click', () => {
    if (!state.isRecording) {
        wsSend({ type: 'start_recording' });
        state.isRecording = true;
        el.recordBtn.textContent = 'Stop Recording';
        el.recordBtn.classList.add('recording');
        el.recordingStatus.style.display = 'flex';
        el.recInfo.textContent = 'Recording...';
        log('Recording started', 'info');
    } else {
        wsSend({ type: 'stop_recording' });
        state.isRecording = false;
        el.recordBtn.textContent = 'Record';
        el.recordBtn.classList.remove('recording');
        el.recordingStatus.style.display = 'none';
        log('Recording stopped', 'info');

        // Refresh recordings list after short delay
        setTimeout(() => wsSend({ type: 'get_recordings' }), 500);
    }
});

el.refreshRecordingsBtn.addEventListener('click', () => {
    wsSend({ type: 'get_recordings' });
    log('Refreshing recordings...', 'info');
});

// ============================================================
// Node Management (adapted from web-timeline.js)
// ============================================================
function createNode(x, y, recordingName, duration, speed = 1.0, delayAfter = 0.0) {
    const node = {
        id: `node-${nodeIdCounter++}`,
        x: x,
        y: y,
        recordingName: recordingName,
        duration: duration,
        speed: speed,
        delayAfter: delayAfter,
        width: 230,
        height: 155
    };

    state.nodes.push(node);
    renderNode(node);
    el.playBtn.disabled = false;
    return node;
}

function renderNode(node) {
    const nodeEl = document.createElement('div');
    nodeEl.id = node.id;
    nodeEl.className = 'node';
    nodeEl.style.left = `${node.x}px`;
    nodeEl.style.top = `${node.y}px`;
    nodeEl.style.width = `${node.width}px`;

    const durationStr = node.duration > 0 ? `${node.duration.toFixed(1)}s` : '?';

    nodeEl.innerHTML = `
        <div class="node-header">
            <span class="node-title">${escapeHtml(node.recordingName)}</span>
        </div>
        <div class="node-content">
            <div class="node-field">
                <label>Duration:</label>
                <span class="field-info">${durationStr}</span>
            </div>
            <div class="node-field">
                <label>Speed:</label>
                <input type="number" class="speed-input" min="0.1" max="4.0" step="0.1" value="${node.speed}">
                <span>x</span>
            </div>
            <div class="node-field">
                <label>Delay after:</label>
                <input type="number" class="delay-input" min="0" max="60" step="0.5" value="${node.delayAfter}">
                <span>s</span>
            </div>
            <button class="node-remove">Remove</button>
        </div>
        <div class="connection-point connection-input" data-node-id="${node.id}" data-type="input"></div>
        <div class="connection-point connection-output" data-node-id="${node.id}" data-type="output"></div>
    `;

    // Event listeners
    const header = nodeEl.querySelector('.node-header');
    header.addEventListener('mousedown', (e) => handleNodeMouseDown(e, node));

    nodeEl.querySelector('.speed-input').addEventListener('change', (e) => {
        node.speed = parseFloat(e.target.value) || 1.0;
    });
    nodeEl.querySelector('.speed-input').addEventListener('mousedown', (e) => e.stopPropagation());

    nodeEl.querySelector('.delay-input').addEventListener('change', (e) => {
        node.delayAfter = parseFloat(e.target.value) || 0;
    });
    nodeEl.querySelector('.delay-input').addEventListener('mousedown', (e) => e.stopPropagation());

    nodeEl.querySelector('.node-remove').addEventListener('click', () => removeNode(node.id));
    nodeEl.querySelector('.node-remove').addEventListener('mousedown', (e) => e.stopPropagation());

    // Connection points
    nodeEl.querySelector('.connection-output').addEventListener('mousedown', (e) => {
        e.stopPropagation();
        state.isConnecting = true;
        state.connectionStart = { node: node, type: 'output' };
    });

    nodeEl.querySelector('.connection-input').addEventListener('mouseup', (e) => {
        e.stopPropagation();
        if (state.isConnecting && state.connectionStart) {
            const from = state.connectionStart.node;
            const to = node;

            if (from.id === to.id) {
                log('Cannot connect node to itself', 'warning');
            } else if (wouldCreateCircularDependency(from.id, to.id)) {
                log('Cannot create circular dependency', 'error');
            } else {
                addConnection(from.id, to.id);
                log(`Connected: ${from.recordingName} -> ${to.recordingName}`, 'success');
            }
        }
        state.isConnecting = false;
        state.connectionStart = null;
    });

    // Click to select
    nodeEl.addEventListener('click', (e) => {
        if (!state.isDragging) selectNode(node.id);
    });

    getCanvasContainer().appendChild(nodeEl);
}

function removeNode(nodeId) {
    state.connections = state.connections.filter(c => c.fromNode !== nodeId && c.toNode !== nodeId);
    state.nodes = state.nodes.filter(n => n.id !== nodeId);

    const element = document.getElementById(nodeId);
    if (element) element.remove();

    if (state.selectedNode && state.selectedNode.id === nodeId) {
        state.selectedNode = null;
    }

    renderAllConnections();

    if (state.nodes.length === 0) el.playBtn.disabled = true;
    log(`Removed node ${nodeId}`, 'info');
}

function selectNode(nodeId) {
    // Deselect previous
    if (state.selectedNode) {
        const prev = document.getElementById(state.selectedNode.id);
        if (prev) prev.classList.remove('selected');
    }

    const node = state.nodes.find(n => n.id === nodeId);
    state.selectedNode = node || null;

    if (node) {
        const elem = document.getElementById(node.id);
        if (elem) elem.classList.add('selected');
    }
}

function updateNodePosition(node, x, y) {
    node.x = x;
    node.y = y;
    const element = document.getElementById(node.id);
    if (element) {
        element.style.left = `${x}px`;
        element.style.top = `${y}px`;
    }
    renderAllConnections();
}

function highlightNode(nodeId, highlight) {
    const element = document.getElementById(nodeId);
    if (element) {
        if (highlight) element.classList.add('executing');
        else element.classList.remove('executing');
    }
}

// ============================================================
// Connection Management (adapted from web-timeline.js)
// ============================================================
function addConnection(fromNodeId, toNodeId) {
    // Only one input connection per node
    state.connections = state.connections.filter(c => c.toNode !== toNodeId);

    state.connections.push({
        id: `conn-${Date.now()}`,
        fromNode: fromNodeId,
        toNode: toNodeId
    });

    renderAllConnections();
}

function wouldCreateCircularDependency(fromId, toId) {
    const visited = new Set();

    function dependsOn(nodeA, nodeB) {
        if (nodeA === nodeB) return true;
        if (visited.has(nodeA)) return false;
        visited.add(nodeA);

        const conns = state.connections.filter(c => c.toNode === nodeA);
        for (const conn of conns) {
            if (dependsOn(conn.fromNode, nodeB)) return true;
        }
        return false;
    }

    return dependsOn(fromId, toId);
}

function renderAllConnections() {
    const container = getCanvasContainer();
    const existing = container.querySelector('.connections-svg');
    if (existing) existing.remove();

    if (state.connections.length === 0) return;

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('connections-svg');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    svg.style.pointerEvents = 'none';
    svg.style.zIndex = '1';
    svg.style.overflow = 'visible';

    // Arrowhead marker
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
    marker.setAttribute('id', 'arrowhead');
    marker.setAttribute('markerWidth', '10');
    marker.setAttribute('markerHeight', '10');
    marker.setAttribute('refX', '9');
    marker.setAttribute('refY', '3');
    marker.setAttribute('orient', 'auto');
    marker.setAttribute('markerUnits', 'strokeWidth');

    const polygon = document.createElementNS('http://www.w3.org/2000/svg', 'polygon');
    polygon.setAttribute('points', '0 0, 10 3, 0 6');
    polygon.setAttribute('fill', '#f0883e');

    marker.appendChild(polygon);
    defs.appendChild(marker);
    svg.appendChild(defs);

    state.connections.forEach(conn => {
        const fromNode = state.nodes.find(n => n.id === conn.fromNode);
        const toNode = state.nodes.find(n => n.id === conn.toNode);
        if (!fromNode || !toNode) return;

        const fromX = fromNode.x + fromNode.width;
        const fromY = fromNode.y + fromNode.height / 2;
        const toX = toNode.x;
        const toY = toNode.y + toNode.height / 2;

        const midX = (fromX + toX) / 2;
        const d = `M ${fromX} ${fromY} C ${midX} ${fromY}, ${midX} ${toY}, ${toX} ${toY}`;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('stroke', '#f0883e');
        path.setAttribute('stroke-width', '3');
        path.setAttribute('fill', 'none');
        path.setAttribute('marker-end', 'url(#arrowhead)');
        svg.appendChild(path);
    });

    container.insertBefore(svg, container.firstChild);
}

// ============================================================
// Canvas Transform (adapted from web-timeline.js)
// ============================================================
function getCanvasContainer() {
    let container = el.nodeEditor.querySelector('.canvas-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'canvas-container';
        container.style.position = 'absolute';
        container.style.transformOrigin = '0 0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.pointerEvents = 'none';
        el.nodeEditor.appendChild(container);
    }
    return container;
}

function updateCanvasTransform() {
    const container = getCanvasContainer();
    container.style.transform = `translate(${state.panOffset.x}px, ${state.panOffset.y}px) scale(${state.scale})`;
    renderAllConnections();
}

function updateZoomDisplay() {
    el.zoomLevel.textContent = `${Math.round(state.scale * 100)}%`;
}

// Mouse wheel zoom
el.nodeEditor.addEventListener('wheel', (e) => {
    e.preventDefault();

    const rect = el.nodeEditor.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const worldX = mouseX / state.scale - state.panOffset.x;
    const worldY = mouseY / state.scale - state.panOffset.y;

    const zoomSpeed = 0.1;
    const delta = e.deltaY > 0 ? -zoomSpeed : zoomSpeed;
    const newScale = Math.max(0.1, Math.min(3, state.scale + delta));

    if (newScale !== state.scale) {
        state.scale = newScale;
        state.panOffset.x = mouseX / state.scale - worldX;
        state.panOffset.y = mouseY / state.scale - worldY;
        updateCanvasTransform();
        updateZoomDisplay();
    }
});

// Panning (middle click or Shift+left click)
el.nodeEditor.addEventListener('mousedown', (e) => {
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
        e.preventDefault();
        state.isPanning = true;
        state.lastPanPoint = { x: e.clientX, y: e.clientY };
        el.nodeEditor.style.cursor = 'grabbing';
    }
});

// Drag-and-drop from sidebar
el.nodeEditor.addEventListener('dragover', (e) => e.preventDefault());

el.nodeEditor.addEventListener('drop', (e) => {
    e.preventDefault();
    try {
        const data = JSON.parse(e.dataTransfer.getData('application/json'));
        if (data.type === 'recording') {
            const rect = el.nodeEditor.getBoundingClientRect();
            const x = (e.clientX - rect.left) / state.scale - state.panOffset.x;
            const y = (e.clientY - rect.top) / state.scale - state.panOffset.y;
            createNode(x, y, data.name, data.duration_sec || 0);
            log(`Added "${data.name}" to canvas`, 'success');
        }
    } catch (err) {
        log(`Drop error: ${err.message}`, 'error');
    }
});

// Node dragging
function handleNodeMouseDown(e, node) {
    e.preventDefault();
    e.stopPropagation();

    const rect = el.nodeEditor.getBoundingClientRect();
    state.isDragging = true;
    state.selectedNode = node;
    state.dragOffset = {
        x: (e.clientX - rect.left) / state.scale - state.panOffset.x - node.x,
        y: (e.clientY - rect.top) / state.scale - state.panOffset.y - node.y
    };

    selectNode(node.id);
}

document.addEventListener('mousemove', (e) => {
    if (state.isDragging && state.selectedNode) {
        const rect = el.nodeEditor.getBoundingClientRect();
        const mouseX = (e.clientX - rect.left) / state.scale - state.panOffset.x;
        const mouseY = (e.clientY - rect.top) / state.scale - state.panOffset.y;
        updateNodePosition(state.selectedNode, mouseX - state.dragOffset.x, mouseY - state.dragOffset.y);
    } else if (state.isPanning) {
        const dx = e.clientX - state.lastPanPoint.x;
        const dy = e.clientY - state.lastPanPoint.y;
        state.panOffset.x += dx / state.scale;
        state.panOffset.y += dy / state.scale;
        state.lastPanPoint = { x: e.clientX, y: e.clientY };
        updateCanvasTransform();
    }
});

document.addEventListener('mouseup', () => {
    state.isDragging = false;
    state.isPanning = false;
    el.nodeEditor.style.cursor = 'default';

    if (state.isConnecting) {
        state.isConnecting = false;
        state.connectionStart = null;
    }
});

// ============================================================
// Playback Controls
// ============================================================
el.playBtn.addEventListener('click', () => {
    if (state.nodes.length === 0) {
        log('No nodes on canvas', 'warning');
        return;
    }

    // Build timeline data from nodes and connections
    const timelineData = buildTimelinePayload();

    wsSend({
        type: 'play_timeline',
        timeline: timelineData,
        speed: parseFloat(el.globalSpeed.value) || 1.0,
        loop: el.loopCheckbox.checked,
        loopDelay: parseFloat(el.loopDelay.value) || 0
    });

    state.isPlaying = true;
    state.isPaused = false;
    el.playBtn.disabled = true;
    el.stopBtn.disabled = false;
    el.pauseBtn.disabled = false;
    updateExecutionStatus('Playing', '#FFC107');
    startTimer();
    log('Timeline playback started', 'info');
});

el.stopBtn.addEventListener('click', () => {
    wsSend({ type: 'stop_playback' });
    state.isPlaying = false;
    state.isPaused = false;
    el.playBtn.disabled = false;
    el.stopBtn.disabled = true;
    el.pauseBtn.disabled = true;
    el.pauseBtn.innerHTML = '<span>&#10074;&#10074;</span> Pause';
    updateExecutionStatus('Stopped', '#f44336');
    stopTimer();
    state.nodes.forEach(n => highlightNode(n.id, false));
    log('Playback stopped', 'warning');
});

el.pauseBtn.addEventListener('click', () => {
    if (!state.isPaused) {
        wsSend({ type: 'pause_playback' });
        state.isPaused = true;
        el.pauseBtn.innerHTML = '<span>&#9654;</span> Resume';
        updateExecutionStatus('Paused', '#b08800');
        log('Playback paused', 'info');
    } else {
        wsSend({ type: 'resume_playback' });
        state.isPaused = false;
        el.pauseBtn.innerHTML = '<span>&#10074;&#10074;</span> Pause';
        updateExecutionStatus('Playing', '#FFC107');
        log('Playback resumed', 'info');
    }
});

function buildTimelinePayload() {
    return {
        nodes: state.nodes.map(n => ({
            id: n.id,
            recordingName: n.recordingName,
            duration: n.duration,
            speed: n.speed,
            delayAfter: n.delayAfter
        })),
        connections: state.connections.map(c => ({
            fromNode: c.fromNode,
            toNode: c.toNode
        }))
    };
}

// ============================================================
// Save / Load / Clear
// ============================================================
el.saveBtn.addEventListener('click', () => {
    const name = prompt('Timeline name:', `timeline_${new Date().toISOString().slice(0, 10)}`);
    if (!name) return;

    const timelineData = {
        nodes: state.nodes.map(n => ({
            id: n.id,
            x: n.x,
            y: n.y,
            recordingName: n.recordingName,
            duration: n.duration,
            speed: n.speed,
            delayAfter: n.delayAfter,
            width: n.width,
            height: n.height
        })),
        connections: state.connections.map(c => ({
            id: c.id,
            fromNode: c.fromNode,
            toNode: c.toNode
        })),
        loopEnabled: el.loopCheckbox.checked,
        loopDelay: parseFloat(el.loopDelay.value) || 0,
        globalSpeed: parseFloat(el.globalSpeed.value) || 1.0
    };

    wsSend({
        type: 'save_timeline',
        name: name,
        data: timelineData
    });

    log(`Saving timeline "${name}"...`, 'info');
});

el.loadBtn.addEventListener('click', () => {
    // Request timelines list and show modal
    wsSend({ type: 'list_timelines' });
    el.timelinesModal.style.display = 'flex';
});

el.modalCloseBtn.addEventListener('click', () => {
    el.timelinesModal.style.display = 'none';
});

el.timelinesModal.addEventListener('click', (e) => {
    if (e.target === el.timelinesModal) {
        el.timelinesModal.style.display = 'none';
    }
});

el.clearBtn.addEventListener('click', () => {
    if (state.nodes.length === 0) return;
    if (!confirm('Clear all nodes from the canvas?')) return;

    state.nodes.forEach(n => {
        const element = document.getElementById(n.id);
        if (element) element.remove();
    });

    state.nodes = [];
    state.connections = [];
    state.selectedNode = null;
    renderAllConnections();
    el.playBtn.disabled = true;
    log('Canvas cleared', 'info');
});

// Load timeline data into the canvas (called when server responds to load_timeline)
function loadTimelineData(data) {
    // Clear existing
    state.nodes.forEach(n => {
        const element = document.getElementById(n.id);
        if (element) element.remove();
    });
    state.nodes = [];
    state.connections = [];

    // Load nodes
    if (data.nodes) {
        data.nodes.forEach(n => {
            const node = {
                id: n.id,
                x: n.x || 0,
                y: n.y || 0,
                recordingName: n.recordingName,
                duration: n.duration || 0,
                speed: n.speed || 1.0,
                delayAfter: n.delayAfter || 0,
                width: n.width || 230,
                height: n.height || 155
            };
            state.nodes.push(node);
            renderNode(node);
        });
    }

    // Load connections
    if (data.connections) {
        state.connections = data.connections.map(c => ({
            id: c.id || `conn-${Date.now()}-${Math.random()}`,
            fromNode: c.fromNode,
            toNode: c.toNode
        }));
    }

    // Load settings
    if (data.loopEnabled != null) el.loopCheckbox.checked = data.loopEnabled;
    if (data.loopDelay != null) el.loopDelay.value = data.loopDelay;
    if (data.globalSpeed != null) el.globalSpeed.value = data.globalSpeed;

    // Update node ID counter
    const maxId = Math.max(0, ...state.nodes.map(n => {
        const match = n.id.match(/node-(\d+)/);
        return match ? parseInt(match[1]) : 0;
    }));
    nodeIdCounter = maxId + 1;

    renderAllConnections();
    if (state.nodes.length > 0) el.playBtn.disabled = false;

    log('Timeline loaded', 'success');
}

// ============================================================
// Zoom Controls
// ============================================================
el.zoomInBtn.addEventListener('click', () => {
    state.scale = Math.min(3, state.scale + 0.1);
    updateCanvasTransform();
    updateZoomDisplay();
});

el.zoomOutBtn.addEventListener('click', () => {
    state.scale = Math.max(0.1, state.scale - 0.1);
    updateCanvasTransform();
    updateZoomDisplay();
});

el.zoomResetBtn.addEventListener('click', () => {
    state.scale = 1;
    state.panOffset = { x: 0, y: 0 };
    updateCanvasTransform();
    updateZoomDisplay();
    log('View reset', 'info');
});

// ============================================================
// Timer
// ============================================================
function startTimer() {
    state.timerStart = Date.now();
    updateTimerDisplay();
    state.timerInterval = setInterval(updateTimerDisplay, 1000);
}

function stopTimer() {
    if (state.timerInterval) {
        clearInterval(state.timerInterval);
        state.timerInterval = null;
    }
}

function updateTimerDisplay() {
    if (!state.timerStart) {
        el.timer.textContent = '00:00:00';
        return;
    }

    const elapsed = Math.floor((Date.now() - state.timerStart) / 1000);
    const h = Math.floor(elapsed / 3600);
    const m = Math.floor((elapsed % 3600) / 60);
    const s = elapsed % 60;
    el.timer.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}

function updateExecutionStatus(text, color) {
    el.executionStatus.textContent = text;
    el.executionStatus.style.background = color;
    el.executionStatus.style.color = 'white';
}

// ============================================================
// Keyboard Shortcuts
// ============================================================
document.addEventListener('keydown', (e) => {
    // Delete selected node
    if (e.key === 'Delete' && state.selectedNode) {
        removeNode(state.selectedNode.id);
    }
});

// ============================================================
// Utility
// ============================================================
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ============================================================
// Reset Robot
// ============================================================
function openResetModal() {
    el.resetModal.style.display = 'flex';
    el.resetConfirmBtn.disabled = false;
    el.resetCancelBtn.disabled = false;
}

function closeResetModal() {
    el.resetModal.style.display = 'none';
}

function confirmReset() {
    closeResetModal();
    el.resetRobotBtn.disabled = true;
    el.resetRobotBtn.textContent = '⟳ Resetting...';
    updateExecutionStatus('Resetting...', '#b08800');
    log('Robot reset requested by user', 'warning');
    wsSend({ type: 'reset_robot' });
}

function handleResetComplete(data) {
    el.resetRobotBtn.disabled = false;
    el.resetRobotBtn.innerHTML = '&#8635; Reset Robot';
    if (data.success) {
        updateExecutionStatus('Ready', '#238636');
        // Refresh status from server
        wsSend({ type: 'get_status' });
    } else {
        updateExecutionStatus('Reset failed', '#da3633');
        log(`Reset failed: ${data.message || 'Unknown error'}`, 'error');
    }
}

el.resetRobotBtn.addEventListener('click', openResetModal);
el.resetConfirmBtn.addEventListener('click', confirmReset);
el.resetCancelBtn.addEventListener('click', closeResetModal);

// Close reset modal on backdrop click
el.resetModal.addEventListener('click', (e) => {
    if (e.target === el.resetModal) closeResetModal();
});

// ============================================================
// Initialize
// ============================================================
function initialize() {
    log('Piper Automation System initialized', 'success');
    connectWebSocket();
}

initialize();
