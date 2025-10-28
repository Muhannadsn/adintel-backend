document.getElementById('scrape-btn').addEventListener('click', async () => {
  const maxAds = parseInt(document.getElementById('maxAds').value);
  const button = document.getElementById('scrape-btn');
  const status = document.getElementById('status');

  // Disable button
  button.disabled = true;
  button.textContent = 'Scraping...';

  // Show status
  status.style.display = 'block';
  status.className = 'info';
  status.textContent = `Starting scrape for ${maxAds} ads...`;

  try {
    // Get active tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    // Check if we're on GATC
    if (!tab.url.includes('adstransparency.google.com')) {
      throw new Error('Please navigate to Google Ad Transparency Center first');
    }

    // Inject and execute scraper
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: scrapeAds,
      args: [maxAds]
    });

    const ads = results[0].result;

    if (ads && ads.length > 0) {
      // Convert to CSV
      const csv = convertToCSV(ads);

      // Download CSV
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);

      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').split('T')[0];
      const filename = `gatc-scraped-data-${timestamp}.csv`;

      // Trigger download
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();

      status.className = 'success';
      status.textContent = `✓ Successfully scraped ${ads.length} ads! Download started.`;
    } else {
      throw new Error('No ads found on page');
    }

  } catch (error) {
    status.className = 'error';
    status.textContent = `✗ Error: ${error.message}`;
  } finally {
    button.disabled = false;
    button.textContent = 'Scrape Current Page';
  }
});

// This function runs in the page context
function scrapeAds(maxAds) {
  const ads = [];
  let scrollAttempts = 0;
  const maxScrollAttempts = 100;

  return new Promise((resolve) => {
    const scrollInterval = setInterval(() => {
      // Scroll to bottom
      window.scrollTo(0, document.body.scrollHeight);

      // Find all ad cards
      const adCards = document.querySelectorAll('[data-creative-id]');

      console.log(`Found ${adCards.length} ads (target: ${maxAds})`);

      // Check if we have enough ads or reached max attempts
      if (adCards.length >= maxAds || scrollAttempts >= maxScrollAttempts) {
        clearInterval(scrollInterval);

        // Extract data from each ad
        adCards.forEach((card, index) => {
          if (index >= maxAds) return;

          try {
            const creativeId = card.getAttribute('data-creative-id') || '';

            // Get advertiser ID from URL
            const urlMatch = window.location.href.match(/advertiser\/(AR[0-9]+)/);
            const advertiserId = urlMatch ? urlMatch[1] : '';

            // Get region from URL
            const regionMatch = window.location.href.match(/region=([A-Z]+)/);
            const region = regionMatch ? regionMatch[1] : '';

            // Try to get image URL
            let imageUrl = '';
            const img = card.querySelector('img');
            if (img) {
              imageUrl = img.src || '';
            }

            // Try to get text content
            const textContent = card.innerText || '';

            // Try to get dates
            let firstShown = '';
            let lastShown = '';
            const dateElements = card.querySelectorAll('[aria-label*="date"], [aria-label*="Date"]');
            if (dateElements.length > 0) {
              lastShown = dateElements[0].innerText || '';
            }

            // Get HTML content (limited)
            const htmlContent = card.innerHTML.substring(0, 500);

            ads.push({
              advertiser_id: advertiserId,
              creative_id: creativeId,
              advertiser_name: 'Unknown',
              image_url: imageUrl,
              creative_url: imageUrl,
              first_shown: firstShown,
              last_shown: lastShown,
              regions: region,
              html_content: htmlContent,
              text_content: textContent.substring(0, 200)
            });

          } catch (error) {
            console.error('Error extracting ad:', error);
          }
        });

        resolve(ads);
      }

      scrollAttempts++;
    }, 500); // Scroll every 500ms
  });
}

function convertToCSV(ads) {
  if (ads.length === 0) return '';

  // Get headers
  const headers = Object.keys(ads[0]);

  // Create CSV content
  let csv = headers.join(',') + '\n';

  // Add data rows
  ads.forEach(ad => {
    const row = headers.map(header => {
      const value = ad[header] || '';
      // Escape quotes and wrap in quotes if contains comma
      const escaped = value.toString().replace(/"/g, '""');
      return escaped.includes(',') ? `"${escaped}"` : escaped;
    });
    csv += row.join(',') + '\n';
  });

  return csv;
}
