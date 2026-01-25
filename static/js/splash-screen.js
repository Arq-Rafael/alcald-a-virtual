/**
 * SCREEN SAVER CONTROLLER
 * Alcaldía Virtual de Supatá
 * 
 * Funcionalidad:
 * - Screen Saver: Se activa después de 10 minutos de inactividad (solo usuarios autenticados)
 */

(function() {
    'use strict';

    // ========== CONFIGURACIÓN ==========
    const CONFIG = {
        inactivityTimeout: 600000,   // 10 minutos (600,000 ms)
        particleCount: 100,
        connectionDistance: 150
    };

    // ========== VARIABLES GLOBALES ==========
    let inactivityTimer = null;
    let screenSaverCanvas = null;
    let screenSaverCtx = null;
    let particles = [];
    let animationFrameId = null;
    let isScreenSaverActive = false;

    // ========== PARTICLE CLASS ==========
    class Particle {
        constructor(canvasWidth, canvasHeight) {
            this.x = Math.random() * canvasWidth;
            this.y = Math.random() * canvasHeight;
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = (Math.random() - 0.5) * 0.5;
            this.size = Math.random() * 2 + 1;
            this.colorType = Math.random() > 0.6 ? 'GOLD' : 'GREEN';
            this.color = this.colorType === 'GOLD' 
                ? 'rgba(255, 215, 0, 0.8)' 
                : 'rgba(57, 255, 20, 0.8)';
        }

        update(canvasWidth, canvasHeight) {
            this.x += this.vx;
            this.y += this.vy;

            if (this.x < 0 || this.x > canvasWidth) this.vx *= -1;
            if (this.y < 0 || this.y > canvasHeight) this.vy *= -1;
        }

        draw(ctx) {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
            ctx.fill();
            ctx.shadowBlur = 0;
        }
    }

    // ========== CANVAS ANIMATION ==========
    function initParticles(canvasWidth, canvasHeight) {
        particles = [];
        for (let i = 0; i < CONFIG.particleCount; i++) {
            particles.push(new Particle(canvasWidth, canvasHeight));
        }
    }

    function drawConnections(ctx, canvasWidth, canvasHeight) {
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const distance = Math.sqrt(dx * dx + dy * dy);

                if (distance < CONFIG.connectionDistance) {
                    const opacity = 1 - (distance / CONFIG.connectionDistance);
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);

                    if (particles[i].colorType === 'GOLD' && particles[j].colorType === 'GOLD') {
                        ctx.strokeStyle = `rgba(255, 215, 0, ${opacity * 0.4})`;
                    } else {
                        ctx.strokeStyle = `rgba(57, 255, 20, ${opacity * 0.3})`;
                    }

                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }
        }
    }

    function animate(canvas, ctx) {
        if (!canvas || !ctx) return;

        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);
        drawConnections(ctx, width, height);

        particles.forEach(p => {
            p.update(width, height);
            p.draw(ctx);
        });

        animationFrameId = requestAnimationFrame(() => animate(canvas, ctx));
    }

    function setupCanvas(canvas) {
        if (!canvas) return null;
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        const ctx = canvas.getContext('2d');
        
        initParticles(canvas.width, canvas.height);
        
        return ctx;
    }

    // ========== SCREEN SAVER ==========
    function showScreenSaver() {
        if (isScreenSaverActive) return;

        const screenSaver = document.getElementById('screenSaver');
        if (!screenSaver) return;

        isScreenSaverActive = true;
        screenSaver.classList.remove('hidden');

        screenSaverCanvas = document.getElementById('screenSaverCanvas');
        if (screenSaverCanvas) {
            screenSaverCtx = setupCanvas(screenSaverCanvas);
            animate(screenSaverCanvas, screenSaverCtx);
        }
    }

    function hideScreenSaver() {
        if (!isScreenSaverActive) return;

        const screenSaver = document.getElementById('screenSaver');
        if (!screenSaver) return;

        isScreenSaverActive = false;
        screenSaver.classList.add('hidden');

        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }

        resetInactivityTimer();
    }

    // ========== INACTIVITY DETECTOR ==========
    function resetInactivityTimer() {
        if (inactivityTimer) {
            clearTimeout(inactivityTimer);
        }

        inactivityTimer = setTimeout(() => {
            showScreenSaver();
        }, CONFIG.inactivityTimeout);
    }

    function startInactivityDetector() {
        // Solo iniciar si el elemento screenSaver existe (usuario autenticado)
        if (!document.getElementById('screenSaver')) return;

        const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart', 'click'];

        events.forEach(event => {
            document.addEventListener(event, () => {
                if (isScreenSaverActive) {
                    hideScreenSaver();
                } else {
                    resetInactivityTimer();
                }
            }, true);
        });

        resetInactivityTimer();
    }

    // ========== RESPONSIVE CANVAS ==========
    function handleResize() {
        if (screenSaverCanvas && screenSaverCtx && isScreenSaverActive) {
            screenSaverCanvas.width = window.innerWidth;
            screenSaverCanvas.height = window.innerHeight;
            initParticles(screenSaverCanvas.width, screenSaverCanvas.height);
        }
    }

    // ========== INICIALIZACIÓN ==========
    window.addEventListener('DOMContentLoaded', () => {
        startInactivityDetector();
    });

    window.addEventListener('resize', handleResize);

})();
