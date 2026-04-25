async function apiRequest(endpoint, method = "GET", body = null) {
    const savedServer = localStorage.getItem("cfg_server") || "https://zapchasti-backend-2.onrender.com";
    const adminToken = localStorage.getItem("cfg_pass") || "";
    const baseUrl = savedServer.replace(/\/$/, '');
    
    let url;
    if (endpoint.startsWith('http')) {
        url = endpoint;
    } else {
        const cleanPath = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        url = `${baseUrl}${cleanPath}`;
    }
    
    const options = { 
        method, 
        mode: 'cors',
        headers: { 
            "Content-Type": "application/json",
            "X-Admin-Token": adminToken
        } 
    };

    if (body) options.body = JSON.stringify(body);

    try {
        const res = await fetch(url, options);
        
        if (res.status === 401 || res.status === 403) {
            console.error(`LOG_AUTH_ERROR: ${res.status} at ${url}`);
            return null;
        }

        const text = await res.text();
        if (!text || text.trim() === "") return { success: true };

        try {
            return JSON.parse(text);
        } catch(e) {
            return { success: true, raw: text };
        }
    } catch (e) {
        console.error(`LOG_NETWORK_ERROR: ${url}`, e);
        return null;
    }
}

function getImgUrl(imgName) {
    if (!imgName || imgName === 'None' || imgName === 'undefined' || imgName === 'null') {
        return 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
    }
    
    if (imgName.startsWith('http')) return imgName;
    
    const savedServer = localStorage.getItem("cfg_server") || "https://zapchasti-backend-2.onrender.com";
    const baseUrl = savedServer.replace(/\/$/, '');
    const fileName = imgName.split('/').pop();
    
    return `${baseUrl}/api/proxy-image?url=https://ik.imagekit.io/xz64newpj/products/${fileName}`;
}

function copyText(text, el) {
    if (!navigator.clipboard || !text) return;
    
    navigator.clipboard.writeText(text).then(() => {
        console.log("LOG_COPY_SUCCESS");
        const oldHtml = el.innerHTML;
        el.innerHTML = "✅";
        el.style.pointerEvents = "none";
        
        setTimeout(() => { 
            el.innerHTML = oldHtml; 
            el.style.pointerEvents = "auto";
        }, 800);
    }).catch(err => {
        console.error("LOG_COPY_FAIL", err);
    });
}