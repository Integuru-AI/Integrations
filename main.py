import asyncio
from robinhood.robinhood_integration import RobinhoodIntegration
from venmo.venmo_integration import VenmoIntegration


async def main():
    venmo = VenmoIntegration("YOUR_ACCESS_TOKEN")
    await venmo.initialize()
    print(await venmo.get_balance())
    # robinhood = RobinhoodIntegration("YOUR_ACCESS_TOKEN")
    # await robinhood.get_tax_documents()


if __name__ == "__main__":
    asyncio.run(main())
