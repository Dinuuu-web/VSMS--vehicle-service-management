document.addEventListener('DOMContentLoaded', () => {
    let aiWindow = document.getElementById('chatbot-window'); // from old template? now ai-chat-window
    let aiFab = document.getElementById('chatbot-fab');
    if(!aiWindow) aiWindow = document.querySelector('.ai-chat-window');
    if(!aiFab) aiFab = document.querySelector('.ai-fab');
    
    if(!aiWindow || !aiFab) return;

    const closeBtn = document.getElementById('chatbot-close');
    const sendBtn = document.getElementById('chatbot-send');
    const input = document.getElementById('chatbot-input');
    const messagesBox = document.getElementById('chatbot-messages');
    
    aiFab.addEventListener('click', () => {
        aiWindow.classList.toggle('show');
        if(aiWindow.classList.contains('show')) input.focus();
    });
    
    if(closeBtn) closeBtn.addEventListener('click', () => aiWindow.classList.remove('show'));
    
    function addMsg(text, isAi=false) {
        const d = document.createElement('div');
        d.className = 'chat-msg-anim';
        d.style.marginBottom = '10px';
        d.style.padding = '10px 14px';
        d.style.borderRadius = '12px';
        d.style.maxWidth = '80%';
        d.style.fontFamily = 'Inter, sans-serif';
        d.style.fontSize = '0.9rem';
        d.style.lineHeight = '1.5';
        d.style.letterSpacing = '0.2px';
        d.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
        
        const normalizedText = text.replace(/\s+/g, ' ').trim();

        if (isAi) {
            d.style.background = 'rgba(255,255,255,0.08)';
            d.style.color = 'var(--text-primary)';
            d.style.alignSelf = 'flex-start';
            d.style.border = '1px solid rgba(255,255,255,0.05)';
            d.innerHTML = `<i class="fas fa-robot text-accent" style="margin-right:8px;"></i> ${normalizedText}`;
        } else {
            d.style.background = 'var(--accent)';
            d.style.color = '#ffffff';
            d.style.alignSelf = 'flex-end';
            d.style.marginLeft = 'auto';
            d.innerHTML = normalizedText;
        }
        messagesBox.appendChild(d);
        messagesBox.scrollTop = messagesBox.scrollHeight;
    }
    
    async function sendMessage() {
        const text = input.value.trim();
        if(!text) return;
        
        addMsg(text, false);
        input.value = '';
        
        // Typing indicator
        const typing = document.createElement('div');
        typing.className = 'chat-msg-anim typing-indicator';
        typing.innerHTML = `<span></span><span></span><span></span>`;
        typing.style.alignSelf = 'flex-start';
        typing.style.margin = '10px 0';
        messagesBox.appendChild(typing);
        messagesBox.scrollTop = messagesBox.scrollHeight;
        
        try {
            const csrfMeta = document.querySelector('meta[name="csrf-token"]');
            const token = csrfMeta ? csrfMeta.getAttribute('content') : '';
            
            const res = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify({ message: text })
            });
            typing.remove();
            
            if(!res.ok) {
                addMsg('Sorry, I encountered an error connecting to the AI service.', true);
                return;
            }
            
            const data = await res.json();
            if(data.success === false) {
                 addMsg(data.error || 'The AI service returned an error.', true);
            } else {
                 addMsg(data.reply || data.response || 'I am not sure how to respond to that.', true);
            }
            
        } catch(err) {
            typing.remove();
            addMsg('Sorry, network error occurred.', true);
        }
    }
    
    if(sendBtn) sendBtn.addEventListener('click', sendMessage);
    if(input) input.addEventListener('keypress', (e) => {
        if(e.key === 'Enter') sendMessage();
    });
    
    // Quick chips support
    document.querySelectorAll('.ai-chip').forEach(chip => {
        chip.addEventListener('click', () => {
             input.value = chip.textContent;
             sendMessage();
        });
    });
});
