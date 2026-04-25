async function loadClients() {
    console.log("LOG_CLIENTS: INIT");
    const list = document.getElementById("clients-list");
    if (!list) {
        console.error("LOG_CLIENTS_ERROR: ELEMENT_NOT_FOUND");
        return;
    }
    
    list.innerHTML = `<div style="text-align:center; padding:20px; color:white;">Завантаження клієнтів...</div>`;
    
    try {
        const clients = await apiRequest("/api/admin/clients");
        console.log(`LOG_CLIENTS_SUCCESS: RECEIVED_${clients ? clients.length : 0}`);
        
        if (!clients || !Array.isArray(clients) || clients.length === 0) {
            console.warn("LOG_CLIENTS_EMPTY");
            list.innerHTML = `<div style="text-align:center; padding:20px; color:white;">Клієнтів не знайдено</div>`;
            return;
        }
        
        list.innerHTML = clients.map(c => {
            const safeFio = (c.fio || "Клієнт").replace(/'/g, "\\'");
            const cleanPhone = c.phone ? c.phone.replace(/\D/g, '') : "";
            const viberPhone = cleanPhone.startsWith('0') ? `38${cleanPhone}` : cleanPhone;
            
            return `
                <div class="client-card" style="display:flex; justify-content:space-between; align-items:center; padding:15px; background:#1a1a1a; margin-bottom:10px; border:1px solid #333; border-radius:12px; color:white;">
                    <div style="flex:1;">
                        <div style="font-weight:bold; font-size:15px; margin-bottom:5px; display:flex; align-items:center; gap:8px;">
                            👤 ${c.fio || 'Без імені'} 
                            <span onclick="copyText('${safeFio}', this)" style="cursor:pointer; font-size:12px; filter:grayscale(1);">📋</span>
                        </div>
                        <div style="color:#7360f2; font-weight:bold; font-size:14px; display:flex; align-items:center; gap:8px;">
                            📞 ${c.phone || '---'} 
                            <span onclick="copyText('${c.phone}', this)" style="cursor:pointer; font-size:12px; filter:grayscale(1);">📋</span>
                        </div>
                    </div>
                    <div style="display:flex; gap:10px;">
                        <button onclick="window.open('viber://chat?number=${viberPhone}')" 
                                style="background:#7360f2; color:white; border:none; border-radius:6px; padding:10px 16px; font-size:13px; font-weight:bold; cursor:pointer;">
                            Viber
                        </button>
                    </div>
                </div>`;
        }).join("");
            
    } catch (e) {
        console.error("LOG_CLIENTS_CRITICAL", e);
        list.innerHTML = `<div style="text-align:center; padding:20px; color:#ff4444;">Помилка завантаження</div>`;
    }
}