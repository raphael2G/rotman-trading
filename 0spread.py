# -*- coding: utf-8 -*-
"""
Created on Tue Sep 24 09:35:00 2024

@author: Oriana.Rahman
"""

import requests
import os
from time import sleep

# numpy, pandas

BASE_URL = "http://localhost:9999"

s = requests.Session()
s.headers.update({'X-API-key': 'TYMMUBC9'}) # Make sure you use YOUR API Key

# global variables
MAX_LONG_EXPOSURE = 1000
MAX_SHORT_EXPOSURE = -1000
ORDER_LIMIT = 5000

def get_tick():
    resp = s.get(BASE_URL + "/v1/case") #'http://localhost:9999/v1/case'
    if resp.ok:
        case = resp.json()
        return case['tick'], case['status']


def get_bid_ask(ticker):
    payload = {'ticker': ticker}
    resp = s.get (BASE_URL+"/v1/securities/book", params = payload) #'http://localhost:9999/v1/securities/book'
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
    resp = s.get (BASE_URL + "/v1/securities/tas", params = payload) #'http://localhost:9999/v1/securities/tas'
    if resp.ok:
        book = resp.json()
        time_sales_book = [item["quantity"] for item in book]
        return time_sales_book

def get_position():
    resp = s.get (BASE_URL + "/v1/securities") #'http://localhost:9999/v1/securities'
    if resp.ok:
        book = resp.json()
        return (book[0]['position']) + (book[1]['position']) + (book[2]['position'])

def get_open_orders(ticker):
    payload = {'ticker': ticker}
    resp = s.get (BASE_URL+"/v1/orders", params = payload) #'http://localhost:9999/v1/orders'
    if resp.ok:
        orders = resp.json()
        buy_orders = [item for item in orders if item["action"] == "BUY"]
        sell_orders = [item for item in orders if item["action"] == "SELL"]
        return buy_orders, sell_orders

def get_order_status(order_id):
    resp = s.get (BASE_URL + '/v1/orders' + str(order_id)) #'http://localhost:9999/v1/orders'
    if resp.ok:
        order = resp.json()
        return order['status']
    
def round_price(price):
    tick_size = 0.01
    return round(price / tick_size) * tick_size

def get_current_position(ticker): 
    resp = s.get ('http://localhost:9999/v1/securities', params={'ticker': ticker})
    if resp.ok: 
        securities = resp.json()
        if securities: 
            security = securities[0]
            return security.get("position", None)
    else: 
        print("did not work")
        return None

def main():
    tick, status = get_tick()
    ticker_list = ['OWL','CROW','DOVE','DUCK']

    while status == 'ACTIVE':   


        for ticker_symbol in ['OWL']:
            print("checking", ticker_symbol)

            current_position = get_current_position(ticker_symbol)
            best_bid_price, best_ask_price = get_bid_ask(ticker_symbol)
            
            split_price = round_price((best_bid_price + best_ask_price) / 2)
            print("current position: ", current_position)
            # put 0 spread buy / sell limit orders

            if current_position == 0: 
                resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': (ORDER_LIMIT), 'price': best_bid_price + 0.01, 'action': 'BUY'})
                resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': best_ask_price - 0.01, 'action': 'SELL'})
            elif current_position < 0: 
                resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': min(-current_position, ORDER_LIMIT), 'price': best_bid_price + 0.01 , 'action': 'BUY'})
            elif current_position > 0: 
                resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': min(current_position, ORDER_LIMIT), 'price': best_ask_price - 0.01, 'action': 'SELL'})
            
            sleep(0.1)
            s.post('http://localhost:9999/v1/commands/cancel', params = {'ticker': ticker_symbol})

            #if -ORDER_LIMIT <= current_position  and current_position <= 0:
                #print("bought: ", current_position)
                #resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': split_price, 'action': 'BUY'})

            #if 0 <= current_position and current_position <= ORDER_LIMIT:
                #print("sold: ", current_position)
                #resp = s.post(BASE_URL + '/v1/orders', params = {'ticker': ticker_symbol, 'type': 'LIMIT', 'quantity': ORDER_LIMIT, 'price': split_price, 'action': 'SELL'})

            

        tick, status = get_tick()

if __name__ == '__main__':
    main()



