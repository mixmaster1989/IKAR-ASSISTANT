document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('prompts-form');
    const systemPrompt = document.getElementById('system-prompt');
    const userPrompt = document.getElementById('user-prompt');
    const saveStatus = document.getElementById('save-status');

    // Загрузка сохранённых значений
    systemPrompt.value = localStorage.getItem('system_prompt') || '';
    userPrompt.value = localStorage.getItem('user_prompt') || '';

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        localStorage.setItem('system_prompt', systemPrompt.value);
        localStorage.setItem('user_prompt', userPrompt.value);
        saveStatus.textContent = 'Промпты сохранены (локально)';
        setTimeout(() => saveStatus.textContent = '', 2000);
    });
}); 