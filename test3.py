from main import send_to_telex
import asyncio

async def test_telex_webhook():
    await send_to_telex(channel_id="01951917-8a60-7fd7-bec2-9c2639d0f806", message="Test message from Telex Integration!")

if __name__ == "__main__":
    asyncio.run(test_telex_webhook())