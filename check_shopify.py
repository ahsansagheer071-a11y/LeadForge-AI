"""Check what Shopify data is available on the actual sites."""
import json, sys, io, urllib.request, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

for url in ["https://kissthehippo.com", "https://www.stumptowncoffee.com"]:
    print(f"\n{'='*60}")
    print(f"Checking {url}...")
    
    # Check products.json
    try:
        purl = url.rstrip("/") + "/products.json?limit=5"
        req = urllib.request.Request(purl, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        products = data.get("products", [])
        print(f"  /products.json: {len(products)} products")
        for p in products[:3]:
            print(f"    - {p.get('title', 'N/A')}: {len(p.get('images', []))} images")
    except Exception as e:
        print(f"  /products.json: FAILED ({str(e)[:80]})")
    
    # Check homepage for JSON-LD
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="replace")
        
        # Count JSON-LD scripts
        jsonld = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        print(f"  JSON-LD scripts: {len(jsonld)}")
        for i, j in enumerate(jsonld[:3]):
            try:
                d = json.loads(j)
                t = d.get("@type", "unknown") if isinstance(d, dict) else type(d).__name__
                print(f"    [{i}] type={t}")
            except:
                print(f"    [{i}] parse error")
        
        # Count product links
        prod_links = re.findall(r'href="[^"]*/products/[^"]*"', html)
        coll_links = re.findall(r'href="[^"]*/collections/[^"]*"', html)
        print(f"  Product links: {len(prod_links)}")
        for pl in prod_links[:5]:
            print(f"    {pl}")
        print(f"  Collection links: {len(coll_links)}")
        for cl in coll_links[:5]:
            print(f"    {cl}")
        
        # Check for product cards
        cards = re.findall(r'class="[^"]*(?:product|card|grid-item)[^"]*"', html, re.IGNORECASE)
        print(f"  Product/card classes: {len(cards)}")
        for c in cards[:5]:
            print(f"    {c}")
            
    except Exception as e:
        print(f"  Homepage fetch failed: {str(e)[:80]}")
