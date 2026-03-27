// main.js - Vanilla JS core logic

const ThemeManager = {
  themes: ['purple', 'blue', 'green', 'light'],
  current: 'purple',
  apply(theme) {
    if (!this.themes.includes(theme)) theme = 'purple';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('vsms-theme', theme);
    this.current = theme;
  },
  init() { 
    let saved = localStorage.getItem('vsms-theme');
    if (!this.themes.includes(saved)) saved = 'purple';
    this.apply(saved); 
  }
};
ThemeManager.init();

function animateCounter(el, target, duration=800) {
  const start = performance.now();
  const update = (time) => {
    const elapsed = time - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * target).toLocaleString('en-IN');
    if (progress < 1) requestAnimationFrame(update);
    else el.textContent = target.toLocaleString('en-IN');
  };
  requestAnimationFrame(update);
}

document.addEventListener('DOMContentLoaded', () => {
  // Counters
  document.querySelectorAll('[data-count]').forEach(el => {
    animateCounter(el, parseInt(el.dataset.count));
  });

  // Staggered Cards
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add('card-enter');
        }, i * 100);
      }
    });
  });
  document.querySelectorAll('.stat-card, .glass-card, .panel-metal').forEach(
    card => observer.observe(card)
  );

  // Sidebar toggle
  const toggleBtn = document.getElementById('sidebar-toggle');
  const sidebar = document.getElementById('sidebar');
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('collapsed');
    });
  }

  // Password toggles on forms
  document.querySelectorAll('.toggle-password').forEach(icon => {
    icon.addEventListener('click', function() {
      const input = this.previousElementSibling;
      if (input.type === 'password') {
        input.type = 'text';
        this.classList.remove('fa-eye');
        this.classList.add('fa-eye-slash');
      } else {
        input.type = 'password';
        this.classList.add('fa-eye');
        this.classList.remove('fa-eye-slash');
      }
    });
  });

  // Confirm generic delete action
  document.querySelectorAll('.needs-confirmation').forEach(btn => {
    btn.addEventListener('click', (e) => {
      if(!confirm("Are you sure you want to perform this action?")) {
        e.preventDefault();
      }
    });
  });

  // Loading state on form submission
  document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
      // Don't show loading if form fails native HTML5 validation
      if(this.checkValidity()) {
        const btn = this.querySelector('button[type="submit"], .btn-metal');
        if(btn) {
            // Slight delay so form submission triggered before disabling
            setTimeout(() => {
                btn.classList.add('btn-loading');
            }, 10);
        }
      }
    });
  });

  // Global Search
  const searchOverlay = document.getElementById('global-search');
  const searchInput = document.getElementById('search-input');
  
  if(searchOverlay) {
      document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
          e.preventDefault();
          searchOverlay.classList.toggle('active');
          if(searchOverlay.classList.contains('active')) searchInput.focus();
        }
        if (e.key === 'Escape') searchOverlay.classList.remove('active');
      });

      searchOverlay.addEventListener('click', (e) => {
        if(e.target === searchOverlay) searchOverlay.classList.remove('active');
      });

      if(searchInput) {
          searchInput.addEventListener('input', debounce(async (e) => {
              const q = e.target.value;
              if(q.length < 2) return;
              const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
              const data = await res.json();
              renderSearchResults(data);
          }, 300));
      }
  }
  
  // Notification toggle
  const notifBtn = document.querySelector('.notif-btn');
  const notifDropdown = document.querySelector('.notif-dropdown');
  if(notifBtn && notifDropdown) {
      notifBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          notifDropdown.classList.toggle('show');
      });
      document.addEventListener('click', (e) => {
          if(!notifDropdown.contains(e.target) && !notifBtn.contains(e.target)) {
              notifDropdown.classList.remove('show');
          }
      });
  }
  // User Profile Dropdown
  const userBtn = document.querySelector('.user-profile-btn');
  const userMenu = document.querySelector('.user-dropdown-menu');
  if(userBtn && userMenu) {
      userBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          userMenu.classList.toggle('show');
      });
      document.addEventListener('click', (e) => {
          if(!userMenu.contains(e.target) && !userBtn.contains(e.target)) {
              userMenu.classList.remove('show');
          }
      });
      document.addEventListener('keydown', (e) => {
          if(e.key === 'Escape') userMenu.classList.remove('show');
      });
  }
});

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => { clearTimeout(timeout); func(...args); };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function renderSearchResults(data) {
    const resultsDiv = document.getElementById('search-results');
    if(!resultsDiv) return;
    resultsDiv.classList.add('has-results');
    resultsDiv.innerHTML = '';
    
    // Simple render
    ['customers', 'vehicles', 'jobs', 'inventory'].forEach(type => {
        if(data[type] && data[type].length > 0) {
            const h = document.createElement('h5');
            h.style.color = 'var(--accent)';
            h.style.padding = '5px 24px';
            h.style.margin = '10px 0 0 0';
            h.textContent = type.toUpperCase();
            resultsDiv.appendChild(h);
            
            data[type].forEach(item => {
                const a = document.createElement('a');
                a.className = 'search-item';
                a.href = `/${type}`; // fallback link
                let text = item.name || item.plate || item.id;
                a.innerHTML = `<i class="fas fa-search"></i> <span>${text}</span>`;
                resultsDiv.appendChild(a);
            });
        }
    });
}

function fetchWithCSRF(url, options = {}) {
  const csrfTokenElement = document.querySelector('input[name="csrf_token"]');
  const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
  const csrfToken = csrfTokenElement ? csrfTokenElement.value : (csrfTokenMeta || '');
  
  const headers = new Headers(options.headers || {});
  if (options.method && ['POST', 'PUT', 'DELETE'].includes(options.method.toUpperCase())) {
    if (csrfToken && !headers.has('X-CSRFToken')) {
      headers.append('X-CSRFToken', csrfToken);
    }
  }
  
  options.headers = headers;
  return fetch(url, options);
}

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  let icon = 'info-circle';
  if(type === 'success') icon = 'check-circle';
  if(type === 'error') icon = 'exclamation-circle';
  if(type === 'warning') icon = 'exclamation-triangle';
  
  toast.innerHTML = `<i class="fas fa-${icon}" style="margin-right:15px; font-size:1.2rem;"></i> <span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => { toast.style.animation = 'slideInLeft 0.3s ease reverse forwards'; setTimeout(() => toast.remove(), 300); }, 4000);
}

// Notification Polling
async function fetchNotifications() {
  try {
    const res = await fetch('/api/notifications');
    if(!res.ok) return;
    const data = await res.json();
    const badge = document.querySelector('.notif-count');
    if(badge) {
        badge.textContent = data.unread_count;
        badge.style.display = data.unread_count > 0 ? 'flex' : 'none';
    }
    const list = document.querySelector('.notif-list');
    if(list) {
        list.innerHTML = '';
        data.notifications.forEach(n => {
            const div = document.createElement('div');
            div.className = 'notif-item';
            div.innerHTML = `
                <div class="notif-icon bg-${n.type === 'error' ? 'red' : 'gold'}"><i class="fas fa-bell"></i></div>
                <div class="notif-content">
                    <h4>${n.title}</h4>
                    <p>${n.message}</p>
                </div>
            `;
            if(!n.is_read) {
                div.addEventListener('click', () => {
                    fetchWithCSRF(`/api/notifications/${n.id}/read`, {method: 'POST'})
                    .then(() => fetchNotifications());
                });
            }
            list.appendChild(div);
        });
    }
  } catch(e) { console.error('Notif parse error', e); }
}
setInterval(fetchNotifications, 30000);
setTimeout(fetchNotifications, 1000); // trigger soon after load

window.markAllRead = function(e) {
    if(e) e.stopPropagation();
    fetchWithCSRF('/api/notifications/read_all', { method: 'POST' }).then(() => fetchNotifications());
};

window.clearAllNotifs = function(e) {
    if(e) e.stopPropagation();
    fetchWithCSRF('/api/notifications/clear_all', { method: 'POST' }).then(() => fetchNotifications());
};
