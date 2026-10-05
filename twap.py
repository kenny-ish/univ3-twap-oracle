"""Uniswap v3 TWAP from the pool's oracle."""
import argparse
import json
import urllib.request

OBSERVE, SLOT0 = "0x883bdbfd", "0x3850c7bd"
TOKEN0, TOKEN1 = "0x0dfe1681", "0xd21220a7"
SYMBOL, DECIMALS = "0x95d89b41", "0x313ce567"
DEFAULT_POOL = "0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"  # USDC/WETH 0.05%


def call(url, to, data):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_call", "params": [{"to": to, "data": data}, "latest"]}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "univ3-twap-oracle"})
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.load(r)
    if "error" in resp:
        raise RuntimeError(resp["error"].get("message", str(resp["error"])))
    return resp["result"]


def signed(word_hex):
    v = int(word_hex, 16)
    return v - 2**256 if v >= 2**255 else v


def encode_observe(seconds_ago):
    return OBSERVE + format(32, "064x") + format(2, "064x") + format(seconds_ago, "064x") + format(0, "064x")


def decode_tick_cumulatives(hexdata):
    d = hexdata[2:]
    w = [d[i:i + 64] for i in range(0, len(d), 64)]
    start = int(w[0], 16) // 32
    n = int(w[start], 16)
    return [signed(w[start + 1 + i]) for i in range(n)]


def average_tick(cum_then, cum_now, seconds):
    delta = cum_now - cum_then
    tick = delta // seconds if delta >= 0 else -((-delta) // seconds)
    if delta < 0 and delta % seconds != 0:
        tick -= 1  # round toward negative infinity, as OracleLibrary does
    return tick


def symbol(url, token):
    raw = bytes.fromhex(call(url, token, SYMBOL)[2:])
    return raw.rstrip(b"\0").decode() if len(raw) == 32 else raw[64:64 + int.from_bytes(raw[32:64], "big")].decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pool", nargs="?", default=DEFAULT_POOL)
    ap.add_argument("--seconds", type=int, default=1800)
    ap.add_argument("--rpc", default="https://ethereum-rpc.publicnode.com")
    a = ap.parse_args()

    t0 = "0x" + call(a.rpc, a.pool, TOKEN0)[-40:]
    t1 = "0x" + call(a.rpc, a.pool, TOKEN1)[-40:]
    s0, s1 = symbol(a.rpc, t0), symbol(a.rpc, t1)
    d0, d1 = (int(call(a.rpc, t, DECIMALS), 16) for t in (t0, t1))
    slot = call(a.rpc, a.pool, SLOT0)[2:]
    spot_tick = signed(slot[64:128])
    cardinality = int(slot[192:256], 16)
    try:
        cums = decode_tick_cumulatives(call(a.rpc, a.pool, encode_observe(a.seconds)))
    except RuntimeError as e:
        raise SystemExit(f"observe failed ({e}); the pool stores {cardinality} observations, try a shorter --seconds")

    tick = average_tick(cums[0], cums[1], a.seconds)
    price = lambda t: 1.0001 ** t * 10 ** (d0 - d1)
    twap, spot = price(tick), price(spot_tick)
    print(f"pool {a.pool} ({s0}/{s1}), {cardinality} observations stored")
    print(f"TWAP {a.seconds}s  tick {tick:>8}  1 {s0} = {twap:.6g} {s1}   1 {s1} = {1 / twap:.6g} {s0}")
    print(f"spot          tick {spot_tick:>8}  1 {s0} = {spot:.6g} {s1}   1 {s1} = {1 / spot:.6g} {s0}")
    print(f"spot vs TWAP  {(spot / twap - 1) * 100:+.3f}%")


if __name__ == "__main__":
    main()
