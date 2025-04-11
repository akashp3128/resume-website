/**
 * Backup Stock Ticker for Resume Website
 * Uses local data only - doesn't require API calls
 */

// Configuration - same symbols as the main ticker
const STOCK_SYMBOLS = [
  'BTC-USD', 'SPY', 'GME', 'AAPL', 'MSFT', 
  'NVDA', 'XRP-USD', 'META', 'TSLA', 'GOOGL', 'PLTR'
];

/**
 * Initialize the stock ticker
 */
function initStockTicker() {
  console.log("Backup stock ticker initialization started");
  
  // Get reference to DOM element
  const stockTickerElement = document.getElementById('stock-ticker');
  
  // If the element doesn't exist, exit early
  if (!stockTickerElement) {
    console.error("Stock ticker element not found");
    return;
  }
  
  // Populate with static data and add random variations
  updateTickerWithRandomData(stockTickerElement);
  
  // Refresh every 30 seconds with new random variations
  setInterval(() => updateTickerWithRandomData(stockTickerElement), 30000);
}

/**
 * Update the ticker with randomized data
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
  // Clear any existing content
  stockTickerElement.innerHTML = '';
  
  // Create ticker content with double the items to ensure smooth looping
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
}

// Initialize the ticker when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', initStockTicker); 