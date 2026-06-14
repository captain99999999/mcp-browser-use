import asyncio, os
from bs4 import BeautifulSoup

async def main():
    with open(r"D:\browser-projects\use-browser\google_dump.html", "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, 'html.parser')

    # Find result containers by looking for h3 parents
    h3s = soup.select("h3")
    print(f"Total H3s: {len(h3s)}")

    for i, h3 in enumerate(h3s[:5]):
        print(f"\n=== Result {i+1} ===")
        print(f"Title: {h3.get_text(strip=True)[:100]}")

        # Find URL - look for the nearest link in parent hierarchy
        parent = h3.parent
        for _ in range(10):
            if parent is None:
                break
            link = parent.select_one("a[href^='http']")
            if link:
                href = link.get('href', '')
                # Google wraps in /url?q= redirect - extract real URL
                if '/url?q=' in href:
                    real_url = href.split('/url?q=')[-1].split('&')[0]
                else:
                    real_url = href
                print(f"URL: {real_url[:150]}")
                break
            parent = parent.parent

        # Find snippet
        snippet_el = None
        parent = h3.parent
        for _ in range(5):
            if parent is None:
                break
            # Look for div with text content
            divs = parent.select("div")
            for div in divs:
                text = div.get_text(strip=True)
                if text and len(text) > 30 and text != h3.get_text(strip=True):
                    snippet_el = div
                    break
            if snippet_el:
                break
            parent = parent.parent

        if snippet_el:
            print(f"Snippet: {snippet_el.get_text(strip=True)[:200]}")

asyncio.run(main())