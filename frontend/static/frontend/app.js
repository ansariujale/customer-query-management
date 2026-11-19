// common helper functions used by all pages

function getToken() {
    return localStorage.getItem('token');
}

function saveLogin(token, username) {
    localStorage.setItem('token', token);
    localStorage.setItem('username', username);
}

function clearLogin() {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
}

// send user to login page if there is no token saved
function requireLogin() {
    if (!getToken()) {
        window.location.href = '/login/';
    }
}

// one function to call our backend api, adds the token header automatically
async function api(url, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {'Content-Type': 'application/json'},
    };

    if (getToken()) {
        options.headers['Authorization'] = 'Token ' + getToken();
    }
    if (body) {
        options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    // token expired or deleted, login again
    if (response.status === 401 && getToken()) {
        clearLogin();
        window.location.href = '/login/';
        return;
    }

    let data = null;
    try {
        data = await response.json();
    } catch (e) {
        data = null;
    }

    return {ok: response.ok, status: response.status, data: data};
}

// DRF returns errors like {"email": ["Enter a valid email"]}, turn it into readable text
function formatErrors(data) {
    if (!data) {
        return 'Something went wrong. Please try again.';
    }
    if (data.error) return escapeHtml(data.error);
    if (data.detail) return escapeHtml(data.detail);

    let lines = [];
    for (const field in data) {
        let msg = Array.isArray(data[field]) ? data[field].join(' ') : data[field];
        msg = escapeHtml(msg);
        if (field === 'non_field_errors') {
            lines.push(msg);
        } else {
            lines.push(field.replace(/_/g, ' ') + ': ' + msg);
        }
    }
    return lines.join('<br>');
}

function showMessage(text, type) {
    const box = document.getElementById('message');
    box.className = 'message ' + type;
    box.innerHTML = text;
}

// escape user text before putting it in innerHTML (avoid XSS)
function escapeHtml(text) {
    if (text === null || text === undefined) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function formatDate(value) {
    if (!value) return '-';
    return new Date(value).toLocaleString();
}

// header: show username and handle logout
document.addEventListener('DOMContentLoaded', function () {
    const userSpan = document.getElementById('nav-user');
    if (userSpan && localStorage.getItem('username')) {
        userSpan.textContent = 'Logged in as ' + localStorage.getItem('username');
    }

    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', async function (e) {
            e.preventDefault();
            await api('/api/logout/', 'POST');
            clearLogin();
            window.location.href = '/login/';
        });
    }
});
