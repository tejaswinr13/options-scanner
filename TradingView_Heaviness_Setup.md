# Heaviness % Indicator for TradingView

## Quick Setup Instructions

1. **Open TradingView** and go to any chart
2. **Click Pine Editor** (bottom panel)
3. **Copy and paste** the entire `heaviness_indicator.pine` script
4. **Click "Add to Chart"**

## How It Works

The Heaviness % indicator mimics the strategy from your $LMND analysis:

### Core Logic
- **Low Heaviness (0-15%)** = Potential reversal/buy zone (like your 10% signals)
- **High Heaviness (85-100%)** = Potential sell/exit zone
- **Mid Range (15-85%)** = Neutral/wait zone

### Components
1. **RSI** - Momentum component
2. **Volume Ratio** - Institutional pressure detection
3. **Price Momentum** - Trend direction factor

## Visual Features

- **Green Background** = Buy zone (Heaviness ≤ 15%)
- **Red Background** = Sell zone (Heaviness ≥ 85%)
- **Triangle Signals** = Entry/exit alerts
- **Info Table** = Real-time values (top-right)

## Customizable Settings

- `Buy Threshold` - Default 15% (adjust based on your strategy)
- `Sell Threshold` - Default 85%
- `RSI Length` - Default 14 periods
- `Volume MA Length` - Default 10 periods for volume comparison

## Alerts Setup

1. Right-click the indicator → **"Add Alert"**
2. Choose **"Heaviness Buy Alert"** or **"Heaviness Sell Alert"**
3. Set notification preferences (email, SMS, webhook)

## Strategy Application

Based on your $LMND success pattern:
- **Wait for Heaviness ≤ 15%** before considering entries
- **Look for volume confirmation** (high volume ratio)
- **Exit when Heaviness ≥ 85%** or use your own profit targets
- **Combine with your options scanner** for additional confirmation

## Integration with Options Scanner

This indicator can complement your existing options volume scanner by:
- Identifying reversal zones for options entry timing
- Confirming dark pool activity with heaviness readings
- Adding technical analysis layer to your fundamental options data
