/**
 * PhotoBridge Frontend - Single Page App
 * No framework, vanilla JS, targeting Mobile Safari
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

let state = {
    configured: false,
    media: [],           // all items loaded so far for current album
    albums: [],          // album list from /api/albums [{name, count}]
    loadedAlbums: {},    // cache: album_name -> {items:[], total:N, has_more:bool, loading:bool}
    currentTab: 'all-photos',
    searchQuery: '',
    selectedAlbum: null,
    currentViewerIndex: 0,
    favorites: JSON.parse(localStorage.getItem('favorites') || '[]'),
    viewerActive: false,
    viewedMedia: [],
    inAlbumDetail: false,
    pinRequired: false,
    albumLoading: false   // true while initial album fetch is in progress
};

const PAGE_SIZE = 100; // items per page

// ============================================================================
// LAZY LOADING OBSERVER
// ============================================================================

let lazyImageObserver = null;

function getLazyImageObserver() {
    if (lazyImageObserver) return lazyImageObserver;

    if ('IntersectionObserver' in window) {
        lazyImageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const el = entry.target;
                    if (el.dataset.src) {
                        el.src = el.dataset.src;
                        el.removeAttribute('data-src');
                        if (el.tagName === 'VIDEO') {
                            el.load(); // Required to trigger video loading in Safari/Chrome
                        }
                    }
                    observer.unobserve(el);
                }
            });
        }, {
            rootMargin: '300px 0px 300px 0px', // Preload 300px before/after viewport
            threshold: 0
        });
    }
    return lazyImageObserver;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', async () => {
    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(() => {
            console.log('Service worker registration failed (expected in development)');
        });
    }

    // Initialize the app
    await initializeApp();
    render();
});

async function initializeApp() {
    let config = null;
    while (!config) {
        try {
            config = await fetchConfig();
        } catch (err) {
            console.log('Server not ready, retrying in 2 seconds...');
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }

    state.configured = config.configured;

    if (state.configured) {
        if (config.pin_required && !localStorage.getItem('pb_pin')) {
            state.pinRequired = true;
        } else {
            try {
                await loadAlbums();
                // Lazy-load the All Photos folder immediately so the main grid works
                await loadAlbumMedia('All Photos');
            } catch (err) {
                console.warn('Initialization fetch failed:', err);
            }
        }
    }
}

// ============================================================================
// API CALLS
// ============================================================================

async function authedFetch(url, options = {}) {
    if (!options.headers) options.headers = {};
    const pin = localStorage.getItem('pb_pin');
    if (pin) {
        options.headers['X-PhotoBridge-PIN'] = pin;
    }
    
    const res = await fetch(url, options);
    
    if (res.status === 401) {
        localStorage.removeItem('pb_pin');
        state.pinRequired = true;
        render();
        throw new Error('Unauthorized');
    }
    
    return res;
}

async function fetchConfig() {
    const headers = {};
    const pin = localStorage.getItem('pb_pin');
    if (pin) {
        headers['X-PhotoBridge-PIN'] = pin;
    }
    const res = await fetch('/api/config', { headers });
    return res.json();
}

async function setPhotosDir(path, pin = null) {
    const headers = { 'Content-Type': 'application/json' };
    const storedPin = pin || localStorage.getItem('pb_pin');
    if (storedPin) {
        headers['X-PhotoBridge-PIN'] = storedPin;
    }

    const res = await fetch('/api/config', {
        method: 'POST',
        headers,
        body: JSON.stringify({ photos_dir: path, access_pin: pin })
    });

    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to set photos directory');
    }

    return res.json();
}

async function loadAlbums() {
    const res = await authedFetch('/api/albums');
    state.albums = await res.json();
}

/**
 * Lazy-load an album's first page from the API.
 * Subsequent pages are loaded by loadMoreAlbumMedia().
 */
async function loadAlbumMedia(albumName) {
    const cached = state.loadedAlbums[albumName];
    if (cached && cached.items.length > 0) {
        // Already have data — just make it the active set
        state.media = cached.items;
        state.viewedMedia = cached.items;
        return;
    }

    state.albumLoading = true;
    render();

    try {
        const url = `/api/media?album=${encodeURIComponent(albumName)}&offset=0&limit=${PAGE_SIZE}`;
        const res = await authedFetch(url);
        const data = await res.json();

        state.loadedAlbums[albumName] = {
            items: data.items,
            total: data.total,
            has_more: data.has_more,
            loading: false
        };
        state.media = data.items;
        state.viewedMedia = data.items;
    } finally {
        state.albumLoading = false;
    }
}

/**
 * Load the next page for the current album and append to the grid.
 */
async function loadMoreAlbumMedia(albumName) {
    const cached = state.loadedAlbums[albumName];
    if (!cached || cached.loading || !cached.has_more) return;

    cached.loading = true;
    const offset = cached.items.length;
    const url = `/api/media?album=${encodeURIComponent(albumName)}&offset=${offset}&limit=${PAGE_SIZE}`;

    try {
        const res = await authedFetch(url);
        const data = await res.json();

        cached.items.push(...data.items);
        cached.total = data.total;
        cached.has_more = data.has_more;
        state.media = cached.items;
        state.viewedMedia = cached.items;

        // Append new items to existing grid instead of full re-render
        appendGridItems(data.items);
    } finally {
        cached.loading = false;
    }
}

async function rescanMedia() {
    const res = await authedFetch('/api/rescan', { method: 'POST' });
    if (res.ok) {
        state.loadedAlbums = {};
        state.media = [];
        await loadAlbums();
        await loadAlbumMedia('All Photos');
        showToast('Photos rescanned');
        render();
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function render() {
    const app = document.getElementById('app');
    app.innerHTML = '';

    if (state.pinRequired) {
        app.appendChild(renderPinScreen());
    } else if (!state.configured) {
        app.appendChild(renderSetupScreen());
    } else {
        app.appendChild(renderMainApp());
    }
}

function renderPinScreen() {
    const div = document.createElement('div');
    div.id = 'pinScreen';
    div.innerHTML = `
        <h1>PhotoBridge Secure Access</h1>
        <p>A secure connection PIN is required to browse photos. Enter the PIN configured on the server laptop.</p>
        <div class="pin-inputs">
            <input type="password" id="pinInput" placeholder="Enter PIN" maxlength="20">
        </div>
        <button id="pinSubmitBtn">Unlock</button>
        <div class="error" id="pinErrorMsg"></div>
    `;

    div.querySelector('#pinSubmitBtn').addEventListener('click', async () => {
        const pin = div.querySelector('#pinInput').value.trim();
        const errEl = div.querySelector('#pinErrorMsg');
        errEl.textContent = '';

        if (!pin) {
            errEl.textContent = 'Please enter the Access PIN.';
            return;
        }

        try {
            // Test if PIN works by loading media with it
            const res = await fetch('/api/media', {
                headers: { 'X-PhotoBridge-PIN': pin }
            });

            if (res.status === 401) {
                errEl.textContent = 'Incorrect Access PIN. Please try again.';
                return;
            }

            if (!res.ok) {
                throw new Error('Server returned error ' + res.status);
            }

            // Pin is correct! Store it and load app
            localStorage.setItem('pb_pin', pin);
            state.pinRequired = false;
            
            const config = await fetchConfig();
            state.configured = config.configured;

            if (state.configured) {
                await loadAlbums();
                await loadAlbumMedia('All Photos');
            }
            render();
        } catch (err) {
            errEl.textContent = 'Verification failed: ' + err.message;
        }
    });

    return div;
}

function renderSetupScreen() {
    const div = document.createElement('div');
    div.id = 'setupScreen';
    div.innerHTML = `
        <h1>PhotoBridge</h1>
        <p>Enter the full path to the folder on your laptop you want to browse.<br>Example: <code>C:\\Users\\yourname\\Pictures</code></p>
        <div class="input-group">
            <input type="text" id="pathInput" placeholder="C:\\Users\\yourname\\Pictures">
            <button id="browseBtn" class="secondary-button">Browse Laptop...</button>
        </div>
        <div style="margin-top: 15px; margin-bottom: 20px; width: 100%; max-width: 320px; text-align: left;">
            <label style="font-size: 13px; color: #888; display: block; margin-bottom: 5px;">Access PIN (Optional - secures access from other devices)</label>
            <input type="password" id="setupPinInput" placeholder="Set connection password" style="width: 100%; padding: 12px; background: #1c1c1c; border: 1px solid #333; border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
        </div>
        <button id="connectBtn">Connect</button>
        <div class="error" id="errorMsg"></div>
    `;

    div.querySelector('#browseBtn').addEventListener('click', async () => {
        const errEl = div.querySelector('#errorMsg');
        errEl.textContent = '';
        try {
            showToast('Check your laptop screen for the folder browser...');
            const res = await fetch('/api/select-folder', { method: 'POST' }).then(r => r.json());
            if (res.path) {
                div.querySelector('#pathInput').value = res.path;
            }
        } catch (err) {
            errEl.textContent = 'Failed to open file explorer: ' + err.message;
        }
    });

    div.querySelector('#connectBtn').addEventListener('click', async () => {
        const path = div.querySelector('#pathInput').value.trim();
        const pin = div.querySelector('#setupPinInput').value.trim();
        if (!path) return;

        try {
            await setPhotosDir(path, pin);
            if (pin) {
                localStorage.setItem('pb_pin', pin);
            } else {
                localStorage.removeItem('pb_pin');
            }
            state.configured = true;
            state.loadedAlbums = {};
            await loadAlbums();
            await loadAlbumMedia('All Photos');
            render();
        } catch (err) {
            div.querySelector('#errorMsg').textContent = err.message;
        }
    });

    return div;
}

function renderMainApp() {
    const div = document.createElement('div');
    div.id = 'mainApp';
    div.innerHTML = `
        <div id="topBar"></div>
        <div id="gridContainer"></div>
        <div id="fullscreenViewer"></div>
    `;

    const topBar = div.querySelector('#topBar');
    topBar.innerHTML = `
        <button class="tab-button${state.currentTab === 'all-photos' ? ' active' : ''}" data-tab="all-photos">All Photos</button>
        <button class="tab-button${state.currentTab === 'albums' ? ' active' : ''}" data-tab="albums">Albums</button>
        <button class="tab-button${state.currentTab === 'favorites' ? ' active' : ''}" data-tab="favorites">Favorites</button>
        <input type="text" id="searchBox" placeholder="Search...">
        <button id="settingsBtn">⚙️</button>
    `;

    // Tab buttons
    topBar.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', () => {
            topBar.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            state.currentTab = btn.dataset.tab;
            state.searchQuery = '';
            state.inAlbumDetail = false; // Reset to album list on tab switch
            const searchBox = topBar.querySelector('#searchBox');
            if (searchBox) searchBox.value = '';
            render();
        });
    });

    // Search
    const searchBox = topBar.querySelector('#searchBox');
    if (searchBox) {
        searchBox.addEventListener('input', (e) => {
            state.searchQuery = e.target.value;
            renderGrid(div);
        });
    }

    // Settings
    topBar.querySelector('#settingsBtn').addEventListener('click', () => {
        openSettings();
    });

    // Grid
    renderGrid(div);

    // Viewer
    const viewer = div.querySelector('#fullscreenViewer');
    viewer.innerHTML = `
        <div id="viewerContent"></div>
        <div id="viewerControls">
            <button class="control-button" id="closeBtn" title="Close">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
            </button>
            <button class="control-button" id="slideshowBtn" title="Slideshow">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8 5v14l11-7z"/>
                </svg>
            </button>
            <button class="control-button" id="favButton" title="Favorite">
                <svg class="icon-outline" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
                </svg>
                <svg class="icon-filled" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
            </button>
            <button class="control-button" id="saveBtn" title="Save to Photos">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
            </button>
        </div>
    `;

    viewer.querySelector('#closeBtn').addEventListener('click', closeViewer);
    viewer.querySelector('#slideshowBtn').addEventListener('click', toggleSlideshow);
    viewer.querySelector('#favButton').addEventListener('click', toggleFavorite);
    viewer.querySelector('#saveBtn').addEventListener('click', saveToPhotos);

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!state.viewerActive) return;
        if (e.key === 'ArrowLeft') previousMedia();
        if (e.key === 'ArrowRight') nextMedia();
        if (e.key === 'Escape') closeViewer();
    });

    return div;
}

function getAlbumList() {
    // Use the album list fetched from /api/albums (has name + count from server)
    return state.albums;
}

function setupPullToRefresh(container) {
    let pullStartY = 0;
    container.addEventListener('touchstart', (e) => {
        if (container.scrollTop === 0) {
            pullStartY = e.touches[0].clientY;
        }
    });

    container.addEventListener('touchend', (e) => {
        if (container.scrollTop === 0 && e.changedTouches[0].clientY - pullStartY > 100) {
            rescanMedia();
        }
    });
}

function renderGrid(app) {
    const container = app.querySelector('#gridContainer');
    container.innerHTML = '';

    // 1. ALBUMS GRID VIEW
    if (state.currentTab === 'albums' && !state.inAlbumDetail) {
        const albumList = getAlbumList();
        const albumsGrid = document.createElement('div');
        albumsGrid.className = 'albums-grid';

        if (albumList.length === 0) {
            const msg = document.createElement('div');
            msg.style.cssText = 'padding:40px;text-align:center;color:#8e8e93;font-size:15px;';
            msg.textContent = 'No albums found. Make sure a photos folder is configured.';
            albumsGrid.appendChild(msg);
        }

        albumList.forEach(album => {
            const card = document.createElement('div');
            card.className = 'album-card';

            // Cover: use first cached image from this album if available
            const cached = state.loadedAlbums[album.name];
            const coverMedia = cached ? cached.find(m => m.type === 'image') || cached[0] : null;

            let coverHtml = '';
            if (coverMedia && coverMedia.type === 'image') {
                coverHtml = `<img src="/api/thumb/${coverMedia.id}?w=300" loading="lazy" alt="${album.name}">`;
            } else {
                coverHtml = `<div class="video-cover-placeholder"><span class="play-icon">📷</span></div>`;
            }

            card.innerHTML = `
                <div class="album-cover">
                    ${coverHtml}
                </div>
                <div class="album-info">
                    <div class="album-name">${album.name}</div>
                    <div class="album-count">${album.count} item${album.count !== 1 ? 's' : ''}</div>
                </div>
            `;

            card.addEventListener('click', async () => {
                state.selectedAlbum = album.name;
                state.inAlbumDetail = true;
                await loadAlbumMedia(album.name);
                render();
            });

            albumsGrid.appendChild(card);
        });

        container.appendChild(albumsGrid);
        setupPullToRefresh(container);
        return;
    }

    // 2. ALBUM DETAIL VIEW HEADER (If in album detail)
    if (state.currentTab === 'albums' && state.inAlbumDetail) {
        const backBar = document.createElement('div');
        backBar.className = 'album-back-bar';
        backBar.innerHTML = `
            <button id="albumBackBtn" class="back-button">◀ Albums</button>
            <span class="album-title">${state.selectedAlbum}</span>
        `;
        backBar.querySelector('#albumBackBtn').addEventListener('click', () => {
            state.inAlbumDetail = false;
            render();
        });
        container.appendChild(backBar);
    }

    // 3. LOADING STATE (album fetch in progress)
    if (state.albumLoading) {
        const loader = document.createElement('div');
        loader.style.cssText = 'padding:60px;text-align:center;color:#8e8e93;font-size:15px;';
        loader.innerHTML = '<div class="spinner" style="margin:0 auto 16px;"></div>Loading photos...';
        container.appendChild(loader);
        return;
    }

    // 4. PHOTO GRID VIEW (For All Photos, Favorites, or Album Detail)
    let filteredMedia = state.media;

    // Filter by tab
    if (state.currentTab === 'favorites') {
        // Favorites: search across all cached loaded albums
        const allLoaded = Object.values(state.loadedAlbums).flatMap(a => a.items || []);
        filteredMedia = allLoaded.filter(m => state.favorites.includes(m.id));
    }

    // Filter by search
    if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filteredMedia = filteredMedia.filter(m => m.filename.toLowerCase().includes(q));
    }

    state.viewedMedia = filteredMedia;

    // Group by date
    const grouped = {};
    filteredMedia.forEach(media => {
        const date = new Date(media.date_taken);
        const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        if (!grouped[dateKey]) grouped[dateKey] = [];
        grouped[dateKey].push(media);
    });

    // Render initial grid tiles
    renderGridTiles(container, filteredMedia);

    // Infinite scroll sentinel — loads next page when scrolled near bottom
    const albumKey = state.currentTab === 'albums' ? state.selectedAlbum : 'All Photos';
    const cached = state.loadedAlbums[albumKey];
    if (cached && cached.has_more) {
        const sentinel = document.createElement('div');
        sentinel.id = 'scrollSentinel';
        sentinel.style.cssText = 'height:60px;display:flex;align-items:center;justify-content:center;color:#8e8e93;font-size:13px;';
        sentinel.textContent = 'Loading more...';
        container.appendChild(sentinel);

        const scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                scrollObserver.disconnect();
                loadMoreAlbumMedia(albumKey);
            }
        }, { rootMargin: '200px' });
        scrollObserver.observe(sentinel);
    } else if (cached && !cached.has_more && filteredMedia.length > 0) {
        // Show total count at the bottom
        const footer = document.createElement('div');
        footer.style.cssText = 'padding:24px;text-align:center;color:#48484a;font-size:12px;';
        footer.textContent = `${cached.total} items`;
        container.appendChild(footer);
    }

    // Pull to refresh
    setupPullToRefresh(container);
}

/**
 * Create a single media tile element.
 */
function createMediaTile(media, filteredMedia) {
    const tile = document.createElement('div');
    tile.className = 'media-tile';

    if (media.type === 'image') {
        const img = document.createElement('img');
        img.alt = media.filename;
        const pin = localStorage.getItem('pb_pin') || '';
        const pinParam = pin ? `&pin=${pin}` : '';
        const observer = getLazyImageObserver();
        if (observer) {
            img.dataset.src = `/api/thumb/${media.id}?w=300${pinParam}`;
            img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"%3E%3C/svg%3E';
            tile.appendChild(img);
            observer.observe(img);
        } else {
            img.src = `/api/thumb/${media.id}?w=300${pinParam}`;
            tile.appendChild(img);
        }
    } else {
        const containerDiv = document.createElement('div');
        containerDiv.className = 'video-tile-container';
        const video = document.createElement('video');
        video.className = 'video-thumbnail';
        video.muted = true;
        video.playsInline = true;
        video.setAttribute('playsinline', '');
        const pin = localStorage.getItem('pb_pin') || '';
        const pinParamUrl = pin ? `?pin=${pin}` : '';
        const observer = getLazyImageObserver();
        if (observer) {
            video.dataset.src = `/api/full/${media.id}${pinParamUrl}#t=0.1`;
            video.preload = 'metadata';
            containerDiv.appendChild(video);
            observer.observe(video);
        } else {
            video.src = `/api/full/${media.id}${pinParamUrl}#t=0.1`;
            video.preload = 'metadata';
            containerDiv.appendChild(video);
        }
        const overlay = document.createElement('div');
        overlay.className = 'video-overlay';
        overlay.innerHTML = '<div class="play-icon">▶</div>';
        containerDiv.appendChild(overlay);
        tile.appendChild(containerDiv);
    }

    tile.addEventListener('click', () => {
        state.currentViewerIndex = state.viewedMedia.indexOf(media);
        if (state.currentViewerIndex < 0) state.currentViewerIndex = 0;
        openViewer();
    });
    return tile;
}

/**
 * Render grid tiles (date-grouped) into a container.
 */
function renderGridTiles(container, mediaList) {
    const grouped = {};
    mediaList.forEach(media => {
        const date = new Date(media.date_taken);
        const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        if (!grouped[dateKey]) grouped[dateKey] = [];
        grouped[dateKey].push(media);
    });

    Object.entries(grouped).forEach(([dateKey, medias]) => {
        const header = document.createElement('div');
        header.className = 'date-header';
        header.dataset.dateKey = dateKey;
        header.textContent = dateKey;
        container.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'grid';
        grid.dataset.dateKey = dateKey;
        medias.forEach(media => grid.appendChild(createMediaTile(media, mediaList)));
        container.appendChild(grid);
    });
}

/**
 * Append new items to the existing grid (called on infinite scroll load-more).
 * Merges new items into existing date-group rows or creates new ones.
 */
function appendGridItems(newItems) {
    const container = document.querySelector('#gridContainer');
    if (!container) return;

    // Remove sentinel and footer before appending
    const old = container.querySelector('#scrollSentinel');
    if (old) old.remove();
    const footer = container.querySelector('[data-footer]');
    if (footer) footer.remove();

    const albumKey = state.currentTab === 'albums' ? state.selectedAlbum : 'All Photos';
    const cached = state.loadedAlbums[albumKey];

    newItems.forEach(media => {
        const date = new Date(media.date_taken);
        const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });

        // Find existing grid row for this date
        let grid = container.querySelector(`.grid[data-date-key="${CSS.escape(dateKey)}"]`);
        if (!grid) {
            // Create new date header + grid row
            const header = document.createElement('div');
            header.className = 'date-header';
            header.dataset.dateKey = dateKey;
            header.textContent = dateKey;
            container.appendChild(header);
            grid = document.createElement('div');
            grid.className = 'grid';
            grid.dataset.dateKey = dateKey;
            container.appendChild(grid);
        }
        grid.appendChild(createMediaTile(media, state.viewedMedia));
    });

    // Re-attach sentinel or footer
    if (cached && cached.has_more) {
        const sentinel = document.createElement('div');
        sentinel.id = 'scrollSentinel';
        sentinel.style.cssText = 'height:60px;display:flex;align-items:center;justify-content:center;color:#8e8e93;font-size:13px;';
        sentinel.textContent = 'Loading more...';
        container.appendChild(sentinel);
        const scrollObserver = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                scrollObserver.disconnect();
                loadMoreAlbumMedia(albumKey);
            }
        }, { rootMargin: '200px' });
        scrollObserver.observe(sentinel);
    } else {
        const footer = document.createElement('div');
        footer.setAttribute('data-footer', '1');
        footer.style.cssText = 'padding:24px;text-align:center;color:#48484a;font-size:12px;';
        footer.textContent = `${cached ? cached.total : state.media.length} items`;
        container.appendChild(footer);
    }
}

// ============================================================================
// VIEWER
// ============================================================================

function openViewer() {
    state.viewerActive = true;
    const viewer = document.getElementById('fullscreenViewer');
    viewer.classList.add('active');
    updateViewer();
}

function closeViewer() {
    state.viewerActive = false;
    document.getElementById('fullscreenViewer').classList.remove('active');
}

function updateViewer() {
    const media = state.viewedMedia[state.currentViewerIndex];
    const content = document.getElementById('viewerContent');
    content.innerHTML = '';

    const pin = localStorage.getItem('pb_pin') || '';
    const pinParam = pin ? `?pin=${pin}` : '';

    if (media.type === 'image') {
        const img = document.createElement('img');
        img.id = 'viewerImage';
        img.src = `/api/full/${media.id}${pinParam}`;
        img.alt = media.filename;
        content.appendChild(img);

        // If this image is a Live Photo, set up the badge and play preview
        if (media.live_video_id) {
            // Add Live Photo badge
            const badge = document.createElement('div');
            badge.className = 'live-badge';
            badge.innerHTML = '<span class="live-icon"></span><span>LIVE</span>';
            content.appendChild(badge);

            // Add background video clip for playback
            const video = document.createElement('video');
            video.id = 'viewerLiveVideo';
            video.src = `/api/full/${media.live_video_id}${pinParam}`;
            video.muted = true;
            video.playsInline = true;
            video.setAttribute('playsinline', '');
            video.loop = true;
            content.appendChild(video);

            let isPlaying = false;

            const startPlayback = (e) => {
                if (isPlaying) return;
                isPlaying = true;
                
                // Add class to display the video element
                video.classList.add('playing');
                video.play().catch(err => console.warn('Live Photo video play failed:', err));
                
                // Premium tactile feedback
                if (navigator.vibrate) {
                    navigator.vibrate(15);
                }
                
                if (e.cancelable) e.preventDefault();
            };

            const stopPlayback = () => {
                if (!isPlaying) return;
                isPlaying = false;
                
                video.classList.remove('playing');
                video.pause();
                video.currentTime = 0;
            };

            // Touch events for mobile
            img.addEventListener('touchstart', startPlayback, { passive: false });
            img.addEventListener('touchend', stopPlayback);
            img.addEventListener('touchcancel', stopPlayback);

            // Mouse events for desktop (click and hold)
            img.addEventListener('mousedown', startPlayback);
            img.addEventListener('mouseup', stopPlayback);
            img.addEventListener('mouseleave', stopPlayback);
        }
    } else {
        const video = document.createElement('video');
        video.id = 'viewerVideo';
        video.controls = true;
        video.src = `/api/full/${media.id}${pinParam}`;
        content.appendChild(video);
    }

    // Update favorite button
    const favBtn = document.getElementById('favButton');
    if (state.favorites.includes(media.id)) {
        favBtn.classList.add('favorited');
    } else {
        favBtn.classList.remove('favorited');
    }

    // Swipe navigation
    let touchStartX = 0;
    content.addEventListener('touchstart', (e) => {
        touchStartX = e.touches[0].clientX;
    });

    content.addEventListener('touchend', (e) => {
        const diff = e.changedTouches[0].clientX - touchStartX;
        if (diff > 50) previousMedia();
        if (diff < -50) nextMedia();
    });
}

function nextMedia() {
    if (!state.viewedMedia.length) return;
    state.currentViewerIndex = (state.currentViewerIndex + 1) % state.viewedMedia.length;
    updateViewer();
}

function previousMedia() {
    if (!state.viewedMedia.length) return;
    state.currentViewerIndex = (state.currentViewerIndex - 1 + state.viewedMedia.length) % state.viewedMedia.length;
    updateViewer();
}

function toggleFavorite() {
    const media = state.viewedMedia[state.currentViewerIndex];
    const idx = state.favorites.indexOf(media.id);
    if (idx >= 0) {
        state.favorites.splice(idx, 1);
    } else {
        state.favorites.push(media.id);
    }
    localStorage.setItem('favorites', JSON.stringify(state.favorites));
    updateViewer();
}

function toggleSlideshow() {
    // TODO: Implement slideshow
    showToast('Slideshow coming soon');
}

async function saveToPhotos() {
    const media = state.viewedMedia[state.currentViewerIndex];
    try {
        showToast('Preparing download...');
        
        // Fetch the still image using authedFetch
        const resImg = await authedFetch(`/api/download/${media.id}`);
        if (!resImg.ok) throw new Error('Failed to download still image');
        const blobImg = await resImg.blob();
        
        let filesToShare = [];
        const imgFile = new File([blobImg], media.filename, { type: blobImg.type });
        filesToShare.push(imgFile);

        let isLivePhoto = false;
        // If it's a Live Photo, fetch the corresponding video file
        if (media.live_video_id) {
            try {
                // Find the video media object in state.media to get its filename
                const videoMedia = state.media.find(m => m.id === media.live_video_id);
                if (videoMedia) {
                    const resVid = await authedFetch(`/api/download/${media.live_video_id}`);
                    if (resVid.ok) {
                        const blobVid = await resVid.blob();
                        const vidFile = new File([blobVid], videoMedia.filename, { type: blobVid.type });
                        filesToShare.push(vidFile);
                        isLivePhoto = true;
                    }
                }
            } catch (vidErr) {
                console.warn('Failed to fetch Live Photo video clip:', vidErr);
            }
        }

        let shared = false;
        // The Web Share API is only supported in secure contexts (HTTPS) and localhost.
        try {
            if (navigator.canShare && navigator.share) {
                if (navigator.canShare({ files: filesToShare })) {
                    await navigator.share({ files: filesToShare });
                    shared = true;
                }
            }
        } catch (shareErr) {
            console.warn('Web Share failed or blocked by context security:', shareErr);
        }

        if (!shared) {
            // Fallback: download files individually
            triggerDownload(blobImg, media.filename);

            if (isLivePhoto && filesToShare[1]) {
                // Delay the second download so the browser doesn't block it
                setTimeout(() => {
                    triggerDownload(filesToShare[1], filesToShare[1].name);
                }, 500);
                showToast('Downloaded still and video clip. Long-press to save.');
            } else {
                showToast('File downloaded. Long-press to save if it didn\'t download.');
            }
        } else {
            showToast(isLivePhoto ? 'Live Photo shared successfully!' : 'File shared successfully!');
        }
    } catch (err) {
        console.error('Save to photos failed:', err);
        showToast('Download failed: ' + err.message);
    }
}

function triggerDownload(blobOrFile, filename) {
    const url = URL.createObjectURL(blobOrFile);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 2000);
}

// ============================================================================
// SETTINGS
// ============================================================================

function openSettings() {
    // Check if modal already exists, remove it
    const existing = document.getElementById('settingsModal');
    if (existing) existing.remove();

    fetchConfig().then(config => {
        const modal = document.createElement('div');
        modal.id = 'settingsModal';
        modal.className = 'modal-backdrop';
        modal.innerHTML = `
            <div class="modal-card">
                <div class="modal-header">
                    <h2>Settings</h2>
                    <button class="close-modal-btn" id="modalCloseBtn">✕</button>
                </div>
                <div class="modal-body">
                    <p style="margin-bottom: 8px;">Photos Folder Path:</p>
                    <div class="input-group" style="margin-bottom: 16px;">
                        <input type="text" id="modalPathInput" value="${config.photos_dir || ''}" placeholder="C:\\Users\\yourname\\Pictures">
                        <button id="modalBrowseBtn" class="secondary-button">Browse...</button>
                    </div>
                    
                    <p style="margin-bottom: 8px;">Access PIN (Optional - secures connections from other devices):</p>
                    <div class="input-group" style="margin-bottom: 16px;">
                        <input type="password" id="modalPinInput" value="${config.access_pin || ''}" placeholder="Set PIN (leave empty to disable)">
                    </div>
                    
                    <div class="error" id="modalErrorMsg"></div>
                </div>
                <div class="modal-footer">
                    <button id="modalCancelBtn" class="modal-btn-cancel">Cancel</button>
                    <button id="modalSaveBtn" class="modal-btn-save">Save Changes</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        // Force reflow for fade-in transition
        modal.offsetHeight;
        modal.classList.add('active');

        const closeModal = () => {
            modal.classList.remove('active');
            setTimeout(() => modal.remove(), 300);
        };

        modal.querySelector('#modalCloseBtn').addEventListener('click', closeModal);
        modal.querySelector('#modalCancelBtn').addEventListener('click', closeModal);

        modal.querySelector('#modalBrowseBtn').addEventListener('click', async () => {
            const errEl = modal.querySelector('#modalErrorMsg');
            errEl.textContent = '';
            try {
                showToast('Check your laptop screen for the folder browser...');
                const res = await fetch('/api/select-folder', { method: 'POST' }).then(r => r.json());
                if (res.path) {
                    modal.querySelector('#modalPathInput').value = res.path;
                }
            } catch (err) {
                errEl.textContent = 'Failed to open file explorer: ' + err.message;
            }
        });

        modal.querySelector('#modalSaveBtn').addEventListener('click', async () => {
            const newPath = modal.querySelector('#modalPathInput').value.trim();
            const newPin = modal.querySelector('#modalPinInput').value.trim();
            if (!newPath) return;

            const errEl = modal.querySelector('#modalErrorMsg');
            errEl.textContent = '';

            try {
                await setPhotosDir(newPath, newPin);
                if (newPin) {
                    localStorage.setItem('pb_pin', newPin);
                } else {
                    localStorage.removeItem('pb_pin');
                }
                await loadMedia();
                render();
                showToast('Settings updated successfully');
                closeModal();
            } catch (err) {
                errEl.textContent = err.message;
            }
        });
    });
}

// ============================================================================
// UTILITIES
// ============================================================================

function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

