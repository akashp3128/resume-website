/**
 * Stock Ticker for Resume Website
 * Fetches stock data and creates a scrolling ticker similar to Wall Street displays
 */

// Configuration
const STOCK_SYMBOLS = [
  'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 
  'TSLA', 'NVDA', 'JPM', 'BAC', 'GS',
  'DIS', 'NFLX', 'AMD', 'INTC', 'CSCO'
];

// Free API endpoint - Alpha Vantage provides a free tier that allows 5 API requests per minute
// and 500 requests per day. This is sufficient for our demo purposes.
const API_KEY = 'demo'; // Replace with your Alpha Vantage API key for production
const API_ENDPOINT = 'https://www.alphavantage.co/query?function=GLOBAL_QUOTE';

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
  
  // Refresh stock data every 5 minutes (300000 ms)
  // Real-world implementation would use WebSockets for real-time updates
  setInterval(() => fetchStockData(stockTickerElement), 300000);
}

/**
 * Populate ticker with mock data initially
 * This ensures the ticker has content even before API call completes
 */
function populateTickerWithMockData(stockTickerElement) {
  console.log("Populating ticker with mock data");
  const mockData = [
    { symbol: 'AAPL', price: '175.34', change: '+1.23', changePercent: '+0.71%' },
    { symbol: 'MSFT', price: '328.79', change: '+3.45', changePercent: '+1.06%' },
    { symbol: 'AMZN', price: '130.47', change: '-0.98', changePercent: '-0.75%' },
    { symbol: 'GOOGL', price: '138.21', change: '+2.56', changePercent: '+1.89%' },
    { symbol: 'META', price: '300.21', change: '+5.84', changePercent: '+1.98%' },
    { symbol: 'TSLA', price: '246.83', change: '-3.42', changePercent: '-1.37%' },
    { symbol: 'NVDA', price: '420.16', change: '+12.56', changePercent: '+3.08%' },
    { symbol: 'JPM', price: '145.23', change: '+0.78', changePercent: '+0.54%' },
    { symbol: 'BAC', price: '33.42', change: '-0.34', changePercent: '-1.01%' },
    { symbol: 'GS', price: '342.18', change: '+4.32', changePercent: '+1.28%' }
  ];
  
  renderStockTicker(stockTickerElement, mockData);
}

/**
 * Fetch real stock data from API
 */
async function fetchStockData(stockTickerElement) {
  try {
    const stockData = [];
    
    // Due to API rate limits, we'll only fetch data for 5 stocks
    // In a real implementation with a paid API, you would fetch all stocks in a batch request
    const symbolsToFetch = STOCK_SYMBOLS.slice(0, 5);
    
    for (const symbol of symbolsToFetch) {
      try {
        const response = await fetch(`${API_ENDPOINT}&symbol=${symbol}&apikey=${API_KEY}`);
        const data = await response.json();
        
        if (data && data['Global Quote']) {
          const quote = data['Global Quote'];
          stockData.push({
            symbol: symbol,
            price: quote['05. price'] || '0.00',
            change: quote['09. change'] || '0.00',
            changePercent: quote['10. change percent'] || '0.00%'
          });
        }
      } catch (err) {
        console.error(`Error fetching data for ${symbol}:`, err);
      }
      
      // Add a small delay between requests to avoid hitting API rate limits
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    if (stockData.length > 0) {
      renderStockTicker(stockTickerElement, stockData);
    } else {
      // If we couldn't get any real data, keep the mock data
      console.warn('Could not retrieve real stock data, keeping mock data');
    }
  } catch (error) {
    console.error('Error fetching stock data:', error);
  }
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