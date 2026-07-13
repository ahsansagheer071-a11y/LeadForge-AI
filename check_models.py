import urllib.request, json
r = urllib.request.Request('https://text.pollinations.ai/models')
resp = urllib.request.urlopen(r, timeout=10)
data = json.loads(resp.read())
for m in data[:30]:
    if isinstance(m, dict):
        print(f"{m.get('name', 'N/A'):40s} ctx={m.get('context_length', 'N/A'):>10} max_out={m.get('max_output', 'N/A'):>10}")
    else:
        print(m)
