import asyncio
from main import generate_outreach_email

async def test_aimlapi():
    content = await generate_outreach_email("Test website", "https://.com", "SEO improvement services")
    print("AIMLAPI Response:", content)

if __name__ == "__main__":
    asyncio.run(test_aimlapi())
