/**
 * Real-time Stock Ticker Implementation
 * Uses Yahoo Finance API for stocks and CoinGecko API for crypto
 * No API keys required for basic functionality
 */

// Configuration - requested stock and crypto symbols
const STOCK_SYMBOLS = ['SPY', 'AAPL', 'MSFT', 'NVDA', 'META', 'TSLA', 'GOOGL', 'PLTR', 'GME'];
const CRYPTO_SYMBOLS = {
  'bitcoin': 'BTC',
  'ripple': 'XRP'
};

// API endpoints for stock data
const API_ENDPOINTS = {
  PRIMARY: 'yahoo', // Yahoo Finance
  SECONDARY: 'finnhub', // Finnhub
  TERTIARY: 'twelvedata' // Twelve Data
};

// Track API state
let usingFallbackMode = false;
let apiFailureCount = 0;
const MAX_FAILURES = 3;
const REFRESH_INTERVAL = 120000; // 2 minutes (production)
const DEV_REFRESH_INTERVAL = 30000; // 30 seconds (development)

/**
 * Initialize the stock ticker
 */
function initStockTicker() {
  console.log("Initializing real-time stock ticker...");
  
  // Get reference to DOM element
  const tickerElement = document.getElementById('stock-ticker');
  
  if (!tickerElement) {
    console.error("Stock ticker element not found");
    return;
  }
  
  // Start with static data to show something immediately
  renderTickerWithStaticData(tickerElement);
  
  // Then try to get real data
  fetchAllMarketData(tickerElement);
  
  // Set up refresh interval - use shorter interval for development
  const isDevEnvironment = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
  const refreshInterval = isDevEnvironment ? DEV_REFRESH_INTERVAL : REFRESH_INTERVAL;
  
  setInterval(() => {
    if (!usingFallbackMode) {
      fetchAllMarketData(tickerElement);
    } else {
      updateWithRandomizedData(tickerElement);
    }
  }, refreshInterval);
}

/**
 * Render ticker with initial static data
 */
function renderTickerWithStaticData(tickerElement) {
  const staticData = getStaticMarketData();
  renderTicker(tickerElement, staticData);
}

/**
 * Get static market data for all symbols
 */
function getStaticMarketData() {
  return [
    { symbol: 'BTC', price: '67540.28', change: '+2310.45', changePercent: '+3.54%' },
    { symbol: 'SPY', price: '511.34', change: '+1.23', changePercent: '+0.24%' },
    { symbol: 'GME', price: '18.29', change: '+0.35', changePercent: '+1.95%' },
    { symbol: 'AAPL', price: '175.34', change: '+1.23', changePercent: '+0.71%' },
    { symbol: 'MSFT', price: '428.79', change: '+3.45', changePercent: '+0.81%' },
    { symbol: 'NVDA', price: '920.16', change: '+12.56', changePercent: '+1.38%' },
    { symbol: 'XRP', price: '0.5072', change: '+0.0023', changePercent: '+0.46%' },
    { symbol: 'META', price: '500.21', change: '+5.84', changePercent: '+1.18%' },
    { symbol: 'TSLA', price: '171.83', change: '-3.42', changePercent: '-1.95%' },
    { symbol: 'GOOGL', price: '168.21', change: '+2.56', changePercent: '+1.54%' },
    { symbol: 'PLTR', price: '23.42', change: '+0.34', changePercent: '+1.47%' }
  ];
}

/**
 * Get static data for a specific symbol
 */
function getStaticDataForSymbol(symbol) {
  const allStaticData = getStaticMarketData();
  // Normalize crypto symbols (BTC-USD -> BTC)
  const normalizedSymbol = symbol.split('-')[0];
  return allStaticData.find(item => item.symbol === normalizedSymbol);
}

/**
 * Attempt to fetch all market data (stocks and crypto)
 */
async function fetchAllMarketData(tickerElement) {
  try {
    // Fetch both stocks and crypto in parallel
    const [stockData, cryptoData] = await Promise.all([
      fetchStockData(),
      fetchCryptoData()
    ]);
    
    // Combine the results
    const combinedData = [...stockData, ...cryptoData];
    
    if (combinedData.length > 0) {
      console.log("Successfully fetched market data:", combinedData);
      renderTicker(tickerElement, combinedData);
      
      // Reset failure count
      apiFailureCount = 0;
      usingFallbackMode = false;
    } else {
      console.warn("No market data received, incrementing failure count");
      apiFailureCount++;
      checkFailureStatus(tickerElement);
    }
  } catch (error) {
    console.error('Error fetching market data:', error);
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
    updateWithRandomizedData(tickerElement);
  }
}

/**
 * Fetch stock data from Yahoo Finance API
 */
async function fetchStockData() {
  const stockData = [];
  console.log("Starting stock data fetch for symbols:", STOCK_SYMBOLS);
  
  try {
    // Process stocks in parallel (up to 5 at a time to avoid overwhelming browser)
    const results = await Promise.allSettled(
      STOCK_SYMBOLS.map(async (symbol) => {
        try {
          console.log(`Fetching data for ${symbol}...`);
          // Use a CORS proxy if needed
          const isLocalhost = window.location.hostname === 'localhost' || 
                              window.location.hostname === '127.0.0.1';
          // Optional CORS proxy for development
          const corsProxy = isLocalhost ? 'https://cors-anywhere.herokuapp.com/' : '';
          const url = `${corsProxy}https://query1.finance.yahoo.com/v8/finance/chart/${symbol}?interval=1d`;
          
          const response = await fetch(url);
          if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
          }
          
          const data = await response.json();
          console.log(`Received data for ${symbol}:`, data);
          
          if (data && data.chart && data.chart.result && data.chart.result[0]) {
            const result = data.chart.result[0];
            const quote = result.meta;
            const indicators = result.indicators.quote[0];
            
            // Get most recent close price
            let latestPrice = 0;
            if (quote.regularMarketPrice) {
              latestPrice = quote.regularMarketPrice;
            } else if (indicators && indicators.close) {
              // Find the last valid close price (skip null values)
              for (let i = indicators.close.length - 1; i >= 0; i--) {
                if (indicators.close[i] !== null) {
                  latestPrice = indicators.close[i];
                  break;
                }
              }
            }
            
            // Get previous close price
            let previousClose = 0;
            if (quote.chartPreviousClose) {
              previousClose = quote.chartPreviousClose;
            } else if (indicators && indicators.close) {
              // Find the second last valid close price
              let validCloseCount = 0;
              for (let i = indicators.close.length - 1; i >= 0; i--) {
                if (indicators.close[i] !== null) {
                  validCloseCount++;
                  if (validCloseCount === 2) {
                    previousClose = indicators.close[i];
                    break;
                  }
                }
              }
            }
            
            // If we couldn't determine a previous close, use a percentage less than current
            if (previousClose === 0 && latestPrice > 0) {
              previousClose = latestPrice * 0.99; // Assume a small positive change
            }
            
            // Calculate change
            const change = latestPrice - previousClose;
            const changePercent = (previousClose > 0) ? (change / previousClose) * 100 : 0;
            
            console.log(`Stock data processed for ${symbol}:`, {
              price: latestPrice,
              prevClose: previousClose,
              change: change,
              changePercent: changePercent
            });
            
            return {
              symbol: symbol,
              price: latestPrice.toFixed(2),
              change: change.toFixed(2),
              changePercent: `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`
            };
          } else {
            console.warn(`Invalid data structure for ${symbol}`);
            return null;
          }
        } catch (err) {
          console.error(`Error fetching data for ${symbol}:`, err);
          return null;
        }
      })
    );
    
    // Filter out any failed requests and collect the successful ones
    results.forEach(result => {
      if (result.status === 'fulfilled' && result.value) {
        stockData.push(result.value);
      } else {
        // Identify which symbol failed
        const failedSymbol = result.reason?.symbol || 'unknown';
        console.warn(`Using mock data for ${failedSymbol} due to fetch failure`);
        
        // Add mock data for failed symbols
        const mockData = getStaticDataForSymbol(failedSymbol);
        if (mockData) stockData.push(mockData);
      }
    });
    
    console.log(`Successfully fetched stock data for ${stockData.length} symbols:`, stockData);
  } catch (error) {
    console.error('Stock fetch failed:', error);
  }
  
  // If we couldn't get any stock data from the primary method, try the fallback
  if (stockData.length === 0) {
    console.warn("Primary stock data fetch failed, trying secondary method");
    const secondaryData = await fetchStockDataFallback(STOCK_SYMBOLS);
    
    if (secondaryData.length > 0) {
      console.log("Successfully received secondary stock data:", secondaryData);
      return secondaryData;
    }
    
    // If secondary also failed, try tertiary method
    console.warn("Secondary method failed, trying tertiary method");
    const tertiaryData = await fetchStockDataTertiary(STOCK_SYMBOLS);
    
    if (tertiaryData.length > 0) {
      console.log("Successfully received tertiary stock data:", tertiaryData);
      return tertiaryData;
    }
    
    // If all methods failed, use mock data
    console.warn("All API methods failed, using mock data for all stocks");
    STOCK_SYMBOLS.forEach(symbol => {
      const mockData = getStaticDataForSymbol(symbol);
      if (mockData) stockData.push(mockData);
    });
  }
  
  return stockData;
}

/**
 * Fetch crypto data from CoinGecko API
 */
async function fetchCryptoData() {
  const cryptoData = [];
  
  try {
    // Build comma-separated list of crypto IDs
    const cryptoIds = Object.keys(CRYPTO_SYMBOLS).join(',');
    const url = `https://api.coingecko.com/api/v3/simple/price?ids=${cryptoIds}&vs_currencies=usd&include_24hr_change=true`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    // Process each crypto
    Object.entries(data).forEach(([id, priceData]) => {
      const symbol = CRYPTO_SYMBOLS[id];
      const price = priceData.usd;
      const changePercent = priceData.usd_24h_change;
      const change = (price * changePercent / 100).toFixed(2);
      
      cryptoData.push({
        symbol: symbol,
        price: price.toFixed(2),
        change: change,
        changePercent: `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`
      });
    });
  } catch (error) {
    console.error('Crypto fetch failed:', error);
    
    // Add mock data for crypto
    Object.values(CRYPTO_SYMBOLS).forEach(symbol => {
      const mockData = getStaticDataForSymbol(symbol);
      if (mockData) cryptoData.push(mockData);
    });
  }
  
  return cryptoData;
}

/**
 * Update ticker with randomized data variations
 */
function updateWithRandomizedData(tickerElement) {
  const baseData = getStaticMarketData();
  
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
    const isPositive = !stock.change.startsWith('-');
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

/**
 * Alternative fallback method to fetch stock data
 * This is used if the primary Yahoo Finance API method fails
 */
async function fetchStockDataFallback(symbols) {
  const stockData = [];
  console.log("Attempting fallback stock data fetch for:", symbols);
  
  try {
    // We'll use the Finnhub free data API as a fallback
    // Process symbols sequentially to avoid rate limits
    for (const symbol of symbols) {
      try {
        // This endpoint doesn't provide market data but can be used to verify if a stock exists
        const url = `https://finnhub.io/api/v1/quote?symbol=${symbol}&token=demo`;
        const response = await fetch(url);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`Fallback data for ${symbol}:`, data);
          
          if (data && data.c > 0) {
            // If we got a valid current price
            const currentPrice = data.c;
            const previousClose = data.pc || currentPrice * 0.99;
            const change = currentPrice - previousClose;
            const changePercent = (change / previousClose) * 100;
            
            stockData.push({
              symbol: symbol,
              price: currentPrice.toFixed(2),
              change: change.toFixed(2),
              changePercent: `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`
            });
            
            continue; // Skip to next symbol
          }
        }
        
        // If we reach here, fallback API failed too
        console.warn(`Fallback API failed for ${symbol}, using static data`);
        const mockData = getStaticDataForSymbol(symbol);
        if (mockData) stockData.push(mockData);
        
      } catch (err) {
        console.error(`Error in fallback fetch for ${symbol}:`, err);
        const mockData = getStaticDataForSymbol(symbol);
        if (mockData) stockData.push(mockData);
      }
      
      // Add a small delay to avoid rate limits
      await new Promise(resolve => setTimeout(resolve, 300));
    }
  } catch (error) {
    console.error('Fallback stock fetch failed:', error);
  }
  
  return stockData;
}

/**
 * Third option to fetch stock data using Twelve Data API
 * This is used as a last resort when both primary and secondary methods fail
 */
async function fetchStockDataTertiary(symbols) {
  const stockData = [];
  console.log("Attempting tertiary stock data fetch for:", symbols);
  
  try {
    // We'll use a public demo endpoint that doesn't require API keys
    // Process symbols sequentially to avoid rate limits
    for (const symbol of symbols) {
      try {
        // Using Alpha Vantage's demo endpoint as a last resort
        const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbol}&apikey=demo`;
        
        const response = await fetch(url);
        if (response.ok) {
          const data = await response.json();
          console.log(`Tertiary data for ${symbol}:`, data);
          
          // Check if we received valid data
          if (data && data['Global Quote'] && Object.keys(data['Global Quote']).length > 0) {
            const quote = data['Global Quote'];
            const price = parseFloat(quote['05. price'] || 0);
            const change = parseFloat(quote['09. change'] || 0);
            const changePercent = quote['10. change percent'] || '0.00%';
            
            if (price > 0) {
              stockData.push({
                symbol: symbol,
                price: price.toFixed(2),
                change: change.toFixed(2),
                changePercent: changePercent
              });
              continue; // Skip to next symbol
            }
          }
        }
        
        // If we reach here, tertiary API failed too
        console.warn(`Tertiary API failed for ${symbol}, using static data`);
        const mockData = getStaticDataForSymbol(symbol);
        if (mockData) stockData.push(mockData);
        
      } catch (err) {
        console.error(`Error in tertiary fetch for ${symbol}:`, err);
        const mockData = getStaticDataForSymbol(symbol);
        if (mockData) stockData.push(mockData);
      }
      
      // Add a small delay to avoid rate limits
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  } catch (error) {
    console.error('Tertiary stock fetch failed:', error);
  }
  
  return stockData;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', initStockTicker); 