import aiohttp
import asyncio
import re

pat = re.compile(r'<meta\s+name="twitter:description"\s+content="([^"]+)"')

async def fetch_url(session, url):
    async with session.get(url) as response:
        return await response.text()

async def fetch_all_urls(urls):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_url(session, f"http://george-abitbol.fr/v/{url}") for url in urls]
        return await asyncio.gather(*tasks)

def main(urls):
    results = asyncio.run(fetch_all_urls(urls))

    file = open("lgd.out.txt", mode='w')

    for i, (url, result) in enumerate(zip(urls, results)):
        try:
            quote = \
                pat.search(result).group(1) \
                .replace("&eacute;", "é") \
                .replace("&Eacute;", "É") \
                .replace("&ucirc;", "ù") \
                .replace("&agrave;", "à") \
                .replace("&Agrave;", "À") \
                .replace("&ugrave;", "ù") \
                .replace("&Ugrave;", "Ù") \
                .replace("&egrave;", "è") \
                .replace("&icirc;", "Î") \
                .replace("&icirc;", "î") \
                .replace("&Ecirc;", "Ê") \
                .replace("&ecirc;", "ê") \
                .replace("&acirc;", "â") \
                .replace("&Acirc;", "Â") \
                .replace("&Ccedil;", "Ç") \
                .replace("&ccedil;", "ç") \
                .replace("&ocirc;", "ô") \
                .replace("&Ocirc;", "Ô") \
                .replace("&quot;", "\"") \
                .replace("&ntilde;", "n") \
                .replace("&iuml;", "ï") \
                .replace("&euml;", "ë")
        except:
            continue

        print(f"{i+1}|{url}|{quote}", file=file)


if __name__ == "__main__":
    with open("legrandet.txt") as f:
        urls = [line[:-1] for line in f.readlines()]

    main(urls)
