// Removidos imports para compatibilidade global

let mediaRecorder;
let audioChunks = [];
let audioBlob = null;
let isRecording = false;
let isPaused = false;
let startTime;
let timerInterval;
let elapsedTime = 0;

document.addEventListener('DOMContentLoaded', async () => {
    await loadProcesses();

    const btnRecord = document.getElementById('btnRecord');
    const btnSave = document.getElementById('btnSave');
    const btnPause = document.getElementById('btnPause');
    const btnCancel = document.getElementById('btnCancel');
    const audioPlayback = document.getElementById('audioPlayback');
    const statusText = document.getElementById('statusText');
    const recordingControls = document.getElementById('recordingControls');
    
    const timerDisplay = document.createElement('div');
    timerDisplay.id = 'timerDisplay';
    timerDisplay.style.fontSize = '24px';
    timerDisplay.style.margin = '10px 0';
    timerDisplay.style.fontWeight = 'bold';
    timerDisplay.style.display = 'none';
    statusText.parentNode.insertBefore(timerDisplay, statusText);

    btnRecord.addEventListener('click', async () => {
        if (!isRecording) {
            await startRecording();
        } else {
            stopRecording();
        }
    });

    btnPause.addEventListener('click', () => {
        togglePause();
    });

    btnCancel.addEventListener('click', () => {
        cancelRecording();
    });

    btnSave.addEventListener('click', () => {
        saveTranscription();
    });
});

async function loadProcesses() {
    try {
        const select = document.getElementById('processSelect');
        const res = await apiGet('/processes');
        if (!select) return;
        select.innerHTML = `
            <option value="">Selecione o processo...</option>
            <option value="NEW_PROCESS" style="font-weight: bold; color: var(--accent);">+ CRIAR NOVO PROCESSO (VIA ÁUDIO)</option>
        `;
        
        res.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.client_name} - ${p.action_type || 'Sem Ação'}`;
            select.appendChild(opt);
        });

        select.addEventListener('change', () => {
            const btn = document.getElementById('btnSave');
            if (select.value === 'NEW_PROCESS') {
                btn.innerHTML = '<i class="fas fa-magic"></i> Gerar Processo + Petição Inicial';
            } else {
                btn.innerHTML = '<i class="fas fa-brain"></i> Transcrever e Salvar no Processo';
            }
        });
    } catch (e) {
        console.error("Erro ao carregar processos:", e);
    }
}

async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const options = { mimeType: 'audio/webm;codecs=opus' };
        mediaRecorder = MediaRecorder.isTypeSupported(options.mimeType) 
            ? new MediaRecorder(stream, options) 
            : new MediaRecorder(stream);

        audioChunks = [];
        mediaRecorder.ondataavailable = event => { if (event.data.size > 0) audioChunks.push(event.data); };
        
        mediaRecorder.onstop = () => {
            audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
        };

        mediaRecorder.start(1000);
        isRecording = true;
        isPaused = false;
        startTime = Date.now();
        elapsedTime = 0;
        
        updateTimer();
        timerInterval = setInterval(updateTimer, 1000);

        document.getElementById('btnRecord').classList.add('recording');
        document.getElementById('btnRecord').innerHTML = '<i class="fas fa-stop"></i>';
        document.getElementById('statusText').textContent = 'Gravando reunião...';
        document.getElementById('recordingControls').style.display = 'flex';
        document.getElementById('timerDisplay').style.display = 'block';
        document.getElementById('audioPlayback').style.display = 'none';
        document.getElementById('btnSave').style.display = 'none';

    } catch (err) {
        alert("Não foi possível acessar o microfone: " + err.message);
    }
}

function updateTimer() {
    if (isPaused) return;
    const totalSeconds = Math.floor((Date.now() - startTime + elapsedTime) / 1000);
    const m = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
    const s = (totalSeconds % 60).toString().padStart(2, '0');
    document.getElementById('timerDisplay').textContent = `${m}:${s}`;
}

function togglePause() {
    if (!isRecording) return;
    const btnPause = document.getElementById('btnPause');
    if (!isPaused) {
        mediaRecorder.pause();
        isPaused = true;
        elapsedTime += Date.now() - startTime;
        btnPause.innerHTML = '<i class="fas fa-play"></i> Retomar';
        document.getElementById('statusText').textContent = 'Gravação pausada.';
    } else {
        mediaRecorder.resume();
        isPaused = false;
        startTime = Date.now();
        btnPause.innerHTML = '<i class="fas fa-pause"></i> Pausar';
        document.getElementById('statusText').textContent = 'Gravando reunião...';
    }
}

function cancelRecording() {
    if (!confirm("Deseja realmente cancelar a gravação? Todo o áudio será perdido.")) return;
    if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
    resetUI();
}

function stopRecording() {
    mediaRecorder.stop();
    isRecording = false;
    clearInterval(timerInterval);
    mediaRecorder.stream.getTracks().forEach(track => track.stop());

    document.getElementById('btnRecord').classList.remove('recording');
    document.getElementById('btnRecord').innerHTML = '<i class="fas fa-microphone"></i>';
    document.getElementById('statusText').textContent = 'Gravação finalizada.';
    document.getElementById('recordingControls').style.display = 'none';

    setTimeout(() => {
        const audioUrl = URL.createObjectURL(audioBlob);
        const player = document.getElementById('audioPlayback');
        player.src = audioUrl;
        player.style.display = 'block';
        document.getElementById('btnSave').style.display = 'block';
    }, 500);
}

function resetUI() {
    isRecording = false;
    isPaused = false;
    clearInterval(timerInterval);
    document.getElementById('btnRecord').classList.remove('recording');
    document.getElementById('btnRecord').innerHTML = '<i class="fas fa-microphone"></i>';
    document.getElementById('statusText').textContent = 'Pronto para gravar';
    document.getElementById('recordingControls').style.display = 'none';
    document.getElementById('timerDisplay').style.display = 'none';
    document.getElementById('audioPlayback').style.display = 'none';
    document.getElementById('btnSave').style.display = 'none';
}

async function saveTranscription() {
    const btnSave = document.getElementById('btnSave');
    const processId = document.getElementById('processSelect').value;
    if (!processId) return alert("Selecione o destino.");
    if (!audioBlob) return;

    btnSave.disabled = true;
    const isNew = (processId === 'NEW_PROCESS');
    btnSave.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processando com IA...';

    const formData = new FormData();
    formData.append("file", audioBlob, "reuniao.webm");
    if (!isNew) formData.append("process_id", processId);

    try {
        const token = localStorage.getItem("token");
        const endpoint = isNew ? `${API}/meetings/fast-track` : `${API}/meetings/transcribe`;
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || 'Erro no processamento');

        if (isNew && data.petition) {
            showPetitionModal(data);
        } else {
            alert("Sucesso! O áudio foi transcrito e vinculado.");
            window.location.href = `process.html?id=${isNew ? data.process_id : processId}`;
        }

    } catch (e) {
        alert("Erro: " + e.message);
        btnSave.disabled = false;
        btnSave.innerHTML = '<i class="fas fa-brain"></i> Tentar Novamente';
    }
}

function showPetitionModal(data) {
    const modal = document.getElementById('petitionModal');
    const body = document.getElementById('modalBody');
    const btnGo = document.getElementById('btnGoToProcess');

    body.textContent = data.petition.full_text || "Petição gerada com sucesso, mas o texto não foi retornado corretamente.";
    modal.style.display = 'flex';

    btnGo.onclick = () => {
        window.location.href = `process.html?id=${data.process_id}`;
    };
}
