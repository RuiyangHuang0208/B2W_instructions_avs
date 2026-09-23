import RFB from '../scripts/noVNC1.3.0/core/rfb.js';

document.addEventListener('DOMContentLoaded', function () {
    let rfb;
    const vncScreen = document.getElementById('vnc-screen');
    const connectBtn = document.getElementById('vnc-connect-btn');
    const disconnectBtn = document.getElementById('vnc-disconnect-btn');
    const statusIndicator = document.getElementById('vnc-status');
    const passwordInput = document.getElementById('vnc-password');
    const hostInput = document.getElementById('vnc-host');
    const portInput = document.getElementById('vnc-port');


    connectBtn.addEventListener('click', connectVNC);
    disconnectBtn.addEventListener('click', disconnectVNC);

    function connectVNC() {
        if (rfb) {
            disconnectVNC();
        }
        const vncHost = hostInput.value;
        const vncPort = portInput.value;
        const password = passwordInput.value;
        const websocket_url = `ws://${vncHost}:${vncPort}`;

        statusIndicator.textContent = 'Connecting...';
        statusIndicator.style.color = 'orange';

        rfb = new RFB(vncScreen, websocket_url, {
            credentials: { password: password }
        });


        rfb.addEventListener("connect", connected);
        rfb.addEventListener("disconnect", disconnected);
        rfb.addEventListener("credentialsrequired", credentialsRequired);
        rfb.addEventListener("securityfailure", securityFailure);
        rfb.addEventListener("clipboard", clipboardReceive);

        rfb.scaleViewport = true;
        rfb.resizeSession = false;
    }

    function disconnectVNC() {
        if (rfb) {
            rfb.disconnect();
        }
    }

    function connected() {
        statusIndicator.textContent = 'Connected';
        statusIndicator.style.color = '#3d8a3d';
        connectBtn.disabled = true;
        disconnectBtn.disabled = false;
    }

    function disconnected(e) {
        statusIndicator.textContent = 'Disconnected: ' + (e.detail.clean ? 'Clean' : 'Invalid Format');
        statusIndicator.style.color = '#cf2323';
        connectBtn.disabled = false;
        disconnectBtn.disabled = true;

        if (!e.detail.clean) {
            setTimeout(connectVNC, 5000);
        }
    }

    function credentialsRequired(e) {
        statusIndicator.textContent = 'Credentials Required';
        statusIndicator.style.color = 'orange';
    }

    function securityFailure(e) {
        statusIndicator.textContent = 'Security Failure: ' + e.detail.status;
        statusIndicator.style.color = 'red';
    }

    function clipboardReceive(e) {
        console.log("Clipboard data received: " + e.detail.text);
    }

});