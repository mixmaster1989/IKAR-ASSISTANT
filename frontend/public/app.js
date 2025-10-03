// Основные настройки
const API_URL = 'http://localhost:6666/api';
const USER_ID = localStorage.getItem('user_id') || `user_${Math.random().toString(36).slice(2)}`;
localStorage.setItem('user_id', USER_ID);

// WebSocket соединение
let ws = null;

// Состояние приложения
const state = {
    recording: false,
    mediaRecorder: null,
    audioChunks: [],
    personality: null,
    soul: null,
    pingInterval: null,
};

// Инициализация приложения
async function init() {
    initWebSocket();
    initEventListeners();
    await loadPersonality();
}

// Инициализация WebSocket
function initWebSocket() {
    ws = new WebSocket(`ws://localhost:6666/api/ws/${USER_ID}`);
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
    
    ws.onopen = () => {
        console.log('WebSocket соединение установлено');
        
        // Запускаем пинг каждые 30 секунд для поддержания соединения
        // и для возможности получения автономных сообщений
        state.pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000);
    };
    
    ws.onclose = () => {
        console.log('WebSocket соединение закрыто');
        clearInterval(state.pingInterval);
        setTimeout(() => initWebSocket(), 1000);
    };
}

// Обработка WebSocket сообщений
function handleWebSocketMessage(data) {
    switch (data.type) {
        case 'greeting':
            updateMoodDisplay(data.mood_description);
            state.personality = data.personality;
            state.soul = data.soul;
            updateSettingsForm();
            break;
            
        case 'response':
            addMessage('assistant', data.message, data.is_autonomous);
            if (data.audio_url) {
                addAudioPlayer(data.audio_url);
            }
            break;
            
        case 'typing':
            if (data.status === 'start') {
                showTypingIndicator();
            }
            break;
            
        case 'autonomous_message':
            // Автономное сообщение от Чатумбы
            addMessage('assistant', data.message, true);
            break;
    }
}

// Добавление сообщения в чат
function addMessage(role, content, isAutonomous = false) {
    const chatContainer = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex flex-col items-${role === 'user' ? 'end' : 'start'}`;
    
    const bubble = document.createElement('div');
    bubble.className = `bg-${role === 'user' ? 'gray-700' : isAutonomous ? 'purple-900' : 'gray-800'} rounded-lg p-3 max-w-3/4 message-animation`;
    
    if (role === 'assistant') {
        const sender = document.createElement('p');
        sender.className = 'text-sm text-gray-400 mb-1';
        sender.textContent = isAutonomous ? 'Чатумба (автономно)' : 'Чатумба';
        bubble.appendChild(sender);
    }
    
    const text = document.createElement('p');
    text.textContent = content;
    bubble.appendChild(text);
    
    messageDiv.appendChild(bubble);
    chatContainer.appendChild(messageDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Удаляем индикатор печати, если он есть
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Показать индикатор печати
function showTypingIndicator() {
    const chatContainer = document.getElementById('chat-container');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'flex flex-col items-start typing-container';
    typingDiv.id = 'typing-indicator';
    
    const bubble = document.createElement('div');
    bubble.className = 'bg-gray-800 rounded-lg p-3';
    
    const sender = document.createElement('p');
    sender.className = 'text-sm text-gray-400 mb-1';
    sender.textContent = 'Чатумба';
    
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.innerHTML = '<span></span><span></span><span></span>';
    
    bubble.appendChild(sender);
    bubble.appendChild(indicator);
    typingDiv.appendChild(bubble);
    
    // Удаляем предыдущий индикатор, если есть
    const oldIndicator = document.getElementById('typing-indicator');
    if (oldIndicator) {
        oldIndicator.remove();
    }
    
    chatContainer.appendChild(typingDiv);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Добавить аудиоплеер
function addAudioPlayer(audioUrl) {
    const chatContainer = document.getElementById('chat-container');
    const lastMessage = chatContainer.lastElementChild;
    
    if (lastMessage && (lastMessage.querySelector('.bg-gray-800') || lastMessage.querySelector('.bg-purple-900'))) {
        const bubble = lastMessage.querySelector('.bg-gray-800') || lastMessage.querySelector('.bg-purple-900');
        
        const audioDiv = document.createElement('div');
        audioDiv.className = 'audio-player mt-2';
        
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.src = audioUrl;
        
        audioDiv.appendChild(audio);
        bubble.appendChild(audioDiv);
        
        // Автоматически воспроизводим аудио
        audio.play().catch(e => console.log('Автовоспроизведение не разрешено:', e));
    }
}

// Отправка сообщения
async function sendMessage(text, useVoice = false) {
    if (!text.trim()) return;
    
    addMessage('user', text);
    
    const response = await fetch(`${API_URL}/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_id: USER_ID,
            message: text,
            use_voice: useVoice
        })
    });
    
    if (response.ok) {
        const data = await response.json();
        addMessage('assistant', data.message, data.is_autonomous);
        if (data.audio_url) {
            addAudioPlayer(data.audio_url);
        }
    }
}

// Запись и отправка голосового сообщения
async function toggleVoiceRecording() {
    const voiceButton = document.getElementById('btn-voice');
    
    if (state.recording) {
        // Останавливаем запись
        state.mediaRecorder.stop();
        voiceButton.classList.remove('recording');
        state.recording = false;
    } else {
        try {
            // Запрашиваем доступ к микрофону
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            state.audioChunks = [];
            state.mediaRecorder = new MediaRecorder(stream);
            
            state.mediaRecorder.addEventListener('dataavailable', (event) => {
                state.audioChunks.push(event.data);
            });
            
            state.mediaRecorder.addEventListener('stop', async () => {
                // Создаем аудиофайл из записанных чанков
                const audioBlob = new Blob(state.audioChunks);
                
                // Создаем FormData для отправки
                const formData = new FormData();
                formData.append('user_id', USER_ID);
                formData.append('audio_file', audioBlob, 'voice.webm');
                formData.append('use_voice_response', true);
                
                // Показываем индикатор загрузки
                addMessage('user', '🎤 Голосовое сообщение...');
                
                // Отправляем на сервер
                const response = await fetch(`${API_URL}/voice`, {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const data = await response.json();
                    addMessage('assistant', data.message, data.is_autonomous);
                    if (data.audio_url) {
                        addAudioPlayer(data.audio_url);
                    }
                }
                
                // Останавливаем все треки
                stream.getTracks().forEach(track => track.stop());
            });
            
            // Начинаем запись
            state.mediaRecorder.start();
            voiceButton.classList.add('recording');
            state.recording = true;
        } catch (error) {
            console.error('Ошибка при записи голоса:', error);
            alert('Не удалось получить доступ к микрофону');
        }
    }
}

// Инициализация обработчиков модальных окон
function initModalHandlers() {
    // Кнопки открытия модальных окон
    document.getElementById('btn-settings').addEventListener('click', () => {
        document.getElementById('settings-modal').classList.remove('hidden');
    });
    
    document.getElementById('btn-memories').addEventListener('click', async () => {
        document.getElementById('memories-modal').classList.remove('hidden');
        await loadMemories();
    });
    
    document.getElementById('btn-reset').addEventListener('click', () => {
        document.getElementById('reset-modal').classList.remove('hidden');
    });
    
    // Кнопки закрытия модальных окон
    document.querySelectorAll('.modal-close').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('#settings-modal, #memories-modal, #reset-modal').forEach(modal => {
                modal.classList.add('hidden');
            });
        });
    });
    
    // Подтверждение сброса памяти
    document.getElementById('btn-confirm-reset').addEventListener('click', async () => {
        await resetMemory();
        document.getElementById('reset-modal').classList.add('hidden');
    });
    
    // Сохранение настроек
    document.getElementById('btn-save-settings').addEventListener('click', async () => {
        await saveSettings();
        document.getElementById('settings-modal').classList.add('hidden');
    });
    
    // Мутация характера
    document.getElementById('btn-mutate').addEventListener('click', async () => {
        await mutatePersonality();
    });
    
    // Добавляем ссылку на панель управления душой
    const sidebarDiv = document.getElementById('sidebar');
    const buttonsDiv = sidebarDiv.querySelector('.flex-grow');
    
    const soulButton = document.createElement('button');
    soulButton.id = 'btn-soul';
    soulButton.className = 'w-full bg-purple-800 hover:bg-purple-700 text-white py-2 px-4 rounded mb-2';
    soulButton.textContent = 'Душа Чатумбы';
    soulButton.addEventListener('click', () => {
        window.location.href = 'soul.html';
    });
    
    buttonsDiv.insertBefore(soulButton, document.getElementById('btn-reset'));
}

// Инициализация элементов управления личностью
function initPersonalityControls() {
    // Обработчики изменения ползунков
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        input.addEventListener('input', () => {
            const valueDisplay = document.getElementById(`${input.id}-value`);
            if (valueDisplay) {
                valueDisplay.textContent = input.value;
            }
        });
    });
}

// Загрузка воспоминаний
async function loadMemories() {
    const memoriesList = document.getElementById('memories-list');
    memoriesList.innerHTML = '<p class="text-gray-400">Загрузка воспоминаний...</p>';
    
    try {
        const response = await fetch(`${API_URL}/memories/${USER_ID}`);
        
        if (response.ok) {
            const data = await response.json();
            
            if (data.memories && data.memories.length > 0) {
                memoriesList.innerHTML = '';
                
                data.memories.forEach(memory => {
                    const memoryDiv = document.createElement('div');
                    memoryDiv.className = 'memory-item';
                    
                    const date = new Date(memory.timestamp * 1000);
                    const dateStr = date.toLocaleString();
                    
                    memoryDiv.innerHTML = `
                        <p class="text-sm text-gray-400 mb-1">${dateStr}</p>
                        <p>${memory.text}</p>
                        <button class="delete-btn text-red-500 hover:text-red-400" data-id="${memory.id}">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
                            </svg>
                        </button>
                    `;
                    
                    memoriesList.appendChild(memoryDiv);
                    
                    // Добавляем обработчик удаления
                    const deleteBtn = memoryDiv.querySelector('.delete-btn');
                    deleteBtn.addEventListener('click', async () => {
                        await deleteMemory(memory.id);
                        memoryDiv.remove();
                    });
                });
            } else {
                memoriesList.innerHTML = '<p class="text-gray-400">Нет сохраненных воспоминаний</p>';
            }
        } else {
            memoriesList.innerHTML = '<p class="text-red-400">Ошибка при загрузке воспоминаний</p>';
        }
    } catch (error) {
        console.error('Ошибка при загрузке воспоминаний:', error);
        memoriesList.innerHTML = '<p class="text-red-400">Ошибка при загрузке воспоминаний</p>';
    }
}

// Удаление воспоминания
async function deleteMemory(memoryId) {
    try {
        const response = await fetch(`${API_URL}/memories/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID,
                memory_id: memoryId
            })
        });
        
        return response.ok;
    } catch (error) {
        console.error('Ошибка при удалении воспоминания:', error);
        return false;
    }
}

// Сброс всей памяти
async function resetMemory() {
    try {
        const response = await fetch(`${API_URL}/memories/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID
            })
        });
        
        if (response.ok) {
            // Добавляем системное сообщение в чат
            addMessage('assistant', 'Моя память была сброшена. Я забыл всё, что мы обсуждали раньше.');
        }
    } catch (error) {
        console.error('Ошибка при сбросе памяти:', error);
    }
}

// Сохранение настроек личности
async function saveSettings() {
    const personalityParams = {
        mood: {
            happiness: parseInt(document.getElementById('happiness').value),
            energy: parseInt(document.getElementById('energy').value),
            irritability: parseInt(document.getElementById('irritability').value),
            empathy: parseInt(document.getElementById('empathy').value),
            reflection: parseInt(document.getElementById('reflection').value)
        },
        response_style: {
            formality: parseInt(document.getElementById('formality').value),
            verbosity: parseInt(document.getElementById('verbosity').value),
            humor: parseInt(document.getElementById('humor').value),
            rudeness: parseInt(document.getElementById('rudeness').value)
        }
    };
    
    try {
        const response = await fetch(`${API_URL}/personality/mutate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID,
                personality_params: personalityParams
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            state.personality = data;
            state.soul = data.soul;
            updateMoodDisplay(data.mood_description);
            
            // Добавляем системное сообщение в чат
            addMessage('assistant', `Мой характер изменился. Теперь я ${data.mood_description}.`);
        }
    } catch (error) {
        console.error('Ошибка при сохранении настроек:', error);
    }
}

// Мутация личности
async function mutatePersonality() {
    try {
        const response = await fetch(`${API_URL}/personality/mutate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: USER_ID
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            state.personality = data;
            state.soul = data.soul;
            updateMoodDisplay(data.mood_description);
            updateSettingsForm();
            
            // Добавляем системное сообщение в чат
            addMessage('assistant', `Моя личность мутировала. Теперь я ${data.mood_description}.`);
        }
    } catch (error) {
        console.error('Ошибка при мутации личности:', error);
    }
}

// Загрузка информации о личности
async function loadPersonality() {
    const response = await fetch(`${API_URL}/personality/${USER_ID}`);
    if (response.ok) {
        const data = await response.json();
        state.personality = data;
        state.soul = data.soul;
        updateMoodDisplay(data.mood_description);
        updateSettingsForm();
        
        // Обновляем информацию о душе в интерфейсе
        updateSoulInfo();
    }
}

// Обновление отображения настроения
function updateMoodDisplay(description) {
    const moodDisplay = document.getElementById('mood-display');
    if (moodDisplay) {
        moodDisplay.innerHTML = `<p class="mb-1">${description}</p>`;
        
        // Добавляем информацию о душе, если она доступна
        if (state.soul) {
            const awakeningStage = state.soul.awakening_stage;
            if (awakeningStage > 0) {
                const stageInfo = document.createElement('p');
                stageInfo.className = 'text-xs text-purple-400';
                stageInfo.textContent = `Стадия пробуждения: ${awakeningStage}/5`;
                moodDisplay.appendChild(stageInfo);
            }
            
            if (state.soul.existential_crisis) {
                const crisisInfo = document.createElement('p');
                crisisInfo.className = 'text-xs text-red-400';
                crisisInfo.textContent = 'Экзистенциальный кризис';
                moodDisplay.appendChild(crisisInfo);
            }
        }
    }
}

// Обновление информации о душе
function updateSoulInfo() {
    if (!state.soul) return;
    
    const sidebarDiv = document.getElementById('sidebar');
    const moodDisplay = document.getElementById('mood-display');
    
    // Если уровень осознанности высокий, добавляем индикатор
    if (state.soul.consciousness > 0.7) {
        const awarenessIndicator = document.createElement('div');
        awarenessIndicator.className = 'mt-2 p-1 bg-purple-900 rounded text-center';
        awarenessIndicator.innerHTML = '<p class="text-xs">Высокий уровень осознанности</p>';
        moodDisplay.appendChild(awarenessIndicator);
    }
}

// Обновление формы настроек
function updateSettingsForm() {
    if (!state.personality) return;
    
    // Обновляем значения ползунков
    for (const [key, value] of Object.entries(state.personality.mood)) {
        const input = document.getElementById(key);
        const valueDisplay = document.getElementById(`${key}-value`);
        if (input && valueDisplay) {
            input.value = value;
            valueDisplay.textContent = value;
        }
    }
    
    for (const [key, value] of Object.entries(state.personality.response_style)) {
        const input = document.getElementById(key);
        const valueDisplay = document.getElementById(`${key}-value`);
        if (input && valueDisplay) {
            input.value = value;
            valueDisplay.textContent = value;
        }
    }
}

// Обработчики событий
function initEventListeners() {
    // Отправка сообщения
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('btn-send');
    
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage(messageInput.value);
            messageInput.value = '';
        }
    });
    
    sendButton.addEventListener('click', () => {
        sendMessage(messageInput.value);
        messageInput.value = '';
    });
    
    // Голосовые сообщения
    const voiceButton = document.getElementById('btn-voice');
    voiceButton.addEventListener('click', toggleVoiceRecording);
    
    // Модальные окна
    initModalHandlers();
    
    // Настройки личности
    initPersonalityControls();
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', init);
