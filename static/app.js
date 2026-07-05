/**
 * PhotoBridge Frontend - Single Page App
 * No framework, vanilla JS, targeting Mobile Safari
 */

// ============================================================================
// STATE MANAGEMENT
// ============================================================================

let state = {
    configured: false,
    media: [],
    albums: [],
    currentTab: 'all-photos',
    searchQuery: '',
    selectedAlbum: 'All Photos',
    currentViewerIndex: 0,
    favorites: JSON.parse(localStorage.getItem('favorites') || '[]'),
    viewerActive: false
};

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
    const config = await fetchConfig();
    state.configured = config.configured;

    if (state.configured) {
        await loadMedia();
    }
}

// ============================================================================
// API CALLS
// ============================================================================

async function fetchConfig() {
    const res = await fetch('/api/config');
    return res.json();
}

async function setPhotosDir(path) {
    const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ photos_dir: path })
    });

    if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to set photos directory');
    }

    return res.json();
}

async function loadMedia() {
    const media = await fetch('/api/media').then(r => r.json());
    state.media = media;

    // Extract unique albums
    const albumSet = new Set(media.map(m => m.album));
    state.albums = Array.from(albumSet).sort();
}

async function rescanMedia() {
    const res = await fetch('/api/rescan', { method: 'POST' });
    if (res.ok) {
        await loadMedia();
        showToast('Photos rescanned');
    }
}

// ============================================================================
// RENDERING
// ============================================================================

function render() {
    const app = document.getElementById('app');
    app.innerHTML = '';

    if (!state.configured) {
        app.appendChild(renderSetupScreen());
    } else {
        app.appendChild(renderMainApp());
    }
}

function renderSetupScreen() {
    const div = document.createElement('div');
    div.id = 'setupScreen';
    div.innerHTML = `
        <h1>PhotoBridge</h1>
        <p>Enter the full path to the folder on your laptop you want to browse.<br>Example: <code>C:\\Users\\yourname\\Pictures</code></p>
        <input type="text" id="pathInput" placeholder="C:\\Users\\yourname\\Pictures">
        <button id="connectBtn">Connect</button>
        <div class="error" id="errorMsg"></div>
    `;

    div.querySelector('#connectBtn').addEventListener('click', async () => {
        const path = div.querySelector('#pathInput').value.trim();
        if (!path) return;

        try {
            await setPhotosDir(path);
            state.configured = true;
            await loadMedia();
            render();
        } catch (err) {
            div.querySelector('#errorMsg').textContent = err.message;
        }
    });

    return div;
}

function renderMainApp() {
    const div = document.createElement('div');
    div.innerHTML = `
        <div id="topBar"></div>
        <div id="albumBar" style="display: none;"></div>
        <div id="gridContainer"></div>
        <div id="fullscreenViewer"></div>
    `;

    const topBar = div.querySelector('#topBar');
    topBar.innerHTML = `
        <button class="tab-button active" data-tab="all-photos">All Photos</button>
        <button class="tab-button" data-tab="albums">Albums</button>
        <button class="tab-button" data-tab="favorites">Favorites</button>
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

    // Album bar
    const albumBar = div.querySelector('#albumBar');
    if (state.currentTab === 'albums') {
        albumBar.style.display = 'flex';
        albumBar.innerHTML = '';
        state.albums.forEach(album => {
            const chip = document.createElement('button');
            chip.className = 'album-chip' + (state.selectedAlbum === album ? ' active' : '');
            chip.textContent = album;
            chip.addEventListener('click', () => {
                state.selectedAlbum = album;
                render();
            });
            albumBar.appendChild(chip);
        });
    }

    // Grid
    renderGrid(div);

    // Viewer
    const viewer = div.querySelector('#fullscreenViewer');
    viewer.innerHTML = `
        <div id="viewerContent"></div>
        <div id="viewerControls">
            <button class="control-button" id="closeBtn">✕</button>
            <button class="control-button" id="slideshowBtn">▶</button>
            <button class="control-button" id="favButton">♡</button>
            <button class="control-button" id="saveBtn">⬇</button>
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

function renderGrid(app) {
    const container = app.querySelector('#gridContainer');
    container.innerHTML = '';

    let filteredMedia = state.media;

    // Filter by tab
    if (state.currentTab === 'favorites') {
        filteredMedia = filteredMedia.filter(m => state.favorites.includes(m.id));
    } else if (state.currentTab === 'albums') {
        filteredMedia = filteredMedia.filter(m => m.album === state.selectedAlbum);
    }

    // Filter by search
    if (state.searchQuery) {
        const q = state.searchQuery.toLowerCase();
        filteredMedia = filteredMedia.filter(m => m.filename.toLowerCase().includes(q));
    }

    // Group by date
    const grouped = {};
    filteredMedia.forEach(media => {
        const date = new Date(media.date_taken);
        const dateKey = date.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
        if (!grouped[dateKey]) grouped[dateKey] = [];
        grouped[dateKey].push(media);
    });

    // Render
    Object.entries(grouped).forEach(([dateKey, medias]) => {
        const header = document.createElement('div');
        header.className = 'date-header';
        header.textContent = dateKey;
        container.appendChild(header);

        const grid = document.createElement('div');
        grid.className = 'grid';

        medias.forEach((media, idx) => {
            const tile = document.createElement('div');
            tile.className = 'media-tile';

            if (media.type === 'image') {
                const img = document.createElement('img');
                img.src = `/api/thumb/${media.id}?w=300`;
                img.loading = 'lazy';
                img.alt = media.filename;
                tile.appendChild(img);
            } else {
                const placeholder = document.createElement('div');
                placeholder.className = 'video-placeholder';
                placeholder.innerHTML = `
                    <div class="play-icon">▶</div>
                    <div>${media.filename}</div>
                `;
                tile.appendChild(placeholder);
            }

            tile.addEventListener('click', () => {
                state.currentViewerIndex = filteredMedia.indexOf(media);
                openViewer();
            });

            grid.appendChild(tile);
        });

        container.appendChild(grid);
    });

    // Pull to refresh
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
    const media = state.media[state.currentViewerIndex];
    const content = document.getElementById('viewerContent');
    content.innerHTML = '';

    if (media.type === 'image') {
        const img = document.createElement('img');
        img.id = 'viewerImage';
        img.src = `/api/full/${media.id}`;
        img.alt = media.filename;
        content.appendChild(img);
    } else {
        const video = document.createElement('video');
        video.id = 'viewerVideo';
        video.controls = true;
        video.src = `/api/full/${media.id}`;
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
    state.currentViewerIndex = (state.currentViewerIndex + 1) % state.media.length;
    updateViewer();
}

function previousMedia() {
    state.currentViewerIndex = (state.currentViewerIndex - 1 + state.media.length) % state.media.length;
    updateViewer();
}

function toggleFavorite() {
    const media = state.media[state.currentViewerIndex];
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
    const media = state.media[state.currentViewerIndex];
    const res = await fetch(`/api/download/${media.id}`);
    const blob = await res.blob();
    const file = new File([blob], media.filename, { type: blob.type });

    if (navigator.canShare && navigator.canShare({ files: [file] })) {
        navigator.share({ files: [file] });
    } else {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = media.filename;
        a.click();
        URL.revokeObjectURL(url);
        showToast('File downloaded. Long-press and choose "Add to Photos".');
    }
}

// ============================================================================
// SETTINGS
// ============================================================================

async function openSettings() {
    const config = await fetchConfig();
    const newPath = prompt('Enter new photos folder path:', config.photos_dir || '');
    if (newPath && newPath !== config.photos_dir) {
        try {
            await setPhotosDir(newPath);
            await loadMedia();
            render();
            showToast('Folder updated');
        } catch (err) {
            showToast(err.message);
        }
    }
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

