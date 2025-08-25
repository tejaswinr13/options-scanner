#!/usr/bin/env python3
"""
Options Trading Simulator
Advanced options position simulator with P&L tracking and Greeks analysis
"""

import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from scipy.stats import norm
import math

class OptionsSimulator:
    def __init__(self):
        """Initialize the options simulator"""
        self.positions = []
        self.risk_free_rate = 0.05
        self.position_id = 1
    
    def calculate_option_price(self, S, K, T, r, sigma, option_type='call'):
        """Calculate theoretical option price using Black-Scholes"""
        try:
            if T <= 0:
                # At expiration
                if option_type.lower() == 'call':
                    return max(S - K, 0)
                else:
                    return max(K - S, 0)
            
            if sigma <= 0:
                sigma = 0.01  # Minimum volatility
            
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            if option_type.lower() == 'call':
                price = S*norm.cdf(d1) - K*np.exp(-r*T)*norm.cdf(d2)
            else:
                price = K*np.exp(-r*T)*norm.cdf(-d2) - S*norm.cdf(-d1)
            
            return max(price, 0.01)  # Minimum price of $0.01
            
        except:
            return 0.01
    
    def calculate_greeks(self, S, K, T, r, sigma, option_type='call'):
        """Calculate option Greeks"""
        try:
            if T <= 0 or sigma <= 0:
                return {'delta': 0, 'gamma': 0, 'theta': 0, 'rho': 0, 'vega': 0}
            
            d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*np.sqrt(T))
            d2 = d1 - sigma*np.sqrt(T)
            
            if option_type.lower() == 'call':
                delta = norm.cdf(d1)
                rho = K*T*np.exp(-r*T)*norm.cdf(d2) / 100
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) - r*K*np.exp(-r*T)*norm.cdf(d2)) / 365
            else:
                delta = norm.cdf(d1) - 1
                rho = -K*T*np.exp(-r*T)*norm.cdf(-d2) / 100
                theta = (-S*norm.pdf(d1)*sigma/(2*np.sqrt(T)) + r*K*np.exp(-r*T)*norm.cdf(-d2)) / 365
            
            gamma = norm.pdf(d1) / (S*sigma*np.sqrt(T))
            vega = S*norm.pdf(d1)*np.sqrt(T) / 100
            
            return {
                'delta': round(delta, 4),
                'gamma': round(gamma, 4),
                'theta': round(theta, 4),
                'rho': round(rho, 4),
                'vega': round(vega, 4)
            }
        except:
            return {'delta': 0, 'gamma': 0, 'theta': 0, 'rho': 0, 'vega': 0}
    
    def get_current_stock_price(self, symbol):
        """Get current stock price from Yahoo Finance"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            return info.get('currentPrice', info.get('regularMarketPrice', 100))
        except:
            return 100  # Default price if unable to fetch
    
    def get_implied_volatility(self, symbol, strike, expiration, option_type):
        """Get implied volatility from market data"""
        try:
            ticker = yf.Ticker(symbol)
            chain = ticker.option_chain(expiration)
            
            if option_type.lower() == 'call':
                options = chain.calls
            else:
                options = chain.puts
            
            # Find matching strike
            matching = options[options['strike'] == strike]
            if not matching.empty:
                iv = matching.iloc[0]['impliedVolatility']
                return iv if iv > 0 else 0.25
            
            return 0.25  # Default IV
        except:
            return 0.25  # Default IV
    
    def add_position(self, symbol, strike, expiration, option_type, quantity, entry_price=None):
        """Add a new options position"""
        try:
            # Get current market data
            current_price = self.get_current_stock_price(symbol)
            
            # Calculate time to expiration
            exp_date = datetime.strptime(expiration, '%Y-%m-%d')
            time_to_exp = (exp_date - datetime.now()).days / 365.0
            
            # Get implied volatility
            iv = self.get_implied_volatility(symbol, strike, expiration, option_type)
            
            # Calculate theoretical price if entry price not provided
            if entry_price is None:
                entry_price = self.calculate_option_price(
                    current_price, strike, time_to_exp, self.risk_free_rate, iv, option_type
                )
            
            # Calculate current Greeks
            greeks = self.calculate_greeks(
                current_price, strike, time_to_exp, self.risk_free_rate, iv, option_type
            )
            
            position = {
                'id': self.position_id,
                'symbol': symbol.upper(),
                'strike': strike,
                'expiration': expiration,
                'type': option_type.upper(),
                'quantity': quantity,
                'entry_price': entry_price,
                'entry_date': datetime.now().strftime('%Y-%m-%d'),
                'current_stock_price': current_price,
                'implied_volatility': iv,
                'time_to_expiration': time_to_exp,
                'greeks': greeks,
                'cost_basis': entry_price * quantity * 100,  # Options are per 100 shares
                'status': 'OPEN'
            }
            
            self.positions.append(position)
            self.position_id += 1
            
            return position
            
        except Exception as e:
            raise Exception(f"Failed to add position: {str(e)}")
    
    def update_positions(self):
        """Update all positions with current market data"""
        for position in self.positions:
            if position['status'] == 'CLOSED':
                continue
                
            try:
                # Get current stock price
                current_price = self.get_current_stock_price(position['symbol'])
                
                # Calculate time to expiration
                exp_date = datetime.strptime(position['expiration'], '%Y-%m-%d')
                time_to_exp = max((exp_date - datetime.now()).days / 365.0, 0)
                
                # Get current implied volatility
                iv = self.get_implied_volatility(
                    position['symbol'], position['strike'], 
                    position['expiration'], position['type']
                )
                
                # Calculate current option price
                current_option_price = self.calculate_option_price(
                    current_price, position['strike'], time_to_exp, 
                    self.risk_free_rate, iv, position['type']
                )
                
                # Calculate current Greeks
                greeks = self.calculate_greeks(
                    current_price, position['strike'], time_to_exp, 
                    self.risk_free_rate, iv, position['type']
                )
                
                # Update position
                position.update({
                    'current_stock_price': current_price,
                    'current_option_price': current_option_price,
                    'implied_volatility': iv,
                    'time_to_expiration': time_to_exp,
                    'greeks': greeks,
                    'current_value': current_option_price * position['quantity'] * 100,
                    'unrealized_pnl': (current_option_price - position['entry_price']) * position['quantity'] * 100,
                    'pnl_percentage': ((current_option_price - position['entry_price']) / position['entry_price']) * 100 if position['entry_price'] > 0 else 0
                })
                
            except Exception as e:
                print(f"Error updating position {position['id']}: {str(e)}")
    
    def close_position(self, position_id, exit_price=None):
        """Close a position"""
        for position in self.positions:
            if position['id'] == position_id and position['status'] == 'OPEN':
                if exit_price is None:
                    # Use current market price
                    self.update_positions()
                    exit_price = position.get('current_option_price', position['entry_price'])
                
                position.update({
                    'exit_price': exit_price,
                    'exit_date': datetime.now().strftime('%Y-%m-%d'),
                    'realized_pnl': (exit_price - position['entry_price']) * position['quantity'] * 100,
                    'status': 'CLOSED'
                })
                
                return position
        
        return None
    
    def get_portfolio_summary(self):
        """Get portfolio summary statistics"""
        self.update_positions()
        
        open_positions = [p for p in self.positions if p['status'] == 'OPEN']
        closed_positions = [p for p in self.positions if p['status'] == 'CLOSED']
        
        # Calculate totals
        total_cost_basis = sum(p['cost_basis'] for p in open_positions)
        total_current_value = sum(p.get('current_value', 0) for p in open_positions)
        total_unrealized_pnl = sum(p.get('unrealized_pnl', 0) for p in open_positions)
        total_realized_pnl = sum(p.get('realized_pnl', 0) for p in closed_positions)
        
        # Calculate portfolio Greeks
        portfolio_delta = sum(p['greeks']['delta'] * p['quantity'] for p in open_positions)
        portfolio_gamma = sum(p['greeks']['gamma'] * p['quantity'] for p in open_positions)
        portfolio_theta = sum(p['greeks']['theta'] * p['quantity'] for p in open_positions)
        portfolio_vega = sum(p['greeks']['vega'] * p['quantity'] for p in open_positions)
        
        return {
            'total_positions': len(self.positions),
            'open_positions': len(open_positions),
            'closed_positions': len(closed_positions),
            'total_cost_basis': total_cost_basis,
            'total_current_value': total_current_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_realized_pnl': total_realized_pnl,
            'total_pnl': total_unrealized_pnl + total_realized_pnl,
            'portfolio_greeks': {
                'delta': portfolio_delta,
                'gamma': portfolio_gamma,
                'theta': portfolio_theta,
                'vega': portfolio_vega
            }
        }
    
    def scenario_analysis(self, stock_price_changes, time_decay_days=0):
        """Perform scenario analysis on portfolio"""
        scenarios = []
        
        for price_change in stock_price_changes:
            scenario_pnl = 0
            
            for position in self.positions:
                if position['status'] == 'CLOSED':
                    continue
                
                # Calculate new stock price
                current_price = position['current_stock_price']
                new_price = current_price * (1 + price_change / 100)
                
                # Calculate new time to expiration
                new_time_to_exp = max(position['time_to_expiration'] - (time_decay_days / 365), 0)
                
                # Calculate new option price
                new_option_price = self.calculate_option_price(
                    new_price, position['strike'], new_time_to_exp,
                    self.risk_free_rate, position['implied_volatility'], position['type']
                )
                
                # Calculate P&L for this position
                position_pnl = (new_option_price - position['entry_price']) * position['quantity'] * 100
                scenario_pnl += position_pnl
            
            scenarios.append({
                'price_change': price_change,
                'time_decay_days': time_decay_days,
                'total_pnl': scenario_pnl
            })
        
        return scenarios
    
    def get_positions_data(self):
        """Get all positions data for display"""
        self.update_positions()
        return self.positions.copy()
