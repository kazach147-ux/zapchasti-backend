let ordersOffset = 0;
let isOrdersLoading = false;
let hasMoreOrders = true;
const ordersLimit = 50;

function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

async function loadOrders(append = false) {
    if (isOrdersLoading || (!hasMoreOrders && append)) return;
    const list = document.getElementById('orders-container');
    if (!list) return;

    if (!append) {
        ordersOffset = 0;
        hasMoreOrders = true;
        list.innerHTML = '<div style="text-align:center; padding:20px; color:white;">Завантаження...</div>';
    }

    isOrdersLoading = true;
    try {
        const url = `/api/admin/orders?limit=${ordersLimit}&offset=${ordersOffset}`;
        const orders = await apiRequest(url);
        isOrdersLoading = false;

        if (orders && Array.isArray(orders) && orders.length > 0) {
            if (!append) list.innerHTML = '';
            renderOrders(orders);
            ordersOffset += orders.length;
            if (orders.length < ordersLimit) hasMoreOrders = false;
        } else {
            hasMoreOrders = false;
            if (!append) list.innerHTML = '<div style="text-align:center; padding:20px; color:white;">Замовлень немає</div>';
        }
    } catch (e) {
        isOrdersLoading = false;
        console.error("ERR_ORDERS:", e);
    }
}

function renderOrders(orders) {
    const list = document.getElementById('orders-container');
    orders.forEach(ord => {
        const card = document.createElement('div');
        const status = (ord.status || 'new').toLowerCase();
        card.className = `order-card-mini status-${status}`;
        card.id = `order-card-${ord.id}`;
        card.style = "background:#1a1a1a; border-radius:12px; padding:15px; margin-bottom:20px; border:1px solid #333; color:white; position:relative;";
        
        let itemsHtml = (ord.items || []).map(item => `
            <div style="display:flex; justify-content:space-between; font-size:13px; border-bottom:1px solid #333; padding:5px 0;">
                <span>${escapeHtml(item.name || item.title_ua || "?")}</span>
                <b style="white-space:nowrap; margin-left:10px;">${item.qty} x ${item.price} ₴</b>
            </div>
        `).join('');

        const dateStr = ord.created_at ? new Date(ord.created_at).toLocaleString('uk-UA') : '—';
        const isNP = ord.delivery_type && ord.delivery_type.toLowerCase().includes('nova');

        card.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; border-bottom:1px solid #444; padding-bottom:8px;">
                <span style="font-weight:bold; font-size:16px;">#${ord.id} <span style="font-size:12px; color:#aaa; font-weight:normal;">${dateStr}</span></span>
                <button onclick="deleteOrder(${ord.id})" style="background:none; border:none; color:#ff4444; cursor:pointer; font-size:18px;">🗑</button>
            </div>

            <div style="display:flex; gap:10px; margin-bottom:15px;">
                <button onclick="updateStatus(${ord.id}, 'PROCESSING')" style="flex:1; background:#f1c40f; color:black; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">🟡 В РОБОТУ</button>
                <button onclick="updateStatus(${ord.id}, 'SHIPPED')" style="flex:1; background:#2ecc71; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">🟢 ВІДПРАВЛЕНО</button>
                <button onclick="updateStatus(${ord.id}, 'CANCELLED')" style="flex:1; background:#e74c3c; color:white; border:none; padding:8px; border-radius:6px; font-weight:bold; cursor:pointer;">🔴 СКАСУВАТИ</button>
            </div>

            <div style="margin-bottom:15px; line-height:1.6;">
                <div style="display:flex; align-items:center; gap:8px;">
                    👤 <b>${escapeHtml(ord.fio)}</b> 
                    <span onclick="copyText('${ord.fio}')" style="cursor:pointer; filter:grayscale(1);">📋</span>
                </div>
                <div style="display:flex; align-items:center; gap:8px;">
                    📞 <b style="color:#7360f2;">${ord.phone}</b>
                    <span onclick="copyText('${ord.phone}')" style="cursor:pointer; filter:grayscale(1);">📋</span>
                </div>
                <div style="display:flex; gap:10px; margin-top:8px;">
                    <button onclick="openViber('${ord.phone}')" style="background:#7360f2; color:white; border:none; padding:5px 12px; border-radius:4px; font-size:12px; cursor:pointer;">🟣 Viber</button>
                    <button onclick="openTelegram('${ord.phone}')" style="background:#0088cc; color:white; border:none; padding:5px 12px; border-radius:4px; font-size:12px; cursor:pointer;">🔵 Telegram</button>
                </div>
            </div>

            <div style="background:#222; padding:10px; border-radius:8px; margin-bottom:15px; border-left:4px solid #0056b3;">
                <div style="font-weight:bold; font-size:13px; margin-bottom:5px;">📦 ${isNP ? 'Nova Poshta' : 'Самовывоз'}</div>
                <div style="font-size:13px;">📍 ${escapeHtml(ord.city_name || '—')}</div>
                <div style="font-size:12px; color:#ccc;">🏢 ${escapeHtml(ord.warehouse || '—')}</div>
                
                ${isNP ? `
                <div style="display:flex; gap:5px; margin-top:10px;">
                    <input type="text" id="ttn-${ord.id}" placeholder="Ввести ТТН" value="${ord.ttn || ''}" 
                        style="flex:1; padding:8px; border:1px solid #444; border-radius:4px; font-size:13px; background:#000; color:white;">
                    <button onclick="saveTtn(${ord.id})" style="background:#0056b3; color:white; border:none; border-radius:4px; padding:0 12px; font-weight:bold; cursor:pointer;">OK</button>
                </div>
                <div style="margin-top:8px;">
                    <button onclick="openNP('${ord.ttn}')" style="width:100%; background:none; border:1px solid #0056b3; color:#0056b3; padding:6px; border-radius:4px; font-size:12px; cursor:pointer;">🔵 Відкрити на сайті НП</button>
                </div>
                ` : ''}
            </div>

            <div style="margin-bottom:15px;">
                <div style="font-weight:bold; font-size:14px; margin-bottom:8px;">🛒 ТОВАРИ:</div>
                ${itemsHtml}
                <div style="text-align:right; margin-top:10px; font-size:18px; font-weight:900; color:#2ecc71;">Разом: ${ord.total_price} ₴</div>
            </div>

            <div style="font-size:13px; color:#aaa; border-top:1px solid #333; padding-top:10px;">
                💳 Оплата: <b>${ord.payment_type === 'cod' ? 'Наложений' : 'Карта'}</b><br>
                💬 Коментар: ${escapeHtml(ord.client_comment || 'немає')}
            </div>
        `;
        list.appendChild(card);
    });
}

async function saveTtn(id) {
    const ttn = document.getElementById(`ttn-${id}`).value;
    const res = await apiRequest(`/api/admin/order/${id}/update-field`, 'PATCH', { ttn: ttn, status: 'SHIPPED' });
    if (res.success) {
        alert("ТТН збережено, статус змінено на ВІДПРАВЛЕНО");
        const card = document.getElementById(`order-card-${id}`);
        if(card) card.style.borderLeft = "5px solid #2ecc71";
    }
}

async function updateStatus(id, newStatus) {
    const res = await apiRequest(`/api/admin/order/${id}/update-field`, 'PATCH', { status: newStatus });
    if (res.success) {
        const card = document.getElementById(`order-card-${id}`);
        const colors = { 'PROCESSING': '#f1c40f', 'SHIPPED': '#2ecc71', 'CANCELLED': '#e74c3c', 'NEW': '#0056b3' };
        if(card) card.style.borderLeft = `5px solid ${colors[newStatus] || '#333'}`;
    }
}

async function deleteOrder(id) {
    if(!confirm("Видалити замовлення?")) return;
    const res = await apiRequest(`/api/admin/order/${id}`, 'DELETE');
    if(res.success) document.getElementById(`order-card-${id}`).remove();
}

function openNP(ttn) {
    const url = ttn ? `https://novaposhta.ua/tracking/?cargo_number=${ttn}` : `https://novaposhta.ua/`;
    window.open(url, '_blank');
}

function openViber(phone) {
    let clean = phone.replace(/\D/g, '');
    if (clean.startsWith('0')) clean = '38' + clean;
    window.open(`viber://chat?number=${clean}`, '_blank');
}

function openTelegram(phone) {
    let clean = phone.replace(/\D/g, '');
    if (clean.startsWith('0')) clean = '38' + clean;
    window.open(`https://t.me/+${clean}`, '_blank');
}

function copyText(text) {
    navigator.clipboard.writeText(text);
    alert("Скопійовано: " + text);
}

window.addEventListener('scroll', () => {
    if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 500) {
        if (!isOrdersLoading && hasMoreOrders) loadOrders(true);
    }
});