/**
 * LOGIN SPLASH SCREEN
 * Alcaldía Virtual de Supatá
 * 
 * Se muestra SOLO una vez cuando el usuario accede al aplicativo por primera vez en la sesión
 * Después redirige al formulario de login
 */

(function() {
    'use strict';

    // Verificar si ya se mostró el splash en esta sesión
    const SPLASH_SHOWN_KEY = 'alcaldia_splash_shown';
    const hasShownSplash = sessionStorage.getItem(SPLASH_SHOWN_KEY);

    // Si ya se mostró, no hacer nada
    if (hasShownSplash) {
        return;
    }

    // ========== CONFIGURACIÓN ==========
    const CONFIG = {
        splashDuration: 4000,        // 4 segundos
        particleCount: 100,
        connectionDistance: 150
    };

    let canvas = null;
    let ctx = null;
    let particles = [];
    let animationFrameId = null;

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

    function animate() {
        if (!canvas || !ctx) return;

        const width = canvas.width;
        const height = canvas.height;

        ctx.clearRect(0, 0, width, height);
        drawConnections(ctx, width, height);

        particles.forEach(p => {
            p.update(width, height);
            p.draw(ctx);
        });

        animationFrameId = requestAnimationFrame(animate);
    }

    function setupCanvas() {
        canvas = document.getElementById('loginSplashCanvas');
        if (!canvas) return;
        
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        ctx = canvas.getContext('2d');
        
        initParticles(canvas.width, canvas.height);
    }

    // ========== SPLASH SCREEN CONTROL ==========
    function initLoginSplash() {
        const splashScreen = document.getElementById('loginSplashScreen');
        if (!splashScreen) return;

        // Mostrar el splash
        splashScreen.classList.remove('hidden');

        setupCanvas();
        animate();

        // Ocultar después de 4 segundos
        setTimeout(() => {
            splashScreen.classList.add('fade-out');
            setTimeout(() => {
                splashScreen.classList.add('hidden');
                if (animationFrameId) {
                    cancelAnimationFrame(animationFrameId);
                }
                // Marcar como mostrado en esta sesión
                sessionStorage.setItem(SPLASH_SHOWN_KEY, 'true');
            }, 800);
        }, CONFIG.splashDuration);
    }

    // ========== RESPONSIVE ==========
    function handleResize() {
        if (canvas && ctx) {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            initParticles(canvas.width, canvas.height);
        }
    }

    // ========== INICIALIZACIÓN ==========
    window.addEventListener('DOMContentLoaded', initLoginSplash);
    window.addEventListener('resize', handleResize);

})();
