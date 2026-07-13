import re
html = open("tmp_kissthehippo_latest.html", "r", encoding="utf-8").read()
imgs = re.findall(r'<img[^>]+src="([^"]+)"', html)
print(f"Total images: {len(imgs)}")
ui_icons = [i for i in imgs if "icon" in i.lower() or "width=48" in i or "width=24" in i or "width=32" in i or "Layer_1" in i or "bean-icon" in i]
print(f"UI icons: {len(ui_icons)}")
for i in ui_icons[:10]:
    print(f"  {i[:120]}")
