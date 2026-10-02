from PIL import Image, ImageDraw

S = 512
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([8, 8, S-8, S-8], radius=120, fill=(13, 13, 20, 255), outline=(38, 38, 48, 255), width=6)
cx, cy, R = S//2, S//2 + 30, 150
d.ellipse([cx-R, cy-R, cx+R, cy+R], fill=(255, 92, 57, 255), outline=(190, 50, 30, 255), width=10)
d.ellipse([cx-115, cy-110, cx-35, cy-10], fill=(255, 255, 255, 70))
d.rounded_rectangle([cx-12, cy-R-52, cx+12, cy-R+10], radius=10, fill=(45, 212, 191, 255), outline=(20, 120, 110, 255), width=4)
d.ellipse([cx-110, cy-R-70, cx-10, cy-R+10], fill=(45, 212, 191, 255), outline=(20, 120, 110, 255), width=5)
d.ellipse([cx+10, cy-R-70, cx+110, cy-R+10], fill=(45, 212, 191, 255), outline=(20, 120, 110, 255), width=5)
for ex in (cx-55, cx+55):
    d.ellipse([ex-26, cy-20, ex+26, cy+32], fill=(15, 10, 12, 255))
    d.ellipse([ex-6, cy-10, ex+12, cy+8], fill=(255, 255, 255, 255))
d.arc([cx-45, cy+30, cx+45, cy+110], start=15, end=165, fill=(15, 10, 12, 255), width=12)
d.ellipse([cx-110, cy+30, cx-70, cy+58], fill=(255, 130, 130, 200))
d.ellipse([cx+70, cy+30, cx+110, cy+58], fill=(255, 130, 130, 200))
bx, by, br = cx+105, cy+105, 52
d.ellipse([bx-br, by-br, bx+br, by+br], fill=(250, 250, 252, 255), outline=(38, 38, 48, 255), width=6)
d.line([bx, by, bx, by-30], fill=(20, 20, 26, 255), width=8, joint="curve")
d.line([bx, by, bx+20, by+8], fill=(255, 92, 57, 255), width=8, joint="curve")
d.ellipse([bx-7, by-7, bx+7, by+7], fill=(20, 20, 26, 255))
img.save("pomodoro.png")
img.save("pomodoro.ico", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("icon saved")
