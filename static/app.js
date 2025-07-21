async function api(url, method, data) {
    const res = await fetch(url, {
        method: method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text);
    }
    return res.json();
}

document.getElementById('device-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        await api('/devices', 'POST', {
            name: document.getElementById('device-name').value,
            ip: document.getElementById('device-ip').value,
            port: parseInt(document.getElementById('device-port').value),
            pixels: parseInt(document.getElementById('device-pixels').value)
        });
        alert('Device added');
    } catch (err) {
        alert('Error adding device: ' + err.message);
    }
});

document.getElementById('group-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        const names = document.getElementById('group-devices').value.split(',').map(s => s.trim());
        await api('/groups', 'POST', {
            name: document.getElementById('group-name').value,
            devices: names
        });
        alert('Group added');
    } catch (err) {
        alert('Error adding group: ' + err.message);
    }
});

document.getElementById('color-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    try {
        await api('/color', 'POST', {
            group: document.getElementById('color-group').value,
            r: parseInt(document.getElementById('color-r').value),
            g: parseInt(document.getElementById('color-g').value),
            b: parseInt(document.getElementById('color-b').value)
        });
        alert('Color set');
    } catch (err) {
        alert('Error setting color: ' + err.message);
    }
});
