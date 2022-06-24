
api_key = ''
api_secret = ''
import asyncio
from binance import AsyncClient, BinanceSocketManager
import pandas as pd
import datetime as dt
from binance.client import Client
from sqlalchemy import create_engine
engine = create_engine('sqlite:///Maksim.db')
client = Client(api_key,api_secret)
symbols = pd.read_sql('SELECT name FROM sqlite_master WHERE type = "table"', engine).name.to_list()
def qry(symbol, lookback:int):
	now = dt.datetime.now() - dt.timedelta(hours = 1)# бинанс время
	before = now - dt.timedelta(minutes = lookback)
	qry_str = f"""SELECT * FROM '{symbol}' WHERE TIME >='{before}'"""
	return pd.read_sql(qry_str, engine)
# цена крипты за последние lookback минут

rets = []
for symbol in symbols:
	prices = qry(symbol, 3).Price
	cumret = (prices.pct_change() +1).prod() - 1
	rets.append(cumret)
top_coin = symbols[rets.index(max(rets))]# кто больше всех поднялся

investment_amt = 13# 13.12 долларов в 1000 рублей
info = client.get_symbol_info(symbol = top_coin)
Lotsize = float([i for i in info['filters'] if i['filterType'] == 'LOT_SIZE'][0]['minQty'])
prize = float(client.get_symbol_ticker(symbol = top_coin)['price'])
buy_quantity = round(investment_amt/prize, len(str(Lotsize).split('.')[1]))
free_usd = [i for i in client.get_account()['balances'] if i['asset'] == 'USDT'][0]['free']
if float(free_usd) > investment_amt:#изменить investment_amt
	order = client.create_order(symbol = top_coin,
		side = 'BUY',
		type = 'MARKET', 
		quantity = buy_quantity)
	print(order)
else:
	print('order has not been executed. You are already invested.')#заказ не выполнен. Вы уже вложили деньги.
	quit()

buyprice = float(order['fills'][0]['price'])
def createframe(msg):
	df = pd.DataFrame([msg])
	df = df.loc[:,['s','E','p']]
	df.columns = ['symbol','Time','Price']
	df.Price = df.Price.astype(float)
	df.Time = pd.to_datetime(df.Time, unit = 'ms')
	return df
async def main(coin):
	bm = BinanceSocketManager(client)
	ts = bm.trade_socket(coin)
	async with ts as tscm:
		while True:
			res = await tscm.recv()
			if res:
				frame = createframe(res)
				if frame.Price[0] < buyprice * 0.97 or frame.Price[0] > 1.005 * buyprice:
					order = client.create_order(symbol = coin,
						side = 'SELL',
						type = 'MARKET',
						quantity = buy_quantity)
					print(order)
					loop.stop()
	await client.close_connection()
if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main(top_coin))