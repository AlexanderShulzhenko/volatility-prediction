import asyncio
import datetime as dt
import time

import aiohttp
import pandas as pd
from tqdm import tqdm

div = "-" * 60
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
        weight_used = resp.headers["x-mbx-used-weight-1m"]
        return trades_dct, weight_used


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

        output = await asyncio.gather(*tasks)
        batch = [tup[0] for tup in output]
        weights_used = [int(tup[-1]) for tup in output]

        api_load = max(weights_used)
        api_load_tracker = [[time.time(), api_load]]
        print(f"Got API load of {api_load}")

        # get last trade ids for each trade list in the first batch
        from_trade_id = []
        for i, trades_dct in enumerate(batch):
            if len(trades_dct) > 0:
                last_trade_id = trades_dct[-1]["a"]
            else:
                # if Binance refuses to provide trades
                spine[i].flag = True
            from_trade_id.append(last_trade_id)

            spine[i].trades_dct_list.append(trades_dct)

        print("Pulling batches...")

        b_num = 0
        all_branches_complete = False
        while not all_branches_complete:
            start = time.time()
            tasks = []
            # go through full spine, but request those branches that are not finished yet
            for i in range(len(spine)):
                if not spine[i].flag:
                    url = "https://api.binance.com/api/v3/aggTrades?symbol=BTCUSDT&limit=1000"
                    url += f"&fromId={from_trade_id[i] + 1}"
                    tasks.append(asyncio.ensure_future(get_trades(session, url)))

            print(f"> Generated tasks in {time.time() - start}")

            if (api_load + len(tasks) * 2) > 6000:
                print("Sleeping to fit the API limits...")
                time.sleep(65)

            start = time.time()
            output = await asyncio.gather(*tasks)
            print(f"> Pulled raw data in {time.time() - start}")

            start = time.time()
            batch = [tup[0] for tup in output]
            weights_used = [int(tup[-1]) for tup in output]
            api_load = max(weights_used)
            api_load_tracker.append([time.time(), api_load])
            print(f"API load after pulling batch: {api_load}")

            from_trade_id = [None] * len(spine)
            cnt = 0
            for i in range(len(spine)):
                if not spine[i].flag:
                    # spine[i].trades_dct_list.append(batch[cnt])
                    try:
                        last_trade_id = batch[cnt][-1]["a"]
                    except KeyError:
                        print("ERROR ON", batch[cnt], cnt)
                        1()
                    last_trade_time = batch[cnt][-1]["T"]
                    from_trade_id[i] = last_trade_id
                    cnt += 1

                    if last_trade_time >= spine[i].end_stamp:
                        spine[i].flag = True

            # print([b.flag for b in spine])
            print(f"> Processed pulled data in {time.time() - start}")

            b_num += 1
            unfinished_branches = len([b for b in spine if not b.flag])
            print(f"Batch {b_num} received, number of unfinished branches: {unfinished_branches}\n{div}")

            all_branches_complete = all(b.flag for b in spine)

    return spine, api_load_tracker


start_time = time.time()
spine, api_load_tracker = asyncio.run(main())
end_time = time.time()
print("--- %s seconds ---" % (end_time - start_time))

full_trades_df_list = process_spine(spine)
print(full_trades_df_list[567])
