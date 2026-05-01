import asyncio
import logging
import sys
from .config import API_TOKEN, APP_ID, SYMBOL, STAKE_AMOUNT, TICK_WINDOW, TRADE_DURATION, MAX_RUNS, SLEEP_BETWEEN_TRADES
from .ws_client import DerivWSClient
from .strategy import evaluate_ldp_strategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    if not API_TOKEN:
        logger.error("API_TOKEN is not set. Please check your .env file.")
        sys.exit(1)

    client = DerivWSClient(app_id=APP_ID, api_token=API_TOKEN)

    try:
        await client.connect()
    except Exception as e:
        logger.error(f"Failed to initialize client: {e}")
        sys.exit(1)

    runs = 0

    try:
        while True:
            if MAX_RUNS > 0 and runs >= MAX_RUNS:
                logger.info(f"Reached maximum runs ({MAX_RUNS}). Stopping.")
                break

            logger.info(f"Fetching last {TICK_WINDOW} ticks for {SYMBOL}...")
            prices = await client.get_ticks_history(SYMBOL, count=TICK_WINDOW)

            if len(prices) < TICK_WINDOW:
                logger.warning(f"Received {len(prices)} ticks, expected {TICK_WINDOW}. Waiting and retrying...")
                await asyncio.sleep(5)
                continue

            logger.info(f"Evaluating LDP Strategy on {len(prices)} ticks...")
            contract_type, barrier = evaluate_ldp_strategy(prices)

            if contract_type and barrier:
                logger.info(f"Signal generated: {contract_type} with barrier {barrier}")

                # Execute Trade
                response = await client.buy_contract(
                    symbol=SYMBOL,
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
