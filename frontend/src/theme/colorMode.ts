const THEME_STORAGE_KEY = 'sandesh-color-mode';

export type ColorMode = 'light' | 'dark';

export function readStoredColorMode(): ColorMode {
  try {
    const v = localStorage.getItem(THEME_STORAGE_KEY);
    if (v === 'dark' || v === 'light') return v;
  } catch { /* ignore */ }
  return 'light';
}

export function persistColorMode(mode: ColorMode) {
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode);
  } catch { /* ignore */ }

  // Toggle body class for CSS-level dark mode
  if (mode === 'dark') {
    document.body.classList.add('dark-mode');
  } else {
    document.body.classList.remove('dark-mode');
  }

  window.dispatchEvent(new CustomEvent('sandesh-theme-change', { detail: mode }));
}

/** Apply stored theme on page load (call from index.tsx) */
export function applyStoredColorMode() {
  const mode = readStoredColorMode();
  if (mode === 'dark') document.body.classList.add('dark-mode');
}
