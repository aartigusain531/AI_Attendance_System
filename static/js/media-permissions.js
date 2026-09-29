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

    function combineStreams(videoStream, audioStream) {
        const combinedStream = new MediaStream();

        if (videoStream) {
            videoStream.getVideoTracks().forEach(track => combinedStream.addTrack(track));
        }

        if (audioStream) {
            audioStream.getAudioTracks().forEach(track => combinedStream.addTrack(track));
        }

        return combinedStream;
    }

    async function requestBoth() {
        const preferredConstraints = {
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
        };

        try {
            return await request(preferredConstraints);
        } catch (error) {
            const isDeviceBusy = error && (
                error.name === "NotReadableError" ||
                error.name === "AbortError" ||
                /already in use|Could not start video source/i.test(error.message || "")
            );

            if (!isDeviceBusy) {
                throw error;
            }

            console.warn("Combined camera/audio request failed. Retrying with simpler device constraints:", error);

            let videoStream = null;
            let audioStream = null;

            try {
                videoStream = await request({ video: { facingMode: "user" } });
            } catch (videoError) {
                console.warn("Video-only fallback failed:", videoError);
                try {
                    videoStream = await request({ video: true });
                } catch (fallbackVideoError) {
                    console.warn("Basic video fallback failed:", fallbackVideoError);
                }
            }

            try {
                audioStream = await request({ audio: true });
            } catch (audioError) {
                console.warn("Audio-only fallback failed:", audioError);
            }

            if (!videoStream && !audioStream) {
                throw error;
            }

            return combineStreams(videoStream, audioStream);
        }
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
