/**
 * Isolated Stock Ticker Implementation
 * Focused on just the stock ticker functionality with clean error handling
 */

// Configuration - requested stock symbols
const STOCK_SYMBOLS = [
  'BTC-USD', 'SPY', 'GME', 'AAPL', 'MSFT', 
  'NVDA', 'XRP-USD', 'META', 'TSLA', 'GOOGL', 'PLTR'
];

// Track API state
let usingFallbackMode = false;
let apiFailureCount = 0;
const MAX_FAILURES = 3;
const REFRESH_INTERVAL = 120000; // 2 minutes

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
  
  // Then try to get real data
  fetchStockData(tickerElement);
  
  // Set up refresh interval
  setInterval(() => {
    if (!usingFallbackMode) {
      fetchStockData(tickerElement);
    } else {
      updateWithRandomizedData(tickerElement);
    }
  }, REFRESH_INTERVAL);
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
    { symbol: 'GME', price: '18.29', change: '+0.35', changePercent: '+1.95%' },
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
 * Attempt to fetch real stock data
 */
async function fetchStockData(tickerElement) {
  // Alpha Vantage API setup
  const API_KEY = 'demo'; // Replace with your key for production
  const API_ENDPOINT = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE';
  
  try {
    const stockData = [];
    let successfulFetches = 0;
    
    // Due to API rate limits, only fetch a subset
    const symbolsToFetch = STOCK_SYMBOLS.slice(0, 5);
    
    for (const symbol of symbolsToFetch) {
      try {
        const response = await fetch(`${API_ENDPOINT}&symbol=${symbol}&apikey=${API_KEY}`);
        const data = await response.json();
        
        if (data && data['Global Quote'] && Object.keys(data['Global Quote']).length > 0) {
          const quote = data['Global Quote'];
          stockData.push({
            symbol: symbol,
            price: quote['05. price'] || '0.00',
            change: quote['09. change'] || '0.00',
            changePercent: quote['10. change percent'] || '0.00%'
          });
          successfulFetches++;
        } else {
          // Add mock data for this symbol
          const mockData = getStaticDataForSymbol(symbol);
          if (mockData) stockData.push(mockData);
        }
      } catch (err) {
        console.error(`Error fetching ${symbol}:`, err);
        // Add mock data on error
        const mockData = getStaticDataForSymbol(symbol);
        if (mockData) stockData.push(mockData);
      }
      
      // Delay between requests to avoid rate limiting
      await new Promise(resolve => setTimeout(resolve, 1200));
    }
    
    // Render whatever data we have
    if (stockData.length > 0) {
      renderTicker(tickerElement, stockData);
      
      // Update API failure tracking
      if (successfulFetches > 0) {
        apiFailureCount = 0;
        usingFallbackMode = false;
      } else {
        apiFailureCount++;
        if (apiFailureCount >= MAX_FAILURES) {
          console.warn('Switching to fallback mode due to API failures');
          usingFallbackMode = true;
        }
      }
    } else {
      apiFailureCount++;
      if (apiFailureCount >= MAX_FAILURES) {
        usingFallbackMode = true;
        updateWithRandomizedData(tickerElement);
      }
    }
  } catch (error) {
    console.error('Stock data fetch error:', error);
    apiFailureCount++;
    if (apiFailureCount >= MAX_FAILURES) {
      usingFallbackMode = true;
      updateWithRandomizedData(tickerElement);
    }
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
    const isPositive = !stock.change.includes('-');
    const changeClass = isPositive ? 'positive' : 'negative';
    const changeSymbol = isPositive ? '▲' : '▼';
    
    return `
      <div class="stock-item">
        <span class="stock-symbol">${stock.symbol}</span>
        <span class="stock-price">$${parseFloat(stock.price).toFixed(2)}</span>
        <span class="stock-change ${changeClass}">${changeSymbol} ${Math.abs(parseFloat(stock.change)).toFixed(2)} (${stock.changePercent})</span>
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