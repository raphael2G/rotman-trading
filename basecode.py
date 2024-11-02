# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 09:35:00 2024

@author: Oriana.Rahman
"""

import requests
from datetime import datetime, timedelta
import numpy as np
from time import sleep

# numpy, pandas

s = requests.Session()
s.headers.update({'X-API-key': 'TYMMUBC9'}) # Make sure you use YOUR API Key

# global variables
MAX_LONG_EXPOSURE = 300000
MAX_SHORT_EXPOSURE = -100000
ORDER_LIMIT = 5000
MIN_SPREAD = 0.05

def get_tick():
    resp = s.get('http://localhost:9999/v1/case')
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']


def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/book', params = payload)
    if resp.ok:
        book = resp.json()
        bid_side_book = book['bids']
        ask_side_book = book['asks']
        
        bid_prices_book = [item["price"] for item in bid_side_book]
        ask_prices_book = [item['price'] for item in ask_side_book]
        
        best_bid_price = bid_prices_book[0]
        best_ask_price = ask_prices_book[0]
  
        return best_bid_price, best_ask_price

def get_time_sales(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/securities/tas', params = payload)
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get ('http://localhost:9999/v1/securities')
    if resp.ok:
        book = resp.json()
        return (book[0]['position']) + (book[1]['position']) + (book[2]['position'])

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get ('http://localhost:9999/v1/orders', params = payload)
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get ('http://localhost:9999/v1/orders' + '/' + str(order_id))
    if resp.ok:
        order = resp.json()
        return order['status']

def get_current_position(ticker): 
    resp = s.get ('http://localhost:9999/v1/securities' + '/' + str(ticker))
    if resp.ok: 
        security = resp.json()
        return security["position"]


def fetch_price_history(ticker, count):
    # Fetch the latest 60 trades as a list in chronological order
    resp = s.get('http://localhost:9999/v1/securities/tas', 
                params={
                    'ticker': ticker,
                    'limit': count
                })
    
    if resp.ok: 
        data = resp.json()
        prices = [entry['price'] for entry in data]
        return prices[::-1]  # Reverse to get chronological order

def calculate_volatility(ticker, count=60):
    prices = fetch_price_history(ticker, count)
    # this returns the std of the log volatility
    # this is the log of how much each trade increases
    log_returns = np.log(prices[1:]/prices[:-1])
    volatility = np.std(log_returns)
    return volatility

def calculate_order_arrival_rate(ticker, time_window_seconds=60):
    resp = s.get('http://localhost:9999/v1/orders', params={'ticker': ticker})
    if not resp.ok: 
        return -1
    
    orders = resp.json()
    
    if not orders:
        return -1

    end_time = max(datetime.strptime(order['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ') for order in orders)
    earliest_order = min(datetime.strptime(order['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ') for order in orders)

    start_time = end_time - timedelta(seconds=time_window_seconds)

    if earliest_order > start_time:
        start_time = earliest_order
        actual_window_size = (end_time - start_time).total_seconds()  # Adjust window size to the actual time range
    else:
        actual_window_size = time_window_seconds

    filled_orders = [
        order for order in orders
        if order['type'] == 'LIMIT' and order['status'] in ['FILLED', 'PARTIAL FILLED']
        and start_time <= datetime.strptime(order['last_updated'], '%Y-%m-%dT%H:%M:%S.%fZ') <= end_time
    ]

    number_of_orders_in_window = len(filled_orders)
    
    return number_of_orders_in_window / actual_window_size


def round_price(price):
    tick_size = 0.01
    return round(price / tick_size) * tick_size

def OWL_trading_strat(GAMMA = 0.1): 
    
    best_bid_price, best_ask_price = get_bid_ask('OWL')
    mid_price = (best_bid_price + best_ask_price) / 2

    current_position = get_current_position('OWL')
    order_arrival_rate = calculate_order_arrival_rate('OWL', 60)
    std_volatility = calculate_volatility()


    base_spread = GAMMA * std_volatility * std_volatility / 2

    # this will be positive if our current position is postiive. This makes us have lower buy offers, and lower sell offers, pushing our inventory back to 0. this will cause us to buy less and sell more
    # this is cause we subtrqact 
    inventory_adjustment = GAMMA * std_volatility * std_volatility * current_position / order_arrival_rate

    calculated_price_of_bid = mid_price - base_spread + inventory_adjustment
    calculated_price_of_ask = mid_price + base_spread + inventory_adjustment

    buy_resp = s.post('http://localhost:9999/v1/orders', params = {
        'ticker': 'OWL', 
        'type': 'LIMIT', 
        'quantity': ORDER_LIMIT, 
        'price': round_price(calculated_price_of_bid), 
        'action': 'BUY'
    })

    sell_resp = s.post('http://localhost:9999/v1/orders', params = {
        'ticker': 'OWL', 
        'type': 'LIMIT', 
        'quantity': ORDER_LIMIT, 
        'price': round_price(calculated_price_of_ask), 
        'action': 'SELL'
    })




def main():
    tick, status = get_tick()
    ticker_list = ['OWL','CROW','DOVE','DUCK']
    MIN_SPREAD = {'OWL':  0.05, 
                  'CROW': 0.05, 
                  'DOVE': 0.05,
                  'DUCK': 0.05 }

    while status == 'ACTIVE':        
        OWL_trading_strat()
        # for i in range(4):
            
        #     ticker_symbol = ticker_list[i]
        #     position = get_position()
        #     best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)


        #     # only place orders if we meet a certain spread
        #     spread = best_ask_price - best_bid_price
        #     if spread >= MIN_SPREAD[ticker_symbol]: 
        #         if position < MAX_LONG_EXPOSURE:
        #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_bid_price + 0.01, 'action': 'BUY'})
        #             print("just placed buy")

        #         if position > MAX_SHORT_EXPOSURE:
        #             resp = s.post('http://localhost:9999/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_ask_price - 0.01, 'action': 'SELL'})
        #             print("just placed sell")
        #     else: 
        #         print("Spread too low: ", spread)

        #     sleep(0.2) 
        #     s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': ticker_symbol})

        tick, status = get_tick()

if __name__ == '__main__':
    print("Beggining Execution")
    main()
    print("finished execution")



