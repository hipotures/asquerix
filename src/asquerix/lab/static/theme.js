/* Light/dark theme: follows the system until the header toggle stores a choice. Loaded before paint. */
(() => {
  const root = document.documentElement, key = 'asquerix-theme';
  const stored = () => { try { return localStorage.getItem(key); } catch { return null; } };
  const choice = stored();
  if (choice === 'light' || choice === 'dark') root.dataset.theme = choice;
  const effective = () => root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const label = button => {
    const dark = effective() === 'dark';
    button.setAttribute('aria-pressed', String(dark));
    button.title = dark ? 'Switch to light theme' : 'Switch to dark theme';
  };
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    label(button);
    button.addEventListener('click', () => {
      root.dataset.theme = effective() === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem(key, root.dataset.theme); } catch {}
      label(button);
    });
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => label(button));
  });
})();
