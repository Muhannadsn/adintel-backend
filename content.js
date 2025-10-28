// CSS Selectors for GATC data extraction
// These selectors need to be updated based on the actual GATC page structure

// Prevent duplicate injection
if (!window.GATCScraperLoaded) {
    window.GATCScraperLoaded = true;
    console.log('=== GATC SCRAPER CONTENT SCRIPT LOADED - VERSION 3.2 ===');

// ================================
// ANTI-DETECTION & EVASION SYSTEM
// ================================

// Realistic User-Agent pool (recent Chrome versions across different platforms)
const USER_AGENTS = [
    // Chrome on macOS
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    
    // Chrome on Windows
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
    
    // Chrome on Linux
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
];

// Accept-Language variations (common combinations)
const ACCEPT_LANGUAGES = [
    'en-US,en;q=0.9',
    'en-US,en;q=0.9,zh;q=0.8',
    'en-US,en;q=0.9,zh;q=0.8,zh-CN;q=0.7',
    'en-US,en;q=0.9,es;q=0.8',
    'en-US,en;q=0.9,fr;q=0.8',
    'en-GB,en;q=0.9,en-US;q=0.8',
    'en-US,en;q=0.9,de;q=0.8'
];

// Session fingerprint - maintains consistency within a scraping session
let sessionFingerprint = null;

function getSessionFingerprint() {
    if (!sessionFingerprint) {
        sessionFingerprint = {
            userAgent: USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)],
            acceptLanguage: ACCEPT_LANGUAGES[Math.floor(Math.random() * ACCEPT_LANGUAGES.length)],
            // Extract platform info from chosen User-Agent for consistency
            platform: null,
            chromeVersion: null
        };
        
        // Extract platform and version for consistent Sec-CH-UA headers
        if (sessionFingerprint.userAgent.includes('Macintosh')) {
            sessionFingerprint.platform = '"macOS"';
        } else if (sessionFingerprint.userAgent.includes('Windows')) {
            sessionFingerprint.platform = '"Windows"';
        } else if (sessionFingerprint.userAgent.includes('Linux')) {
            sessionFingerprint.platform = '"Linux"';
        }
        
        // Extract Chrome version
        const versionMatch = sessionFingerprint.userAgent.match(/Chrome\/(\d+)/);
        if (versionMatch) {
            sessionFingerprint.chromeVersion = versionMatch[1];
        }
        
        console.log('🎭 Generated session fingerprint:', {
            userAgent: sessionFingerprint.userAgent.substring(0, 50) + '...',
            acceptLanguage: sessionFingerprint.acceptLanguage,
            platform: sessionFingerprint.platform,
            chromeVersion: sessionFingerprint.chromeVersion
        });
    }
    return sessionFingerprint;
}

// Advanced throttling detection and session management
let throttleDetectionCount = 0;
let lastThrottleTime = 0;
const THROTTLE_RESET_THRESHOLD = 3; // Reset session after 3 throttling incidents
const THROTTLE_RESET_WINDOW = 300000; // 5 minutes

function detectThrottling(response) {
    const isThrottled = response.url.includes('www.google.com/sorry') || 
                       response.url.includes('/sorry/index') ||
                       response.status === 429;
    
    if (isThrottled) {
        const now = Date.now();
        
        // Reset counter if enough time has passed
        if (now - lastThrottleTime > THROTTLE_RESET_WINDOW) {
            throttleDetectionCount = 0;
        }
        
        throttleDetectionCount++;
        lastThrottleTime = now;
        
        console.log(`🚫 Throttling detected! Count: ${throttleDetectionCount}/${THROTTLE_RESET_THRESHOLD} in last 5min`);
        
        // Intelligent session reset if we're getting throttled repeatedly
        if (throttleDetectionCount >= THROTTLE_RESET_THRESHOLD) {
            console.log('🔄 Triggering intelligent session reset due to repeated throttling...');
            resetSessionFingerprint();
            throttleDetectionCount = 0; // Reset counter after fingerprint reset
        }
    }
    
    return isThrottled;
}

function resetSessionFingerprint() {
    console.log('🎭 Resetting session fingerprint for fresh identity...');
    sessionFingerprint = null; // Force regeneration on next call
    
    // Add a longer pause to let the session "cool down"
    return new Promise(resolve => {
        const cooldownTime = 3000 + Math.random() * 2000; // 3-5 second cooldown
        console.log(`❄️  Session cooldown: ${Math.round(cooldownTime)}ms`);
        setTimeout(resolve, cooldownTime);
    });
}

// ================================
// GATC SCRAPER CORE FUNCTIONALITY
// ================================

// Professional Loading Overlay System
let scrapingOverlay = null;
let progressData = { current: 0, total: 0, step: 'Initializing...' };

/**
 * Creates and shows a minimal dark overlay with clear user instructions
 * Clean, professional design with actionable guidance
 */
function showScrapingOverlay() {
    if (scrapingOverlay) return; // Already showing
    
    // Create minimal overlay container
    scrapingOverlay = document.createElement('div');
    scrapingOverlay.id = 'gatc-scraper-overlay';
    scrapingOverlay.innerHTML = `
        <div class="gatc-overlay-backdrop">
            <div class="gatc-status-indicator">
                <div class="gatc-pulse-dot"></div>
                <div class="gatc-status-content">
                    <div class="gatc-status-title">GATC Scraper Running</div>
                    <div class="gatc-user-instructions">
                        <div class="instruction-item">⚠️ Don't switch tabs or close this window</div>
                        <div class="instruction-item">📊 Check extension popup for progress</div>
                        <div class="instruction-item">⏱️ This may take a few minutes</div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add refined CSS styles with brand-consistent colors
    const style = document.createElement('style');
    style.textContent = `
        #gatc-scraper-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            z-index: 2147483647;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            animation: gatc-fade-in 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .gatc-overlay-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
        }
        
        .gatc-status-indicator {
            position: absolute;
            top: 24px;
            left: 24px;
            background: linear-gradient(135deg, rgba(66, 133, 244, 0.95) 0%, rgba(52, 168, 83, 0.95) 25%, rgba(251, 188, 4, 0.95) 50%, rgba(234, 67, 53, 0.95) 100%);
            color: white;
            padding: 20px 24px;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(12px);
            display: flex;
            align-items: flex-start;
            gap: 16px;
            max-width: 380px;
            transition: all 0.3s ease;
        }
        
        .gatc-status-indicator:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255, 255, 255, 0.15);
        }
        
        .gatc-pulse-dot {
            width: 12px;
            height: 12px;
            background: #fff;
            border-radius: 50%;
            animation: gatc-pulse 2s ease-in-out infinite;
            flex-shrink: 0;
            margin-top: 4px;
        }
        
        .gatc-status-content {
            flex: 1;
        }
        
        .gatc-status-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 12px;
            color: white;
        }
        
        .gatc-user-instructions {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        
        .instruction-item {
            font-size: 14px;
            font-weight: 500;
            color: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            gap: 8px;
            line-height: 1.4;
        }
        
        @keyframes gatc-fade-in {
            from { 
                opacity: 0; 
                backdrop-filter: blur(0px);
            }
            to { 
                opacity: 1; 
                backdrop-filter: blur(4px);
            }
        }
        
        @keyframes gatc-pulse {
            0%, 100% { 
                opacity: 1; 
                transform: scale(1);
            }
            50% { 
                opacity: 0.7; 
                transform: scale(1.1);
            }
        }
    `;
    
    // Append to document
    document.head.appendChild(style);
    document.body.appendChild(scrapingOverlay);
    
    console.log('✨ Enhanced scraping overlay activated with user guidance');
}

/**
 * Updates progress - now just sends message to popup instead of updating overlay
 */
function updateScrapingProgress(step, current = 0, total = 0, statusText = 'Processing...', adsFound = 0, apiCalls = 0) {
    // Send progress update to popup instead of updating overlay
    try {
        chrome.runtime.sendMessage({
            type: 'SCRAPING_PROGRESS_UPDATE',
            progress: {
                step,
                current,
                total,
                statusText,
                adsFound,
                apiCalls,
                percentage: total > 0 ? Math.round((current / total) * 100) : 0
            }
        }).catch(() => {
            // Ignore errors if popup is closed
        });
    } catch (error) {
        // Ignore messaging errors
    }
    
    console.log(`📊 Progress: ${step} - ${current}/${total} (${total > 0 ? Math.round((current / total) * 100) : 0}%)`);
}

/**
 * Hides and removes the simple overlay
 */
function hideScrapingOverlay() {
    if (!scrapingOverlay) return;
    
    // Remove event listeners
    document.removeEventListener('keydown', preventTabSwitching, true);
    document.removeEventListener('contextmenu', preventInteractions, true);
    window.removeEventListener('beforeunload', preventNavigation, true);
    
    // Animate out and remove
    scrapingOverlay.style.animation = 'gatc-fade-in 0.3s ease-out reverse';
    
    setTimeout(() => {
        if (scrapingOverlay && scrapingOverlay.parentNode) {
            scrapingOverlay.parentNode.removeChild(scrapingOverlay);
        }
        scrapingOverlay = null;
        document.body.classList.remove('gatc-scraping-active');
    }, 300);
    
    console.log('🎨 Simple dark overlay deactivated');
}

/**
 * Prevents tab switching during scraping
 */
function preventTabSwitching(event) {
    // Prevent Ctrl+Tab, Ctrl+Shift+Tab, Ctrl+W, Ctrl+T, etc.
    if (event.ctrlKey || event.metaKey) {
        if (['Tab', 'w', 'W', 't', 'T', 'n', 'N', 'r', 'R'].includes(event.key)) {
            event.preventDefault();
            event.stopPropagation();
            return false;
        }
    }
    
    // Prevent Alt+Tab
    if (event.altKey && event.key === 'Tab') {
        event.preventDefault();
        event.stopPropagation();
        return false;
    }
}

/**
 * Prevents right-click and other interactions
 */
function preventInteractions(event) {
    event.preventDefault();
    return false;
}

/**
 * Prevents navigation away from page
 */
function preventNavigation(event) {
    event.preventDefault();
    event.returnValue = 'GATC Scraper is currently running. Are you sure you want to leave?';
    return 'GATC Scraper is currently running. Are you sure you want to leave?';
}

const SEARCH_PAGE_SELECTORS = {
    // The main container for a single ad card.
    AD_CONTAINER: 'creative-preview',
    
    // The element containing the advertiser's name, found within an ad card.
    ADVERTISER: '.advertiser-name',
    
    // The image element for the ad creative, found within an ad card.
    AD_CREATIVE_IMAGE: 'img',
  
    // The video element for the ad creative, found within an ad card.
    AD_CREATIVE_VIDEO: 'video',
    
    // The iframe element for the ad creative (for iframe-based ads)
    AD_CREATIVE_IFRAME: 'iframe[src*="/adframe"]',
    
    // The region element found within an ad card (if available).
    AD_REGION: '.region, .country, [data-testid="region"]',
    
    // --- Global Filter Selectors (top of page) ---
    
    // The element containing the overall ad format filter text.
    AD_FORMAT: 'creative-type-filter .button-label-text',
    
    // The element containing the overall region filter text.
    REGION: 'target-region-filter .button-text',
    
    // The element containing the overall date range filter text.
    DATES: 'date-range-filter .primary-text'
};

// Detail page selectors removed - detail page scraping deprecated

/**
 * Main scraping function - now only handles search pages
 * Detail page scraping has been deprecated
 * @returns {Array} Array of ad objects with extracted data
 */
async function scrapeCurrentPage() {
    // Check if we're on a Google Ads Transparency Center page
    if (!window.location.hostname.includes('adstransparency.google.com')) {
        throw new Error('Please navigate to the Google Ads Transparency Center (adstransparency.google.com) to use this extension.');
    }

    const path = window.location.pathname;
    
    // Check if this is a detail page
    if (path.includes('/creative/CR')) {
        throw new Error('Detail page scraping is not supported. Please use the download button or right-click to save the ad manually.');
    }
    
    console.log('🚀 Detected Search/Advertiser Page - using API-based scraping with SearchCreatives');
    return await scrapeSearchPageWithAPIFormats();
}

/**
 * Extract creative data from an ad element on search page
 * @param {Element} adElement - The ad container element
 * @returns {Object} Creative data object
 */
function extractSearchPageAdCreative(adElement) {
    const creative = {
        text: '',
        imageUrl: null,
        videoUrl: null,
        hasIframe: false
    };
    
    try {
        // Check for iframe first
        const iframeElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.AD_CREATIVE_IFRAME);
        if (iframeElement) {
            creative.hasIframe = true;
            console.log('Found iframe-based creative');
            return creative;
        }
        
        // Extract image URL
        const imageElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.AD_CREATIVE_IMAGE);
        if (imageElement && imageElement.src) {
            let imageUrl = imageElement.src;
            
            // Check if this is a YouTube thumbnail (convert to video URL)
            const youtubeMatch = imageUrl.match(/\/vi\/([^\/]+)\//);
            if (youtubeMatch) {
                const videoId = youtubeMatch[1];
                creative.videoUrl = `https://www.youtube.com/watch?v=${videoId}`;
                console.log(`Converted YouTube thumbnail to video URL: ${creative.videoUrl}`);
            } else {
                creative.imageUrl = imageUrl;
            }
        }
        
        // Extract video URL
        const videoElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.AD_CREATIVE_VIDEO);
        if (videoElement && videoElement.src) {
            creative.videoUrl = videoElement.src;
        }
        
    } catch (error) {
        console.error('Error extracting creative data:', error);
    }
    
    return creative;
}

/**
 * Clean region text by removing "Shown in" prefix
 * @param {string} regionText - Raw region text
 * @returns {string} Cleaned region text
 */
function cleanRegionText(regionText) {
    if (!regionText) return 'Unknown';
    
    // Remove "Shown in the" or "Shown in" prefix
    const cleaned = regionText.replace(/^Shown in (the\s+)?/i, '').trim();
    
    return cleaned || regionText;
}

/**
 * Extract region parameter from current page URL
 * @returns {string} Region parameter for GATC URL
 */
function getRegionFromCurrentUrl() {
    try {
        const url = new URL(window.location.href);
        const regionParam = url.searchParams.get('region');
        
        if (regionParam) {
            return regionParam.toLowerCase();
        }
        
        // Default to 'anywhere' if no region parameter found
        return 'anywhere';
    } catch (error) {
        console.error('Error extracting region from URL:', error);
        return 'anywhere';
    }
}

/**
 * Get user-friendly search region name from URL parameter
 * @returns {string} User-friendly region name
 */
function getSearchRegionFromUrl() {
    try {
        const url = new URL(window.location.href);
        const regionParam = url.searchParams.get('region');
        
        if (!regionParam) {
            return 'Anywhere';
        }
        
        // Convert common region codes to user-friendly names
        const regionMap = {
            'anywhere': 'Anywhere',
            'us': 'United States',
            'gb': 'United Kingdom', 
            'ca': 'Canada',
            'au': 'Australia',
            'de': 'Germany',
            'fr': 'France',
            'jp': 'Japan',
            'in': 'India',
            'br': 'Brazil',
            'mx': 'Mexico',
            'it': 'Italy',
            'es': 'Spain',
            'nl': 'Netherlands',
            'se': 'Sweden',
            'no': 'Norway',
            'dk': 'Denmark',
            'fi': 'Finland',
            'ch': 'Switzerland',
            'at': 'Austria',
            'be': 'Belgium',
            'ie': 'Ireland',
            'nz': 'New Zealand',
            'za': 'South Africa',
            'kr': 'South Korea',
            'tw': 'Taiwan',
            'hk': 'Hong Kong',
            'sg': 'Singapore',
            'my': 'Malaysia',
            'th': 'Thailand',
            'ph': 'Philippines',
            'id': 'Indonesia',
            'vn': 'Vietnam',
            'ae': 'United Arab Emirates',
            'sa': 'Saudi Arabia',
            'eg': 'Egypt',
            'il': 'Israel',
            'tr': 'Turkey',
            'ru': 'Russia',
            'pl': 'Poland',
            'cz': 'Czech Republic',
            'hu': 'Hungary',
            'ro': 'Romania',
            'bg': 'Bulgaria',
            'hr': 'Croatia',
            'si': 'Slovenia',
            'sk': 'Slovakia',
            'lt': 'Lithuania',
            'lv': 'Latvia',
            'ee': 'Estonia',
            'ar': 'Argentina',
            'cl': 'Chile',
            'co': 'Colombia',
            'pe': 'Peru',
            'uy': 'Uruguay',
            'ec': 'Ecuador',
            've': 'Venezuela'
        };
        
        const lowerRegion = regionParam.toLowerCase();
        return regionMap[lowerRegion] || regionParam.toUpperCase();
        
    } catch (error) {
        console.error('Error extracting search region from URL:', error);
        return 'Anywhere';
    }
}

/**
 * Wait for DOM attributes to populate on loaded ads
 * @param {number} targetCount - Number of ads to check
 * @returns {Promise<void>}
 */
async function waitForAttributesToPopulate(targetCount) {
    const maxWaitTime = 10000; // Maximum 10 seconds
    const checkInterval = 500; // Check every 500ms
    let waitTime = 0;
    
    while (waitTime < maxWaitTime) {
        const adElements = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
        const adsToCheck = Math.min(adElements.length, targetCount);
        
        let adsWithIds = 0;
        for (let i = 0; i < adsToCheck; i++) {
            const advertiserId = adElements[i].getAttribute('advertiser-id');
            const creativeId = adElements[i].getAttribute('creative-id');
            
            if (advertiserId && creativeId && advertiserId !== 'null' && creativeId !== 'null') {
                adsWithIds++;
            }
        }
        
        const percentageWithIds = (adsWithIds / adsToCheck) * 100;
        console.log(`Attributes check: ${adsWithIds}/${adsToCheck} ads have IDs (${percentageWithIds.toFixed(1)}%)`);
        
        // If at least 80% of ads have IDs, we're good to go (format tabs might be more variable)
        if (percentageWithIds >= 80) {
            console.log('DOM attributes sufficiently populated, proceeding...');
            return;
        }
        
        await new Promise(resolve => setTimeout(resolve, checkInterval));
        waitTime += checkInterval;
    }
    
    console.log('Timeout waiting for attributes, proceeding anyway...');
}

/**
 * Scroll down and wait for more ads to load
 * @param {number} targetCount - Target number of ads to load
 * @param {number} maxAttempts - Maximum scroll attempts
 * @returns {Promise<boolean>} True if target reached, false if max attempts reached
 */
async function scrollToLoadMoreAds(targetCount, maxAttempts = 15) {
    let attempts = 0;
    let lastAdCount = 0;
    let stableCount = 0;
    
    // Initial check - if we already have enough ads, don't scroll at all
    const initialAds = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
    if (initialAds.length >= targetCount) {
        console.log(`Already have ${initialAds.length} ads (target: ${targetCount}), no scrolling needed`);
        return true;
    }
    
    console.log(`Starting scroll to load more ads. Current: ${initialAds.length}, Target: ${targetCount}`);
    
    while (attempts < maxAttempts) {
        // Count current ads
        const currentAds = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
        const currentCount = currentAds.length;
        
        console.log(`Scroll attempt ${attempts + 1}: Found ${currentCount} ads (target: ${targetCount})`);
        
        // Send progress update for scrolling (keep it generic, don't show total)
        chrome.runtime.sendMessage({
            type: 'PROGRESS_UPDATE',
            step: `Loading ads... (${currentCount} found)`,
            current: currentCount,
            total: 0, // Don't show total during scrolling to avoid confusion
            percentage: Math.min(70, 25 + (attempts / 15) * 45) // Progress based on scroll attempts instead
        }).catch(() => {});
        
        // Check if we've reached our target
        if (currentCount >= targetCount) {
            console.log(`Target reached: ${currentCount} ads loaded`);
            return true;
        }
        
        // Check if ads count hasn't changed (might be end of results)
        if (currentCount === lastAdCount) {
            stableCount++;
            if (stableCount >= 3) {
                console.log(`No more ads loading after ${stableCount} stable attempts. Final count: ${currentCount}`);
                return false;
            }
        } else {
            stableCount = 0; // Reset stable counter if new ads loaded
        }
        
        lastAdCount = currentCount;
        
        // Scroll to bottom of page smoothly
        window.scrollTo({
            top: document.body.scrollHeight,
            behavior: 'smooth'
        });
        
        // Wait for new content to load AND for DOM attributes to populate
        await new Promise(resolve => setTimeout(resolve, 2500));
        
        attempts++;
    }
    
    console.log(`Max scroll attempts (${maxAttempts}) reached. Final count: ${lastAdCount}`);
    return false;
}

/**
 * Parse date range text to extract first and last seen dates
 * @param {string} dateText - Date range text
 * @returns {Object} Object with firstSeen and lastSeen dates
 */
function parseDateRange(dateText) {
    const result = {
        firstSeen: 'Unknown',
        lastSeen: 'Unknown'
    };
    
    try {
        // Try to extract date range patterns
        const dateRangeMatch = dateText.match(/(\w+ \d+, \d+)\s*-\s*(\w+ \d+, \d+)/);
        if (dateRangeMatch) {
            result.firstSeen = dateRangeMatch[1];
            result.lastSeen = dateRangeMatch[2];
        } else {
            // Single date or other format
            result.lastSeen = dateText.trim();
        }
    } catch (error) {
        console.error('Error parsing date range:', error);
    }
    
    return result;
}

/**
 * Extract global filter data from a document
 * @param {Document} doc - The document to extract from
 * @returns {Object} Global filter data
 */
function extractGlobalFiltersFromDoc(doc) {
    const filters = {
        region: 'Unknown',
        adFormat: 'Unknown',
        firstSeen: 'Unknown',
        lastSeen: 'Unknown'
    };
    
    try {
        // Extract region filter
        const regionElement = doc.querySelector(SEARCH_PAGE_SELECTORS.REGION);
        if (regionElement) {
            const rawRegion = regionElement.textContent.trim();
            filters.region = cleanRegionText(rawRegion);
        }
        
        // Extract ad format filter
        const adFormatElement = doc.querySelector(SEARCH_PAGE_SELECTORS.AD_FORMAT);
        if (adFormatElement) {
            filters.adFormat = adFormatElement.textContent.trim();
        }
        
        // Extract date range filter
        const datesElement = doc.querySelector(SEARCH_PAGE_SELECTORS.DATES);
        if (datesElement) {
            const dateText = datesElement.textContent.trim();
            // Parse date range to extract first and last seen dates
            const dateRange = parseDateRange(dateText);
            filters.firstSeen = dateRange.firstSeen;
            filters.lastSeen = dateRange.lastSeen;
        }
        
    } catch (error) {
        console.error('Error extracting global filters from document:', error);
    }
    
    return filters;
}

// scrapeDetailPage function removed - detail page scraping deprecated

/**
 * Fallback scraping method when filters can't be found
 * @returns {Array} Array of ad objects with content-based format detection
 */
async function scrapeCurrentPageFallback(adsLimit = 50) {
    console.log(`Using fallback: scraping current page with content-based format detection (limit: ${adsLimit})`);
    
    const ads = [];
    const adElements = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
    console.log(`Found ${adElements.length} ad containers on current page`);
    
    // Limit the number of ads to process
    const adsToProcess = Math.min(adElements.length, adsLimit);
    
    for (let i = 0; i < adsToProcess; i++) {
        try {
            const adData = extractAdDataWithContentBasedFormat(adElements[i], i, document);
            if (adData) {
                ads.push(adData);
            }
        } catch (error) {
            console.error(`Error extracting ad ${i + 1}:`, error);
        }
    }
    
    console.log(`Successfully processed ${ads.length}/${adsToProcess} ads with content-based format detection`);
    return ads;
}

/**
 * Extract ad data with content-based format detection (fallback method)
 * @param {Element} adElement - The ad container element
 * @param {number} index - Index of the ad for logging
 * @param {Document} doc - The document context for global filters
 * @returns {Object|null} Extracted ad data or null if extraction failed
 */
function extractAdDataWithContentBasedFormat(adElement, index, doc) {
    try {
        // Extract advertiser name
        const advertiserElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.ADVERTISER);
        const advertiserName = advertiserElement ? advertiserElement.textContent.trim() : 'Unknown';
        
        // Extract region
        let region = 'Unknown';
        const adRegionElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.AD_REGION);
        
        if (adRegionElement) {
            const rawRegion = adRegionElement.textContent.trim();
            region = cleanRegionText(rawRegion);
        } else {
            const globalFilters = extractGlobalFiltersFromDoc(doc);
            region = globalFilters.region;
        }
        
        // Extract ad creative data
        const adCreative = extractSearchPageAdCreative(adElement);
        
        // Handle iframe-based ads - include them but with empty creative
        if (adCreative.hasIframe) {
            console.log(`Ad ${index + 1} - Iframe-based ad detected, including with empty creative`);
            // Clear the creative data for iframe ads
            adCreative.imageUrl = null;
            adCreative.videoUrl = null;
            adCreative.text = '';
        } else {
            // Check if we have any creative content for non-iframe ads
            const hasCreativeContent = adCreative.imageUrl || adCreative.videoUrl || (adCreative.text && adCreative.text.trim());
            if (!hasCreativeContent) {
                console.log(`Ad ${index + 1} - No creative content found, skipping`);
                return null;
            }
        }
        
        // Determine format based on content
        const format = determineFormatFromCreative(adCreative);
        
        // Extract advertiser-id and creative-id for GATC link
        const advertiserId = adElement.getAttribute('advertiser-id');
        const creativeId = adElement.getAttribute('creative-id');
        
        // Don't skip ads without IDs - include all ads for better matching
        
        // Construct GATC link with region from current page URL (if IDs available)
        const regionParam = getRegionFromCurrentUrl();
        const gatcLink = (advertiserId && creativeId) ? 
            `https://adstransparency.google.com/advertiser/${advertiserId}/creative/${creativeId}?region=${regionParam}` : 
            null;
        
        // Extract global filter data
        const globalFilters = extractGlobalFiltersFromDoc(doc);
        
        // Create ad data object
        const adData = {
            advertiserName: advertiserName,
            adCreative: adCreative,
            format: format,
            region: region,
            firstSeenDate: globalFilters.firstSeen,
            lastSeenDate: globalFilters.lastSeen,
            gatcLink: gatcLink
        };
        
        return adData;
        
    } catch (error) {
        console.error(`Error extracting data from ad ${index + 1}:`, error);
        return null;
    }
}

/**
 * Determine format from creative content (improved version)
 * @param {Object} adCreative - The creative data object
 * @returns {string} The determined format
 */
function determineFormatFromCreative(adCreative) {
    // Check for video content first (highest priority)
    if (adCreative.videoUrl && adCreative.videoUrl !== 'null' && adCreative.videoUrl.trim()) {
        return 'Video';
    }
    
    // Check for image content
    if (adCreative.imageUrl && adCreative.imageUrl !== 'null' && adCreative.imageUrl.trim()) {
        return 'Image';
    }
    
    // Check for text content
    if (adCreative.text && adCreative.text !== 'null' && adCreative.text.trim()) {
        return 'Text';
    }
    
    // Default fallback
    return 'Unknown';
}

/**
 * Get the original order of ads from the main search page
 * @param {number} adsLimit - Maximum number of ads to get order for
 * @returns {Array} Array of objects with position-based identifiers for all ads
 */
function getAdOrderFromSearchPage(adsLimit) {
    console.log(`Extracting ad order from search page (limit: ${adsLimit})`);
    
    const adElements = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
    console.log(`Found ${adElements.length} ad containers on search page`);
    
    const adOrder = [];
    const adsToProcess = Math.min(adElements.length, adsLimit);
    
    for (let i = 0; i < adsToProcess; i++) {
        const adElement = adElements[i];
        
        // Extract advertiser name for matching (more reliable than IDs)
        const advertiserElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.ADVERTISER);
        const advertiserName = advertiserElement ? advertiserElement.textContent.trim() : `Ad-${i}`;
        
        // Extract some creative content for additional matching
        const creativeElement = adElement.querySelector('img') || adElement.querySelector('[src]');
        const creativeHint = creativeElement ? creativeElement.getAttribute('src') || creativeElement.textContent?.slice(0, 50) : '';
        
        // Try to get IDs if available, but don't require them
        const advertiserId = adElement.getAttribute('advertiser-id') || null;
        const creativeId = adElement.getAttribute('creative-id') || null;
        
        adOrder.push({
            originalIndex: i,
            advertiserName: advertiserName,
            creativeHint: creativeHint,
            advertiserId: advertiserId,
            creativeId: creativeId
        });
    }
    
    console.log(`Extracted order for ${adOrder.length} ads (all ads included)`);
    
    // Log all advertiser-id and creative-id pairs from search page
    console.log('=== SEARCH PAGE AD IDs ===');
    adOrder.forEach((item, index) => {
        console.log(`Search Page Ad ${index + 1}: advertiserId="${item.advertiserId}", creativeId="${item.creativeId}", advertiserName="${item.advertiserName}"`);
    });
    console.log('=== END SEARCH PAGE AD IDs ===');
    
    return adOrder;
}

/**
 * Listen for messages from the popup/background script
 * Following the data transmission flow from DESIGN_DOC.md
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'CHECK_PAGE_TYPE') {
        // Check if we're on a Google Ads Transparency Center page
        if (!window.location.hostname.includes('adstransparency.google.com')) {
            sendResponse({ type: 'PAGE_TYPE_RESPONSE', pageType: 'UNKNOWN' });
            return;
        }

        const path = window.location.pathname;
        
        // Detect page type based on URL path
        if (path.includes('/creative/CR')) {
            sendResponse({ type: 'PAGE_TYPE_RESPONSE', pageType: 'DETAIL_PAGE_DEPRECATED' });
        } else {
            sendResponse({ type: 'PAGE_TYPE_RESPONSE', pageType: 'SEARCH_PAGE' });
        }
    }
    // SCRAPE_GATC_DATA handler removed - detail page scraping deprecated
    else if (request.type === 'SCRAPE_WITH_HTTP_FORMATS') {
        console.log('🚀 Starting API-based format detection scraping...');
        
        // Use GATC API-based format detection (most accurate method)
        scrapeSearchPageWithAPIFormats(request.adsLimit || 50)
            .then(result => {
                if (result.success) {
                    console.log('✅ API-based scraping completed successfully:', {
                        dataLength: result.data.length,
                        sampleData: result.data.slice(0, 2),
                        message: result.message
                    });
                    const response = { type: 'SCRAPE_SUCCESS', data: result.data, count: result.data.length };
                    sendResponse(response);
                } else {
                    console.error('❌ API-based scraping failed:', result.message);
                    const errorResponse = { type: 'SCRAPE_ERROR', error: result.message };
                    sendResponse(errorResponse);
                }
            })
            .catch(error => {
                console.error('❌ API-based scraping failed:', error);
                const errorResponse = { type: 'SCRAPE_ERROR', error: error.message };
                sendResponse(errorResponse);
            });
        return true;
    }
    else if (request.type === 'GET_AD_ORDER') {
        // Get the original order of ads from the main search page
        (async () => {
            try {
                const adsLimit = request.adsLimit || 50;
                console.log(`Getting original ad order with limit: ${adsLimit}`);
                
                // Scroll to load more ads if needed
                await scrollToLoadMoreAds(adsLimit);
                
                // Additional wait after scrolling for DOM attributes to fully populate
                console.log('Waiting for DOM attributes to populate after scrolling...');
                await waitForAttributesToPopulate(adsLimit);
                
                const adOrder = getAdOrderFromSearchPage(adsLimit);
                sendResponse({ type: 'AD_ORDER_SUCCESS', adOrder: adOrder });
            } catch (error) {
                console.error('Error getting ad order:', error);
                sendResponse({ type: 'AD_ORDER_ERROR', error: error.message });
            }
        })();
        
        // Return true to indicate async response
        return true;
    }
});

/**
 * Scrape ads from a tab that's already filtered to a specific format
 * @param {string} format - The format this tab is filtered for (IMAGE, TEXT, VIDEO)
 * @param {number} adsLimit - Maximum number of ads to scrape
 * @returns {Array} Array of ad objects with the known format
 */
async function scrapeFormatFilteredTab(format, adsLimit = 50) {
    console.log(`Scraping format-filtered tab for ${format} ads with limit: ${adsLimit}`);
    
    try {
        // Find all ad containers on this filtered page
        const adElements = document.querySelectorAll(SEARCH_PAGE_SELECTORS.AD_CONTAINER);
        console.log(`Found ${adElements.length} ad containers on ${format} filtered page`);
        
        if (adElements.length === 0) {
            console.log(`No ads found on ${format} filtered page`);
            return [];
        }
        
        const scrapedAds = [];
        const knownFormat = format.toUpperCase(); // Convert to uppercase for consistency
        
        // Limit the number of ads to process
        const adsToProcess = Math.min(adElements.length, adsLimit);
        console.log(`Processing ${adsToProcess} ads (limit: ${adsLimit})`);
        
        for (let i = 0; i < adsToProcess; i++) {
            const adElement = adElements[i];
            const adData = extractAdDataFromFilteredTab(adElement, i, knownFormat);
            
            if (adData) {
                scrapedAds.push(adData);
            }
        }
        
        console.log(`Successfully scraped ${scrapedAds.length} ${format} ads`);
        
        // Log all advertiser-id and creative-id pairs from this format tab
        console.log(`=== ${format} TAB AD IDs ===`);
        let adsWithValidIds = 0;
        scrapedAds.forEach((ad, index) => {
            // Extract IDs from GATC link
            const gatcMatch = ad.gatcLink?.match(/advertiser\/([^\/]+)\/creative\/([^?]+)/);
            const advertiserId = gatcMatch ? gatcMatch[1] : 'NO_ID';
            const creativeId = gatcMatch ? gatcMatch[2] : 'NO_ID';
            if (advertiserId !== 'NO_ID' && creativeId !== 'NO_ID') {
                adsWithValidIds++;
            }
            console.log(`${format} Ad ${index + 1}: advertiserId="${advertiserId}", creativeId="${creativeId}", advertiserName="${ad.advertiserName}", gatcLink="${ad.gatcLink}"`);
        });
        console.log(`=== END ${format} TAB AD IDs (${adsWithValidIds}/${scrapedAds.length} have valid IDs) ===`);
        
        return scrapedAds;
        
    } catch (error) {
        console.error(`Error scraping ${format} format tab:`, error);
        throw error;
    }
}

/**
 * Extract ad data from an element in a format-filtered tab
 * @param {Element} adElement - The ad container element
 * @param {number} index - Index of the ad for logging
 * @param {string} knownFormat - The known format from the tab filter
 * @returns {Object|null} Extracted ad data or null if extraction failed
 */
function extractAdDataFromFilteredTab(adElement, index, knownFormat) {
    try {
        console.log(`Processing ${knownFormat} ad ${index + 1} from filtered tab`);
        
        // Extract advertiser name
        const advertiserElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.ADVERTISER);
        const advertiserName = advertiserElement ? advertiserElement.textContent.trim() : 'Unknown';
        
        // Extract region from within the ad container first, fall back to global filters
        let region = 'Unknown';
        const adRegionElement = adElement.querySelector(SEARCH_PAGE_SELECTORS.AD_REGION);
        
        if (adRegionElement) {
            const rawRegion = adRegionElement.textContent.trim();
            region = cleanRegionText(rawRegion);
        } else {
            // Fall back to global filters from the document
            const globalFilters = extractGlobalFiltersFromDoc(document);
            region = globalFilters.region;
        }
        
        // Extract ad creative data
        const adCreative = extractSearchPageAdCreative(adElement);
        
        // Handle iframe-based ads - include them but with empty creative
        if (adCreative.hasIframe) {
            console.log(`${knownFormat} ad ${index + 1} - Iframe-based ad detected, including with empty creative`);
            // Clear the creative data for iframe ads
            adCreative.imageUrl = null;
            adCreative.videoUrl = null;
            adCreative.text = '';
        } else {
            // Check if we have any creative content for non-iframe ads - if not, skip this ad
            const hasCreativeContent = adCreative.imageUrl || adCreative.videoUrl || (adCreative.text && adCreative.text.trim());
            if (!hasCreativeContent) {
                console.log(`${knownFormat} ad ${index + 1} - No creative content found, skipping`);
                return null;
            }
        }
        
        // Use the known format from the tab filter (capitalize first letter)
        const format = knownFormat.charAt(0).toUpperCase() + knownFormat.slice(1).toLowerCase();
        
        // Extract advertiser-id and creative-id for GATC link
        const advertiserId = adElement.getAttribute('advertiser-id');
        const creativeId = adElement.getAttribute('creative-id');
        
        // Don't skip ads without IDs - include all ads for better matching
        
        // Construct GATC link with region from current page URL (if IDs available)
        const regionParam = getRegionFromCurrentUrl();
        const searchRegion = getSearchRegionFromUrl();
        const gatcLink = `https://adstransparency.google.com/advertiser/${advertiserId}/creative/${creativeId}?region=${regionParam}`;
        
        // Extract global filter data from the document
        const globalFilters = extractGlobalFiltersFromDoc(document);
        
        // Create ad data object following the schema from DESIGN_DOC.md
        const adData = {
            advertiserName: advertiserName,
            adCreative: adCreative,
            format: format,
            region: region,
            firstSeenDate: globalFilters.firstSeen,
            lastSeenDate: globalFilters.lastSeen,
            gatcLink: gatcLink
        };
        
        console.log(`Successfully extracted ${knownFormat} ad ${index + 1}:`, {
            advertiser: advertiserName,
            format: format,
            hasImage: !!adCreative.imageUrl,
            hasVideo: !!adCreative.videoUrl,
            hasText: !!adCreative.text
        });
        
        return adData;
        
    } catch (error) {
        console.error(`Error extracting data from ${knownFormat} ad ${index + 1}:`, error);
        return null;
    }
}

/**
 * Fetch ad data using GATC's internal SearchCreatives RPC API
 * @param {string} searchQuery - The search query or parameters
 * @param {string} regionParam - The region parameter
 * @returns {Promise<Array>} Array of ad data with format information
 */
async function fetchAdsFromGATCAPI(searchQuery, regionParam) {
    try {
        const apiUrl = 'https://adstransparency.google.com/anji/_/rpc/SearchService/SearchCreatives?authuser=0';
        console.log(`🚀 Calling GATC SearchCreatives API...`);
        
        // The API expects a POST request with the search parameters
        // We'll need to construct the proper request body based on the current search page
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-protobuf'
            },
            // We'll need to extract the actual request body from the network tab
            // For now, let's try a basic approach
        });
        
        if (!response.ok) {
            console.warn(`GATC API request failed: ${response.status}`);
            return [];
        }
        
        const data = await response.json();
        console.log(`✅ GATC API response received:`, data);
        
        // Parse the response and extract ad data with formats
        return parseGATCAPIResponse(data);
        
    } catch (error) {
        console.error('Error calling GATC API:', error);
        return [];
    }
}

/**
 * Parse GATC API response and extract ad data with correct formats
 * @param {Object} apiResponse - The API response data
 * @returns {Array} Array of parsed ad data
 */
function parseGATCAPIResponse(apiResponse) {
    try {
        if (!apiResponse || !apiResponse["1"]) {
            console.warn('Invalid API response structure');
            return [];
        }
        
        const ads = apiResponse["1"];
        const parsedAds = [];
        
        for (const ad of ads) {
            try {
                const advertiserId = ad["1"];
                const creativeId = ad["2"];
                const formatCode = ad["4"]; // This is the format field we discovered!
                const advertiserName = ad["12"] || 'Unknown';
                const creativeData = ad["3"];
                
                                 // Map format codes to format names
                 let format = 'Unknown';
                 if (formatCode === 1) {
                     format = 'Text';
                 } else if (formatCode === 2) {
                     format = 'Image';
                 } else if (formatCode === 3) {
                     format = 'Video';
                 } else if (creativeData && creativeData["1"]) {
                     // Interactive/iframe content
                     format = 'Interactive';
                 }
                
                // Extract creative content
                let imageUrl = null;
                let videoUrl = null;
                let text = '';
                let hasIframe = false;
                
                if (creativeData) {
                    if (creativeData["3"] && creativeData["3"]["2"]) {
                        // HTML content (image or iframe)
                        const htmlContent = creativeData["3"]["2"];
                        if (htmlContent.includes('<img')) {
                            // Extract image URL
                            const imgMatch = htmlContent.match(/src="([^"]+)"/);
                            if (imgMatch) {
                                imageUrl = imgMatch[1];
                            }
                        } else if (htmlContent.includes('<iframe')) {
                            hasIframe = true;
                        }
                    } else if (creativeData["1"]) {
                        // Interactive content URL
                        hasIframe = true;
                    }
                }
                
                // Construct GATC link
                const regionParam = getRegionFromCurrentUrl();
                const gatcLink = `https://adstransparency.google.com/advertiser/${advertiserId}/creative/${creativeId}?region=${regionParam}`;
                
                const adData = {
                    advertiserName: advertiserName,
                    adCreative: {
                        imageUrl: imageUrl,
                        videoUrl: videoUrl,
                        text: text,
                        hasIframe: hasIframe
                    },
                    format: format,
                    region: 'Unknown', // We'll extract this from global filters
                    searchRegion: getSearchRegionFromUrl(),              // NEW: User's search filter region
                    firstSeenDate: 'Unknown',
                    lastSeenDate: 'Unknown',
                    gatcLink: gatcLink
                };
                
                parsedAds.push(adData);
                console.log(`✅ Parsed ad: ${advertiserId}/${creativeId} - ${format} - ${advertiserName}`);
                
            } catch (error) {
                console.error('Error parsing individual ad:', error);
            }
        }
        
        console.log(`🎯 Successfully parsed ${parsedAds.length} ads from GATC API`);
        return parsedAds;
        
    } catch (error) {
        console.error('Error parsing GATC API response:', error);
        return [];
    }
}

async function scrapeSearchPageWithAPIFormats(adsLimit = 50) {
    console.log('🚀 Starting REVOLUTIONARY SearchCreatives API scraping...');
    
    // Show professional overlay
    showScrapingOverlay();
    updateScrapingProgress('Initializing...', 0, adsLimit, 'Starting up', 0, 0);
    
    try {
        // Extract authuser from URL
        const urlParams = new URLSearchParams(window.location.search);
        const authUser = urlParams.get('authuser') || '0';
        console.log(`🔑 Auth User: ${authUser}`);
        
        // Log which page type we're on for debugging
        const urlMatch = window.location.pathname.match(/\/advertiser\/([^\/]+)/);
        if (urlMatch) {
            console.log(`📍 Advertiser page detected: ${urlMatch[1]}`);
        } else {
            console.log(`📍 Homepage detected`);
        }

        // ===== REVOLUTIONARY SEARCHCREATIVES APPROACH =====
        // Instead of 50+ individual API calls, make 2-3 SearchCreatives calls
        const processedAds = [];
        let pageToken = null;
        let apiCallCount = 0;
        
        console.log(`🚀 Using SearchCreatives API - up to 40 ads per call!`);
        
        // Keep calling SearchCreatives with pagination until we have enough ads
        while (processedAds.length < adsLimit) {
            apiCallCount++;
            const remainingAds = adsLimit - processedAds.length;
            
            console.log(`📡 SearchCreatives call ${apiCallCount}: requesting up to 40 ads (need ${remainingAds} more)`);
            
            updateScrapingProgress(
                `Processing batch ${apiCallCount}...`,
                processedAds.length,
                adsLimit,
                `Getting ads`,
                processedAds.length,
                apiCallCount
            );
            
            try {
                // Get current page search parameters
                const searchParams = extractCurrentSearchParameters();
                
                // Make SearchCreatives API call
                const apiResult = await callSearchCreativesAPI(authUser, searchParams, pageToken);
                
                if (!apiResult || !apiResult.ads || apiResult.ads.length === 0) {
                    console.log('🔚 No more ads available from SearchCreatives API');
                    break;
                }
                
                console.log(`✅ SearchCreatives returned ${apiResult.ads.length} ads in one call!`);
                
                // Add the new ads to our results
                const adsToAdd = apiResult.ads.slice(0, remainingAds);
                processedAds.push(...adsToAdd);
                
                // Update pagination token for next request
                pageToken = apiResult.nextPageToken;
                
                console.log(`📊 Total ads collected: ${processedAds.length}/${adsLimit}`);
                
                updateScrapingProgress(
                    `Collected ${processedAds.length} ads...`,
                    processedAds.length,
                    adsLimit,
                    processedAds.length >= adsLimit ? 'Complete!' : 'Getting more ads',
                    processedAds.length,
                    apiCallCount
                );
                
                // If we got fewer than 40 ads or no next page token, we've reached the end
                if (apiResult.ads.length < 40 || !apiResult.hasMore) {
                    console.log('🔚 Reached end of available ads');
                    break;
                }
                
                // Small delay between SearchCreatives calls (much faster than individual calls)
                if (processedAds.length < adsLimit && pageToken) {
                    console.log('⏱️ Brief delay between SearchCreatives calls...');
                    await new Promise(resolve => setTimeout(resolve, 300)); // Only 300ms between batches!
                }
                
            } catch (error) {
                console.error(`❌ SearchCreatives API call ${apiCallCount} failed:`, error);
                
                // If first call fails, fall back to individual API calls
                if (apiCallCount === 1) {
                    console.log('🔄 Falling back to individual GetCreativeById calls...');
                    return await fallbackToIndividualAPICalls(adsLimit, authUser);
                }
                break;
            }
        }
        
        console.log(`🎯 REVOLUTIONARY SUCCESS! Collected ${processedAds.length} ads with only ${apiCallCount} API calls!`);
        console.log(`⚡ Performance: ${(processedAds.length / apiCallCount).toFixed(1)} ads per API call (vs 1 ad per call with old method)`);
        
        updateScrapingProgress('Finalizing results...', processedAds.length, adsLimit, 'Updating UI', processedAds.length, apiCallCount);
        
        // Update DOM with format information
        await updateDOMWithAPIFormats(processedAds);
        
        // Hide overlay before returning
        setTimeout(hideScrapingOverlay, 1000);
        
        return {
            success: true,
            message: `🚀 REVOLUTIONARY! Got ${processedAds.length} ads with only ${apiCallCount} API calls (${(processedAds.length / apiCallCount).toFixed(1)}x faster!)`,
            data: processedAds
        };
        
    } catch (error) {
        console.error('❌ Error in SearchCreatives scraping:', error);
        hideScrapingOverlay();
        
        // Fall back to individual API calls if SearchCreatives fails
        console.log('🔄 Falling back to individual GetCreativeById calls...');
        return await fallbackToIndividualAPICalls(adsLimit, authUser);
    }
}

/**
 * Fallback function to use individual GetCreativeById API calls
 * Used when SearchCreatives API fails
 */
async function fallbackToIndividualAPICalls(adsLimit, authUser) {
    console.log('🔄 Starting fallback: Individual GetCreativeById API calls...');
    
    try {
        // Extract advertiser-id and creative-id pairs from DOM
        const creativeIdPairs = [];
        const adElements = document.querySelectorAll('[advertiser-id][creative-id]');
        
        console.log(`📊 Found ${adElements.length} ad elements with IDs in DOM`);
        
        for (const adElement of adElements) {
            if (creativeIdPairs.length >= adsLimit) break;
            
            const advertiserId = adElement.getAttribute('advertiser-id');
            const creativeId = adElement.getAttribute('creative-id');
            
            if (advertiserId && creativeId) {
                creativeIdPairs.push({ advertiserId, creativeId, element: adElement });
            }
        }
        
        if (creativeIdPairs.length === 0) {
            return {
                success: false,
                message: 'No ads found with advertiser-id and creative-id attributes',
                data: []
            };
        }
        
        console.log(`🎯 Processing ${creativeIdPairs.length} ads with individual API calls...`);
        
        const processedAds = [];
        let apiCallCount = 0;
        
        for (let i = 0; i < creativeIdPairs.length; i++) {
            const { advertiserId, creativeId, element } = creativeIdPairs[i];
            
            updateScrapingProgress(
                `Processing individual ad ${i + 1}/${creativeIdPairs.length}...`,
                i + 1,
                creativeIdPairs.length,
                `Getting ${creativeId}`,
                processedAds.length,
                apiCallCount
            );
            
            try {
                apiCallCount++;
                const apiData = await getCreativeByIdAPI(advertiserId, creativeId, authUser);
                
                if (apiData) {
                    // Extract additional data from DOM element
                    const advertiserName = element.querySelector('.advertiser-name')?.textContent?.trim() || 'Unknown';
                    const region = getRegionFromCurrentUrl();
                    const searchRegion = getSearchRegionFromUrl();
                    const adCreative = extractSearchPageAdCreative(element);
                    
                    const adObject = {
                        advertiserName: advertiserName,
                        adFormat: apiData.format || 'Unknown',
                        adCreative: adCreative,
                        region: region,
                        searchRegion: searchRegion,              // NEW: User's search filter region
                        firstSeenDate: apiData.firstSeenDate || 'Unknown',
                        lastSeenDate: apiData.lastSeenDate || 'Unknown',
                        gatcLink: `https://adstransparency.google.com/advertiser/${advertiserId}/creative/${creativeId}?authuser=${authUser}&region=${region}`,
                        
                        // Additional competitive data
                        formatCode: apiData.formatCode,
                        adType: apiData.format || 'Unknown',
                        imageUrl: adCreative.imageUrl,
                        youtubeVideoId: apiData.youtubeVideoId || null,
                        videoThumbnailUrl: apiData.videoThumbnailUrl || null,
                        
                        // Unique advantages
                        hasInteractiveContent: adCreative.hasIframe,
                        campaignDuration: (() => {
                            try {
                                return calculateCampaignDuration(firstSeenDate, lastSeenDate);
                            } catch (e) {
                                console.warn(`⚠️  Campaign duration calculation failed for ${creativeId}:`, e.message);
                                return 'Unknown';
                            }
                        })(),
                        creativeDimensions: (() => {
                            try {
                                return extractImageDimensions(adCreative.imageUrl);
                            } catch (e) {
                                console.warn(`⚠️  Image dimensions extraction failed for ${creativeId}:`, e.message);
                                return 'Unknown';
                            }
                        })(),
                        
                        // Technical metadata
                        apiData: {
                            advertiserId: advertiserId,
                            creativeId: creativeId,
                            formatCode: apiData.formatCode
                        }
                    };
                    
                    processedAds.push(adObject);
                }
                
                // Add delay between individual API calls to avoid throttling
                if (i < creativeIdPairs.length - 1) {
                    await new Promise(resolve => setTimeout(resolve, 750)); // 750ms delay
                }
                
            } catch (error) {
                console.error(`❌ Failed to get data for ${creativeId}:`, error);
                // Continue with next ad
            }
        }
        
        return {
            success: true,
            message: `✅ Fallback completed: ${processedAds.length} ads processed with ${apiCallCount} individual API calls`,
            data: processedAds
        };
        
    } catch (error) {
        console.error('❌ Error in fallback individual API calls:', error);
        return {
            success: false,
            message: `Fallback failed: ${error.message}`,
            data: []
        };
    }
}

async function getCreativeByIdAPI(advertiserId, creativeId, authUser, retryCount = 0) {
    console.log(`🔍 Calling GetCreativeById API for ${advertiserId}/${creativeId}${retryCount > 0 ? ` (retry ${retryCount})` : ''}`);
    
    try {
        // Extract XSRF token
        let xsrfToken = '';
        const xsrfMeta = document.querySelector('meta[name="framework-xsrf-token"]');
        if (xsrfMeta) {
            xsrfToken = xsrfMeta.getAttribute('content');
        } else {
            // Try to find it in the page source or window object
            const pageSource = document.documentElement.innerHTML;
            const xsrfMatch = pageSource.match(/["']([A-Za-z0-9_-]+:[0-9]+)["']/);
            if (xsrfMatch) {
                xsrfToken = xsrfMatch[1];
            } else if (window.WIZ_global_data) {
                const wizStr = JSON.stringify(window.WIZ_global_data);
                const wizMatch = wizStr.match(/["']([A-Za-z0-9_-]+:[0-9]+)["']/);
                if (wizMatch) {
                    xsrfToken = wizMatch[1];
                }
            }
        }
        
        // Construct API URL for GetCreativeById
        const apiUrl = `https://adstransparency.google.com/anji/_/rpc/LookupService/GetCreativeById?authuser=${authUser}`;
        const requestPayload = {
            "1": advertiserId,
            "2": creativeId,
            "5": {
                "1": 1,
                "2": 29,
                "3": 2840
            }
        };
        
        // Get dynamic session fingerprint for anti-detection
        const fingerprint = getSessionFingerprint();
        
        // Prepare headers with dynamic fingerprinting
        const headers = {
            'Accept': '*/*',
            'Accept-Language': fingerprint.acceptLanguage,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://adstransparency.google.com',
            'Pragma': 'no-cache',
            'Priority': 'u=1, i',
            'Referer': window.location.href,
            'Sec-CH-UA': fingerprint.chromeVersion ? `"Not)A;Brand";v="8", "Chromium";v="${fingerprint.chromeVersion}", "Google Chrome";v="${fingerprint.chromeVersion}"` : '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': fingerprint.platform || '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': fingerprint.userAgent,
            'X-Browser-Copyright': 'Copyright 2025 Google LLC. All rights reserved.',
            'X-Browser-Validation': 'qvLgIVtG4U8GgiRPSI9IJ22mUlI=',
            'X-Browser-Year': '2025',
            'X-Client-Data': 'CIW2yQEIo7bJAQipncoBCKuSywEIlKHLAQiSo8sBCIagzQEI/aXOAQij8s4BCJP2zgEI5/fOAQjS+M4BGOHizgE=',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Same-Domain': '1'
        };
        
        // Add XSRF token if available
        if (xsrfToken) {
            headers['X-Framework-XSRF-Token'] = xsrfToken;
        }
        
        // Construct request body
        const requestBody = `authuser=${authUser}&f.req=` + encodeURIComponent(JSON.stringify(requestPayload));
        
        console.log(`🌐 API URL: ${apiUrl}`);
        console.log(`📦 Request Payload:`, requestPayload);
        
        // Make the API call
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: headers,
            body: requestBody,
            credentials: 'include'
        });
        
        console.log(`📡 Response Status: ${response.status}`);
        
        // Advanced throttling detection and session management
        const isThrottled = detectThrottling(response);
        
        // Handle rate limiting (429) or redirects to sorry page
        if (!response.ok || isThrottled) {
            if (retryCount < 3) {
                // If we've triggered session reset, wait for cooldown
                if (throttleDetectionCount === 0 && retryCount === 0) {
                    console.log('🔄 Waiting for session reset cooldown...');
                    await resetSessionFingerprint();
                }
                
                const baseBackoff = Math.pow(2, retryCount) * 1000; // 1s, 2s, 4s
                const jitterBackoff = baseBackoff + (Math.random() * 500); // Add jitter to backoff
                console.log(`⏳ Rate limited or error (${response.status}), retrying in ${Math.round(jitterBackoff)}ms...`);
                await new Promise(resolve => setTimeout(resolve, jitterBackoff));
                return await getCreativeByIdAPI(advertiserId, creativeId, authUser, retryCount + 1);
            } else {
                console.error(`❌ API Request Failed after ${retryCount} retries: ${response.status}`);
                // Throw specific error for throttling so parallel system can detect it
                if (isThrottled) {
                    throw new Error(`Throttling detected: sorry/index redirect after ${retryCount} retries`);
                }
                return null;
            }
        }
        
        const responseText = await response.text();
        console.log(`📄 Raw Response (first 200 chars):`, responseText.substring(0, 200));
        
        // Parse the response
        let responseData;
        try {
            const cleanResponse = responseText.replace(/^\)\]\}'\s*/, '');
            responseData = JSON.parse(cleanResponse);
            console.log(`✅ Parsed Response:`, responseData);
        } catch (parseError) {
            console.error('❌ Failed to parse response:', parseError);
            return null;
        }
        
        // Extract format from response - the format should be in field "8" for GetCreativeById
        let formatCode = null;
        if (responseData && responseData["1"] && responseData["1"]["8"]) {
            formatCode = responseData["1"]["8"];
        }
        
        if (formatCode === null) {
            console.error('❌ Could not find format code in response');
            return null;
        }
        
        // Convert format code to human-readable format
        let format = 'Unknown';
        switch (formatCode) {
            case 1:
                format = 'Text';
                break;
            case 2:
                format = 'Image';
                break;
            case 3:
                format = 'Video';
                break;
            default:
                format = `Unknown (${formatCode})`;
        }
        
        console.log(`✅ Creative ${creativeId} format: ${format} (code: ${formatCode})`);
        
        return {
            advertiserId,
            creativeId,
            format,
            formatCode
        };
        
    } catch (error) {
        if (retryCount < 3 && (error.message.includes('Failed to fetch') || error.message.includes('NetworkError'))) {
            const backoffDelay = Math.pow(2, retryCount) * 1000;
            console.log(`⏳ Network error, retrying in ${backoffDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, backoffDelay));
            return await getCreativeByIdAPI(advertiserId, creativeId, authUser, retryCount + 1);
        }
        
        console.error(`❌ Error in getCreativeByIdAPI for ${creativeId}:`, error);
        return null;
    }
}

async function updateDOMWithAPIFormats(adsData) {
    console.log('🎨 Updating DOM with API format data...');
    
    // Create a map for quick lookup by creative ID
    const formatMap = new Map();
    adsData.forEach(ad => {
        formatMap.set(ad.creativeId, ad);
    });
    
    // Find all ad elements on the page
    const adElements = document.querySelectorAll('[data-creative-id], [href*="/creative/CR"], a[href*="/creative/"]');
    console.log(`🔍 Found ${adElements.length} ad elements in DOM`);
    
    let updatedCount = 0;
    
    adElements.forEach(element => {
        let creativeId = null;
        
        // Try different ways to extract creative ID
        if (element.dataset.creativeId) {
            creativeId = element.dataset.creativeId;
        } else if (element.href) {
            const match = element.href.match(/\/creative\/(CR[^\/\?]+)/);
            if (match) {
                creativeId = match[1];
            }
        }
        
        if (creativeId && formatMap.has(creativeId)) {
            const adData = formatMap.get(creativeId);
            
            // Add format information to the element
            element.dataset.apiFormat = adData.format;
            element.dataset.apiFormatCode = adData.formatCode;
            
            // Add visual indicator
            let indicator = element.querySelector('.api-format-indicator');
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'api-format-indicator';
                indicator.style.cssText = `
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    padding: 2px 6px;
                    border-radius: 3px;
                    font-size: 10px;
                    font-weight: bold;
                    color: white;
                    z-index: 1000;
                    pointer-events: none;
                `;
                
                // Make sure parent has relative positioning
                if (getComputedStyle(element).position === 'static') {
                    element.style.position = 'relative';
                }
                
                element.appendChild(indicator);
            }
            
            // Set color and text based on format
            switch (adData.format) {
                case 'Text':
                    indicator.style.backgroundColor = '#4CAF50';
                    indicator.textContent = '📝 TEXT';
                    break;
                case 'Image':
                    indicator.style.backgroundColor = '#2196F3';
                    indicator.textContent = '🖼️ IMAGE';
                    break;
                case 'Video':
                    indicator.style.backgroundColor = '#FF9800';
                    indicator.textContent = '🎥 VIDEO';
                    break;
                default:
                    indicator.style.backgroundColor = '#9E9E9E';
                    indicator.textContent = '❓ UNKNOWN';
            }
            
            updatedCount++;
            console.log(`✅ Updated element with creative ID ${creativeId}: ${adData.format}`);
        }
    });
    
    console.log(`🎨 Updated ${updatedCount} DOM elements with API format data`);
}

/**
 * Fallback DOM-based format detection (simplified version)
 */
async function scrapeSearchPageFallback(adsLimit = 50) {
    console.log('🔄 Using fallback DOM-based format detection...');
    
    const ads = [];
    const adElements = document.querySelectorAll('[jsname][data-ved]');
    
    for (const element of adElements) {
        try {
            // Basic format detection based on DOM structure
            let format = 'Unknown';
            
            if (element.querySelector('video, [data-video-url]')) {
                format = 'Video';
            } else if (element.querySelector('img[src*="googleusercontent"], [data-image-url]')) {
                format = 'Image';
            } else if (element.textContent && element.textContent.trim().length > 0) {
                format = 'Text';
            }
            
            ads.push({
                creativeId: `FALLBACK_${Date.now()}_${Math.random()}`,
                format,
                formatCode: format === 'Text' ? 1 : format === 'Image' ? 2 : format === 'Video' ? 3 : 0,
                advertiserName: 'Unknown',
                element
            });
            
        } catch (error) {
            console.warn('⚠️ Error in fallback detection:', error);
        }
    }
    
    console.log(`✅ Fallback detection found ${ads.length} ads`);
    return ads;
}

/**
 * Find the real format from DOM element attributes or data
 * @param {Element} adElement - The ad container element
 * @returns {string} The real format if found
 */
function findRealFormatFromDOM(adElement) {
    try {
        // Log all attributes to see what data is available
        console.log(`🔍 Inspecting ad element attributes:`);
        for (let i = 0; i < adElement.attributes.length; i++) {
            const attr = adElement.attributes[i];
            console.log(`  ${attr.name}: ${attr.value}`);
        }
        
        // Look for any data attributes that might contain format info
        const allAttributes = {};
        for (let i = 0; i < adElement.attributes.length; i++) {
            const attr = adElement.attributes[i];
            allAttributes[attr.name] = attr.value;
        }
        
        // Check for format-related attributes
        for (const [name, value] of Object.entries(allAttributes)) {
            if (name.includes('format') || name.includes('type') || name.includes('category')) {
                console.log(`📍 Found potential format attribute: ${name} = ${value}`);
                
                // Try to map the value to our known formats
                if (value === '1' || value.toLowerCase().includes('text')) {
                    return 'Text';
                } else if (value === '2' || value.toLowerCase().includes('image')) {
                    return 'Image';
                } else if (value === '3' || value.toLowerCase().includes('video')) {
                    return 'Video';
                }
            }
        }
        
        // Check if there are any child elements with format data
        const formatElements = adElement.querySelectorAll('[data-format], [data-type], [format], [type]');
        for (const elem of formatElements) {
            console.log(`📍 Found child element with format data:`, elem.outerHTML.substring(0, 200));
        }
        
        return 'Unknown';
        
    } catch (error) {
        console.error('Error finding real format from DOM:', error);
        return 'Unknown';
    }
}

/**
 * Detect format from creative content using improved logic based on API insights
 * @param {Object} adCreative - The ad creative object
 * @returns {string} The detected format
 */
function detectFormatFromCreativeContent(adCreative) {
    // If it's an iframe, it's Interactive/Video
    if (adCreative.hasIframe) {
        return 'Interactive';
    }
    
    // If it has an image URL, it's likely Image format
    if (adCreative.imageUrl) {
        return 'Image';
    }
    
    // If it has video URL, it's Video format
    if (adCreative.videoUrl) {
        return 'Video';
    }
    
    // If it has text content but no images/videos, it's likely Text format
    if (adCreative.text && adCreative.text.trim().length > 0 && !adCreative.imageUrl && !adCreative.videoUrl) {
        return 'Text';
    }
    
    return 'Unknown';
}

// Log that content script has loaded
console.log('GATC Scraper content script loaded');

/**
 * Global function to dismiss the overlay (accessible from onclick)
 */
window.gatcDismissOverlay = function() {
    if (scrapingOverlay) {
        scrapingOverlay.style.display = 'none';
        document.body.classList.remove('gatc-scraping-active');
        
        // Still prevent navigation but allow tab switching
        document.removeEventListener('keydown', preventTabSwitching, true);
        document.removeEventListener('contextmenu', preventInteractions, true);
        // Keep navigation prevention for safety
        
        // Show minimized notification
        showMinimizedNotification();
        
        console.log('🎨 Overlay minimized - scraping continues in background');
    }
};

/**
 * Shows a minimized notification when overlay is dismissed
 */
function showMinimizedNotification() {
    const notification = document.createElement('div');
    notification.id = 'gatc-minimized-notification';
    notification.innerHTML = `
        <div class="gatc-mini-notification">
            <div class="gatc-mini-spinner"></div>
            <span>GATC Scraper running...</span>
            <button onclick="window.gatcShowOverlay()" class="gatc-mini-restore">Show</button>
        </div>
    `;
    
    const miniStyle = document.createElement('style');
    miniStyle.textContent = `
        #gatc-minimized-notification {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 2147483646;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        
        .gatc-mini-notification {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 16px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            font-size: 14px;
            font-weight: 500;
        }
        
        .gatc-mini-spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-top: 2px solid white;
            border-radius: 50%;
            animation: gatc-spin 1s linear infinite;
        }
        
        .gatc-mini-restore {
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.2s ease;
        }
        
        .gatc-mini-restore:hover {
            background: rgba(255, 255, 255, 0.3);
        }
    `;
    
    document.head.appendChild(miniStyle);
    document.body.appendChild(notification);
}

/**
 * Global function to restore the overlay
 */
window.gatcShowOverlay = function() {
    if (scrapingOverlay) {
        scrapingOverlay.style.display = 'block';
        document.body.classList.add('gatc-scraping-active');
        
        // Re-enable protections
        document.addEventListener('keydown', preventTabSwitching, true);
        document.addEventListener('contextmenu', preventInteractions, true);
        
        // Remove minimized notification
        const notification = document.getElementById('gatc-minimized-notification');
        if (notification) {
            notification.remove();
        }
        
        console.log('🎨 Overlay restored');
    }
};

/**
 * Extract current search parameters from the page for SearchCreatives API
 */
function extractCurrentSearchParameters() {
    console.log('🔍 Extracting search parameters from current page...');
    
    // Get advertiser ID if we're on an advertiser page
    let advertiserId = null;
    const urlMatch = window.location.pathname.match(/\/advertiser\/([^\/]+)/);
    if (urlMatch) {
        advertiserId = urlMatch[1];
        console.log(`📍 Found advertiser ID: ${advertiserId}`);
    }
    
    // Get region from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const region = urlParams.get('region') || 'US';
    
    // Get format filter from URL parameter (e.g., &format=IMAGE)
    const formatFilter = urlParams.get('format');
    
    console.log('📋 Search parameters:', {
        advertiserId,
        region,
        formatFilter
    });
    
    return {
        advertiserId,
        region,
        formatFilter
    };
}

/**
 * Call the SearchCreatives API to get a batch of ads
 * Fixed with real API format from network capture
 */
async function callSearchCreativesAPI(authUser, searchParams, pageToken = null) {
    console.log('🚀 Calling SearchCreatives API with REAL format...');
    
    try {
        // Extract XSRF token
        let xsrfToken = '';
        const xsrfMeta = document.querySelector('meta[name="framework-xsrf-token"]');
        if (xsrfMeta) {
            xsrfToken = xsrfMeta.getAttribute('content');
        } else {
            const pageSource = document.documentElement.innerHTML;
            const xsrfMatch = pageSource.match(/["']([A-Za-z0-9_-]+:[0-9]+)["']/);
            if (xsrfMatch) {
                xsrfToken = xsrfMatch[1];
            }
        }
        
        // Get dynamic session fingerprint
        const fingerprint = getSessionFingerprint();
        
        // Construct API URL
        const apiUrl = `https://adstransparency.google.com/anji/_/rpc/SearchService/SearchCreatives?authuser=${authUser}`;
        
        // Build REAL request payload based on network capture
        const requestPayload = {
            "2": 40, // Results per page
            "3": {
                "12": {
                    "1": "", // Empty search query
                    "2": true // Some boolean flag
                }
            },
            "7": {
                "1": 1,
                "2": 29, 
                "3": 2840
            }
        };
        
        // Add format filter if specified in URL
        if (searchParams.formatFilter) {
            // Map format names to Google's internal format codes
            const formatCodeMap = {
                'TEXT': 1,
                'IMAGE': 2, 
                'VIDEO': 3
            };
            
            const formatCode = formatCodeMap[searchParams.formatFilter];
            if (formatCode) {
                requestPayload["3"]["4"] = formatCode; // Format filter field
                requestPayload["3"]["8"] = [2840]; // Feature flag for format filtering
                console.log(`🎯 Applying format filter: ${searchParams.formatFilter} (code: ${formatCode})`);
            }
        }
        
        // Add advertiser IDs if we have them
        if (searchParams.advertiserId) {
            requestPayload["3"]["13"] = {
                "1": [searchParams.advertiserId] // Array of advertiser IDs
            };
        } else {
            // For homepage, we might need to extract advertiser IDs from DOM
            const advertiserIds = extractAdvertiserIdsFromDOM();
            if (advertiserIds.length > 0) {
                requestPayload["3"]["13"] = {
                    "1": advertiserIds.slice(0, 10) // Limit to first 10 advertisers
                };
                console.log(`📍 Using ${advertiserIds.length} advertiser IDs from DOM:`, advertiserIds.slice(0, 5));
            }
        }
        
        // Add pagination token if available
        if (pageToken) {
            requestPayload["4"] = pageToken; // Pagination token field
        }
        
        // Prepare headers with anti-detection (matching real request)
        const headers = {
            'Accept': '*/*',
            'Accept-Language': fingerprint.acceptLanguage,
            'Cache-Control': 'no-cache',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://adstransparency.google.com',
            'Pragma': 'no-cache',
            'Priority': 'u=1, i',
            'Referer': window.location.href,
            'Sec-CH-UA': fingerprint.chromeVersion ? `"Not)A;Brand";v="8", "Chromium";v="${fingerprint.chromeVersion}", "Google Chrome";v="${fingerprint.chromeVersion}"` : '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'Sec-CH-UA-Mobile': '?0',
            'Sec-CH-UA-Platform': fingerprint.platform || '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': fingerprint.userAgent,
            'X-Browser-Copyright': 'Copyright 2025 Google LLC. All rights reserved.',
            'X-Browser-Validation': 'qvLgIVtG4U8GgiRPSI9IJ22mUlI=',
            'X-Browser-Year': '2025',
            'X-Client-Data': 'CIW2yQEIo7bJAQipncoBCKuSywEIlKHLAQiSo8sBCIagzQEI/aXOAQij8s4BCJP2zgEI5/fOAQjS+M4BGOHizgE=',
            'X-Requested-With': 'XMLHttpRequest',
            'X-Same-Domain': '1'
        };
        
        // Add XSRF token if available
        if (xsrfToken) {
            headers['X-Framework-XSRF-Token'] = xsrfToken;
        }
        
        // Construct request body (matching real format)
        const requestBody = `f.req=${encodeURIComponent(JSON.stringify(requestPayload))}`;
        
        console.log(`🌐 SearchCreatives URL: ${apiUrl}`);
        console.log(`📦 REAL Request Payload:`, requestPayload);
        
        // Make the API call
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: headers,
            body: requestBody,
            credentials: 'include'
        });
        
        console.log(`📡 SearchCreatives Response Status: ${response.status}`);
        
        if (!response.ok) {
            throw new Error(`SearchCreatives API failed: ${response.status}`);
        }
        
        const responseText = await response.text();
        console.log(`📄 SearchCreatives Response (first 200 chars):`, responseText.substring(0, 200));
        
        // Parse the response (handle Google's response format)
        const cleanResponse = responseText.replace(/^\)\]\}'\s*/, '');
        const responseData = JSON.parse(cleanResponse);
        
        // Extract pagination token for next request
        let nextPageToken = null;
        if (responseData["2"]) {
            nextPageToken = responseData["2"];
            console.log(`📄 Next page token: ${nextPageToken.substring(0, 20)}...`);
        }
        
        // Parse ads from response
        const ads = parseSearchCreativesResponse(responseData);
        
        return {
            ads: ads,
            nextPageToken: nextPageToken,
            hasMore: ads.length === 40 // If we got 40 ads, there might be more
        };
        
    } catch (error) {
        console.error('❌ SearchCreatives API error:', error);
        throw error;
    }
}

/**
 * Extract advertiser IDs from DOM elements on the page
 */
function extractAdvertiserIdsFromDOM() {
    console.log('🔍 Extracting advertiser IDs from DOM...');
    
    const advertiserIds = new Set();
    
    // Look for advertiser-id attributes
    const adElements = document.querySelectorAll('[advertiser-id]');
    adElements.forEach(element => {
        const advertiserId = element.getAttribute('advertiser-id');
        if (advertiserId && advertiserId !== 'null') {
            advertiserIds.add(advertiserId);
        }
    });
    
    // Also look for advertiser links
    const advertiserLinks = document.querySelectorAll('a[href*="/advertiser/AR"]');
    advertiserLinks.forEach(link => {
        const href = link.getAttribute('href');
        const match = href.match(/\/advertiser\/(AR[^\/\?]+)/);
        if (match) {
            advertiserIds.add(match[1]);
        }
    });
    
    const result = Array.from(advertiserIds);
    console.log(`📊 Found ${result.length} unique advertiser IDs from DOM`);
    return result;
}

/**
 * Parse SearchCreatives API response into our standard format
 * Updated with REAL response format from network capture
 */
function parseSearchCreativesResponse(responseData) {
    console.log('🔍 Parsing SearchCreatives response with REAL format...');
    
    try {
        if (!responseData || !responseData["1"]) {
            console.warn('Invalid SearchCreatives response structure');
            return [];
        }
        
        const ads = responseData["1"];
        const parsedAds = [];
        let successCount = 0;
        let skipCount = 0;
        let errorCount = 0;
        
        console.log(`📊 Processing ${ads.length} ads from SearchCreatives response`);
        
        for (const ad of ads) {
            try {
                // Validate required fields first
                if (!ad["1"] || !ad["2"]) {
                    console.warn(`⚠️  Skipping ad with missing advertiser ID (${ad["1"]}) or creative ID (${ad["2"]})`);
                    skipCount++;
                    continue;
                }
                
                const advertiserId = ad["1"];
                const creativeId = ad["2"];
                const formatCode = ad["4"] || 0; // Default to 0 if missing
                const advertiserName = ad["12"] || 'Unknown';
                
                console.log(`🔄 Processing ad ${parsedAds.length + 1} of ${ads.length}: ${advertiserId}/${creativeId}`);
                console.log(`📊 Ad fields available:`, Object.keys(ad));
                
                // Map format codes to format names (confirmed from real data)
                let format = 'Unknown';
                switch (formatCode) {
                    case 1:
                        format = 'Text';
                        break;
                    case 2:
                        format = 'Image';
                        break;
                    case 3:
                        format = 'Video';
                        break;
                    default:
                        format = `Unknown (${formatCode})`;
                }
                
                // Extract creative content from the response
                const adCreative = {
                    imageUrl: null,
                    videoUrl: null,
                    text: '',
                    hasIframe: false
                };
                
                if (ad["3"]) {
                    const creativeData = ad["3"];
                    
                    // Handle image content (field "3"."3"."2")
                    if (creativeData["3"] && creativeData["3"]["2"]) {
                        const htmlContent = creativeData["3"]["2"];
                        console.log(`🖼️  Processing HTML content for ${creativeId}:`, htmlContent.substring(0, 100));
                        
                        if (htmlContent.includes('<img')) {
                            // Extract image URL from HTML
                            const imgMatch = htmlContent.match(/src\s*=\s*["']([^"']+)["']/);
                            if (imgMatch) {
                                adCreative.imageUrl = imgMatch[1];
                                console.log(`✅ Extracted image URL: ${adCreative.imageUrl.substring(0, 50)}...`);
                                
                                // Check if this is a YouTube thumbnail URL (for ALL ads, not just Video format)
                                if (adCreative.imageUrl && adCreative.imageUrl.includes('i.ytimg.com/vi/')) {
                                    const youtubeMatch = adCreative.imageUrl.match(/\/vi\/([^\/]+)\//);
                                    if (youtubeMatch && youtubeMatch[1]) {
                                        const youtubeId = youtubeMatch[1];
                                        adCreative.videoUrl = `https://www.youtube.com/watch?v=${youtubeId}`;
                                        adCreative.youtubeId = youtubeId;
                                        console.log(`🎬 Found YouTube thumbnail, constructed video URL: ${adCreative.videoUrl}`);
                                        
                                        // Also set the variables used in the final ad object
                                        youtubeVideoId = youtubeId;
                                        actualVideoUrl = adCreative.videoUrl;
                                        videoThumbnailUrl = adCreative.imageUrl;
                                    }
                                }
                            }
                        } else if (htmlContent.includes('<iframe')) {
                            adCreative.hasIframe = true;
                            console.log(`✅ Detected iframe content`);
                        }
                    }
                    
                    // Handle interactive content (field "3"."1"."4")
                    if (creativeData["1"] && creativeData["1"]["4"]) {
                        const interactiveUrl = creativeData["1"]["4"];
                        console.log(`🎮 Processing interactive content for ${creativeId}:`, interactiveUrl.substring(0, 100));
                        
                        if (interactiveUrl.includes('displayads-formats.googleusercontent.com')) {
                            adCreative.hasIframe = true;
                            // Replace complex iframe URL with user-friendly message
                            adCreative.videoUrl = 'Check GATC link';
                            console.log(`🖼️  Replaced complex iframe URL with user-friendly message`);
                        }
                    }
                }
                
                // Extract timestamps (fields "6" and "7")
                let firstSeenDate = 'Unknown';
                let lastSeenDate = 'Unknown';
                
                if (ad["6"] && ad["6"]["1"]) {
                    const timestamp = parseInt(ad["6"]["1"]);
                    firstSeenDate = new Date(timestamp * 1000).toLocaleDateString();
                }
                
                if (ad["7"] && ad["7"]["1"]) {
                    const timestamp = parseInt(ad["7"]["1"]);
                    lastSeenDate = new Date(timestamp * 1000).toLocaleDateString();
                }
                
                // Build GATC link
                const regionParam = getRegionFromCurrentUrl();
                const searchRegion = getSearchRegionFromUrl();
                const gatcLink = `https://adstransparency.google.com/advertiser/${advertiserId}/creative/${creativeId}?region=${regionParam}`;
                
                // HYBRID YouTube extraction: API format detection + DOM targeting
                let youtubeVideoId = null;
                let videoThumbnailUrl = null;
                let actualVideoUrl = null;
                
                // If API says this is a VIDEO, use DOM method to extract YouTube URL
                if (format === 'Video') {
                    console.log(`🎬 Video format detected for ${advertiserId}/${creativeId}, searching DOM...`);
                    
                    // Method 1: Find the exact DOM element using advertiser-id and creative-id
                    const targetAdElement = document.querySelector(`[advertiser-id="${advertiserId}"][creative-id="${creativeId}"]`);
                    
                    if (targetAdElement) {
                        console.log(`🎯 Found target DOM element for ${creativeId}`);
                        
                        // Use the ORIGINAL DOM METHOD to extract YouTube from thumbnails
                        const imageElements = targetAdElement.querySelectorAll('img');
                        
                        for (const imageElement of imageElements) {
                            if (imageElement.src) {
                                console.log(`🔍 Checking image URL: ${imageElement.src.substring(0, 80)}...`);
                                
                                // ORIGINAL REGEX: Check if this is a YouTube thumbnail
                                const youtubeMatch = imageElement.src.match(/\/vi\/([^\/]+)\//);
                                if (youtubeMatch && youtubeMatch[1]) {
                                    youtubeVideoId = youtubeMatch[1];
                                    actualVideoUrl = `https://www.youtube.com/watch?v=${youtubeVideoId}`;
                                    videoThumbnailUrl = imageElement.src;
                                    
                                    console.log(`✅ SUCCESS! Extracted YouTube ID from DOM: ${youtubeVideoId}`);
                                    console.log(`🔄 Constructed YouTube URL: ${actualVideoUrl}`);
                                    console.log(`🖼️  Original thumbnail URL: ${videoThumbnailUrl}`);
                                    
                                    // Update the adCreative with the real YouTube URL and thumbnail
                                    adCreative.videoUrl = actualVideoUrl;
                                    adCreative.imageUrl = videoThumbnailUrl;
                                    
                                    // Also store the YouTube ID separately for easy access
                                    adCreative.youtubeId = youtubeVideoId;
                                    
                                    console.log(`📦 Updated adCreative:`, {
                                        videoUrl: adCreative.videoUrl,
                                        imageUrl: adCreative.imageUrl,
                                        youtubeId: adCreative.youtubeId
                                    });
                                    
                                    break; // Found it, stop searching
                                }
                            }
                        }
                        
                        // If no YouTube found in images, check for video elements
                        if (!youtubeVideoId) {
                            const videoElements = targetAdElement.querySelectorAll('video');
                            for (const videoElement of videoElements) {
                                if (videoElement.src) {
                                    const youtubeMatch = videoElement.src.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)/);
                                    if (youtubeMatch && youtubeMatch[1]) {
                                        youtubeVideoId = youtubeMatch[1];
                                        actualVideoUrl = videoElement.src;
                                        videoThumbnailUrl = `https://i.ytimg.com/vi/${youtubeVideoId}/hqdefault.jpg`;
                                        
                                        console.log(`✅ SUCCESS! Extracted YouTube ID from video element: ${youtubeVideoId}`);
                                        adCreative.videoUrl = actualVideoUrl;
                                        break;
                                    }
                                }
                            }
                        }
                        
                    } else {
                        console.log(`⚠️  Could not find DOM element for ${advertiserId}/${creativeId}`);
                    }
                    
                    // Method 2: Fallback - check API image URL for YouTube thumbnail pattern
                    if (!youtubeVideoId && adCreative.imageUrl) {
                        console.log(`🔄 Fallback: Checking API image URL for YouTube pattern`);
                        const youtubeThumbnailMatch = adCreative.imageUrl.match(/\/vi\/([^\/]+)\//);
                        if (youtubeThumbnailMatch && youtubeThumbnailMatch[1]) {
                            youtubeVideoId = youtubeThumbnailMatch[1];
                            actualVideoUrl = `https://www.youtube.com/watch?v=${youtubeVideoId}`;
                            videoThumbnailUrl = adCreative.imageUrl;
                            
                            console.log(`✅ FALLBACK SUCCESS! YouTube ID from API: ${youtubeVideoId}`);
                            console.log(`🔄 Constructed YouTube URL: ${actualVideoUrl}`);
                            
                            // Update adCreative with constructed YouTube URL
                            adCreative.videoUrl = actualVideoUrl;
                            adCreative.youtubeId = youtubeVideoId;
                            
                            console.log(`📦 Updated adCreative (fallback):`, {
                                videoUrl: adCreative.videoUrl,
                                youtubeId: adCreative.youtubeId
                            });
                        }
                    }
                    
                    // Method 3: Final fallback - use creative ID if no YouTube found
                    if (!youtubeVideoId) {
                        console.log(`⚠️  No YouTube URL found for video ad ${creativeId}, using creative ID`);
                        youtubeVideoId = `video_${creativeId.substring(creativeId.length - 8)}`; // Last 8 chars
                    }
                    
                } else if (adCreative.hasIframe) {
                    // For iframe content, replace complex URL with user-friendly message
                    console.log(`🖼️  Iframe content detected for ${creativeId}, replacing with user-friendly message`);
                    adCreative.videoUrl = 'Check GATC link';
                    adCreative.imageUrl = 'Check GATC link';
                }
                
                // Enhanced ad object with competitive features
                const adObject = {
                    // Core fields (parity)
                    advertiserName: advertiserName,
                    adCreative: adCreative,
                    format: format,
                    region: regionParam,
                    searchRegion: searchRegion,              // NEW: User's search filter region
                    firstSeenDate: firstSeenDate,
                    lastSeenDate: lastSeenDate,
                    gatcLink: gatcLink,
                    
                    // COMPETITIVE ADVANTAGES (what competitor has)
                    formatCode: formatCode,                // "format" (numeric)
                    adType: format,                        // "ad_type" (same as format)
                    imageUrl: adCreative.imageUrl,         // "image_url" (direct access)
                    youtubeVideoId: youtubeVideoId || adCreative.youtubeId,        // "youtube_video_id"
                    videoThumbnailUrl: videoThumbnailUrl || adCreative.imageUrl,  // "video_thumbnail_url"
                    
                    // YOUR UNIQUE ADVANTAGES (what competitor doesn't have)
                    hasInteractiveContent: adCreative.hasIframe,
                    campaignDuration: (() => {
                        try {
                            return calculateCampaignDuration(firstSeenDate, lastSeenDate);
                        } catch (e) {
                            console.warn(`⚠️  Campaign duration calculation failed for ${creativeId}:`, e.message);
                            return 'Unknown';
                        }
                    })(),
                    creativeDimensions: (() => {
                        try {
                            return extractImageDimensions(adCreative.imageUrl);
                        } catch (e) {
                            console.warn(`⚠️  Image dimensions extraction failed for ${creativeId}:`, e.message);
                            return 'Unknown';
                        }
                    })(),
                    
                    // Technical metadata
                    apiData: {
                        advertiserId: advertiserId,         // "advertiser_id" 
                        creativeId: creativeId,            // "creative_id"
                        formatCode: formatCode
                    }
                };
                
                parsedAds.push(adObject);
                successCount++;
                console.log(`✅ Parsed SearchCreatives ad ${successCount}/${ads.length}: ${advertiserId}/${creativeId} - ${format} - ${advertiserName}`);
                
            } catch (error) {
                errorCount++;
                console.error(`❌ Error parsing individual SearchCreatives ad ${errorCount} (${ad["1"]}/${ad["2"]}):`, error);
                console.error(`📊 Ad data that failed:`, {
                    advertiserId: ad["1"],
                    creativeId: ad["2"], 
                    formatCode: ad["4"],
                    advertiserName: ad["12"],
                    hasCreativeData: !!ad["3"],
                    creativeDataKeys: ad["3"] ? Object.keys(ad["3"]) : null
                });
                // Continue processing other ads instead of stopping
            }
        }
        
        console.log(`✅ SearchCreatives parsing complete: ${successCount} success, ${errorCount} errors, ${skipCount} skipped out of ${ads.length} total`);
        console.log(`Found ${parsedAds.length} ads`);
        
        return parsedAds;
        
    } catch (error) {
        console.error('❌ Error in parseSearchCreativesAPIResponse:', error);
        return [];
    }
}

// Helper function to calculate campaign duration
function calculateCampaignDuration(firstSeenDate, lastSeenDate) {
    try {
        if (!firstSeenDate || !lastSeenDate) return 'Unknown';
        
        const first = new Date(firstSeenDate);
        const last = new Date(lastSeenDate);
        const diffTime = Math.abs(last - first);
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return 'Same day';
        if (diffDays === 1) return '1 day';
        if (diffDays < 30) return `${diffDays} days`;
        if (diffDays < 365) return `${Math.round(diffDays / 30)} months`;
        return `${Math.round(diffDays / 365)} years`;
    } catch (error) {
        console.error('Error calculating campaign duration:', error);
        return 'Unknown';
    }
}

// Helper function to extract image dimensions from URL
function extractImageDimensions(imageUrl) {
    try {
        if (!imageUrl) return 'Unknown';
        
        // Look for width/height patterns in Google's image URLs
        const dimensionMatch = imageUrl.match(/(?:width[=:](\d+).*?height[=:](\d+))|(?:height[=:](\d+).*?width[=:](\d+))|(?:w(\d+).*?h(\d+))|(?:h(\d+).*?w(\d+))/i);
        
        if (dimensionMatch) {
            const width = dimensionMatch[1] || dimensionMatch[4] || dimensionMatch[6] || dimensionMatch[8];
            const height = dimensionMatch[2] || dimensionMatch[3] || dimensionMatch[5] || dimensionMatch[7];
            
            if (width && height) {
                return `${width}x${height}`;
            }
        }
        
        // Fallback: look for common dimension patterns
        const commonDimensions = imageUrl.match(/(\d{2,4})[x×](\d{2,4})/);
        if (commonDimensions) {
            return `${commonDimensions[1]}x${commonDimensions[2]}`;
        }
        
        return 'Unknown';
    } catch (error) {
        console.error('Error extracting image dimensions:', error);
        return 'Unknown';
    }
}
}