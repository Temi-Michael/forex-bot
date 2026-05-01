import asyncio
import logging
import sys
from .config import API_TOKEN, APP_ID, SYMBOL, STAKE_AMOUNT, TICK_WINDOW, TRADE_DURATION, MAX_RUNS, SLEEP_BETWEEN_TRADES
from .ws_client import DerivWSClient
from .strategy import evaluate_ldp_strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def interactive_setup():
    """Prompts the user via terminal to set up the bot's parameters interactively."""
    print("========================================")
    print("    Deriv Over/Under Bot Setup Setup    ")
    print("========================================")

    use_interactive = input("Do you want to setup interactively? (y/n) [Default: y]: ").strip().lower()
    if use_interactive == 'n':
        print(f"Using defaults from config.py: {SYMBOL}, {TICK_WINDOW} ticks, Max Runs: {MAX_RUNS}")
        return SYMBOL, TICK_WINDOW, MAX_RUNS

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

    print("\n========================================")
    print(f"Setup Complete! Starting bot for {symbol_str} analyzing last {ticks_val} ticks.")
    if max_runs_val == 0:
        print("Execution mode: Continuous")
    else:
        print(f"Execution mode: {max_runs_val} runs")
    print("========================================\n")

    return symbol_str, ticks_val, max_runs_val

async def main():
    if not API_TOKEN:
        logger.error("API_TOKEN is not set. Please check your .env file.")
        sys.exit(1)

    # Run interactive setup
    active_symbol, active_tick_window, active_max_runs = interactive_setup()

    client = DerivWSClient(app_id=APP_ID, api_token=API_TOKEN)

    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        sys.exit(1)

    runs = 0

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
            contract_type, barrier = evaluate_ldp_strategy(prices)

            if contract_type and barrier:
                logger.info(f"Signal generated: {contract_type} with barrier {barrier}")

                # Execute Trade
                response = await client.buy_contract(
                    symbol=active_symbol,
                    amount=STAKE_AMOUNT,
                    contract_type=contract_type,
                    barrier=barrier,
                    duration=TRADE_DURATION
                )

                if "error" in response:
                    logger.error(f"Trade Error: {response['error']['message']}")
                else:
                    buy_details = response.get("buy", {})
                    logger.info(f"Trade successful! Contract ID: {buy_details.get('contract_id')} - Balance after: {buy_details.get('balance_after')}")

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
