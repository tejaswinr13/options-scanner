#!/usr/bin/env python3
"""
News Service
Provides real-time news data for stocks from multiple sources
"""

import yfinance as yf
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import time

class NewsService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_duration = 300  # 5 minutes cache
        
    def get_stock_news(self, symbol: str, limit: int = 10) -> Dict:
        """Get comprehensive news for a stock symbol"""
        try:
            # Check cache first
            cache_key = f"{symbol}_{limit}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            news_data = {
                'symbol': symbol,
                'news': [],
                'summary': {
                    'total_articles': 0,
                    'sentiment_score': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            # Get news from Yahoo Finance
            yahoo_news = self._get_yahoo_news(symbol, limit)
            news_data['news'].extend(yahoo_news)
            
            # Get additional news from other sources
            additional_news = self._get_additional_news(symbol, limit // 2)
            news_data['news'].extend(additional_news)
            
            # If we don't have enough news, get general market news
            if len(news_data['news']) < 3:
                market_news = self._get_fallback_market_news(symbol, 5)
                news_data['news'].extend(market_news)
            
            # Sort by date and limit
            news_data['news'] = sorted(
                news_data['news'], 
                key=lambda x: x.get('published_date', ''), 
                reverse=True
            )[:limit]
            
            # Calculate summary
            news_data['summary']['total_articles'] = len(news_data['news'])
            news_data['summary']['sentiment_score'] = self._calculate_sentiment_score(news_data['news'])
            
            # Cache the result
            self._cache_data(cache_key, news_data)
            
            return news_data
            
        except Exception as e:
            self.logger.error(f'Error getting news for {symbol}: {str(e)}')
            return {'error': str(e)}
    
    def _get_yahoo_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get news from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news
            
            yahoo_news = []
            for article in news[:limit]:
                # Extract content from nested structure
                content = article.get('content', article)
                
                title = content.get('title', 'No title')
                summary = content.get('summary', content.get('description', ''))
                
                # Get URL from multiple possible locations
                url = ''
                if 'canonicalUrl' in content:
                    url = content['canonicalUrl'].get('url', '')
                elif 'clickThroughUrl' in content:
                    url = content['clickThroughUrl'].get('url', '')
                elif 'link' in article:
                    url = article.get('link', '')
                
                # Get thumbnail URL
                thumbnail_url = ''
                if 'thumbnail' in content and content['thumbnail']:
                    resolutions = content['thumbnail'].get('resolutions', [])
                    if resolutions and len(resolutions) > 0:
                        thumbnail_url = resolutions[0].get('url', '')
                
                # Get publish date
                pub_date = content.get('pubDate') or content.get('displayTime') or article.get('providerPublishTime')
                
                news_item = {
                    'title': title,
                    'summary': summary,
                    'url': url,
                    'source': 'Yahoo Finance',
                    'published_date': self._format_timestamp(pub_date),
                    'thumbnail': thumbnail_url,
                    'sentiment': self._analyze_sentiment(title + ' ' + summary),
                    'type': 'yahoo'
                }
                yahoo_news.append(news_item)
            
            return yahoo_news
            
        except Exception as e:
            self.logger.error(f'Error getting Yahoo news for {symbol}: {str(e)}')
            return []
    
    def _get_additional_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get news from additional sources using real APIs"""
        try:
            additional_news = []
            
            # Get real-time news from multiple sources
            real_time_articles = self._get_real_time_news_feeds(symbol, limit)
            additional_news.extend(real_time_articles)
            
            # Get news from MarketWatch scraping
            marketwatch_articles = self._scrape_marketwatch_news(symbol)
            additional_news.extend(marketwatch_articles)
            
            # Get news from financial websites
            website_articles = self._scrape_financial_websites(symbol)
            additional_news.extend(website_articles)
            
            return additional_news[:limit]
            
        except Exception as e:
            self.logger.error(f'Error getting additional news for {symbol}: {str(e)}')
            return []
    
    def _get_fallback_market_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get general market news as fallback"""
        try:
            # Get general market news from Yahoo Finance
            ticker = yf.Ticker("^GSPC")  # S&P 500 for general market news
            news = ticker.news
            
            fallback_news = []
            for article in news[:limit]:
                content = article.get('content', article)
                
                title = content.get('title', 'Market Update')
                summary = content.get('summary', content.get('description', ''))
                
                url = ''
                if 'canonicalUrl' in content:
                    url = content['canonicalUrl'].get('url', '')
                elif 'clickThroughUrl' in content:
                    url = content['clickThroughUrl'].get('url', '')
                
                pub_date = content.get('pubDate') or content.get('displayTime')
                
                news_item = {
                    'title': f"{title} (Market News)",
                    'summary': summary,
                    'url': url,
                    'source': 'Yahoo Finance - Market',
                    'published_date': self._format_timestamp(pub_date),
                    'thumbnail': '',
                    'sentiment': self._analyze_sentiment(title + ' ' + summary),
                    'type': 'market'
                }
                fallback_news.append(news_item)
            
            return fallback_news
            
        except Exception as e:
            self.logger.error(f'Error getting fallback market news: {str(e)}')
            return []
    
    def _get_newsapi_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get news from NewsAPI.org (free tier available)"""
        try:
            # NewsAPI free tier - you can get an API key at https://newsapi.org/
            # For demo purposes, using a search without API key (limited results)
            
            # Search for stock-related news using web scraping approach
            search_terms = [
                f'{symbol} stock',
                f'{symbol} earnings',
                f'{symbol} financial',
                f'{symbol} market'
            ]
            
            news_articles = []
            
            # Use requests to get news from financial news websites
            for term in search_terms[:2]:  # Limit to avoid rate limiting
                try:
                    # Search MarketWatch
                    marketwatch_articles = self._scrape_marketwatch_news(symbol)
                    news_articles.extend(marketwatch_articles)
                    
                    # Search Yahoo Finance (already implemented)
                    break  # Use existing Yahoo Finance integration
                    
                except Exception as e:
                    self.logger.error(f'Error scraping news for {term}: {str(e)}')
                    continue
            
            return news_articles[:limit]
            
        except Exception as e:
            self.logger.error(f'Error getting NewsAPI news for {symbol}: {str(e)}')
            return []
    
    def _scrape_marketwatch_news(self, symbol: str) -> List[Dict]:
        """Scrape recent news from MarketWatch"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # MarketWatch stock page
            url = f'https://www.marketwatch.com/investing/stock/{symbol.lower()}'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            news_articles = []
            
            # Find news articles from MarketWatch
            news_elements = soup.find_all('div', class_='article__content')[:3]
            
            for element in news_elements:
                try:
                    title_elem = element.find('h3') or element.find('h2') or element.find('a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link_elem = element.find('a')
                        url_link = link_elem.get('href', '') if link_elem else ''
                        
                        if title and len(title) > 10:
                            # Get summary if available
                            summary_elem = element.find('p')
                            summary = summary_elem.get_text().strip()[:200] if summary_elem else f'Latest news about {symbol} from MarketWatch'
                            
                            article = {
                                'title': title,
                                'summary': summary,
                                'url': url_link if url_link.startswith('http') else f'https://www.marketwatch.com{url_link}',
                                'source': 'MarketWatch',
                                'published_date': datetime.now().isoformat(),
                                'thumbnail': '',
                                'sentiment': self._analyze_sentiment(title + ' ' + summary),
                                'type': 'marketwatch'
                            }
                            news_articles.append(article)
                except Exception as e:
                    continue
            
            return news_articles
            
        except Exception as e:
            self.logger.error(f'Error scraping MarketWatch for {symbol}: {str(e)}')
            return []
    
    def _get_real_time_news_feeds(self, symbol: str, limit: int) -> List[Dict]:
        """Get real-time news from multiple RSS feeds and sources"""
        try:
            import requests
            from bs4 import BeautifulSoup
            import xml.etree.ElementTree as ET
            
            news_articles = []
            
            # RSS feeds for financial news
            rss_feeds = [
                f'https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US',
                'https://feeds.reuters.com/reuters/businessNews',
                'https://feeds.bloomberg.com/markets/news.rss',
                'https://feeds.cnbc.com/cnbc/world'
            ]
            
            for feed_url in rss_feeds[:2]:  # Limit to avoid timeouts
                try:
                    response = requests.get(feed_url, timeout=5)
                    if response.status_code == 200:
                        articles = self._parse_rss_feed(response.content, symbol)
                        news_articles.extend(articles)
                except Exception as e:
                    self.logger.error(f'Error fetching RSS feed {feed_url}: {str(e)}')
                    continue
            
            # Get news from financial websites
            website_news = self._scrape_financial_websites(symbol)
            news_articles.extend(website_news)
            
            # Sort by date and return limited results
            news_articles = sorted(
                news_articles, 
                key=lambda x: x.get('published_date', ''), 
                reverse=True
            )[:limit]
            
            return news_articles
            
        except Exception as e:
            self.logger.error(f'Error getting real-time news feeds for {symbol}: {str(e)}')
            return []
    
    def _parse_rss_feed(self, rss_content: bytes, symbol: str) -> List[Dict]:
        """Parse RSS feed content"""
        try:
            import xml.etree.ElementTree as ET
            from datetime import datetime
            
            root = ET.fromstring(rss_content)
            articles = []
            
            # Find all item elements
            for item in root.findall('.//item')[:5]:  # Limit to 5 items per feed
                try:
                    title = item.find('title').text if item.find('title') is not None else ''
                    description = item.find('description').text if item.find('description') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else ''
                    pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    
                    # Check if article is relevant to the symbol
                    if symbol.upper() in title.upper() or symbol.upper() in description.upper():
                        article = {
                            'title': title,
                            'summary': description[:300] if description else '',
                            'url': link,
                            'source': 'RSS Feed',
                            'published_date': pub_date or datetime.now().isoformat(),
                            'thumbnail': '',
                            'sentiment': self._analyze_sentiment(title + ' ' + description),
                            'type': 'rss'
                        }
                        articles.append(article)
                except Exception as e:
                    continue
            
            return articles
            
        except Exception as e:
            self.logger.error(f'Error parsing RSS feed: {str(e)}')
            return []
    
    def _scrape_financial_websites(self, symbol: str) -> List[Dict]:
        """Scrape news from financial websites"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            news_articles = []
            
            # Scrape from Seeking Alpha
            seeking_alpha_articles = self._scrape_seeking_alpha(symbol)
            news_articles.extend(seeking_alpha_articles)
            
            # Scrape from Yahoo Finance (additional to API)
            yahoo_web_articles = self._scrape_yahoo_finance_web(symbol)
            news_articles.extend(yahoo_web_articles)
            
            return news_articles
            
        except Exception as e:
            self.logger.error(f'Error scraping financial websites for {symbol}: {str(e)}')
            return []
    
    def _scrape_seeking_alpha(self, symbol: str) -> List[Dict]:
        """Scrape news from Seeking Alpha"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = f'https://seekingalpha.com/symbol/{symbol.upper()}/news'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find article elements (simplified)
            article_elements = soup.find_all('article')[:3]
            
            for article in article_elements:
                try:
                    title_elem = article.find('h3') or article.find('h2')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link_elem = article.find('a')
                        url_link = link_elem.get('href', '') if link_elem else ''
                        
                        if title and len(title) > 10:
                            article_data = {
                                'title': title,
                                'summary': f'Analysis and insights about {symbol} from Seeking Alpha',
                                'url': f'https://seekingalpha.com{url_link}' if url_link.startswith('/') else url_link,
                                'source': 'Seeking Alpha',
                                'published_date': datetime.now().isoformat(),
                                'thumbnail': '',
                                'sentiment': self._analyze_sentiment(title),
                                'type': 'seeking_alpha'
                            }
                            articles.append(article_data)
                except Exception as e:
                    continue
            
            return articles
            
        except Exception as e:
            self.logger.error(f'Error scraping Seeking Alpha for {symbol}: {str(e)}')
            return []
    
    def _scrape_yahoo_finance_web(self, symbol: str) -> List[Dict]:
        """Scrape additional news from Yahoo Finance web interface"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            url = f'https://finance.yahoo.com/quote/{symbol}/news'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = []
            
            # Find news items
            news_items = soup.find_all('div', {'data-test-locator': 'mega'})[:3]
            
            for item in news_items:
                try:
                    title_elem = item.find('h3') or item.find('a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link_elem = item.find('a')
                        url_link = link_elem.get('href', '') if link_elem else ''
                        
                        if title and len(title) > 10:
                            article_data = {
                                'title': title,
                                'summary': f'Latest {symbol} news from Yahoo Finance',
                                'url': url_link if url_link.startswith('http') else f'https://finance.yahoo.com{url_link}',
                                'source': 'Yahoo Finance Web',
                                'published_date': datetime.now().isoformat(),
                                'thumbnail': '',
                                'sentiment': self._analyze_sentiment(title),
                                'type': 'yahoo_web'
                            }
                            articles.append(article_data)
                except Exception as e:
                    continue
            
            return articles
            
        except Exception as e:
            self.logger.error(f'Error scraping Yahoo Finance web for {symbol}: {str(e)}')
            return []
    
    def _get_alpha_vantage_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get news from Alpha Vantage API"""
        try:
            # Alpha Vantage requires API key - for demo, return empty
            # To implement: get API key from https://www.alphavantage.co/support/#api-key
            
            # Example implementation:
            # api_key = 'YOUR_ALPHA_VANTAGE_API_KEY'
            # url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&apikey={api_key}'
            # response = requests.get(url)
            # data = response.json()
            # return self._parse_alpha_vantage_news(data, limit)
            
            return []
            
        except Exception as e:
            self.logger.error(f'Error getting Alpha Vantage news for {symbol}: {str(e)}')
            return []
    
    def _get_finnhub_news(self, symbol: str, limit: int) -> List[Dict]:
        """Get news from Finnhub API"""
        try:
            # Finnhub offers free tier - get API key from https://finnhub.io/
            # For demo purposes, using a mock implementation
            
            # Example implementation:
            # api_key = 'YOUR_FINNHUB_API_KEY'
            # url = f'https://finnhub.io/api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}&token={api_key}'
            # response = requests.get(url)
            # data = response.json()
            # return self._parse_finnhub_news(data, limit)
            
            return []
            
        except Exception as e:
            self.logger.error(f'Error getting Finnhub news for {symbol}: {str(e)}')
            return []
    
    def _analyze_sentiment(self, text: str) -> float:
        """Basic sentiment analysis (mock implementation)"""
        try:
            if not text:
                return 0.0
            
            # Simple keyword-based sentiment analysis
            positive_words = ['gain', 'rise', 'up', 'bull', 'positive', 'growth', 'strong', 'beat', 'exceed', 'outperform']
            negative_words = ['fall', 'drop', 'down', 'bear', 'negative', 'decline', 'weak', 'miss', 'underperform', 'loss']
            
            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            total_words = len(text.split())
            if total_words == 0:
                return 0.0
            
            sentiment_score = (positive_count - negative_count) / max(total_words, 1)
            return max(-1.0, min(1.0, sentiment_score * 10))  # Scale and clamp
            
        except Exception as e:
            self.logger.error(f'Error analyzing sentiment: {str(e)}')
            return 0.0
    
    def _calculate_sentiment_score(self, news_list: List[Dict]) -> float:
        """Calculate overall sentiment score from news articles"""
        try:
            if not news_list:
                return 0.0
            
            total_sentiment = sum(article.get('sentiment', 0.0) for article in news_list)
            return total_sentiment / len(news_list)
            
        except Exception as e:
            self.logger.error(f'Error calculating sentiment score: {str(e)}')
            return 0.0
    
    def _format_timestamp(self, timestamp) -> str:
        """Format timestamp to ISO string"""
        try:
            if timestamp is None:
                return datetime.now().isoformat()
            
            if isinstance(timestamp, (int, float)):
                return datetime.fromtimestamp(timestamp).isoformat()
            
            return str(timestamp)
            
        except Exception as e:
            self.logger.error(f'Error formatting timestamp: {str(e)}')
            return datetime.now().isoformat()
    
    def _is_cached(self, cache_key: str) -> bool:
        """Check if data is cached and still valid"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        return (time.time() - cache_time) < self.cache_duration
    
    def _cache_data(self, cache_key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
    
    def get_market_news(self, limit: int = 20) -> Dict:
        """Get general market news"""
        try:
            # Check cache
            cache_key = f"market_news_{limit}"
            if self._is_cached(cache_key):
                return self.cache[cache_key]['data']
            
            market_news = {
                'news': [],
                'summary': {
                    'total_articles': 0,
                    'sentiment_score': 0.0,
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            # Get market news from major indices
            major_symbols = ['SPY', 'QQQ', 'DIA', 'IWM']
            
            for symbol in major_symbols:
                symbol_news = self._get_yahoo_news(symbol, limit // len(major_symbols))
                for article in symbol_news:
                    article['category'] = 'market'
                market_news['news'].extend(symbol_news)
            
            # Sort and limit
            market_news['news'] = sorted(
                market_news['news'], 
                key=lambda x: x.get('published_date', ''), 
                reverse=True
            )[:limit]
            
            # Calculate summary
            market_news['summary']['total_articles'] = len(market_news['news'])
            market_news['summary']['sentiment_score'] = self._calculate_sentiment_score(market_news['news'])
            
            # Cache the result
            self._cache_data(cache_key, market_news)
            
            return market_news
            
        except Exception as e:
            self.logger.error(f'Error getting market news: {str(e)}')
            return {'error': str(e)}
    
    def get_trending_news(self, limit: int = 15) -> Dict:
        """Get trending financial news"""
        try:
            # This would integrate with trending news APIs
            # For now, return a combination of major stock news
            trending_symbols = ['AAPL', 'TSLA', 'NVDA', 'MSFT', 'GOOGL']
            
            trending_news = {
                'news': [],
                'summary': {
                    'total_articles': 0,
                    'trending_topics': [],
                    'last_updated': datetime.now().isoformat()
                }
            }
            
            for symbol in trending_symbols:
                symbol_news = self._get_yahoo_news(symbol, 3)
                for article in symbol_news:
                    article['trending_symbol'] = symbol
                trending_news['news'].extend(symbol_news)
            
            # Sort and limit
            trending_news['news'] = sorted(
                trending_news['news'], 
                key=lambda x: x.get('published_date', ''), 
                reverse=True
            )[:limit]
            
            trending_news['summary']['total_articles'] = len(trending_news['news'])
            trending_news['summary']['trending_topics'] = trending_symbols
            
            return trending_news
            
        except Exception as e:
            self.logger.error(f'Error getting trending news: {str(e)}')
            return {'error': str(e)}

# Global instance
news_service = NewsService()
