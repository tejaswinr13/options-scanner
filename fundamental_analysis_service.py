#!/usr/bin/env python3
"""
Fundamental Analysis Service
Provides comprehensive fundamental analysis including financial metrics, valuation ratios, and forecasting
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from typing import Dict, List, Optional, Any
from sklearn.linear_model import LinearRegression
import warnings
import json
warnings.filterwarnings('ignore')

class FundamentalAnalysisService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_duration = 300  # 5 minutes cache
        self._cache = {}
    
    def _convert_numpy_types(self, obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self._convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_types(item) for item in obj]
        elif pd.isna(obj) or (isinstance(obj, (int, float)) and (np.isnan(obj) or np.isinf(obj))):
            return None
        return obj
        
    def _get_cached_data(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_duration:
                return data
        return None
    
    def _set_cached_data(self, key: str, data: Dict) -> None:
        """Cache data with timestamp"""
        self._cache[key] = (data, time.time())
    
    def get_fundamental_analysis(self, symbol: str) -> Dict:
        """Get comprehensive fundamental analysis for a stock"""
        cache_key = f"fundamental_{symbol}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        try:
            ticker = yf.Ticker(symbol)
            
            # Get basic info
            info = ticker.info
            
            # Get financial statements
            financials = self._get_financial_statements(ticker)
            
            # Calculate key metrics
            key_metrics = self._calculate_key_metrics(info, financials)
            
            # Get valuation ratios
            valuation = self._calculate_valuation_ratios(info, financials)
            
            # Get profitability metrics
            profitability = self._calculate_profitability_metrics(info, financials)
            
            # Get liquidity and solvency
            liquidity = self._calculate_liquidity_metrics(info, financials)
            
            # Get efficiency metrics
            efficiency = self._calculate_efficiency_metrics(info, financials)
            
            # Get growth metrics
            growth = self._calculate_growth_metrics(financials)
            
            # Generate forecasts
            forecasts = self._generate_forecasts(symbol, financials, info)
            
            # Calculate fair value estimates
            fair_value = self._calculate_fair_value(symbol, financials, info)
            
            # Get analyst recommendations
            analyst_data = self._get_analyst_data(ticker)
            
            result = {
                'symbol': symbol,
                'company_name': info.get('longName', symbol),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'current_price': info.get('currentPrice', 0),
                'key_metrics': key_metrics,
                'valuation': valuation,
                'profitability': profitability,
                'liquidity': liquidity,
                'efficiency': efficiency,
                'growth': growth,
                'forecasts': forecasts,
                'fair_value': fair_value,
                'analyst_data': analyst_data,
                'last_updated': datetime.now().isoformat(),
                'recommendation': self._generate_investment_recommendation(
                    key_metrics, valuation, profitability, growth, fair_value, info
                )
            }
            
            # Convert numpy types to native Python types for JSON serialization
            result = self._convert_numpy_types(result)
            
            self._set_cached_data(cache_key, result)
            return result
            
        except Exception as e:
            self.logger.error(f'Error in fundamental analysis for {symbol}: {str(e)}')
            return {'error': str(e), 'symbol': symbol}
    
    def _get_financial_statements(self, ticker) -> Dict:
        """Get financial statements data"""
        try:
            financials = {}
            
            # Income statement
            try:
                income_stmt = ticker.financials
                if not income_stmt.empty:
                    financials['income_statement'] = income_stmt
            except:
                financials['income_statement'] = pd.DataFrame()
            
            # Balance sheet
            try:
                balance_sheet = ticker.balance_sheet
                if not balance_sheet.empty:
                    financials['balance_sheet'] = balance_sheet
            except:
                financials['balance_sheet'] = pd.DataFrame()
            
            # Cash flow
            try:
                cash_flow = ticker.cashflow
                if not cash_flow.empty:
                    financials['cash_flow'] = cash_flow
            except:
                financials['cash_flow'] = pd.DataFrame()
            
            return financials
            
        except Exception as e:
            self.logger.error(f'Error getting financial statements: {str(e)}')
            return {}
    
    def _calculate_key_metrics(self, info: Dict, financials: Dict) -> Dict:
        """Calculate key financial metrics"""
        try:
            metrics = {}
            
            # Basic metrics from info
            metrics['eps_ttm'] = info.get('trailingEps', 0)
            metrics['eps_forward'] = info.get('forwardEps', 0)
            metrics['revenue_ttm'] = info.get('totalRevenue', 0)
            metrics['gross_profit'] = info.get('grossProfits', 0)
            metrics['operating_income'] = info.get('operatingIncome', 0)
            metrics['net_income'] = info.get('netIncomeToCommon', 0)
            metrics['total_assets'] = info.get('totalAssets', 0)
            metrics['total_debt'] = info.get('totalDebt', 0)
            metrics['free_cash_flow'] = info.get('freeCashflow', 0)
            metrics['shares_outstanding'] = info.get('sharesOutstanding', 0)
            
            # Calculate additional metrics from financial statements
            if 'income_statement' in financials and not financials['income_statement'].empty:
                income_stmt = financials['income_statement']
                if len(income_stmt.columns) > 0:
                    latest_col = income_stmt.columns[0]
                    
                    # Revenue growth
                    if len(income_stmt.columns) > 1:
                        current_revenue = income_stmt.loc['Total Revenue', latest_col] if 'Total Revenue' in income_stmt.index else 0
                        prev_revenue = income_stmt.loc['Total Revenue', income_stmt.columns[1]] if 'Total Revenue' in income_stmt.index else 0
                        if prev_revenue != 0:
                            metrics['revenue_growth_yoy'] = ((current_revenue - prev_revenue) / prev_revenue) * 100
                        else:
                            metrics['revenue_growth_yoy'] = 0
                    else:
                        metrics['revenue_growth_yoy'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating key metrics: {str(e)}')
            return {}
    
    def _calculate_valuation_ratios(self, info: Dict, financials: Dict) -> Dict:
        """Calculate valuation ratios"""
        try:
            ratios = {}
            
            # P/E ratios
            ratios['pe_ratio_ttm'] = info.get('trailingPE', 0)
            ratios['pe_ratio_forward'] = info.get('forwardPE', 0)
            
            # Price ratios
            ratios['price_to_book'] = info.get('priceToBook', 0)
            ratios['price_to_sales'] = info.get('priceToSalesTrailing12Months', 0)
            ratios['price_to_cash_flow'] = info.get('priceToCashFlow', 0)
            
            # Enterprise ratios
            ratios['ev_to_revenue'] = info.get('enterpriseToRevenue', 0)
            ratios['ev_to_ebitda'] = info.get('enterpriseToEbitda', 0)
            
            # Dividend ratios
            ratios['dividend_yield'] = info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0
            ratios['payout_ratio'] = info.get('payoutRatio', 0) * 100 if info.get('payoutRatio') else 0
            
            # Calculate PEG ratio
            pe_ratio = ratios['pe_ratio_ttm']
            growth_rate = info.get('earningsGrowth', 0) * 100 if info.get('earningsGrowth') else 0
            if pe_ratio > 0 and growth_rate > 0:
                ratios['peg_ratio'] = pe_ratio / growth_rate
            else:
                ratios['peg_ratio'] = 0
            
            return ratios
            
        except Exception as e:
            self.logger.error(f'Error calculating valuation ratios: {str(e)}')
            return {}
    
    def _calculate_profitability_metrics(self, info: Dict, financials: Dict) -> Dict:
        """Calculate profitability metrics"""
        try:
            metrics = {}
            
            # Margin ratios
            metrics['gross_margin'] = info.get('grossMargins', 0) * 100 if info.get('grossMargins') else 0
            metrics['operating_margin'] = info.get('operatingMargins', 0) * 100 if info.get('operatingMargins') else 0
            metrics['profit_margin'] = info.get('profitMargins', 0) * 100 if info.get('profitMargins') else 0
            
            # Return ratios
            metrics['roe'] = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
            metrics['roa'] = info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0
            metrics['roic'] = info.get('returnOnCapital', 0) * 100 if info.get('returnOnCapital') else 0
            
            # Calculate additional metrics
            total_revenue = info.get('totalRevenue', 0)
            if total_revenue > 0:
                ebitda = info.get('ebitda', 0)
                if ebitda > 0:
                    metrics['ebitda_margin'] = (ebitda / total_revenue) * 100
                else:
                    metrics['ebitda_margin'] = 0
            else:
                metrics['ebitda_margin'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating profitability metrics: {str(e)}')
            return {}
    
    def _calculate_liquidity_metrics(self, info: Dict, financials: Dict) -> Dict:
        """Calculate liquidity and solvency metrics"""
        try:
            metrics = {}
            
            # Liquidity ratios
            metrics['current_ratio'] = info.get('currentRatio', 0)
            metrics['quick_ratio'] = info.get('quickRatio', 0)
            
            # Debt ratios
            metrics['debt_to_equity'] = info.get('debtToEquity', 0)
            
            # Calculate additional ratios from balance sheet
            if 'balance_sheet' in financials and not financials['balance_sheet'].empty:
                balance_sheet = financials['balance_sheet']
                if len(balance_sheet.columns) > 0:
                    latest_col = balance_sheet.columns[0]
                    
                    # Working capital
                    current_assets = 0
                    current_liabilities = 0
                    
                    if 'Current Assets' in balance_sheet.index:
                        current_assets = balance_sheet.loc['Current Assets', latest_col]
                    if 'Current Liabilities' in balance_sheet.index:
                        current_liabilities = balance_sheet.loc['Current Liabilities', latest_col]
                    
                    metrics['working_capital'] = current_assets - current_liabilities
                    
                    # Interest coverage ratio
                    operating_income = info.get('operatingIncome', 0)
                    interest_expense = info.get('interestExpense', 0)
                    if interest_expense > 0:
                        metrics['interest_coverage'] = operating_income / interest_expense
                    else:
                        metrics['interest_coverage'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating liquidity metrics: {str(e)}')
            return {}
    
    def _calculate_efficiency_metrics(self, info: Dict, financials: Dict) -> Dict:
        """Calculate efficiency metrics"""
        try:
            metrics = {}
            
            # Turnover ratios
            total_revenue = info.get('totalRevenue', 0)
            total_assets = info.get('totalAssets', 0)
            
            if total_assets > 0:
                metrics['asset_turnover'] = total_revenue / total_assets
            else:
                metrics['asset_turnover'] = 0
            
            # Inventory turnover (if available)
            if 'balance_sheet' in financials and not financials['balance_sheet'].empty:
                balance_sheet = financials['balance_sheet']
                if len(balance_sheet.columns) > 0:
                    latest_col = balance_sheet.columns[0]
                    
                    if 'Inventory' in balance_sheet.index:
                        inventory = balance_sheet.loc['Inventory', latest_col]
                        cost_of_goods = info.get('costOfRevenue', 0)
                        if inventory > 0:
                            metrics['inventory_turnover'] = cost_of_goods / inventory
                        else:
                            metrics['inventory_turnover'] = 0
                    else:
                        metrics['inventory_turnover'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating efficiency metrics: {str(e)}')
            return {}
    
    def _calculate_growth_metrics(self, financials: Dict) -> Dict:
        """Calculate growth metrics"""
        try:
            metrics = {}
            
            # Calculate growth rates from financial statements
            if 'income_statement' in financials and not financials['income_statement'].empty:
                income_stmt = financials['income_statement']
                
                if len(income_stmt.columns) >= 2:
                    # Revenue growth
                    if 'Total Revenue' in income_stmt.index:
                        current = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                        previous = income_stmt.loc['Total Revenue', income_stmt.columns[1]]
                        if previous != 0:
                            metrics['revenue_growth_1y'] = ((current - previous) / previous) * 100
                        else:
                            metrics['revenue_growth_1y'] = 0
                    
                    # EPS growth
                    if 'Basic EPS' in income_stmt.index:
                        current_eps = income_stmt.loc['Basic EPS', income_stmt.columns[0]]
                        previous_eps = income_stmt.loc['Basic EPS', income_stmt.columns[1]]
                        if previous_eps != 0:
                            metrics['eps_growth_1y'] = ((current_eps - previous_eps) / previous_eps) * 100
                        else:
                            metrics['eps_growth_1y'] = 0
                
                # Calculate 3-year CAGR if enough data
                if len(income_stmt.columns) >= 4:
                    if 'Total Revenue' in income_stmt.index:
                        current = income_stmt.loc['Total Revenue', income_stmt.columns[0]]
                        three_years_ago = income_stmt.loc['Total Revenue', income_stmt.columns[3]]
                        if three_years_ago > 0:
                            metrics['revenue_cagr_3y'] = (((current / three_years_ago) ** (1/3)) - 1) * 100
                        else:
                            metrics['revenue_cagr_3y'] = 0
            
            return metrics
            
        except Exception as e:
            self.logger.error(f'Error calculating growth metrics: {str(e)}')
            return {}
    
    def _generate_forecasts(self, symbol: str, financials: Dict, info: Dict) -> Dict:
        """Generate financial forecasts"""
        try:
            forecasts = {}
            
            # Simple linear regression forecast for revenue
            if 'income_statement' in financials and not financials['income_statement'].empty:
                income_stmt = financials['income_statement']
                
                if 'Total Revenue' in income_stmt.index and len(income_stmt.columns) >= 3:
                    revenues = []
                    for col in income_stmt.columns[:4]:  # Last 4 years
                        if 'Total Revenue' in income_stmt.index:
                            revenues.append(income_stmt.loc['Total Revenue', col])
                    
                    if len(revenues) >= 3:
                        # Calculate trend
                        x = np.arange(len(revenues))
                        y = np.array(revenues)
                        
                        # Linear regression
                        slope, intercept = np.polyfit(x, y, 1)
                        
                        # Forecast next year
                        next_year_revenue = slope * len(revenues) + intercept
                        forecasts['revenue_forecast_1y'] = max(0, next_year_revenue)
                        
                        # Calculate growth rate
                        if revenues[0] > 0:
                            forecasts['revenue_growth_forecast'] = ((next_year_revenue - revenues[0]) / revenues[0]) * 100
                        else:
                            forecasts['revenue_growth_forecast'] = 0
            
            # EPS forecast based on analyst estimates
            forward_eps = info.get('forwardEps', 0)
            if forward_eps > 0:
                forecasts['eps_forecast_1y'] = forward_eps
                
                current_eps = info.get('trailingEps', 0)
                if current_eps > 0:
                    forecasts['eps_growth_forecast'] = ((forward_eps - current_eps) / current_eps) * 100
                else:
                    forecasts['eps_growth_forecast'] = 0
            
            # Price target based on P/E expansion
            pe_ratio = info.get('trailingPE', 0)
            if pe_ratio > 0 and forward_eps > 0:
                # Assume P/E remains constant
                forecasts['price_target_pe_based'] = forward_eps * pe_ratio
                
                current_price = info.get('currentPrice', 0)
                if current_price > 0:
                    forecasts['price_target_upside'] = ((forecasts['price_target_pe_based'] - current_price) / current_price) * 100
                else:
                    forecasts['price_target_upside'] = 0
            
            return forecasts
            
        except Exception as e:
            self.logger.error(f'Error generating forecasts: {str(e)}')
            return {}
    
    def _calculate_fair_value(self, symbol: str, financials: Dict, info: Dict) -> Dict:
        """Calculate fair value estimates using multiple methods"""
        try:
            fair_value = {}
            current_price = info.get('currentPrice', 0)
            
            # DCF-based estimate (simplified)
            free_cash_flow = info.get('freeCashflow', 0)
            if free_cash_flow > 0:
                # Assume 5% growth and 10% discount rate
                growth_rate = 0.05
                discount_rate = 0.10
                terminal_growth = 0.02
                
                # 5-year DCF
                dcf_value = 0
                for year in range(1, 6):
                    future_fcf = free_cash_flow * ((1 + growth_rate) ** year)
                    present_value = future_fcf / ((1 + discount_rate) ** year)
                    dcf_value += present_value
                
                # Terminal value
                terminal_fcf = free_cash_flow * ((1 + growth_rate) ** 5) * (1 + terminal_growth)
                terminal_value = terminal_fcf / (discount_rate - terminal_growth)
                terminal_pv = terminal_value / ((1 + discount_rate) ** 5)
                
                total_value = dcf_value + terminal_pv
                shares_outstanding = info.get('sharesOutstanding', 0)
                
                if shares_outstanding > 0:
                    fair_value['dcf_value'] = total_value / shares_outstanding
                    if current_price > 0:
                        fair_value['dcf_upside'] = ((fair_value['dcf_value'] - current_price) / current_price) * 100
                else:
                    fair_value['dcf_value'] = 0
                    fair_value['dcf_upside'] = 0
            
            # P/E based valuation
            industry_pe = 15  # Assume average P/E of 15
            eps_ttm = info.get('trailingEps', 0)
            if eps_ttm > 0:
                fair_value['pe_based_value'] = eps_ttm * industry_pe
                if current_price > 0:
                    fair_value['pe_based_upside'] = ((fair_value['pe_based_value'] - current_price) / current_price) * 100
                else:
                    fair_value['pe_based_upside'] = 0
            
            # Book value multiple
            book_value = info.get('bookValue', 0)
            if book_value > 0:
                fair_value['book_value'] = book_value
                fair_value['price_to_book_current'] = current_price / book_value if book_value > 0 else 0
            
            # Average fair value
            values = []
            if 'dcf_value' in fair_value and fair_value['dcf_value'] > 0:
                values.append(fair_value['dcf_value'])
            if 'pe_based_value' in fair_value and fair_value['pe_based_value'] > 0:
                values.append(fair_value['pe_based_value'])
            
            if values:
                fair_value['average_fair_value'] = sum(values) / len(values)
                if current_price > 0:
                    fair_value['average_upside'] = ((fair_value['average_fair_value'] - current_price) / current_price) * 100
                else:
                    fair_value['average_upside'] = 0
            
            return fair_value
            
        except Exception as e:
            self.logger.error(f'Error calculating fair value: {str(e)}')
            return {}
    
    def _get_analyst_data(self, ticker) -> Dict:
        """Get analyst recommendations and price targets"""
        try:
            analyst_data = {}
            
            # Get recommendations
            try:
                recommendations = ticker.recommendations
                if recommendations is not None and not recommendations.empty:
                    latest_rec = recommendations.iloc[-1]
                    analyst_data['strong_buy'] = latest_rec.get('strongBuy', 0)
                    analyst_data['buy'] = latest_rec.get('buy', 0)
                    analyst_data['hold'] = latest_rec.get('hold', 0)
                    analyst_data['sell'] = latest_rec.get('sell', 0)
                    analyst_data['strong_sell'] = latest_rec.get('strongSell', 0)
                    
                    total_analysts = sum([
                        analyst_data['strong_buy'], analyst_data['buy'], 
                        analyst_data['hold'], analyst_data['sell'], analyst_data['strong_sell']
                    ])
                    
                    if total_analysts > 0:
                        # Calculate consensus score (1-5 scale)
                        score = (
                            analyst_data['strong_buy'] * 5 +
                            analyst_data['buy'] * 4 +
                            analyst_data['hold'] * 3 +
                            analyst_data['sell'] * 2 +
                            analyst_data['strong_sell'] * 1
                        ) / total_analysts
                        
                        analyst_data['consensus_score'] = score
                        analyst_data['total_analysts'] = total_analysts
                        
                        # Convert to recommendation
                        if score >= 4.5:
                            analyst_data['consensus'] = 'Strong Buy'
                        elif score >= 3.5:
                            analyst_data['consensus'] = 'Buy'
                        elif score >= 2.5:
                            analyst_data['consensus'] = 'Hold'
                        elif score >= 1.5:
                            analyst_data['consensus'] = 'Sell'
                        else:
                            analyst_data['consensus'] = 'Strong Sell'
            except:
                pass
            
            # Get price targets from info
            info = ticker.info
            analyst_data['target_high'] = info.get('targetHighPrice', 0)
            analyst_data['target_low'] = info.get('targetLowPrice', 0)
            analyst_data['target_mean'] = info.get('targetMeanPrice', 0)
            analyst_data['target_median'] = info.get('targetMedianPrice', 0)
            
            current_price = info.get('currentPrice', 0)
            if current_price > 0 and analyst_data['target_mean'] > 0:
                analyst_data['target_upside'] = ((analyst_data['target_mean'] - current_price) / current_price) * 100
            else:
                analyst_data['target_upside'] = 0
            
            return analyst_data
            
        except Exception as e:
            self.logger.error(f'Error getting analyst data: {str(e)}')
            return {}
    
    def _generate_investment_recommendation(self, key_metrics: Dict, valuation: Dict, 
                                          profitability: Dict, growth: Dict, 
                                          fair_value: Dict, info: Dict) -> Dict:
        """Generate investment recommendation based on fundamental analysis"""
        try:
            recommendation = {}
            score = 0
            max_score = 0
            factors = []
            
            # Valuation scoring
            pe_ratio = valuation.get('pe_ratio_ttm', 0)
            if pe_ratio > 0:
                max_score += 2
                if pe_ratio < 15:
                    score += 2
                    factors.append("Attractive P/E ratio")
                elif pe_ratio < 25:
                    score += 1
                    factors.append("Reasonable P/E ratio")
                else:
                    factors.append("High P/E ratio")
            
            # Profitability scoring
            roe = profitability.get('roe', 0)
            if roe > 0:
                max_score += 2
                if roe > 15:
                    score += 2
                    factors.append("Strong ROE")
                elif roe > 10:
                    score += 1
                    factors.append("Good ROE")
                else:
                    factors.append("Low ROE")
            
            # Growth scoring
            revenue_growth = growth.get('revenue_growth_1y', 0)
            max_score += 2
            if revenue_growth > 10:
                score += 2
                factors.append("Strong revenue growth")
            elif revenue_growth > 5:
                score += 1
                factors.append("Moderate revenue growth")
            elif revenue_growth < -5:
                factors.append("Declining revenue")
            else:
                factors.append("Slow revenue growth")
            
            # Debt scoring
            debt_to_equity = valuation.get('debt_to_equity', 0)
            max_score += 1
            if debt_to_equity < 0.5:
                score += 1
                factors.append("Low debt levels")
            elif debt_to_equity > 1.5:
                factors.append("High debt levels")
            
            # Fair value scoring
            if 'average_upside' in fair_value:
                upside = fair_value['average_upside']
                max_score += 2
                if upside > 20:
                    score += 2
                    factors.append("Significantly undervalued")
                elif upside > 10:
                    score += 1
                    factors.append("Moderately undervalued")
                elif upside < -10:
                    factors.append("Overvalued")
            
            # Calculate final score
            if max_score > 0:
                final_score = (score / max_score) * 100
            else:
                final_score = 50
            
            # Generate recommendation
            if final_score >= 80:
                recommendation['rating'] = 'Strong Buy'
                recommendation['color'] = '#00ff00'
            elif final_score >= 65:
                recommendation['rating'] = 'Buy'
                recommendation['color'] = '#90EE90'
            elif final_score >= 45:
                recommendation['rating'] = 'Hold'
                recommendation['color'] = '#FFD700'
            elif final_score >= 30:
                recommendation['rating'] = 'Sell'
                recommendation['color'] = '#FFA500'
            else:
                recommendation['rating'] = 'Strong Sell'
                recommendation['color'] = '#ff4444'
            
            recommendation['score'] = round(final_score, 1)
            recommendation['factors'] = factors
            recommendation['summary'] = f"Based on fundamental analysis, {info.get('longName', 'this stock')} receives a {recommendation['rating']} rating with a score of {recommendation['score']}/100."
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f'Error generating recommendation: {str(e)}')
            return {
                'rating': 'Hold',
                'score': 50,
                'factors': ['Analysis incomplete'],
                'summary': 'Unable to generate complete recommendation due to data limitations.',
                'color': '#FFD700'
            }

# Global service instance
fundamental_service = FundamentalAnalysisService()
