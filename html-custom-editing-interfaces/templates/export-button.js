async function copyExportText(text, statusEl) {
  try {
    await navigator.clipboard.writeText(text);
    statusEl.textContent = 'Copied export text.';
  } catch (error) {
    statusEl.textContent = 'Clipboard failed; select and copy the export text manually.';
  }
}
