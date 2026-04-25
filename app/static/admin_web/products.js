let searchTimer;
let currentOffset = 0;
let isLoading = false;
let hasMore = true;
const limit = 50;

async function loadProducts(append = false) {
    if (isLoading || (!hasMore && append)) return;
    
    const list = document.getElementById("products-list");
    const searchInput = document.getElementById("product-search");
    const search = searchInput ? searchInput.value : "";

    if (!append) {
        currentOffset = 0;
        list.innerHTML = `<div style="text-align:center; padding:20px; color:white; font-weight:bold;">ЗАВАНТАЖЕННЯ...</div>`;
        hasMore = true;
    }

    isLoading = true;
    try {
        const url = `/api/admin/products?search=${encodeURIComponent(search)}&limit=${limit}&offset=${currentOffset}`;
        const products = await apiRequest(url);
        isLoading = false;

        if (!products || !Array.isArray(products) || products.length === 0) {
            if (!append) list.innerHTML = `<div style="text-align:center; padding:20px; color:white; font-weight:bold;">ТОВАРІВ НЕ ЗНАЙДЕНО</div>`;
            hasMore = false;
            return;
        }

        const html = products.map(p => `
            <div class="product-card" style="display:flex; align-items:center; gap:12px; padding:15px; background:#1a1a1a; margin-bottom:10px; border:1px solid #333; border-radius:10px;">
                <img src="${getImgUrl(p.image)}" style="width:70px; height:70px; object-fit:contain; background:#fff; border-radius:6px;" 
                    onerror="this.src='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII='">
                <div style="flex:1;">
                    <div style="font-size:14px; font-weight:bold; color:white; margin-bottom:4px; text-transform:uppercase;">${p.name}</div>
                    <div style="font-size:11px; color:#888; margin-bottom:8px;">SKU: ${p.sku}</div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <input type="number" value="${p.price}" 
                            onchange="updateProductField('${p.id}', 'price', this.value)" 
                            style="width:80px; padding:6px; border:1px solid #444; border-radius:4px; background:#222; color:white; font-weight:bold; font-size:14px;">
                        <span style="font-size:12px; color:#888;">UAH</span>
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; gap:12px; align-items:center; padding-left:10px; border-left:1px solid #333;">
                    <button onclick="deleteProductById('${p.id}')" style="background:none; border:none; font-size:20px; cursor:pointer;">🗑️</button>
                    <div style="font-size:11px; font-weight:bold; color:${p.stock > 0 ? '#27ae60' : '#e74c3c'}; background:#222; padding:3px 8px; border-radius:4px; border:1px solid #333;">
                        ${p.stock} ШТ
                    </div>
                </div>
            </div>
        `).join("");

        if (append) {
            list.insertAdjacentHTML('beforeend', html);
        } else {
            list.innerHTML = html;
        }

        currentOffset += products.length;
        if (products.length < limit) hasMore = false;

    } catch (e) {
        isLoading = false;
        if (!append) list.innerHTML = `<div style="color:#e74c3c; text-align:center; padding:20px;">ПОМИЛКА ЗАВАНТАЖЕННЯ</div>`;
    }
}

async function updateProductField(id, field, value) {
    const res = await apiRequest(`/api/admin/product/${id}/update`, 'PATCH', { [field]: value });
    if (res && res.success) {
        const notify = document.createElement('div');
        notify.innerText = "ЗБЕРЕЖЕНО";
        notify.style = "position:fixed; top:20px; left:50%; transform:translateX(-50%); background:#27ae60; color:white; padding:10px 30px; font-weight:bold; z-index:10000; border-radius:20px; box-shadow:0 4px 15px rgba(0,0,0,0.5);";
        document.body.appendChild(notify);
        setTimeout(() => notify.remove(), 1000);
    }
}

async function deleteProductById(id) {
    if (!confirm(`ВИДАЛИТИ ТОВАР?`)) return;
    const res = await apiRequest(`/api/admin/product/${id}`, 'DELETE'); 
    if (res && res.success) loadProducts(false);
}

// Поиск с задержкой, чтобы не спамить сервер
const pSearch = document.getElementById("product-search");
if (pSearch) {
    pSearch.addEventListener('input', () => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            loadProducts(false);
        }, 500);
    });
}

// Бесконечный скролл
window.addEventListener('scroll', () => {
    const sec = document.getElementById('products-section');
    if (sec && sec.style.display !== 'none') {
        if ((window.innerHeight + window.scrollY) >= document.body.offsetHeight - 800) {
            if (!isLoading && hasMore) loadProducts(true);
        }
    }
});