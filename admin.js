let SERVER_URL = document.getElementById("server_url").value;

function saveURL() {
    SERVER_URL = document.getElementById("server_url").value;
    alert("URL збережено: " + SERVER_URL);
}

async function updateTTN() {
    let oid = document.getElementById("order_id").value;
    let ttn = document.getElementById("ttn").value;
    if (!oid || !ttn) { alert("Заповніть ID та ТТН"); return; }

    let res = await fetch(`${SERVER_URL}/orders/update_ttn`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: parseInt(oid), ttn: ttn })
    });

    if (res.ok) alert("TTN оновлено");
    else alert("Помилка оновлення TTN");
    loadOrders();
}

async function bulkSend() {
    let msg = document.getElementById("bulk_msg").value;
    if (!msg) { alert("Введіть текст повідомлення"); return; }

    let res = await fetch(`${SERVER_URL}/orders/all`);
    if (res.ok) {
        let orders = await res.json();
        let phones = Array.from(new Set(orders.map(o => o.phone)));
        alert("Повідомлення буде надіслано " + phones.length + " користувачам");
    } else {
        alert("Помилка завантаження замовлень");
    }
}

async function changePass() {
    let new_pass = document.getElementById("new_pass").value;
    if (!new_pass) { alert("Введіть новий пароль"); return; }

    let res = await fetch(`${SERVER_URL}/admin/change_password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: new_pass })
    });

    if (res.ok) alert("Пароль змінено");
    else alert("Помилка зміни пароля");
}

async function syncCatalog() {
    let res = await fetch(`${SERVER_URL}/catalog/sync`);
    if (res.ok) alert("Синхронізація каталогу запущена");
    else alert("Помилка синхронізації");
}

async function clearAllOrders() {
    if (!confirm("Видалити всі замовлення?")) return;

    let res = await fetch(`${SERVER_URL}/orders/clear_all`, { method: "DELETE" });
    if (res.ok) {
        alert("Всі замовлення видалено");
        loadOrders();
    } else {
        alert("Помилка очищення замовлень");
    }
}

async function loadOrders() {
    let ordersDiv = document.getElementById("orders");
    ordersDiv.innerHTML = "";

    let res = await fetch(`${SERVER_URL}/orders/all`);
    if (res.ok) {
        let orders = await res.json();
        orders.reverse().forEach(o => {
            let tr = document.createElement("tr");

            tr.innerHTML = `
                <td>${o.id}</td>
                <td>${o.fio}</td>
                <td>${o.phone}</td>
                <td>${o.total_price}</td>
                <td>${o.status || "---"}</td>
                <td>${o.ttn || ""}</td>
            `;

            ordersDiv.appendChild(tr);
        });
    } else {
        ordersDiv.innerHTML = `<tr><td colspan="6">Помилка завантаження</td></tr>`;
    }
}

window.onload = loadOrders;
