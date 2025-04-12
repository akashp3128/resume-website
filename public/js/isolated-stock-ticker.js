/**
 * Isolated Stock Ticker Implementation
 * Uses CoinGecko API for cryptocurrency prices, with fallback to static data
 */

// Configuration - requested crypto symbols
const CRYPTO_SYMBOLS = [
  'BTC', 'ETH', 'XRP', 'DOGE', 'SOL', 
  'ADA', 'DOT', 'MATIC', 'LINK', 'AVAX'
];

// CoinGecko backend configuration
// Instead of hardcoding full URLs, use relative paths that work in both environments
const API_PATH = '/api/crypto';  // This will be proxied by your webserver in production
const isLocalHost = typeof window !== 'undefined' && 
                   (window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1');

// Use localhost direct connection in development, but use the proxied API path in production
// Note: We've changed the port to 3003 where our server is now running
const BACKEND_URL = isLocalHost ? 'http://localhost:3003' : API_PATH;

// Track API state
let usingFallbackMode = false;
let apiFailureCount = 0;
const MAX_FAILURES = 3;
const REFRESH_INTERVAL = 120000; // 2 minutes
const DEV_REFRESH_INTERVAL = 30000; // 30 seconds for development

/**
 * Initialize the stock ticker
 */
function initStockTicker() {
  console.log("Initializing crypto ticker with CoinGecko backend...");
  
  // Get reference to DOM element
  const tickerElement = document.getElementById('stock-ticker');
  
  if (!tickerElement) {
    console.error("Stock ticker element not found");
    return;
  }
  
  // Start with static data to show something immediately
  renderTickerWithStaticData(tickerElement);
  
  // Then try to get real data if backend might be available
  if (!usingFallbackMode) {
    fetchCryptoData(tickerElement);
  }
  
  // Set up refresh interval - shorter in development
  const isDevEnvironment = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
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
    { symbol: 'BTC', price: '67540.28', change: '+2310.45', changePercent: '+3.54%' },
    { symbol: 'ETH', price: '3524.12', change: '+105.33', changePercent: '+3.08%' },
    { symbol: 'XRP', price: '0.5072', change: '+0.0023', changePercent: '+0.46%' },
    { symbol: 'DOGE', price: '0.1586', change: '+0.0024', changePercent: '+1.47%' },
    { symbol: 'SOL', price: '120.88', change: '+3.45', changePercent: '+2.94%' },
    { symbol: 'ADA', price: '0.6206', change: '+0.0142', changePercent: '+2.34%' },
    { symbol: 'DOT', price: '3.56', change: '+0.12', changePercent: '+3.49%' },
    { symbol: 'MATIC', price: '0.2182', change: '+0.0045', changePercent: '+2.11%' },
    { symbol: 'LINK', price: '12.55', change: '+0.42', changePercent: '+3.46%' },
    { symbol: 'AVAX', price: '18.95', change: '+0.56', changePercent: '+3.05%' }
  ];
}

/**
 * Attempt to fetch data from CoinGecko backend
 */
async function fetchCryptoData(tickerElement) {
  try {
    console.log(`Attempting to fetch data from CoinGecko backend at ${BACKEND_URL}...`);
    
    // Determine the correct health endpoint path
    const healthEndpoint = isLocalHost ? `${BACKEND_URL}/health` : `${BACKEND_URL}/health`;
    const cryptoEndpoint = isLocalHost ? `${BACKEND_URL}/api/crypto` : `${BACKEND_URL}/crypto`;
    
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
        
        // Estimate change amount based on percentage (since we might not have the exact previous price)
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
      
      // Add a data source indicator to the console (but don't affect the ticker itself)
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
 * Legacy function - attempt to fetch from Alpha Vantage
 * Only kept for backward compatibility, not actually used anymore
 */
async function fetchStockData(tickerElement) {
  // We now use CoinGecko backend instead - route to that function if called
  if (!usingFallbackMode) {
    fetchCryptoData(tickerElement);
  } else {
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
 * Render the ticker with provided stock data
 */
function renderTicker(tickerElement, stockData) {
  // Clear existing content
  tickerElement.innerHTML = '';
  
  // Double the items for smooth looping animation
  const tickerContent = [...stockData, ...stockData].map(stock => {
    // Parse change and determine if positive
    const change = typeof stock.change === 'string' ? stock.change : stock.change.toString();
    const isPositive = !change.startsWith('-');
    const changeClass = isPositive ? 'positive' : 'negative';
    const changeSymbol = isPositive ? '▲' : '▼';
    
    // Format price - ensure we're using the exact price from the data
    const price = typeof stock.price === 'string' ? stock.price : stock.price.toString();
    
    // Format the change value correctly - remove + or - and use the absolute value
    const changeAbs = isPositive ? 
                     (change.startsWith('+') ? change.substring(1) : change) : 
                     change.substring(1);
    
    return `
      <div class="stock-item">
        <span class="stock-symbol">${stock.symbol}</span>
        <span class="stock-price">$${price}</span>
        <span class="stock-change ${changeClass}">${changeSymbol} ${changeAbs} (${stock.changePercent})</span>
      </div>
    `;
  }).join('');
  
  tickerElement.innerHTML = tickerContent;
  
  // Set animation duration based on number of items
  const duration = stockData.length * 5; // 5 seconds per stock
  tickerElement.style.animationDuration = `${duration}s`;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initStockTicker); 