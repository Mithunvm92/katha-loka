(() => {
  const shareButton = document.querySelector('#share-home');
  const qrButton = document.querySelector('#toggle-home-qr');
  const qrPanel = document.querySelector('#home-qr-panel');
  const qrImage = document.querySelector('#home-qr-image');
  const qrLink = document.querySelector('#home-qr-link');

  if (!shareButton || !qrButton || !qrPanel || !qrImage || !qrLink) return;

  const pageUrl = location.origin + '/';
  qrLink.href = pageUrl;

  shareButton.addEventListener('click', async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: 'Katha Loka · ಕಥಾಲೋಕ',
          text: 'Discover illustrated stories in English and Kannada.',
          url: pageUrl
        });
      } else if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(pageUrl);
        shareButton.textContent = '✓ Link copied';
        setTimeout(() => {
          shareButton.textContent = '↗ Share Katha Loka';
        }, 2000);
      } else {
        window.prompt('Copy this link to share Katha Loka:', pageUrl);
      }
    } catch (error) {
      if (error?.name !== 'AbortError') {
        window.prompt('Copy this link to share Katha Loka:', pageUrl);
      }
    }
  });

  qrButton.addEventListener('click', () => {
    const opening = qrPanel.hidden;
    qrPanel.hidden = !opening;
    qrButton.setAttribute('aria-expanded', String(opening));
    qrButton.textContent = opening ? '✕ Hide QR Code' : '▦ Show QR Code';

    if (opening && !qrImage.dataset.loaded) {
      qrImage.src =
        'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' +
        encodeURIComponent(pageUrl);
      qrImage.dataset.loaded = 'true';
      qrImage.onerror = () => {
        qrImage.alt = 'QR code could not be loaded. Check your internet connection.';
        qrImage.dataset.loaded = '';
      };
    }
  });
})();
