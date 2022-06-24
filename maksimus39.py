import pandas as pd 
from binance.client import Client
import asyncio
from binance import AsyncClient, BinanceSocketManager
import nest_asyncio
nest_asyncio.apply()

from sqlalchemy import create_engine

engine = create_engine('sqlite:///Maksim.db')
client = Client()
info = client.get_exchange_info()
symbols = [x['symbol'] for x in info['symbols']]
exclude = ['UP','DOWN','BEAR','BULL']
non_lev = [symbol for symbol in symbols if all(excludes not in symbol for excludes in exclude)]
relevant = [symbol for symbol in non_lev if symbol.endswith('USDT')]
multi = [i.lower() +'@trade' for i in relevant]
def createframe(msg):
	df = pd.DataFrame([msg['data']])
	df = df.loc[:,['s','E','p']]
	df.columns = ['symbol','Time','Price']
	df.Price = df.Price.astype(float)
	df.Time = pd.to_datetime(df.Time, unit = 'ms')
	return df
async def main():
	client = await AsyncClient.create()
	bm = BinanceSocketManager(client)
	ms = bm.multiplex_socket(multi)
	async with ms as tscm:
		while True:
			res = await tscm.recv()
			if res:
				frame = createframe(res)
				frame.to_sql(frame.symbol[0], engine, if_exists = 'append', index = False)

	await client.close_connection()

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	loop.run_until_complete(main()) 