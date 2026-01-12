// ========================================
// MODERN FAKE NEWS DETECTOR - JavaScript
// Animations, Interactions, UX Enhancements
// ========================================

// === GLOBAL STATE ===
const APP = {
    initialized: false,
    scrollThreshold: 300,
    navActive: false
};

// === DOM READY ===
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

// === INITIALIZATION ===
function initializeApp() {
    if (APP.initialized) return;
    
    // Initialize all modules
    initSmoothScroll();
    initScrollToTop();
    initMobileNav();
    initCharacterCounter();
    initFormHandling();
    initSocialVerification();
    initConfidenceBar();
    initScrollAnimations();
    initNavbarScroll();
    
    // Focus on textarea if detector section is visible
    const newsInput = document.getElementById('newsInput');
    if (newsInput && isInViewport(newsInput)) {
        newsInput.focus();
    }
    
    APP.initialized = true;
    console.log('✓ Fake News Detector initialized');
}

// === SMOOTH SCROLL ===
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip empty anchors
            if (href === '#' || !href) return;
            
            e.preventDefault();
            const target = document.querySelector(href);
            
            if (target) {
                const navHeight = document.querySelector('.navbar')?.offsetHeight || 70;
                const targetPosition = target.offsetTop - navHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
                
                // Close mobile menu if open
                if (APP.navActive) {
                    toggleMobileNav();
                }
            }
        });
    });
}

// === SCROLL TO TOP ===
function initScrollToTop() {
    const scrollBtn = document.getElementById('scrollToTop');
    if (!scrollBtn) return;
    
    // Show/hide on scroll
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > APP.scrollThreshold) {
            scrollBtn.classList.add('visible');
        } else {
            scrollBtn.classList.remove('visible');
        }
    });
    
    // Click handler
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// === MOBILE NAVIGATION ===
function initMobileNav() {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (!navToggle || !navMenu) return;
    
    navToggle.addEventListener('click', toggleMobileNav);
}

function toggleMobileNav() {
    const navMenu = document.querySelector('.nav-menu');
    const navToggle = document.querySelector('.nav-toggle');
    
    APP.navActive = !APP.navActive;
    navMenu?.classList.toggle('active');
    navToggle?.classList.toggle('active');
}

// === NAVBAR SCROLL EFFECT ===
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;
    
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 4px 16px rgba(0, 0, 0, 0.3)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
}

// === CHARACTER COUNTER ===
function initCharacterCounter() {
    const newsInput = document.getElementById('newsInput');
    const charCount = document.getElementById('charCount');
    
    if (!newsInput || !charCount) return;
    
    // Update counter on input
    newsInput.addEventListener('input', () => {
        const count = newsInput.value.length;
        const maxLength = newsInput.getAttribute('maxlength') || 5000;
        
        charCount.textContent = count;
        
        // Visual feedback at 90%
        if (count >= maxLength * 0.9) {
            charCount.style.color = '#f59e0b'; // Warning color
        } else {
            charCount.style.color = '#00ffff'; // Primary color
        }
    });
    
    // Initialize on page load
    charCount.textContent = newsInput.value.length;
}

// === SOCIAL VERIFICATION ===
function initSocialVerification() {
    const form = document.getElementById('socialForm');
    const platformSelect = document.getElementById('socialPlatform');
    const input = document.getElementById('socialInput');
    const charCount = document.getElementById('socialCharCount');
    const clearBtn = document.getElementById('socialClear');
    const submitBtn = document.getElementById('socialSubmit');
    const progress = document.getElementById('socialProgress');
    const resultContainer = document.getElementById('socialResult');
    const platformHint = document.getElementById('platformHint');

    if (!form || !input) return;

    const hints = {
        twitter: 'Paste tweet text or thread snippet',
        facebook: 'Paste Facebook post text',
        instagram: 'Paste caption or short description',
        youtube: 'Paste title or description',
        'news url': 'Paste full article URL to auto-fetch'
    };

    const updateHint = () => {
        const selected = (platformSelect?.value || '').toLowerCase();
        if (platformHint) {
            platformHint.textContent = hints[selected] || 'Paste text or URL to verify';
        }
    };

    platformSelect?.addEventListener('change', updateHint);
    updateHint();

    const updateCounter = () => {
        if (!charCount) return;
        const count = input.value.length;
        const maxLength = input.getAttribute('maxlength') || 5000;
        charCount.textContent = count;
        charCount.style.color = count >= maxLength * 0.9 ? '#f59e0b' : '#00ffff';
    };

    input.addEventListener('input', updateCounter);
    updateCounter();

    clearBtn?.addEventListener('click', () => {
        input.value = '';
        input.focus();
        updateCounter();
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const content = input.value.trim();
        const platform = platformSelect?.value || 'news';

        if (!content) {
            showNotification('Please paste some content or a URL to verify.', 'error');
            input.focus();
            return;
        }

        toggleSocialLoading(true, submitBtn, progress);

        try {
            const response = await fetch('/api/social-verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ platform, content })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                const message = data.error || 'Verification failed. Please try again.';
                showNotification(message, 'error');
                resultContainer.innerHTML = '';
                return;
            }

            renderSocialResult(data, resultContainer);
            initConfidenceBar();
            showNotification('Verification complete', 'success');
        } catch (err) {
            console.error('Social verify error:', err);
            showNotification('Something went wrong. Please retry.', 'error');
        } finally {
            toggleSocialLoading(false, submitBtn, progress);
        }
    });
}

function toggleSocialLoading(isLoading, submitBtn, progress) {
    if (submitBtn) {
        submitBtn.classList.toggle('loading', isLoading);
        submitBtn.disabled = !!isLoading;
    }
    if (progress) {
        progress.classList.toggle('active', isLoading);
    }
}

function renderSocialResult(payload, container) {
    if (!container) return;

    const {
        prediction = 'Result unavailable',
        label = 'neutral',
        confidence = 0,
        reason_summary = '',
        reasons = [],
        processing_time = '-',
        platform = 'social'
    } = payload;

    const badgeClass = label === 'fake' ? 'fake' : label === 'real' ? 'real' : 'neutral';
    const reasonTags = reasons.map(item => `<span class="reason-tag">${item}</span>`).join('');

    container.innerHTML = `
        <div class="social-result-card">
            <div>
                <div class="result-badge ${badgeClass}">${label.toUpperCase()}</div>
                <h3 class="result-title">${prediction}</h3>
                <p class="confidence-text">Confidence: ${confidence}%</p>
                <p class="processing-time">Source: ${platform} • ${processing_time}</p>
                <p class="about-description">${reason_summary}</p>
                <div class="reason-tags">${reasonTags}</div>
            </div>
            <div>
                <div class="confidence-bar">
                    <div class="confidence-fill" data-confidence="${confidence}"></div>
                </div>
                <p class="processing-time">Top indicators drive the bar width.</p>
            </div>
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// === CONFIDENCE BAR WIDTH ===
function initConfidenceBar() {
    const bars = document.querySelectorAll('.confidence-fill[data-confidence]');
    if (!bars.length) return;

    bars.forEach(bar => {
        const value = Number.parseFloat(bar.dataset.confidence);
        if (!Number.isFinite(value)) return;

        const clamped = Math.min(100, Math.max(0, value));
        bar.style.width = `${clamped}%`;
    });
}

// === FORM HANDLING ===
function initFormHandling() {
    const form = document.getElementById('detectionForm');
    const predictBtn = document.getElementById('predictBtn');
    const newsInput = document.getElementById('newsInput');
    
    if (!form || !predictBtn) return;
    
    form.addEventListener('submit', (e) => {
        // Validate input
        if (!newsInput || newsInput.value.trim().length === 0) {
            e.preventDefault();
            showNotification('Please enter some text to analyze', 'error');
            newsInput?.focus();
            return;
        }
        
        if (newsInput.value.trim().length < 10) {
            e.preventDefault();
            showNotification('Please enter at least 10 characters', 'error');
            return;
        }
        
        // Show loading state
        predictBtn.classList.add('loading');
        predictBtn.disabled = true;
        
        // The form will submit naturally
        // Loading state will be maintained until page reloads
    });
}

// === CLEAR INPUT ===
window.clearInput = function() {
    const newsInput = document.getElementById('newsInput');
    const charCount = document.getElementById('charCount');
    
    if (newsInput) {
        newsInput.value = '';
        newsInput.focus();
        
        if (charCount) {
            charCount.textContent = '0';
            charCount.style.color = '#00ffff';
        }
        
        // Trigger input event for any listeners
        newsInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
};

// === LOAD SAMPLE NEWS ===
window.loadSample = function(type) {
    const newsInput = document.getElementById('newsInput');
    if (!newsInput) return;
    
    // Show loading state
    newsInput.style.opacity = '0.5';
    newsInput.disabled = true;
    
    // Fetch sample from API
    fetch(`/api/sample?type=${type}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to fetch sample');
            }
            return response.json();
        })
        .then(data => {
            if (data.news) {
                newsInput.value = data.news;
                newsInput.dispatchEvent(new Event('input', { bubbles: true }));
                showNotification(`Sample ${type} news loaded`, 'success');
            } else {
                throw new Error('No sample data received');
            }
        })
        .catch(error => {
            console.error('Error loading sample:', error);
            showNotification('Failed to load sample. Please try again.', 'error');
            
            // Fallback samples
            const fallbackSamples = {
                fake: "BREAKING: Scientists discover that chocolate cures all diseases! Doctors hate this one simple trick that Big Pharma doesn't want you to know about.",
                real: "Researchers at a major university have published a peer-reviewed study in a scientific journal showing promising results in early-stage cancer treatment trials."
            };
            
            newsInput.value = fallbackSamples[type] || fallbackSamples.real;
            newsInput.dispatchEvent(new Event('input', { bubbles: true }));
        })
        .finally(() => {
            newsInput.style.opacity = '1';
            newsInput.disabled = false;
            newsInput.focus();
        });
};

// === SCROLL ANIMATIONS ===
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe all cards and sections
    const elements = document.querySelectorAll('.glass-card, .feature-card, .step-card, .roadmap-card');
    
    elements.forEach((el, index) => {
        // Initial state
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = `opacity 0.6s ease-out ${index * 0.1}s, transform 0.6s ease-out ${index * 0.1}s`;
        
        // Observe
        observer.observe(el);
    });
}

// === UTILITY: CHECK IF IN VIEWPORT ===
function isInViewport(element) {
    if (!element) return false;
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// === NOTIFICATION SYSTEM ===
function showNotification(message, type = 'info') {
    // Remove existing notification
    const existing = document.querySelector('.notification');
    if (existing) {
        existing.remove();
    }
    
    // Create notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    
    // Styles
    Object.assign(notification.style, {
        position: 'fixed',
        top: '100px',
        right: '20px',
        padding: '1rem 1.5rem',
        backgroundColor: type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#00ffff',
        color: type === 'error' || type === 'success' ? '#ffffff' : '#0a0a0f',
        borderRadius: '12px',
        boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
        zIndex: '10000',
        fontWeight: '600',
        animation: 'slideInRight 0.4s ease-out',
        backdropFilter: 'blur(16px)'
    });
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.4s ease-out';
        setTimeout(() => notification.remove(), 400);
    }, 3000);
}

// === ANIMATIONS CSS (injected dynamically) ===
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(100px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes slideOutRight {
        from {
            opacity: 1;
            transform: translateX(0);
        }
        to {
            opacity: 0;
            transform: translateX(100px);
        }
    }
    
    .nav-toggle.active span:nth-child(1) {
        transform: rotate(45deg) translate(5px, 5px);
    }
    
    .nav-toggle.active span:nth-child(2) {
        opacity: 0;
    }
    
    .nav-toggle.active span:nth-child(3) {
        transform: rotate(-45deg) translate(7px, -6px);
    }
`;
document.head.appendChild(style);

// === RESULT ANIMATION ===
// Animate result card if it exists on page load
window.addEventListener('load', () => {
    const resultCard = document.querySelector('.result-card');
    if (resultCard) {
        resultCard.classList.add('animate-result');
        
        // Scroll to result
        setTimeout(() => {
            resultCard.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }, 500);
    }
});

// === KEYBOARD SHORTCUTS ===
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit form
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        const form = document.getElementById('detectionForm');
        const newsInput = document.getElementById('newsInput');
        
        if (form && newsInput && document.activeElement === newsInput) {
            e.preventDefault();
            form.requestSubmit();
        }
    }
    
    // Escape to clear input (when focused)
    if (e.key === 'Escape') {
        const newsInput = document.getElementById('newsInput');
        if (newsInput && document.activeElement === newsInput) {
            clearInput();
        }
    }
});

// === PERFORMANCE OPTIMIZATION ===
// Debounce scroll events
let scrollTimeout;
const originalScrollHandler = window.onscroll;

window.addEventListener('scroll', () => {
    if (scrollTimeout) {
        window.cancelAnimationFrame(scrollTimeout);
    }
    
    scrollTimeout = window.requestAnimationFrame(() => {
        // Scroll handling is already attached in individual functions
    });
}, { passive: true });

// === EXPORT FOR TESTING ===
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        clearInput,
        loadSample,
        showNotification
    };
}

// === CONSOLE BRANDING ===
console.log(
    '%c🔍 Fake News Detector %cv3.0',
    'font-size: 20px; font-weight: bold; color: #00ffff;',
    'font-size: 12px; color: #8b5cf6;'
);
console.log(
    '%cPowered by AI & Machine Learning',
    'font-size: 12px; color: #64748b; font-style: italic;'
);
console.log(
    '%cKeyboard Shortcuts:\n• Ctrl+Enter: Submit form\n• Escape: Clear input',
    'font-size: 11px; color: #a8b2d1; margin-top: 8px;'
);
