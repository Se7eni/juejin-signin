from PIL import Image, ImageDraw, ImageFont
import sys, os

def add_watermark(src, dst):
    img = Image.open(src).convert('RGBA')
    W, H = img.size
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        ft_time = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.095))
        ft_date = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.036))
        ft_day = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.033))
        ft_loc = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.027))
        ft_logo = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.045))
        ft_sub = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.027))
        ft_code = ImageFont.truetype('C:\\Windows\\Fonts\\simhei.ttf', int(H * 0.020))
    except:
        ft_time = ft_date = ft_day = ft_loc = ft_logo = ft_sub = ft_code = ImageFont.load_default()

    def shadow_text(x, y, txt, f, fill=(255,255,255,255), s=2):
        draw.text((x+s, y+s), txt, fill=(0,0,0,100), font=f)
        draw.text((x, y), txt, fill=fill, font=f)

    lx = int(W * 0.03)
    ly = H - int(H * 0.22)

    shadow_text(lx, ly, '10:54', ft_time)
    tw = draw.textlength('10:54', font=ft_time)

    sep_x = lx + tw + 14
    draw.line([(sep_x, ly + 12), (sep_x, ly + int(H * 0.085))], fill=(255, 200, 0, 255), width=3)

    rx_date = sep_x + 14
    shadow_text(rx_date, ly + 6, '2025-08-05', ft_date)
    shadow_text(rx_date, ly + 6 + int(H * 0.044), '星期三  晴 33°C', ft_day)

    shadow_text(lx, ly + int(H * 0.115), '聊城市东昌府区新区街道·聊城市民政局', ft_loc, s=1)

    rmargin = int(W * 0.03)
    rx = W - rmargin
    lines_r = [
        ('今日水印', ft_logo),
        ('相机 真实可验', ft_sub),
        ('防伪 AHM2BN969H2PH2', ft_code),
    ]
    ry = H - int(H * 0.20)
    for txt, f in lines_r:
        bbox = draw.textbbox((0, 0), txt, font=f)
        tw = bbox[2] - bbox[0]
        shadow_text(rx - tw, ry, txt, f, s=1)
        ry += int(H * 0.042)

    out = Image.alpha_composite(img, overlay).convert('RGB')
    out.save(dst, quality=95)
    print(f'已保存: {dst}')

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else r'D:\111.jpg'
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + '_watermark.jpg'
    add_watermark(src, dst)
