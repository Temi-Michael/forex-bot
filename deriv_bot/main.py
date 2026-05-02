import asyncio
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from config import API_TOKEN, APP_ID, SYMBOL, STAKE_AMOUNT, TICK_WINDOW, TRADE_DURATION, MAX_RUNS, SLEEP_BETWEEN_TRADES, USE_MARTINGALE, MARTINGALE_MULTIPLIER, MAX_MARTINGALE_LEVEL
from ws_client import DerivWSClient
from strategy import evaluate_ldp_strategy

# Setup robust logging (Console + File)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

file_handler = RotatingFileHandler(
    os.path.join(os.path.dirname(__file__), "deriv_bot.log"),
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3
)
file_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])
logger = logging.getLogger(__name__)

def interactive_setup():
    """
    Interactively collect runtime configuration values for the trading bot via terminal prompts.
    
    Prompts the user (unless they choose the non-interactive default path) to select an asset symbol (synthetic index or forex pair), the number of past ticks to analyze, the number of runs before stopping (0 for continuous), the strategy mode (auto_median, strict_over, strict_under), the initial stake amount, and optional Martingale settings (enabled, multiplier, max level). Invalid numeric inputs fall back to configured defaults; choosing non-interactive returns the configured defaults immediately.
    
    Returns:
        tuple: (symbol_str, ticks_val, max_runs_val, use_martingale_val, strategy_mode, active_stake, active_multiplier, active_max_level)
            - symbol_str (str): Selected trading symbol.
            - ticks_val (int): Number of past ticks to analyze.
            - max_runs_val (int): Number of runs before stopping (0 for continuous).
            - use_martingale_val (bool): Whether Martingale recovery is enabled.
            - strategy_mode (str): Strategy mode: 'auto_median', 'strict_over', or 'strict_under'.
            - active_stake (float): Initial stake amount.
            - active_multiplier (float): Martingale multiplier to apply after a loss.
            - active_max_level (int): Maximum Martingale recovery levels to attempt.
    """
    print("========================================")
    print("    Deriv Over/Under Bot Setup Setup    ")
    print("========================================")

    use_interactive = input("Do you want to setup interactively? (y/n) [Default: y]: ").strip().lower()
    if use_interactive == 'n':
        print(f"Using defaults: {SYMBOL}, {TICK_WINDOW} ticks, Stake: ${STAKE_AMOUNT}, Max Runs: {MAX_RUNS}, Martingale: {USE_MARTINGALE}")
        return SYMBOL, TICK_WINDOW, MAX_RUNS, USE_MARTINGALE, "auto_median", STAKE_AMOUNT, MARTINGALE_MULTIPLIER, MAX_MARTINGALE_LEVEL

    # 1. Ask for Type
    print("\nSelect the type of asset:")
    print("1) Synthetic Indices")
    print("2) Forex Pairs")
    asset_choice = input("Enter 1 or 2 [Default: 1]: ").strip()

    symbol_str = SYMBOL
    if asset_choice == '2':
        print("\nSample Forex Pairs: frxEURUSD, frxGBPUSD, frxUSDJPY, frxAUDUSD")
        user_symbol = input("Enter the Forex Pair symbol [Default: frxEURUSD]: ").strip()
        symbol_str = user_symbol if user_symbol else "frxEURUSD"
    else:
        print("\nSample Synthetic Indices: R_10, R_25, R_50, R_75, R_100")
        user_symbol = input("Enter the Synthetic Index symbol [Default: R_100]: ").strip()
        symbol_str = user_symbol if user_symbol else "R_100"

    # 2. Ask for Tick Window
    tick_input = input(f"\nEnter the number of past ticks to analyze [Default: {TICK_WINDOW}]: ").strip()
    try:
        ticks_val = int(tick_input) if tick_input else TICK_WINDOW
    except ValueError:
        print(f"Invalid input, using default: {TICK_WINDOW}")
        ticks_val = TICK_WINDOW

    # 3. Ask for Execution Mode (Runs)
    runs_input = input(f"\nEnter the number of runs before stopping (0 for continuous) [Default: {MAX_RUNS}]: ").strip()
    try:
        max_runs_val = int(runs_input) if runs_input else MAX_RUNS
    except ValueError:
        print(f"Invalid input, using default: {MAX_RUNS}")
        max_runs_val = MAX_RUNS

    # 4. Ask for Strategy Mode
    print("\nSelect the Strategy Mode:")
    print("1) Auto Median (Switches between Over/Under based on moving median)")
    print("2) Strict OVER 3 Mode (Waits for low digit streaks, trades Over 3)")
    print("3) Strict UNDER 6 Mode (Waits for high digit streaks, trades Under 6)")
    mode_choice = input("Enter 1, 2, or 3 [Default: 1]: ").strip()

    if mode_choice == '2':
        strategy_mode = 'strict_over'
    elif mode_choice == '3':
        strategy_mode = 'strict_under'
    else:
        strategy_mode = 'auto_median'

    # 5. Ask for Stake Amount
    stake_input = input(f"\nEnter the initial stake amount [Default: ${STAKE_AMOUNT:.2f}]: ").strip()
    try:
        active_stake = float(stake_input) if stake_input else STAKE_AMOUNT
    except ValueError:
        print(f"Invalid input, using default: ${STAKE_AMOUNT:.2f}")
        active_stake = STAKE_AMOUNT

    # 6. Ask for Martingale
    martingale_input = input(f"\nEnable Martingale recovery system? (y/n) [Default: {'y' if USE_MARTINGALE else 'n'}]: ").strip().lower()
    if martingale_input == 'y':
        use_martingale_val = True
    elif martingale_input == 'n':
        use_martingale_val = False
    else:
        use_martingale_val = USE_MARTINGALE

    active_multiplier = MARTINGALE_MULTIPLIER
    active_max_level = MAX_MARTINGALE_LEVEL

    if use_martingale_val:
        mult_input = input(f"  Enter Martingale Multiplier [Default: {MARTINGALE_MULTIPLIER}]: ").strip()
        try:
            active_multiplier = float(mult_input) if mult_input else MARTINGALE_MULTIPLIER
        except ValueError:
            print(f"  Invalid input, using default multiplier: {MARTINGALE_MULTIPLIER}")

        level_input = input(f"  Enter Max Martingale Level [Default: {MAX_MARTINGALE_LEVEL}]: ").strip()
        try:
            active_max_level = int(level_input) if level_input else MAX_MARTINGALE_LEVEL
        except ValueError:
            print(f"  Invalid input, using default max level: {MAX_MARTINGALE_LEVEL}")

    print("\n========================================")
    print(f"Setup Complete! Starting bot for {symbol_str} analyzing last {ticks_val} ticks.")
    print(f"Initial Stake : ${active_stake:.2f}")
    print(f"Execution mode: {'Continuous' if max_runs_val == 0 else f'{max_runs_val} runs'}")
    print(f"Strategy Mode : {strategy_mode.upper()}")
    if use_martingale_val:
        print(f"Martingale    : Enabled (Multiplier: {active_multiplier}x | Max Level: {active_max_level})")
    else:
        print("Martingale    : Disabled")
    print("========================================\n")

    return symbol_str, ticks_val, max_runs_val, use_martingale_val, strategy_mode, active_stake, active_multiplier, active_max_level

async def main():
    """
    Run the trading bot: connect to the Deriv WebSocket API, execute the configured strategy loop, place contracts, and manage staking.
    
    Performs an interactive setup to determine runtime parameters, attempts to connect to the Deriv API, determines pip size for the active symbol, then enters a trade loop that:
    - fetches recent ticks,
    - evaluates and places contracts using the selected strategy mode,
    - polls for contract results,
    - updates running balances and win/loss counts,
    - resets stake on wins and optionally applies a Martingale sequence on losses.
    
    Ensures the client is disconnected on shutdown and logs a formatted session summary. Exits early if API credentials are missing or the client fails to initialize.
    """
    if not API_TOKEN:
        logger.error("API_TOKEN is not set. Please check your .env file.")
        sys.exit(1)

    # Run interactive setup
    active_symbol, active_tick_window, active_max_runs, active_martingale, strategy_mode, active_stake, active_multiplier, active_max_level = interactive_setup()

    client = DerivWSClient(app_id=APP_ID, api_token=API_TOKEN)

    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        sys.exit(1)

    # 1. Fetch pip size for active symbol
    pip_size = 4  # Default fallback
    try:
        logger.info("Fetching active symbols to determine precise pip size...")
        symbols_resp = await client.get_active_symbols()
        if "active_symbols" in symbols_resp:
            for sym_data in symbols_resp["active_symbols"]:
                if sym_data["symbol"] == active_symbol:
                    pip_size = sym_data.get("pip_size", 4)
                    logger.info(f"Pip size for {active_symbol} determined as {pip_size}")
                    break
    except Exception as e:
        logger.error(f"Could not fetch pip size, using default {pip_size}: {e}")

    runs = 0
    current_stake = active_stake
    consecutive_losses = 0

    session_start_balance = None
    final_balance = None
    total_wins = 0
    total_losses = 0

    # ANSI escape sequences for colors
    GREEN = '\033[92m'
    RED = '\033[91m'
    RESET = '\033[0m'

    try:
        while True:
            if active_max_runs > 0 and runs >= active_max_runs:
                print(f"\nReached maximum runs ({active_max_runs}). Stopping.")
                break

            # Fetch ticks quietly without spamming the console
            prices = await client.get_ticks_history(active_symbol, count=active_tick_window)

            if len(prices) < active_tick_window:
                await asyncio.sleep(5)
                continue

            contract_type, barrier = evaluate_ldp_strategy(prices, pip_size, strategy_mode)

            if contract_type and barrier:
                print("\n" + "-"*40)

                response = await client.buy_contract(
                    symbol=active_symbol,
                    amount=current_stake,
                    contract_type=contract_type,
                    barrier=barrier,
                    duration=TRADE_DURATION
                )

                if "error" in response:
                    logger.error(f"Trade Error: {response['error']['message']}")
                else:
                    buy_details = response.get("buy", {})
                    contract_id = buy_details.get('contract_id')
                    balance_after_buy = buy_details.get('balance_after')

                    # Capture starting balance on the very first trade
                    if session_start_balance is None:
                        session_start_balance = balance_after_buy + current_stake

                    logger.info("-" * 40)
                    logger.info(f"Trade Taken: {contract_type} {barrier}")
                    logger.info(f"Stake: ${current_stake:.2f}")
                    logger.info(f"Balance Before: ${(balance_after_buy + current_stake):.2f}")

                    # Poll for contract result
                    while True:
                        await asyncio.sleep(2)
                        status_resp = await client.get_contract_status(contract_id)
                        contract_info = status_resp.get("proposal_open_contract", {})

                        if contract_info.get("is_sold") == 1:
                            profit = contract_info.get("profit", 0)

                            # Fetch final balance by hitting API again or deriving it.
                            # But wait, balance after sell is inside proposal_open_contract?
                            # No, but if we do a quick account check we can get it, or we just track delta.
                            # We can also just pull it from the status if it's there.
                            # Let's just track final_balance roughly.
                            if final_balance is None:
                                final_balance = session_start_balance
                            final_balance += profit

                            if profit > 0:
                                logger.info(f"{GREEN}[WIN]{RESET} Profit: +${profit:.2f}")
                                total_wins += 1
                                current_stake = active_stake
                                consecutive_losses = 0
                            else:
                                logger.info(f"{RED}[LOSS]{RESET} Profit: -${abs(profit):.2f}")
                                total_losses += 1
                                if active_martingale:
                                    consecutive_losses += 1
                                    if consecutive_losses <= active_max_level:
                                        current_stake = current_stake * active_multiplier
                                        logger.info(f"Martingale Active. Next Stake: ${current_stake:.2f}")
                                    else:
                                        logger.warning(f"Max Martingale Level Reached. Resetting Stake.")
                                        current_stake = active_stake
                                        consecutive_losses = 0
                            break

                runs += 1
                await asyncio.sleep(SLEEP_BETWEEN_TRADES)

            else:
                await asyncio.sleep(2)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        await client.disconnect()

        # Print Session Summary
        logger.info("\n" + "="*40)
        logger.info("          SESSION SUMMARY")
        logger.info("="*40)
        logger.info(f"Total Trades : {runs}")
        logger.info(f"Wins         : {GREEN}{total_wins}{RESET}")
        logger.info(f"Losses       : {RED}{total_losses}{RESET}")

        if session_start_balance is not None and final_balance is not None:
            pl = final_balance - session_start_balance
            color = GREEN if pl > 0 else RED if pl < 0 else RESET
            logger.info(f"Session P/L  : {color}${pl:.2f}{RESET}")
        else:
            logger.info("Session P/L  : $0.00")

        logger.info("="*40)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
