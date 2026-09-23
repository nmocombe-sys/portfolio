(() => {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        return;
    }

    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');
    const points = [];
    const trailLifetime = 950;
    const minimumPointDistance = 5;

    canvas.setAttribute('aria-hidden', 'true');
    canvas.style.cssText = [
        'position: fixed',
        'inset: 0',
        'width: 100%',
        'height: 100%',
        'pointer-events: none',
        'z-index: 20000'
    ].join(';');
    document.body.appendChild(canvas);

    function resizeCanvas() {
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = window.innerWidth * pixelRatio;
        canvas.height = window.innerHeight * pixelRatio;
        context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);
    }

    function addPoint(event) {
        const nextPoint = { x: event.clientX, y: event.clientY, time: performance.now() };
        const previousPoint = points[points.length - 1];

        if (!previousPoint || Math.hypot(nextPoint.x - previousPoint.x, nextPoint.y - previousPoint.y) >= minimumPointDistance) {
            points.push(nextPoint);
        } else {
            previousPoint.x = nextPoint.x;
            previousPoint.y = nextPoint.y;
            previousPoint.time = nextPoint.time;
        }
    }

    function drawTrail(now) {
        context.clearRect(0, 0, window.innerWidth, window.innerHeight);

        while (points.length && now - points[0].time > trailLifetime) {
            points.shift();
        }

        if (points.length > 1) {
            context.lineWidth = 1;
            context.lineCap = 'butt';
            context.lineJoin = 'miter';
            context.strokeStyle = '#EC133E';
            context.shadowColor = 'rgba(236, 19, 62, 0.55)';
            context.shadowBlur = 5;

            for (let index = 1; index < points.length; index += 1) {
                const start = points[index - 1];
                const end = points[index];
                const age = now - end.time;
                const opacity = Math.max(0, 1 - age / trailLifetime);

                context.globalAlpha = opacity;
                context.beginPath();
                context.moveTo(start.x, start.y);
                context.lineTo(end.x, end.y);
                context.stroke();
            }
        }

        context.globalAlpha = 1;
        context.shadowBlur = 0;
        requestAnimationFrame(drawTrail);
    }

    window.addEventListener('resize', resizeCanvas, { passive: true });
    window.addEventListener('pointermove', addPoint, { passive: true });
    resizeCanvas();
    requestAnimationFrame(drawTrail);
})();
