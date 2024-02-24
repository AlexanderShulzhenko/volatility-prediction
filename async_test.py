import asyncio
import datetime as dt
import time

import aiohttp
import pandas as pd
from tqdm import tqdm

master_list = pd.read_csv("data/01_raw/master_list.csv")
master_list["close_time"] = pd.to_datetime(master_list["close_time"])


class branch:
    def __init__(self, flag: bool, trades_dct_list: list, start_stamp: str, end_stamp: str):
        self.flag = flag
        self.trades_dct_list = trades_dct_list
        self.start_stamp = start_stamp
        self.end_stamp = end_stamp


def process_spine(spine):
    print("Processing loaded data...")
    full_trades_df_list = []
    # concat all trades_dct for each branch
    for br in tqdm(spine):
        full_trades_df = pd.DataFrame()
        for trades_dct in br.trades_dct_list:
            trades_df = pd.DataFrame.from_records(trades_dct)
            full_trades_df = pd.concat((full_trades_df, trades_df))
        full_trades_df = full_trades_df.reset_index(drop=True)
        # in case of non-empty df crop by timestamp
        if len(full_trades_df) > 0:
            full_trades_df = full_trades_df[full_trades_df["T"] < br.end_stamp]
        full_trades_df_list.append(full_trades_df)
    return full_trades_df_list


def get_stamps():
    # get lists of t1 and t2
    t1_list = []
    t2_list = []
    for i in range(len(master_list)):
        t2 = dt.datetime(
            master_list["close_time"][i].year,
            master_list["close_time"][i].month,
            master_list["close_time"][i].day,
            master_list["close_time"][i].hour,
            master_list["close_time"][i].minute,
            0,
        ) + dt.timedelta(minutes=1)
        t1 = t2 - dt.timedelta(minutes=15)
        t1_list.append(str(int(t1.timestamp() * 1000)))
        t2_list.append(str(int(t2.timestamp() * 1000)))
    return t1_list, t2_list


async def get_trades(session, url):
    async with session.get(url) as resp:
        trades_dct = await resp.json()
        return trades_dct


# ruff: noqa: C901
async def main():
    BATCH_LEN = len(master_list)
    start_stamps, end_stamps = get_stamps()
    spine = [branch(False, [], int(start_stamps[i]), int(end_stamps[i])) for i in range(BATCH_LEN)]

    async with aiohttp.ClientSession() as session:
        # First batch: based on start time and ran for ALL branches
        tasks = []
        for i in range(BATCH_LEN):
            url = "https://api.binance.com/api/v3/aggTrades?symbol=BTCUSDT&limit=1000"
            url += f"&startTime={start_stamps[i]}"
            url += f"&endTime={end_stamps[i]}"
            tasks.append(asyncio.ensure_future(get_trades(session, url)))

        batch = await asyncio.gather(*tasks)
        print("Sleeping to fit the API limits...")
        time.sleep(60)

        # get last trade ids for each trade list in the first batch
        from_trade_id = []
        for i, trades_dct in enumerate(batch):
            if len(trades_dct) > 0:
                last_trade_id = trades_dct[-1]["a"]
            else:
                spine[i].flag = True
            from_trade_id.append(last_trade_id)

            spine[i].trades_dct_list.append(trades_dct)

        print("Pulling batches...")

        b_num = 0
        api_load = 0
        all_branches_complete = False
        while not all_branches_complete:
            tasks = []
            # go through full spine, but request only for branches that are not finished yet
            for i in range(len(spine)):
                if not spine[i].flag:
                    url = "https://api.binance.com/api/v3/aggTrades?symbol=BTCUSDT&limit=1000"
                    url += f"&fromId={from_trade_id[i] + 1}"
                    tasks.append(asyncio.ensure_future(get_trades(session, url)))

            api_load += len(tasks) * 2
            if api_load > 4000:
                print("Sleeping to fit the API limits...")
                time.sleep(70)
                api_load = 0
            batch = await asyncio.gather(*tasks)

            from_trade_id = [None] * len(spine)
            cnt = 0
            for i in range(len(spine)):
                if not spine[i].flag:
                    spine[i].trades_dct_list.append(batch[cnt])
                    try:
                        last_trade_id = batch[cnt][-1]["a"]
                    except KeyError:
                        print("ERROR ON", batch[cnt], cnt)
                        1()
                    last_trade_time = batch[cnt][-1]["T"]
                    from_trade_id[i] = last_trade_id
                    cnt += 1

                    # print(f"{last_trade_time:,d}", f"{spine[i].end_stamp:,d}")

                    if last_trade_time >= spine[i].end_stamp:
                        spine[i].flag = True

            # print([b.flag for b in spine])
            b_num += 1
            unfinished_branches = len([b for b in spine if not b.flag])
            print(f"Batch {b_num} received. Number of unfinished brabches: {unfinished_branches}.")

            all_branches_complete = all(b.flag for b in spine)

    return spine


start_time = time.time()
spine = asyncio.run(main())
end_time = time.time()
print("--- %s seconds ---" % (end_time - start_time))

full_trades_df_list = process_spine(spine)
print(full_trades_df_list[567])
