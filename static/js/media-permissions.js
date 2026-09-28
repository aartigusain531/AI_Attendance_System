(function () {
    "use strict";

    function isLocalhost() {
        return ["localhost", "127.0.0.1", "[::1]"].includes(window.location.hostname);
    }

    function isSecureMediaOrigin() {
        return window.isSecureContext || isLocalhost();
    }

    function ensureSupported() {
        if (!isSecureMediaOrigin()) {
            throw new Error("Camera and microphone require HTTPS. Open the HTTPS address printed by the server, then allow both devices in the browser prompt.");
        }
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("This browser does not support camera and microphone access.");
        }
    }

    function describe(error, device) {
        if (!error) {
            return `${device} access failed.`;
        }
        if (error.name === "NotAllowedError" || error.name === "SecurityError") {
            return `${device} access was blocked. Select the lock icon in Chrome, set ${device.toLowerCase()} to Allow, and reload the page.`;
        }
        if (error.name === "NotFoundError") {
            return `No ${device.toLowerCase()} was found. Connect a ${device.toLowerCase()} and try again.`;
        }
        if (error.name === "NotReadableError") {
            return `The ${device.toLowerCase()} is busy. Close other apps or browser tabs using it and try again.`;
        }
        return error.message || `${device} access failed.`;
    }

    async function request(constraints) {
        ensureSupported();
        return navigator.mediaDevices.getUserMedia(constraints);
    }

    async function requestBoth() {
        return request({
            video: {
                facingMode: { ideal: "user" },
                width: { ideal: 1280 },
                height: { ideal: 720 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                channelCount: { ideal: 1 }
            }
        });
    }

    window.AttendanceMedia = {
        isSecureMediaOrigin,
        request,
        requestBoth,
        describe,
        stop(stream) {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        }
    };
}());
