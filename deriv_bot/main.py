import asyncio
import logging
import sys
from config import API_TOKEN, APP_ID, SYMBOL, STAKE_AMOUNT, TICK_WINDOW, TRADE_DURATION, MAX_RUNS, SLEEP_BETWEEN_TRADES, USE_MARTINGALE, MARTINGALE_MULTIPLIER, MAX_MARTINGALE_LEVEL
from ws_client import DerivWSClient
from strategy import evaluate_ldp_strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def interactive_setup():
    """Prompts the user via terminal to set up the bot's parameters interactively."""
    print("========================================")
    print("    Deriv Over/Under Bot Setup Setup    ")
    print("========================================")

    use_interactive = input("Do you want to setup interactively? (y/n) [Default: y]: ").strip().lower()
    if use_interactive == 'n':
        print(f"Using defaults: {SYMBOL}, {TICK_WINDOW} ticks, Max Runs: {MAX_RUNS}, Martingale: {USE_MARTINGALE}")
        return SYMBOL, TICK_WINDOW, MAX_RUNS, USE_MARTINGALE

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

    # 4. Ask for Martingale
    martingale_input = input(f"\nEnable Martingale recovery system? (y/n) [Default: {'y' if USE_MARTINGALE else 'n'}]: ").strip().lower()
    if martingale_input == 'y':
        use_martingale_val = True
    elif martingale_input == 'n':
        use_martingale_val = False
    else:
        use_martingale_val = USE_MARTINGALE

    print("\n========================================")
    print(f"Setup Complete! Starting bot for {symbol_str} analyzing last {ticks_val} ticks.")
    print(f"Execution mode: {'Continuous' if max_runs_val == 0 else f'{max_runs_val} runs'}")
    print(f"Martingale: {'Enabled' if use_martingale_val else 'Disabled'}")
    print("========================================\n")

    return symbol_str, ticks_val, max_runs_val, use_martingale_val

async def main():
    if not API_TOKEN:
        logger.error("API_TOKEN is not set. Please check your .env file.")
        sys.exit(1)

    # Run interactive setup
    active_symbol, active_tick_window, active_max_runs, active_martingale = interactive_setup()

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
    current_stake = STAKE_AMOUNT
    consecutive_losses = 0

    try:
        while True:
            if active_max_runs > 0 and runs >= active_max_runs:
                logger.info(f"Reached maximum runs ({active_max_runs}). Stopping.")
                break

            logger.info(f"Fetching last {active_tick_window} ticks for {active_symbol}...")
            prices = await client.get_ticks_history(active_symbol, count=active_tick_window)

            if len(prices) < active_tick_window:
                logger.warning(f"Received {len(prices)} ticks, expected {active_tick_window}. Waiting and retrying...")
                await asyncio.sleep(5)
                continue

            logger.info(f"Evaluating LDP Strategy on {len(prices)} ticks...")
            contract_type, barrier = evaluate_ldp_strategy(prices, pip_size)

            if contract_type and barrier:
                logger.info(f"Signal generated: {contract_type} with barrier {barrier}")

                # Execute Trade
                logger.info(f"Placing trade with stake: {current_stake:.2f}")
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
                    logger.info(f"Trade opened! Contract ID: {contract_id} - Balance after: {buy_details.get('balance_after')}")

                    # Poll for contract result
                    logger.info("Waiting for contract to close...")
                    while True:
                        await asyncio.sleep(2)
                        status_resp = await client.get_contract_status(contract_id)
                        contract_info = status_resp.get("proposal_open_contract", {})

                        if contract_info.get("is_sold") == 1:
                            profit = contract_info.get("profit", 0)
                            if profit > 0:
                                logger.info(f"WIN! Profit: {profit}")
                                current_stake = STAKE_AMOUNT
                                consecutive_losses = 0
                            else:
                                logger.info(f"LOSS. Profit: {profit}")
                                if active_martingale:
                                    consecutive_losses += 1
                                    if consecutive_losses <= MAX_MARTINGALE_LEVEL:
                                        current_stake = current_stake * MARTINGALE_MULTIPLIER
                                        logger.info(f"Martingale active. Next stake multiplied to: {current_stake:.2f}")
                                    else:
                                        logger.warning(f"Max Martingale Level ({MAX_MARTINGALE_LEVEL}) reached. Resetting stake.")
                                        current_stake = STAKE_AMOUNT
                                        consecutive_losses = 0
                            break

                runs += 1
                logger.info(f"Sleeping for {SLEEP_BETWEEN_TRADES} seconds before next cycle...")
                await asyncio.sleep(SLEEP_BETWEEN_TRADES)

            else:
                logger.info("No clear signal (Median exactly 4.5). Waiting before checking again.")
                await asyncio.sleep(2)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
    except Exception as e:
        logger.error(f"Unexpected error in main loop: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
