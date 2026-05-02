import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Ensure deriv_bot/ is on the path so imports resolve correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Inject a mock for ws_client before importing main, so the
# `from ws_client import DerivWSClient` in main.py does not require
# the websockets package or a live connection.
_mock_ws_client = MagicMock()
_mock_ws_client.DerivWSClient = MagicMock()
sys.modules.setdefault('ws_client', _mock_ws_client)

import main as main_module  # noqa: E402 – intentional late import

from config import (  # noqa: E402
    SYMBOL,
    TICK_WINDOW,
    MAX_RUNS,
    USE_MARTINGALE,
    STAKE_AMOUNT,
    MARTINGALE_MULTIPLIER,
    MAX_MARTINGALE_LEVEL,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _setup(inputs):
    """Run interactive_setup() with the given sequence of input() responses."""
    with patch('builtins.input', side_effect=inputs):
        return main_module.interactive_setup()


# ---------------------------------------------------------------------------
# Non-interactive path
# ---------------------------------------------------------------------------

class TestInteractiveSetupNonInteractive(unittest.TestCase):
    """Covers the 'n' (skip) path that returns all eight defaults."""

    @patch('builtins.input', return_value='n')
    def test_returns_8_tuple(self, _):
        result = main_module.interactive_setup()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 8)

    @patch('builtins.input', return_value='n')
    def test_strategy_mode_is_auto_median(self, _):
        result = main_module.interactive_setup()
        # strategy_mode is index 4
        self.assertEqual(result[4], 'auto_median')

    @patch('builtins.input', return_value='n')
    def test_returns_config_defaults(self, _):
        symbol, ticks, runs, martingale, mode, stake, multiplier, max_level = \
            main_module.interactive_setup()
        self.assertEqual(symbol, SYMBOL)
        self.assertEqual(ticks, TICK_WINDOW)
        self.assertEqual(runs, MAX_RUNS)
        self.assertEqual(martingale, USE_MARTINGALE)
        self.assertEqual(mode, 'auto_median')
        self.assertEqual(stake, STAKE_AMOUNT)
        self.assertEqual(multiplier, MARTINGALE_MULTIPLIER)
        self.assertEqual(max_level, MAX_MARTINGALE_LEVEL)


# ---------------------------------------------------------------------------
# Strategy mode selection
# ---------------------------------------------------------------------------

class TestStrategyModeSelection(unittest.TestCase):
    """Covers the strategy-mode prompt (step 4 in the interactive flow)."""

    # Helper: use synthetic asset, all empty defaults, no martingale
    # input order: use_interactive, asset_choice, user_symbol, ticks, runs,
    #              mode_choice, stake, martingale
    def _inputs(self, mode_choice):
        return ['y', '1', '', '', '', mode_choice, '', 'n']

    def test_choice_2_gives_strict_over(self):
        result = _setup(self._inputs('2'))
        self.assertEqual(result[4], 'strict_over')

    def test_choice_3_gives_strict_under(self):
        result = _setup(self._inputs('3'))
        self.assertEqual(result[4], 'strict_under')

    def test_choice_1_gives_auto_median(self):
        result = _setup(self._inputs('1'))
        self.assertEqual(result[4], 'auto_median')

    def test_empty_choice_gives_auto_median(self):
        result = _setup(self._inputs(''))
        self.assertEqual(result[4], 'auto_median')

    def test_invalid_choice_gives_auto_median(self):
        result = _setup(self._inputs('99'))
        self.assertEqual(result[4], 'auto_median')


# ---------------------------------------------------------------------------
# Stake amount
# ---------------------------------------------------------------------------

class TestStakeAmountInput(unittest.TestCase):
    """Covers step 5 – initial stake amount."""

    def _inputs(self, stake_str):
        return ['y', '1', '', '', '', '1', stake_str, 'n']

    def test_valid_float_stake_is_used(self):
        result = _setup(self._inputs('5.00'))
        self.assertAlmostEqual(result[5], 5.00)

    def test_empty_stake_uses_default(self):
        result = _setup(self._inputs(''))
        self.assertEqual(result[5], STAKE_AMOUNT)

    def test_invalid_stake_uses_default(self):
        result = _setup(self._inputs('abc'))
        self.assertEqual(result[5], STAKE_AMOUNT)

    def test_stake_is_float_type(self):
        result = _setup(self._inputs('2.50'))
        self.assertIsInstance(result[5], float)

    def test_decimal_stake_preserved(self):
        result = _setup(self._inputs('0.50'))
        self.assertAlmostEqual(result[5], 0.50)


# ---------------------------------------------------------------------------
# Martingale enable/disable
# ---------------------------------------------------------------------------

class TestMartingaleToggle(unittest.TestCase):
    """Covers step 6 – enabling or disabling Martingale."""

    def test_martingale_y_enables_it(self):
        # When enabled: also prompt for multiplier and level
        inputs = ['y', '1', '', '', '', '1', '', 'y', '2.5', '5']
        result = _setup(inputs)
        self.assertTrue(result[3])

    def test_martingale_n_disables_it(self):
        inputs = ['y', '1', '', '', '', '1', '', 'n']
        result = _setup(inputs)
        self.assertFalse(result[3])

    def test_martingale_empty_uses_config_default(self):
        # Empty input falls back to USE_MARTINGALE from config
        if USE_MARTINGALE:
            # Martingale will be True, so multiplier + level prompts follow
            inputs = ['y', '1', '', '', '', '1', '', '', '2.5', '5']
        else:
            inputs = ['y', '1', '', '', '', '1', '', '']
        result = _setup(inputs)
        self.assertEqual(result[3], USE_MARTINGALE)

    def test_martingale_disabled_does_not_prompt_for_multiplier(self):
        """Providing only 8 inputs with 'n' for martingale should not raise StopIteration."""
        inputs = ['y', '1', '', '', '', '1', '', 'n']
        try:
            result = _setup(inputs)
        except StopIteration:
            self.fail("interactive_setup() consumed too many inputs when martingale=n")
        self.assertFalse(result[3])


# ---------------------------------------------------------------------------
# Martingale multiplier and max level
# ---------------------------------------------------------------------------

class TestMartingaleSettings(unittest.TestCase):
    """Covers the sub-prompts for multiplier and max level when Martingale is on."""

    def _inputs(self, mult_str, level_str):
        return ['y', '1', '', '', '', '1', '', 'y', mult_str, level_str]

    def test_valid_multiplier_is_used(self):
        result = _setup(self._inputs('3.0', '5'))
        self.assertAlmostEqual(result[6], 3.0)

    def test_empty_multiplier_uses_default(self):
        result = _setup(self._inputs('', '5'))
        self.assertEqual(result[6], MARTINGALE_MULTIPLIER)

    def test_invalid_multiplier_uses_default(self):
        result = _setup(self._inputs('bad_val', '5'))
        self.assertEqual(result[6], MARTINGALE_MULTIPLIER)

    def test_valid_max_level_is_used(self):
        result = _setup(self._inputs('2.5', '7'))
        self.assertEqual(result[7], 7)

    def test_empty_max_level_uses_default(self):
        result = _setup(self._inputs('2.5', ''))
        self.assertEqual(result[7], MAX_MARTINGALE_LEVEL)

    def test_invalid_max_level_uses_default(self):
        result = _setup(self._inputs('2.5', 'not_a_number'))
        self.assertEqual(result[7], MAX_MARTINGALE_LEVEL)

    def test_multiplier_is_float_type(self):
        result = _setup(self._inputs('2.5', '5'))
        self.assertIsInstance(result[6], float)

    def test_max_level_is_int_type(self):
        result = _setup(self._inputs('2.5', '5'))
        self.assertIsInstance(result[7], int)


# ---------------------------------------------------------------------------
# Symbol and tick window
# ---------------------------------------------------------------------------

class TestSymbolAndTickSelection(unittest.TestCase):
    """Covers the symbol and tick-window inputs."""

    def test_synthetic_empty_symbol_defaults_to_R_100(self):
        result = _setup(['y', '1', '', '', '', '1', '', 'n'])
        self.assertEqual(result[0], 'R_100')

    def test_forex_empty_symbol_defaults_to_frxEURUSD(self):
        result = _setup(['y', '2', '', '', '', '1', '', 'n'])
        self.assertEqual(result[0], 'frxEURUSD')

    def test_custom_synthetic_symbol_is_used(self):
        result = _setup(['y', '1', 'R_50', '', '', '1', '', 'n'])
        self.assertEqual(result[0], 'R_50')

    def test_custom_forex_symbol_is_used(self):
        result = _setup(['y', '2', 'frxGBPUSD', '', '', '1', '', 'n'])
        self.assertEqual(result[0], 'frxGBPUSD')

    def test_valid_tick_window_input(self):
        result = _setup(['y', '1', '', '200', '', '1', '', 'n'])
        self.assertEqual(result[1], 200)

    def test_invalid_tick_window_uses_default(self):
        result = _setup(['y', '1', '', 'bad', '', '1', '', 'n'])
        self.assertEqual(result[1], TICK_WINDOW)

    def test_valid_max_runs_input(self):
        result = _setup(['y', '1', '', '', '10', '1', '', 'n'])
        self.assertEqual(result[2], 10)

    def test_invalid_max_runs_uses_default(self):
        result = _setup(['y', '1', '', '', 'bad', '1', '', 'n'])
        self.assertEqual(result[2], MAX_RUNS)

    def test_zero_max_runs_is_continuous(self):
        result = _setup(['y', '1', '', '', '0', '1', '', 'n'])
        self.assertEqual(result[2], 0)


# ---------------------------------------------------------------------------
# Config values changed in this PR
# ---------------------------------------------------------------------------

class TestConfigChanges(unittest.TestCase):
    """Verifies configuration constants changed by this PR."""

    def test_martingale_multiplier_is_2_5(self):
        # PR changed MARTINGALE_MULTIPLIER from 2.0 to 2.5
        self.assertEqual(MARTINGALE_MULTIPLIER, 2.5)

    def test_martingale_multiplier_is_not_old_value(self):
        self.assertNotEqual(MARTINGALE_MULTIPLIER, 2.0)


if __name__ == '__main__':
    unittest.main()