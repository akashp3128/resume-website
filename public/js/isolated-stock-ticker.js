/**
 * Crypto Ticker Implementation
 * Uses CoinGecko API data via our MongoDB backend
 */

// Configuration - requested crypto symbols
const CRYPTO_SYMBOLS = [
  'BTC', 'ETH', 'XRP', 'DOGE', 'SOL', 
  'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX'
];

// Backend configuration
// Use localhost direct connection in development, but use the proxied API path in production
const isLocalHost = typeof window !== 'undefined' && 
                   (window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1');

// Update to use the running MongoDB-CoinGecko server on port 3003
const BACKEND_URL = isLocalHost ? 'http://localhost:3003' : '/api/crypto';

// Track API state
let usingFallbackMode = false;
let apiFailureCount = 0;
const MAX_FAILURES = 3;
const REFRESH_INTERVAL = 60000; // 1 minute
const DEV_REFRESH_INTERVAL = 30000; // 30 seconds for development

/**
 * Initialize the crypto ticker
 */
function initCryptoTicker() {
  console.log("Initializing crypto ticker with CoinGecko backend...");
  
  // Get reference to DOM element
  const tickerElement = document.getElementById('stock-ticker');
  
  if (!tickerElement) {
    console.error("Ticker element not found");
    return;
  }
  
  // Start with static data to show something immediately
  renderTickerWithStaticData(tickerElement);
  
  // Then try to get real data
  fetchCryptoData(tickerElement);
  
  // Set up refresh interval - shorter in development
  const isDevEnvironment = isLocalHost;
  const refreshInterval = isDevEnvironment ? DEV_REFRESH_INTERVAL : REFRESH_INTERVAL;
  
  setInterval(() => {
    if (!usingFallbackMode) {
      fetchCryptoData(tickerElement);
    } else {
      updateWithRandomizedData(tickerElement);
    }
  }, refreshInterval);
}

/**
 * Render ticker with initial static data
 */
function renderTickerWithStaticData(tickerElement) {
  const staticData = getStaticCryptoData();
  renderTicker(tickerElement, staticData);
}

/**
 * Get static crypto data for all symbols
 */
function getStaticCryptoData() {
  return [
    { symbol: 'BTC', price: '83174.00', change: '+1232.45', changePercent: '+1.50%' },
    { symbol: 'ETH', price: '1552.87', change: '+32.15', changePercent: '+2.11%' },
    { symbol: 'XRP', price: '2.02', change: '+0.08', changePercent: '+4.12%' },
    { symbol: 'DOGE', price: '0.1585', change: '+0.0054', changePercent: '+3.52%' },
    { symbol: 'SOL', price: '120.88', change: '+3.45', changePercent: '+2.94%' },
    { symbol: 'ADA', price: '0.5280', change: '+0.0142', changePercent: '+2.77%' },
    { symbol: 'DOT', price: '5.23', change: '+0.12', changePercent: '+2.35%' },
    { symbol: 'MATIC', price: '0.4582', change: '+0.0123', changePercent: '+2.76%' },
    { symbol: 'LINK', price: '13.75', change: '+0.32', changePercent: '+2.38%' },
    { symbol: 'AVAX', price: '23.45', change: '+0.67', changePercent: '+2.94%' }
  ];
}

/**
 * Attempt to fetch data from our CoinGecko backend
 */
async function fetchCryptoData(tickerElement) {
  try {
    console.log(`Fetching data from CoinGecko backend at ${BACKEND_URL}...`);
    
    // Define API endpoints
    const healthEndpoint = `${BACKEND_URL}/health`;
    const cryptoEndpoint = `${BACKEND_URL}/api/crypto`;
    
    console.log(`Health check endpoint: ${healthEndpoint}`);
    
    // First check if backend is available with a health check
    const healthResponse = await Promise.race([
      fetch(healthEndpoint).then(response => response.ok),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 2000))
    ]).catch(() => false);
    
    if (!healthResponse) {
      console.warn(`CoinGecko backend at ${healthEndpoint} not available, falling back to static data`);
      apiFailureCount++;
      checkFailureStatus(tickerElement);
      return;
    }
    
    // Fetch data from backend
    console.log(`Fetching crypto from: ${cryptoEndpoint}`);
    const response = await Promise.race([
      fetch(cryptoEndpoint),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
    ]);
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (Array.isArray(data) && data.length > 0) {
      console.log(`Successfully fetched crypto data from CoinGecko backend`, data);
      
      // Process data to match our format
      const processedData = data.map(item => {
        // Format the price with appropriate decimal places
        const price = parseFloat(item.price);
        const formattedPrice = price < 1 ? price.toFixed(4) : price.toFixed(2);
        
        // Calculate change percentage
        const changePercent = item.change_percent_24h || 0;
        const isPositive = changePercent >= 0;
        const formattedChangePercent = (isPositive ? '+' : '') + changePercent.toFixed(2) + '%';
        
        // Estimate change amount based on percentage
        const changeAmount = (price * changePercent / 100);
        const formattedChange = (isPositive ? '+' : '') + 
                               (price < 1 ? changeAmount.toFixed(4) : changeAmount.toFixed(2));
        
        return {
          symbol: item.symbol,
          price: formattedPrice,
          change: formattedChange,
          changePercent: formattedChangePercent
        };
      });
      
      // Log data source
      console.info(`Crypto ticker using live data from CoinGecko backend`);
      
      // Render the data
      renderTicker(tickerElement, processedData);
      
      // Reset failure count since we got data successfully
      apiFailureCount = 0;
      usingFallbackMode = false;
    } else {
      console.warn("CoinGecko backend returned no data");
      apiFailureCount++;
      checkFailureStatus(tickerElement);
    }
  } catch (error) {
    console.error(`Error fetching from CoinGecko backend:`, error);
    apiFailureCount++;
    checkFailureStatus(tickerElement);
  }
}

/**
 * Check if we've hit max failures and should switch to fallback mode
 */
function checkFailureStatus(tickerElement) {
  if (apiFailureCount >= MAX_FAILURES) {
    console.warn('Switching to fallback mode due to API failures');
    usingFallbackMode = true;
    
    // If we don't have data yet, update with randomized data
    updateWithRandomizedData(tickerElement);
  }
}

/**
 * Get static data for a specific symbol
 */
function getStaticDataForSymbol(symbol) {
  const allStaticData = getStaticCryptoData();
  return allStaticData.find(item => item.symbol === symbol);
}

/**
 * Update ticker with randomized data variations
 */
function updateWithRandomizedData(tickerElement) {
  const baseData = getStaticCryptoData();
  
  const randomizedData = baseData.map(crypto => {
    const newCrypto = { ...crypto };
    const basePrice = parseFloat(crypto.price);
    const randomPercent = (Math.random() * 4 - 2) / 100; // -2% to +2%
    const newPrice = basePrice * (1 + randomPercent);
    const changeAmount = newPrice - basePrice;
    
    newCrypto.price = basePrice < 1 ? newPrice.toFixed(4) : newPrice.toFixed(2);
    newCrypto.change = (changeAmount >= 0 ? '+' : '') + 
                       (basePrice < 1 ? changeAmount.toFixed(4) : changeAmount.toFixed(2));
    newCrypto.changePercent = (changeAmount >= 0 ? '+' : '') + (randomPercent * 100).toFixed(2) + '%';
    
    return newCrypto;
  });
  
  renderTicker(tickerElement, randomizedData);
}

/**
 * Render the ticker with provided crypto data
 */
function renderTicker(tickerElement, cryptoData) {
  // Clear existing content
  tickerElement.innerHTML = '';
  
  // Double the items for smooth looping animation
  const tickerContent = [...cryptoData, ...cryptoData].map(crypto => {
    // Parse change and determine if positive
    const change = typeof crypto.change === 'string' ? crypto.change : crypto.change.toString();
    const isPositive = !change.startsWith('-');
    const changeClass = isPositive ? 'positive' : 'negative';
    const changeSymbol = isPositive ? '▲' : '▼';
    
    // Format price - ensure we're using the exact price from the data
    const price = typeof crypto.price === 'string' ? crypto.price : crypto.price.toString();
    
    // Format the change value correctly
    const changeAbs = isPositive ? 
                     (change.startsWith('+') ? change.substring(1) : change) : 
                     change.substring(1);
    
    return `
      <div class="stock-item">
        <span class="stock-symbol">${crypto.symbol}</span>
        <span class="stock-price">$${price}</span>
        <span class="stock-change ${changeClass}">${changeSymbol} ${changeAbs} (${crypto.changePercent})</span>
      </div>
    `;
  }).join('');
  
  tickerElement.innerHTML = tickerContent;
  
  // Set animation duration based on number of items
  const duration = cryptoData.length * 5; // 5 seconds per crypto
  tickerElement.style.animationDuration = `${duration}s`;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initCryptoTicker); 