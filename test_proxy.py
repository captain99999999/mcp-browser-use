import httpx, json, asyncio

async def main():
    async with httpx.AsyncClient(proxy='http://127.0.0.1:7897', follow_redirects=True) as c:
        r = await c.get('https://api.duckduckgo.com/', params={'q': 'python', 'format': 'json'})
        data = r.json()

        # Check RelatedTopics structure
        topics = data.get('RelatedTopics', [])
        print(f"RelatedTopics: {len(topics)} items")
        if topics:
            t0 = topics[0]
            print(f"First topic keys: {list(t0.keys())}")
            print(f"First topic full: {json.dumps(t0, indent=2)[:500]}")

        # Check Results
        results = data.get('Results', [])
        print(f"\nResults: {len(results)} items")
        if results:
            print(f"First result keys: {list(results[0].keys())}")
            print(f"First result: {json.dumps(results[0], indent=2)[:500]}")

asyncio.run(main())