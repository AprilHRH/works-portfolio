document.addEventListener('DOMContentLoaded', () => {
    const twoPlayerModeBtn = document.getElementById('two-player-mode');
    const aiModeBtn = document.getElementById('ai-mode');
    const twoPlayerOptions = document.getElementById('two-player-options');
    const aiOptions = document.getElementById('ai-options');
    const localPlayBtn = document.getElementById('local-play');
    const onlinePlayBtn = document.getElementById('online-play');
    const easyAIBtn = document.getElementById('easy-ai');
    const mediumAIBtn = document.getElementById('medium-ai');
    const hardAIBtn = document.getElementById('hard-ai');
    const backFromTwoPlayerBtn = document.getElementById('back-from-two-player');
    const backFromAIBtn = document.getElementById('back-from-ai');
    const rulesButton = document.getElementById('rules-button');
    const themeBtn = document.getElementById('theme-btn');
    const rulesModal = document.getElementById('rules-modal');
    const closeRulesBtn = document.getElementById('close-rules');
    
    function initTheme() {
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-mode');
            themeBtn.textContent = '☀️';
        } else {
            themeBtn.textContent = '🌙';
        }
    }
    
    function toggleTheme() {
        const body = document.body;
        const isDarkMode = body.classList.contains('dark-mode');
        
        if (isDarkMode) {
            body.classList.remove('dark-mode');
            themeBtn.textContent = '🌙';
            localStorage.setItem('theme', 'light');
        } else {
            body.classList.add('dark-mode');
            themeBtn.textContent = '☀️';
            localStorage.setItem('theme', 'dark');
        }
        
        body.style.transition = 'all 0.3s ease';
        playClickSound();
    }
    //点击音效
    function playClickSound() {
        try {
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.value = 800;
            oscillator.type = 'sine';
            
            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.1);
        } catch (e) {
        }
    }
    //浮动效果
    function addFloatAnimation(button) {
        button.classList.remove('animate');
        void button.offsetWidth;
        button.classList.add('animate');
    }
    //显示子选项
    function showSubOptions(mode) {
        if (mode === 'two-player') {
            aiOptions.classList.remove('show');
            setTimeout(() => {
                aiOptions.classList.add('hidden');
                twoPlayerOptions.classList.remove('hidden');
                setTimeout(() => {
                    twoPlayerOptions.classList.add('show');
                }, 10);
            }, 300);
        } else if (mode === 'ai') {
            twoPlayerOptions.classList.remove('show');
            setTimeout(() => {
                twoPlayerOptions.classList.add('hidden');
                aiOptions.classList.remove('hidden');
                setTimeout(() => {
                    aiOptions.classList.add('show');
                }, 10);
            }, 300);
        }
    }
    
    function hideSubOptions() {
        twoPlayerOptions.classList.remove('show');
        aiOptions.classList.remove('show');
        
        setTimeout(() => {
            twoPlayerOptions.classList.add('hidden');
            aiOptions.classList.add('hidden');
        }, 300);
    }
    //规则现实
    function closeRulesModal() {
        rulesModal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }
    //双人模式
    twoPlayerModeBtn.addEventListener('click', () => {
        addFloatAnimation(twoPlayerModeBtn);
        playClickSound();
        showSubOptions('two-player');
    });
    //人机模式
    aiModeBtn.addEventListener('click', () => {
        addFloatAnimation(aiModeBtn);
        playClickSound();
        showSubOptions('ai');
    });
    //双人模式的本地对战
    localPlayBtn.addEventListener('click', () => {
        playClickSound();
        setTimeout(() => {
            window.location.href = '/HTML/STTT-PVPLocal.html';
        }, 200);
    });
    //双人模式的联机对战
    onlinePlayBtn.addEventListener('click', () => {
        playClickSound();
        setTimeout(() => {
            window.location.href = '/HTML/STTT-PVPOnline.html';
        }, 200);
    });
    //人机模式的简单难度
    easyAIBtn.addEventListener('click', () => {
        playClickSound();
        setTimeout(() => {
            window.location.href = '/HTML/STTT-PVEeasy.html';
        }, 200);
    });
    //人机模式的中等难度
    mediumAIBtn.addEventListener('click', () => {
        playClickSound();
        setTimeout(() => {
            window.location.href = '/HTML/STTT-PVEpro.html';
        }, 200);
    });
    //人机模式的困难难度
    hardAIBtn.addEventListener('click', () => {
        playClickSound();
        setTimeout(() => {
            window.location.href = '/HTML/STTT-PVEhard.html';
        }, 200);
    });
    //返回按钮
    backFromTwoPlayerBtn.addEventListener('click', () => {
        playClickSound();
        hideSubOptions();
    });
    //人机模式的返回按钮
    backFromAIBtn.addEventListener('click', () => {
        playClickSound();
        hideSubOptions();
    });
    //规则按钮
    rulesButton.addEventListener('click', () => {
        addFloatAnimation(rulesButton);
        playClickSound();
        setTimeout(() => {
            rulesModal.classList.add('show');
            document.body.style.overflow = 'hidden';
        }, 200);
    });
    //主题切换按钮
    themeBtn.addEventListener('click', toggleTheme);
    //关闭规则
    closeRulesBtn.addEventListener('click', () => {
        playClickSound();
        closeRulesModal();
    });
    //点击外边关闭规则
    rulesModal.addEventListener('click', (e) => {
        if (e.target === rulesModal) {
            closeRulesModal();
        }
    });
    //按下Esc关闭规则
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && rulesModal.classList.contains('show')) {
            closeRulesModal();
        }
    });
    //所有按钮点击音效
    document.querySelectorAll('.neumorphic-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            playClickSound();
        });
    });
    //快捷键
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey) {
            switch(e.key) {
                case 'd':
                    e.preventDefault();
                    toggleTheme();
                    break;
                case 'h':
                    e.preventDefault();
                    rulesButton.click();
                    break;
            }
        }
    });
    //页面加载动画
    function addPageLoadAnimation() {
        const panel = document.querySelector('.neumorphic-panel');
        if (panel) {
            panel.style.opacity = '0';
            panel.style.transform = 'translateY(30px)';
            
            setTimeout(() => {
                panel.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                panel.style.opacity = '1';
                panel.style.transform = 'translateY(0)';
            }, 100);
        }
    }
    //多设备效果
    if ('ontouchstart' in window) {
        document.querySelectorAll('.neumorphic-btn').forEach(btn => {
            btn.addEventListener('touchstart', function() {
                this.style.transform = 'translateY(-1px) scale(1.01)';
            });
            
            btn.addEventListener('touchend', function() {
                this.style.transform = '';
            });
        });
    }
    //窗口调整
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    const optimizedResize = debounce(() => {
        if (window.innerWidth < 768) {
        } else {
        }
    }, 250);
    
    window.addEventListener('resize', optimizedResize);
    
    window.addEventListener('error', (e) => {
        console.error('页面错误:', e.error);
    });
    
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
        } else {
        }
    });
    
    initTheme();
    addPageLoadAnimation();

    const urlParams = new URLSearchParams(window.location.search);
    const showParam = urlParams.get('show');
    
    if (showParam === 'ai-difficulty') {
        setTimeout(() => {
            showSubOptions('ai');
        }, 1);
    }
    

});