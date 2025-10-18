// Sora 2 AI Video Generation Platform - Main JavaScript

// Global variables
let particles = [];
let particleSystem;
let generationInProgress = false;
let currentProgress = 0;

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initParticleSystem();
    initScrollAnimations();
    initStatsCounters();
    initPromptHandling();
    initStyleSelector();

    // Add smooth scrolling for navigation
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
});

// Particle System using p5.js
function initParticleSystem() {
    new p5(function(p) {
        let particles = [];
        let mouseX = 0;
        let mouseY = 0;

        p.setup = function() {
            let canvas = p.createCanvas(p.windowWidth, p.windowHeight);
            canvas.parent('particle-container');
            canvas.style('position', 'fixed');
            canvas.style('top', '0');
            canvas.style('left', '0');
            canvas.style('z-index', '-1');

            // Create initial particles
            for (let i = 0; i < 50; i++) {
                particles.push(new Particle(p));
            }
        };

        p.draw = function() {
            p.clear();

            // Update and draw particles
            for (let i = particles.length - 1; i >= 0; i--) {
                particles[i].update(p);
                particles[i].display(p);

                if (particles[i].isDead()) {
                    particles.splice(i, 1);
                }
            }

            // Add new particles occasionally
            if (particles.length < 50 && p.random() < 0.02) {
                particles.push(new Particle(p));
            }

            // Connect nearby particles
            connectParticles(p);
        };

        p.windowResized = function() {
            p.resizeCanvas(p.windowWidth, p.windowHeight);
        };

        p.mouseMoved = function() {
            mouseX = p.mouseX;
            mouseY = p.mouseY;
        };

        function Particle(p) {
            this.x = p.random(p.width);
            this.y = p.random(p.height);
            this.vx = p.random(-0.5, 0.5);
            this.vy = p.random(-0.5, 0.5);
            this.alpha = p.random(50, 150);
            this.size = p.random(2, 4);
            this.life = 255;

            this.update = function(p) {
                this.x += this.vx;
                this.y += this.vy;

                // Mouse interaction
                let dx = mouseX - this.x;
                let dy = mouseY - this.y;
                let distance = p.sqrt(dx * dx + dy * dy);

                if (distance < 100) {
                    let force = (100 - distance) / 100;
                    this.vx -= (dx / distance) * force * 0.01;
                    this.vy -= (dy / distance) * force * 0.01;
                }

                // Wrap around edges
                if (this.x < 0) this.x = p.width;
                if (this.x > p.width) this.x = 0;
                if (this.y < 0) this.y = p.height;
                if (this.y > p.height) this.y = 0;

                this.life -= 0.5;
            };

            this.display = function(p) {
                p.noStroke();
                p.fill(0, 212, 255, this.alpha * (this.life / 255));
                p.ellipse(this.x, this.y, this.size);
            };

            this.isDead = function() {
                return this.life <= 0;
            };
        }

        function connectParticles(p) {
            for (let i = 0; i < particles.length; i++) {
                for (let j = i + 1; j < particles.length; j++) {
                    let distance = p.dist(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    if (distance < 80) {
                        let alpha = p.map(distance, 0, 80, 100, 0);
                        p.stroke(0, 212, 255, alpha);
                        p.strokeWeight(0.5);
                        p.line(particles[i].x, particles[i].y, particles[j].x, particles[j].y);
                    }
                }
            }
        }
    });
}

// Scroll animations
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, observerOptions);

    document.querySelectorAll('.reveal').forEach(el => {
        observer.observe(el);
    });
}

// Animated statistics counters
function initStatsCounters() {
    const counters = document.querySelectorAll('.stats-counter');

    const observerOptions = {
        threshold: 0.5
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const counter = entry.target;
                const target = parseInt(counter.getAttribute('data-target'));
                animateCounter(counter, target);
                observer.unobserve(counter);
            }
        });
    }, observerOptions);

    counters.forEach(counter => {
        observer.observe(counter);
    });
}

function animateCounter(element, target) {
    let current = 0;
    const increment = target / 100;
    const duration = 2000;
    const stepTime = duration / 100;

    const timer = setInterval(() => {
        current += increment;
        if (current >= target) {
            current = target;
            clearInterval(timer);
        }

        if (target >= 1000000) {
            element.textContent = (current / 1000000).toFixed(1) + 'M';
        } else if (target >= 1000) {
            element.textContent = (current / 1000).toFixed(0) + 'K';
        } else {
            element.textContent = Math.floor(current);
        }
    }, stepTime);
}

// Prompt handling
function initPromptHandling() {
    const promptTextarea = document.getElementById('video-prompt');
    const charCount = document.getElementById('char-count');

    if (promptTextarea && charCount) {
        promptTextarea.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = `${length}/500`;

            if (length > 450) {
                charCount.style.color = '#FF6B35';
            } else {
                charCount.style.color = '#9CA3AF';
            }
        });
    }
}

// Style selector
function initStyleSelector() {
    const styleOptions = document.querySelectorAll('.style-option');

    styleOptions.forEach(option => {
        option.addEventListener('click', function() {
            // Remove selected class from all options
            styleOptions.forEach(opt => opt.classList.remove('selected'));
            // Add selected class to clicked option
            this.classList.add('selected');

            // Add visual feedback
            anime({
                targets: this,
                scale: [0.95, 1],
                duration: 200,
                easing: 'easeOutQuad'
            });
        });
    });
}

// Video generation simulation
function generateVideo() {
    if (generationInProgress) return;

    const prompt = document.getElementById('video-prompt').value.trim();
    if (!prompt) {
        alert('Please enter a video description first!');
        return;
    }

    generationInProgress = true;
    currentProgress = 0;

    // Show progress container
    const progressContainer = document.getElementById('progress-container');
    const videoPreview = document.getElementById('video-preview');
    const generateBtn = document.getElementById('generate-btn');

    progressContainer.classList.remove('hidden');
    videoPreview.classList.remove('hidden');
    generateBtn.textContent = 'Generating...';
    generateBtn.disabled = true;

    // Simulate generation process
    const generationSteps = [
        'Analyzing prompt...',
        'Initializing AI models...',
        'Generating video frames...',
        'Applying style effects...',
        'Processing audio...',
        'Finalizing video...',
        'Generation complete!'
    ];

    let stepIndex = 0;
    const progressInterval = setInterval(() => {
        currentProgress += Math.random() * 15 + 5;
        if (currentProgress > 100) currentProgress = 100;

        updateProgress(currentProgress, generationSteps[stepIndex]);

        if (currentProgress >= 100) {
            clearInterval(progressInterval);
            setTimeout(() => {
                completeGeneration();
            }, 1000);
        } else if (currentProgress > (stepIndex + 1) * (100 / generationSteps.length)) {
            stepIndex = Math.min(stepIndex + 1, generationSteps.length - 1);
        }
    }, 500);
}

function updateProgress(progress, status) {
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');
    const statusElement = document.getElementById('generation-status');

    if (progressBar) {
        anime({
            targets: progressBar,
            width: `${progress}%`,
            duration: 500,
            easing: 'easeOutQuad'
        });
    }

    if (progressText) {
        progressText.textContent = `${Math.floor(progress)}%`;
    }

    if (statusElement) {
        statusElement.textContent = status;
    }
}

function completeGeneration() {
    const videoPreview = document.getElementById('video-preview');
    const generateBtn = document.getElementById('generate-btn');
    const progressContainer = document.getElementById('progress-container');

    // Show completion message
    videoPreview.innerHTML = `
        <div class="text-center">
            <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                </svg>
            </div>
            <h3 class="text-lg font-bold mb-2">Video Generated Successfully!</h3>
            <p class="text-sm text-gray-400 mb-4">Your AI-generated video is ready for download</p>
            <div class="flex gap-3 justify-center">
                <button class="btn-primary px-4 py-2 rounded-lg text-sm" onclick="downloadVideo()">
                    Download MP4
                </button>
                <button class="btn-secondary px-4 py-2 rounded-lg text-sm" onclick="shareVideo()">
                    Share
                </button>
            </div>
        </div>
    `;

    // Reset button
    generateBtn.textContent = 'Generate Another Video';
    generateBtn.disabled = false;

    // Hide progress after delay
    setTimeout(() => {
        progressContainer.classList.add('hidden');
    }, 2000);

    generationInProgress = false;

    // Add celebration animation
    anime({
        targets: videoPreview,
        scale: [0.9, 1],
        opacity: [0.7, 1],
        duration: 800,
        easing: 'easeOutElastic(1, .8)'
    });
}

// Utility functions
function scrollToGenerator() {
    const generator = document.getElementById('video-generator');
    if (generator) {
        generator.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

function playDemo() {
    alert('Demo video coming soon! Try the video generator below to see Sora 2 in action.');
}

function usePrompt(element) {
    const promptTextarea = document.getElementById('video-prompt');
    if (promptTextarea && element) {
        promptTextarea.value = element.textContent.trim();
        promptTextarea.dispatchEvent(new Event('input'));

        // Add visual feedback
        anime({
            targets: element,
            backgroundColor: ['rgba(0, 212, 255, 0.1)', 'rgba(255, 255, 255, 0.05)'],
            duration: 1000,
            easing: 'easeOutQuad'
        });
    }
}

function downloadVideo() {
    // Simulate download
    const link = document.createElement('a');
    link.href = '#';
    link.download = 'sora2-generated-video.mp4';
    link.click();

    // Show notification
    showNotification('Video download started!');
}

function shareVideo() {
    // Simulate share functionality
    if (navigator.share) {
        navigator.share({
            title: 'Check out my AI-generated video!',
            text: 'I created this amazing video using Sora 2 AI',
            url: window.location.href
        });
    } else {
        // Fallback: copy link to clipboard
        navigator.clipboard.writeText(window.location.href);
        showNotification('Link copied to clipboard!');
    }
}

function showNotification(message) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'fixed top-20 right-6 bg-cyan-500 text-white px-6 py-3 rounded-lg shadow-lg z-50';
    notification.textContent = message;

    document.body.appendChild(notification);

    // Animate in
    anime({
        targets: notification,
        translateX: [300, 0],
        opacity: [0, 1],
        duration: 500,
        easing: 'easeOutQuad'
    });

    // Remove after delay
    setTimeout(() => {
        anime({
            targets: notification,
            translateX: [0, 300],
            opacity: [1, 0],
            duration: 500,
            easing: 'easeInQuad',
            complete: () => {
                document.body.removeChild(notification);
            }
        });
    }, 3000);
}

// Navigation scroll effect
window.addEventListener('scroll', function() {
    const nav = document.querySelector('nav');
    if (window.scrollY > 50) {
        nav.style.background = 'rgba(10, 14, 26, 0.95)';
    } else {
        nav.style.background = 'rgba(10, 14, 26, 0.8)';
    }
});

// Initialize tooltips and additional interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add hover effects to feature cards
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            anime({
                targets: this,
                translateY: -8,
                duration: 300,
                easing: 'easeOutQuad'
            });
        });

        card.addEventListener('mouseleave', function() {
            anime({
                targets: this,
                translateY: 0,
                duration: 300,
                easing: 'easeOutQuad'
            });
        });
    });

    // Add click effects to buttons
    const buttons = document.querySelectorAll('button');
    buttons.forEach(button => {
        button.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            ripple.classList.add('ripple');

            this.appendChild(ripple);

            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});

// Add CSS for ripple effect
const style = document.createElement('style');
style.textContent = `
    button {
        position: relative;
        overflow: hidden;
    }

    .ripple {
        position: absolute;
        border-radius: 50%;
        background: rgba(255, 255, 255, 0.3);
        transform: scale(0);
        animation: ripple-animation 0.6s linear;
        pointer-events: none;
    }

    @keyframes ripple-animation {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);