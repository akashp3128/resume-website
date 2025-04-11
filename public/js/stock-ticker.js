/**
 * Stock Ticker for Resume Website
 * Fetches stock data and creates a scrolling ticker similar to Wall Street displays
 */

// Configuration
const STOCK_SYMBOLS = [
  'BTC-USD', 'SPY', 'GME', 'AAPL', 'MSFT', 
  'NVDA', 'XRP-USD', 'META', 'TSLA', 'GOOGL', 'PLTR'
];

// Free API endpoint - Alpha Vantage provides a free tier that allows 5 API requests per minute
// and 500 requests per day. This is sufficient for our demo purposes.
const API_KEY = 'demo'; // Replace with your Alpha Vantage API key for production
const API_ENDPOINT = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE';

// Track failures to determine if we need to switch to backup mode
let apiFailureCount = 0;
const MAX_FAILURES = 3;
let usingBackupMode = false;

/**
 * Initialize the stock ticker
 */
function initStockTicker() {
  console.log("Stock ticker initialization started");
  
  // Get reference to DOM element
  const stockTickerElement = document.getElementById('stock-ticker');
  
  // If the element doesn't exist, exit early
  if (!stockTickerElement) {
    console.error("Stock ticker element not found, initialization failed");
    return;
  }
  
  // Initially use mock data to immediately show something
  populateTickerWithMockData(stockTickerElement);
  
  // Then attempt to fetch real data
  fetchStockData(stockTickerElement);
  
  // Refresh stock data every 2 minutes (120000 ms)
  setInterval(() => {
    if (!usingBackupMode) {
      fetchStockData(stockTickerElement);
    } else {
      updateTickerWithRandomData(stockTickerElement);
    }
  }, 120000);
}

/**
 * Populate ticker with mock data initially
 * This ensures the ticker has content even before API call completes
 */
function populateTickerWithMockData(stockTickerElement) {
  console.log("Populating ticker with mock data");
  const mockData = [
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
  
  renderStockTicker(stockTickerElement, mockData);
}

/**
 * Fetch real stock data from API
 */
async function fetchStockData(stockTickerElement) {
  try {
    const stockData = [];
    let successfulFetches = 0;
    
    // Due to API rate limits, we fetch a subset of stocks
    // Using the first 5 to stay within free tier limits
    const symbolsToFetch = STOCK_SYMBOLS.slice(0, 5);
    
    for (const symbol of symbolsToFetch) {
      try {
        // Use a proxy or direct API call depending on your setup
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
          console.log(`Fetched data for ${symbol}`);
          successfulFetches++;
        } else {
          console.warn(`No data returned for ${symbol}`, data);
          // Add mock data for this symbol to avoid gaps
          const mockEntry = getMockEntryForSymbol(symbol);
          if (mockEntry) {
            stockData.push(mockEntry);
            console.log(`Using mock data for ${symbol}`);
          }
        }
      } catch (err) {
        console.error(`Error fetching data for ${symbol}:`, err);
        // Add mock data on error
        const mockEntry = getMockEntryForSymbol(symbol);
        if (mockEntry) {
          stockData.push(mockEntry);
          console.log(`Using mock data for ${symbol} due to error`);
        }
      }
      
      // Add a small delay between requests to avoid hitting API rate limits
      await new Promise(resolve => setTimeout(resolve, 1500));
    }
    
    if (stockData.length > 0) {
      renderStockTicker(stockTickerElement, stockData);
      
      // Check if we had any successful API fetches
      if (successfulFetches > 0) {
        // Reset failure count on success
        apiFailureCount = 0;
        usingBackupMode = false;
      } else {
        // Increment failure count
        apiFailureCount++;
        console.warn(`API failure count: ${apiFailureCount}/${MAX_FAILURES}`);
        
        // Switch to backup mode if we've exceeded the max failures
        if (apiFailureCount >= MAX_FAILURES) {
          console.warn('Switching to backup mode due to API failures');
          usingBackupMode = true;
          updateTickerWithRandomData(stockTickerElement);
        }
      }
    } else {
      // If we couldn't get any data, increment failure count
      apiFailureCount++;
      console.warn(`API failure count: ${apiFailureCount}/${MAX_FAILURES}`);
      
      // Switch to backup mode if we've exceeded the max failures
      if (apiFailureCount >= MAX_FAILURES) {
        console.warn('Switching to backup mode due to API failures');
        usingBackupMode = true;
        updateTickerWithRandomData(stockTickerElement);
      }
    }
  } catch (error) {
    console.error('Error fetching stock data:', error);
    apiFailureCount++;
    
    // Switch to backup mode if we've exceeded the max failures
    if (apiFailureCount >= MAX_FAILURES) {
      console.warn('Switching to backup mode due to API failures');
      usingBackupMode = true;
      updateTickerWithRandomData(stockTickerElement);
    }
  }
}

/**
 * Get mock data for a specific symbol
 */
function getMockEntryForSymbol(symbol) {
  const mockDataMap = {
    'BTC-USD': { symbol: 'BTC-USD', price: '67540.28', change: '+2310.45', changePercent: '+3.54%' },
    'SPY': { symbol: 'SPY', price: '511.34', change: '+1.23', changePercent: '+0.24%' },
    'GME': { symbol: 'GME', price: '18.29', change: '+0.35', changePercent: '+1.95%' },
    'AAPL': { symbol: 'AAPL', price: '175.34', change: '+1.23', changePercent: '+0.71%' },
    'MSFT': { symbol: 'MSFT', price: '428.79', change: '+3.45', changePercent: '+0.81%' },
    'NVDA': { symbol: 'NVDA', price: '920.16', change: '+12.56', changePercent: '+1.38%' },
    'XRP-USD': { symbol: 'XRP-USD', price: '0.5072', change: '+0.0023', changePercent: '+0.46%' },
    'META': { symbol: 'META', price: '500.21', change: '+5.84', changePercent: '+1.18%' },
    'TSLA': { symbol: 'TSLA', price: '171.83', change: '-3.42', changePercent: '-1.95%' },
    'GOOGL': { symbol: 'GOOGL', price: '168.21', change: '+2.56', changePercent: '+1.54%' },
    'PLTR': { symbol: 'PLTR', price: '23.42', change: '+0.34', changePercent: '+1.47%' }
  };
  
  return mockDataMap[symbol];
}

/**
 * Update the ticker with randomized data (backup mode)
 */
function updateTickerWithRandomData(stockTickerElement) {
  const baseStockData = [
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
  
  // Add random variations to make it look dynamic
  const randomizedData = baseStockData.map(stock => {
    // Create a copy of the stock object
    const newStock = { ...stock };
    
    // Parse the price as a float
    const basePrice = parseFloat(stock.price);
    
    // Generate a random percentage change between -2% and +2%
    const randomPercentage = (Math.random() * 4 - 2) / 100;
    
    // Calculate the new price
    const newPrice = basePrice * (1 + randomPercentage);
    
    // Calculate the change amount
    const changeAmount = newPrice - basePrice;
    
    // Update the stock object
    newStock.price = newPrice.toFixed(2);
    newStock.change = (changeAmount >= 0 ? '+' : '') + changeAmount.toFixed(2);
    newStock.changePercent = (changeAmount >= 0 ? '+' : '') + (randomPercentage * 100).toFixed(2) + '%';
    
    return newStock;
  });
  
  renderStockTicker(stockTickerElement, randomizedData);
}

/**
 * Render the stock ticker with the provided data
 * @param {Element} stockTickerElement - The DOM element for the ticker
 * @param {Array} stockData - Array of stock objects with symbol, price, change, and changePercent
 */
function renderStockTicker(stockTickerElement, stockData) {
  // Clear any existing content (like the loading message)
  stockTickerElement.innerHTML = '';
  
  // Create ticker content with double the items to ensure smooth looping
  // This technique ensures that there's always content to view during animation
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
  
  stockTickerElement.innerHTML = tickerContent;
  
  // Adjust animation duration based on the number of items
  const duration = stockData.length * 5; // 5 seconds per stock symbol
  stockTickerElement.style.animationDuration = `${duration}s`;
  console.log("Stock ticker rendered with", stockData.length, "items");
}

// Initialize the ticker when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initStockTicker); 