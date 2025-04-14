/**
 * Isolated Stock Ticker Implementation
 * Uses YFinance backend when available, with fallback to static data
 */

// Configuration - requested stock symbols
const STOCK_SYMBOLS = [
  'BTC-USD', 'SPY', 'GME', 'AAPL', 'MSFT', 
  'NVDA', 'XRP-USD', 'META', 'TSLA', 'GOOGL', 'PLTR'
];

// YFinance backend configuration
// Instead of hardcoding full URLs, use relative paths that work in both environments
const API_PATH = '/api/yfinance';  // This will be proxied by your webserver in production
const isLocalHost = typeof window !== 'undefined' && 
                   (window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1');

// Use our API proxy server with full URL instead of relative path
const BACKEND_URL = isLocalHost ? 'http://localhost:8002' : 'https://akashpatelresume.us/api-proxy';

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
  console.log("Initializing isolated stock ticker...");
  
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
    fetchYFinanceData(tickerElement);
  }
  
  // Set up refresh interval - shorter in development
  const isDevEnvironment = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
  const refreshInterval = isDevEnvironment ? DEV_REFRESH_INTERVAL : REFRESH_INTERVAL;
  
  setInterval(() => {
    if (!usingFallbackMode) {
      fetchYFinanceData(tickerElement);
    } else {
      updateWithRandomizedData(tickerElement);
    }
  }, refreshInterval);
}

/**
 * Render ticker with initial static data
 */
function renderTickerWithStaticData(tickerElement) {
  const staticData = getStaticStockData();
  renderTicker(tickerElement, staticData);
}

/**
 * Get static stock data for all symbols
 */
function getStaticStockData() {
  return [
    { symbol: 'BTC-USD', price: '67540.28', change: '+2310.45', changePercent: '+3.54%' },
    { symbol: 'SPY', price: '511.34', change: '+1.23', changePercent: '+0.24%' },
    { symbol: 'GME', price: '25.50', change: '+0.42', changePercent: '+1.67%' }, // Updated GME price
    { symbol: 'AAPL', price: '175.34', change: '+1.23', changePercent: '+0.71%' },
    { symbol: 'MSFT', price: '428.79', change: '+3.45', changePercent: '+0.81%' },
    { symbol: 'NVDA', price: '920.16', change: '+12.56', changePercent: '+1.38%' },
    { symbol: 'XRP-USD', price: '0.5072', change: '+0.0023', changePercent: '+0.46%' },
    { symbol: 'META', price: '500.21', change: '+5.84', changePercent: '+1.18%' },
    { symbol: 'TSLA', price: '171.83', change: '-3.42', changePercent: '-1.95%' },
    { symbol: 'GOOGL', price: '168.21', change: '+2.56', changePercent: '+1.54%' },
    { symbol: 'PLTR', price: '23.42', change: '+0.34', changePercent: '+1.47%' }
  ];
}

/**
 * Attempt to fetch data from YFinance backend
 */
async function fetchYFinanceData(tickerElement) {
  try {
    console.log(`Attempting to fetch data from backend at ${BACKEND_URL}...`);
    
    // Always use full URLs with the proxy server
    const healthEndpoint = `${BACKEND_URL}/health`;
    const quotesEndpoint = `${BACKEND_URL}/api/quotes`;
    
    console.log(`Health check endpoint: ${healthEndpoint}`);
    console.log(`Quotes endpoint: ${quotesEndpoint}`);
    
    // First check if backend is available with a health check
    const healthResponse = await Promise.race([
      fetch(healthEndpoint).then(response => response.ok),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 2000))
    ]).catch(() => false);
    
    if (!healthResponse) {
      console.warn(`YFinance backend at ${healthEndpoint} not available, falling back to static data`);
      apiFailureCount++;
      checkFailureStatus(tickerElement);
      return;
    }
    
    // Fetch data from backend
    console.log(`Fetching quotes from: ${quotesEndpoint}`);
    const response = await Promise.race([
      fetch(quotesEndpoint),
      new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 5000))
    ]);
    
    if (!response.ok) {
      throw new Error(`Server responded with status: ${response.status}`);
    }
    
    const data = await response.json();
    
    if (Array.isArray(data) && data.length > 0) {
      console.log(`Successfully fetched market data from YFinance backend`);
      
      // Process data to match our format
      const processedData = data.map(item => {
        // Convert "BTC" to "BTC-USD" format if needed
        const symbol = item.symbol === 'BTC' ? 'BTC-USD' : 
                       item.symbol === 'XRP' ? 'XRP-USD' : 
                       item.symbol === 'ETH' ? 'ETH-USD' : 
                       item.symbol === 'DOGE' ? 'DOGE-USD' : item.symbol;
        
        return {
          symbol: symbol,
          price: item.price,
          change: item.change,
          changePercent: item.changePercent
        };
      });
      
      // Add a data source indicator to the console (but don't affect the ticker itself)
      console.info(`Stock ticker using live data from backend`);
      
      // Render the data
      renderTicker(tickerElement, processedData);
      
      // Reset failure count since we got data successfully
      apiFailureCount = 0;
      usingFallbackMode = false;
    } else {
      console.warn("YFinance backend returned no data");
      apiFailureCount++;
      checkFailureStatus(tickerElement);
    }
  } catch (error) {
    console.error(`Error fetching from YFinance backend:`, error);
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
  // We now use YFinance backend instead - route to that function if called
  if (!usingFallbackMode) {
    fetchYFinanceData(tickerElement);
  } else {
    updateWithRandomizedData(tickerElement);
  }
}

/**
 * Get static data for a specific symbol
 */
function getStaticDataForSymbol(symbol) {
  const allStaticData = getStaticStockData();
  return allStaticData.find(item => item.symbol === symbol);
}

/**
 * Update ticker with randomized data variations
 */
function updateWithRandomizedData(tickerElement) {
  const baseData = getStaticStockData();
  
  const randomizedData = baseData.map(stock => {
    const newStock = { ...stock };
    const basePrice = parseFloat(stock.price);
    const randomPercent = (Math.random() * 4 - 2) / 100; // -2% to +2%
    const newPrice = basePrice * (1 + randomPercent);
    const changeAmount = newPrice - basePrice;
    
    newStock.price = newPrice.toFixed(2);
    newStock.change = (changeAmount >= 0 ? '+' : '') + changeAmount.toFixed(2);
    newStock.changePercent = (changeAmount >= 0 ? '+' : '') + (randomPercent * 100).toFixed(2) + '%';
    
    return newStock;
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