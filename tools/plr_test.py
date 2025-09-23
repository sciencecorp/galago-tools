print("Hello World")
from pylabrobot.liquid_handling import LiquidHandler
from pylabrobot.liquid_handling.backends import STARBackend
from pylabrobot.resources import Deck
import asyncio

async def main():
    # Load deck and initialize liquid handler
    deck = Deck.load_from_json_file("hamilton-layout.json")
    lh = LiquidHandler(backend=STARBackend(), deck=deck)
    
    # Setup the liquid handler
    await lh.setup()
    
    try:
        # Perform liquid handling operations
        await lh.pick_up_tips(lh.deck.get_resource("tip_rack")["A1"])
        await lh.aspirate(lh.deck.get_resource("plate")["A1"], vols=100)
        await lh.dispense(lh.deck.get_resource("plate")["A2"], vols=100)
        await lh.return_tips()
    finally:
        # Clean up
        await lh.stop()

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())