document.addEventListener('DOMContentLoaded', async () => {
    logger("ADMIN_INIT");
    
    if (typeof loadSettings === 'function') loadSettings();
    await applyTranslations();
    
    const activeSection = sessionStorage.getItem('active_section') || 'orders-section';
    switchSection(activeSection);
    
    if (activeSection === 'orders-section' && typeof loadOrders === 'function') loadOrders();
    if (activeSection === 'products-section' && typeof loadProducts === 'function') loadProducts();
    if (activeSection === 'clients-section' && typeof loadClients === 'function') loadClients();

    document.getElementById('btnOrders')?.addEventListener('click', () => {
        switchSection('orders-section');
        if (typeof loadOrders === 'function') loadOrders();
    });

    document.getElementById('btnProducts')?.addEventListener('click', () => {
        switchSection('products-section');
        if (typeof loadProducts === 'function') loadProducts();
    });

    document.getElementById('btnClients')?.addEventListener('click', () => {
        switchSection('clients-section');
        if (typeof loadClients === 'function') loadClients();
    });

    document.getElementById('btnSms')?.addEventListener('click', () => {
        switchSection('sms-section');
    });

    document.getElementById('runImport')?.addEventListener('click', async () => {
        const st = document.getElementById('import-status');
        if (st) { st.style.display = 'block'; st.innerText = '⏳ Імпорт...'; st.style.background = '#2c3e50'; }
        const res = await apiRequest('/api/admin/import-xml', 'POST');
        if (st) {
            st.innerText = res && res.success ? '✅ Успішно' : '❌ Помилка';
            st.style.background = res && res.success ? '#27ae60' : '#e74c3c';
            setTimeout(() => { st.style.display = 'none'; }, 3000);
        }
    });

    document.getElementById('product-search')?.addEventListener('input', (e) => {
        if (typeof searchProducts === 'function') searchProducts(e.target.value);
    });

    document.getElementById('settingsSave')?.addEventListener('click', () => {
        const fields = ['cfg-lang', 'cfg-server', 'cfg-npkey', 'cfg-smskey', 'cfg-pass'];
        fields.forEach(id => {
            const el = document.getElementById(id);
            if (el) localStorage.setItem(id.replace('-', '_'), el.value.trim());
        });
        location.reload();
    });
});

function logger(msg, data = "") {
    console.log(`[${new Date().toLocaleTimeString()}] ADMIN_LOG: ${msg}`, data);
}

async function apiRequest(path, method = "GET", body = null) {
    const server = localStorage.getItem('cfg_server') || '';
    const pass = localStorage.getItem('cfg_pass') || '';
    const url = `${server.replace(/\/$/, '')}${path}`;
    const options = {
        method,
        headers: { 'Content-Type': 'application/json', 'X-Admin-Token': pass }
    };
    if (body) options.body = JSON.stringify(body);
    try {
        const res = await fetch(url, options);
        if (res.status === 401 || res.status === 403) { alert("Помилка авторизації!"); return null; }
        const text = await res.text();
        return text ? JSON.parse(text) : { success: true };
    } catch (e) { return null; }
}

function loadSettings() {
    ['cfg_lang', 'cfg_server', 'cfg_npkey', 'cfg_smskey', 'cfg_pass'].forEach(key => {
        const el = document.getElementById(key.replace('_', '-'));
        if (el) el.value = localStorage.getItem(key) || '';
    });
}

function switchSection(id) {
    sessionStorage.setItem('active_section', id);
    ['orders-section', 'products-section', 'clients-section', 'sms-section'].forEach(s => {
        const el = document.getElementById(s);
        if (el) el.style.display = (s === id) ? 'block' : 'none';
    });
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.querySelector(`[data-section="${id}"]`);
    if (activeBtn) activeBtn.classList.add('active');
}

async function applyTranslations() {
    const lang = localStorage.getItem('cfg_lang') || 'uk';
    try {
        const res = await fetch('lang.json');
        const dict = (await res.json())[lang];
        if (dict) {
            document.querySelectorAll('[data-lang]').forEach(el => {
                const key = el.getAttribute('data-lang');
                if (dict[key]) el.innerText = dict[key];
            });
            const searchInput = document.getElementById('product-search');
            if (searchInput && dict['search']) searchInput.placeholder = dict['search'];
        }
    } catch (e) {}
}