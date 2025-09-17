"""
API Configuration for Real-time Stock Data
Set your production API keys here for real-time data fetching
"""

import os

# API Keys Configuration
API_KEYS = {
    'finnhub': {
        'key': os.getenv('FINNHUB_API_KEY', 'demo'),  # Get from environment or use demo
        'base_url': 'https://finnhub.io/api/v1',
        'rate_limit': 1.0,  # seconds between calls
        'calls_per_minute': 60
    },
    'alpha_vantage': {
        'key': os.getenv('ALPHA_VANTAGE_API_KEY', 'demo'),
        'base_url': 'https://www.alphavantage.co/query',
        'rate_limit': 12.0,  # 5 calls per minute = 12 seconds between calls
        'calls_per_minute': 5
    },
    'iex_cloud': {
        'key': os.getenv('IEX_CLOUD_API_KEY', 'pk_test'),
        'base_url': 'https://cloud.iexapis.com/stable',
        'rate_limit': 0.5,
        'calls_per_minute': 100
    },
    'polygon': {
        'key': os.getenv('POLYGON_API_KEY', 'demo'),
        'base_url': 'https://api.polygon.io/v2',
        'rate_limit': 12.0,  # Free tier: 5 calls per minute
        'calls_per_minute': 5
    }
}

# Instructions for getting API keys:
API_INSTRUCTIONS = {
    'finnhub': {
        'url': 'https://finnhub.io/register',
        'free_tier': '60 calls/minute',
        'description': 'Real-time stock prices, company profiles, financial data'
    },
    'alpha_vantage': {
        'url': 'https://www.alphavantage.co/support/#api-key',
        'free_tier': '5 calls/minute, 500 calls/day',
        'description': 'Stock prices, technical indicators, fundamental data'
    },
    'iex_cloud': {
        'url': 'https://iexcloud.io/pricing',
        'free_tier': '50,000 calls/month',
        'description': 'Real-time and historical stock data'
    },
    'polygon': {
        'url': 'https://polygon.io/pricing',
        'free_tier': '5 calls/minute',
        'description': 'Real-time stock data, options, forex'
    }
}

def get_api_config():
    """Get API configuration with environment variables"""
    return API_KEYS

def print_api_setup_instructions():
    """Print instructions for setting up API keys"""
    print("\n🔑 API Keys Setup Instructions:")
    print("=" * 50)
    
    for api_name, info in API_INSTRUCTIONS.items():
        print(f"\n{api_name.upper()}:")
        print(f"  URL: {info['url']}")
        print(f"  Free Tier: {info['free_tier']}")
        print(f"  Description: {info['description']}")
        print(f"  Environment Variable: {api_name.upper()}_API_KEY")
    
    print("\n📝 To set up environment variables:")
    print("export FINNHUB_API_KEY='your_key_here'")
    print("export ALPHA_VANTAGE_API_KEY='your_key_here'")
    print("export IEX_CLOUD_API_KEY='your_key_here'")
    print("export POLYGON_API_KEY='your_key_here'")
    
    print("\n💡 Add these to your ~/.bashrc or ~/.zshrc for persistence")

if __name__ == "__main__":
    print_api_setup_instructions()
