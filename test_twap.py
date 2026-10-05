import unittest

from twap import average_tick, decode_tick_cumulatives, encode_observe


def w(n):
    return format(n % 2**256, "064x")


class TwapTest(unittest.TestCase):
    def test_encode_observe(self):
        data = encode_observe(1800)
        self.assertTrue(data.startswith("0x883bdbfd"))
        self.assertEqual(len(data), 10 + 4 * 64)
        self.assertEqual(int(data[10 + 128:10 + 192], 16), 1800)

    def test_decode_cumulatives_with_negative_values(self):
        # (int56[] tickCumulatives, uint160[] secondsPerLiquidity): two dynamic arrays
        data = "0x" + w(64) + w(160) + w(2) + w(-5000) + w(-3000) + w(2) + w(1) + w(2)
        self.assertEqual(decode_tick_cumulatives(data), [-5000, -3000])

    def test_average_tick_rounds_toward_negative_infinity(self):
        self.assertEqual(average_tick(0, 3600, 1800), 2)
        self.assertEqual(average_tick(0, -3601, 1800), -3)  # -2.0005 -> -3
        self.assertEqual(average_tick(0, -3600, 1800), -2)
        self.assertEqual(average_tick(1000, 1000 + 7 * 60, 60), 7)


if __name__ == "__main__":
    unittest.main()
