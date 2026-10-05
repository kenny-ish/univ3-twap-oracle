# univ3-twap-oracle

Every Uniswap v3 pool keeps a running sum of its tick over time (`tickCumulative`). Reading it at two
points in time gives the time-weighted average price. A TWAP is much harder to manipulate than the
spot price, because the price would have to stay skewed for the whole window.

```bash
python twap.py                                    # USDC/WETH 0.05% pool, 30 minute TWAP
python twap.py 0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640 --seconds 3600
python twap.py <pool> --rpc https://mainnet.base.org --seconds 600
```

The steps:

1. `pool.observe([secondsAgo, 0])` returns the `tickCumulatives` for both points in time.
2. `avgTick = (cum_now - cum_then) / secondsAgo`, rounded toward negative infinity like Uniswap's
   `OracleLibrary.consult`.
3. `price = 1.0001^avgTick x 10^(decimals0 - decimals1)`, printed in both directions.

The spot price comes from `slot0()`. A large gap between spot and TWAP means the price moved
recently, or someone is pushing it. Protocols that use the spot price as an oracle get exploited in
exactly that situation.

If the window is longer than the history the pool stores (`observationCardinality`), `observe`
reverts with `OLD`. The tool says so and shows how many observations the pool keeps.

## Tests

```bash
python -m unittest -v
```
