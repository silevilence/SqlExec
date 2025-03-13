import os
from cairosvg import svg2png
from PIL import Image

# 转换 SVG 到 PNG
svg_path = 'src/sqlexec/resources/icons/app.svg'
png_path = 'src/sqlexec/resources/icons/app.png'
ico_path = 'src/sqlexec/resources/icons/app.ico'

# 确保目录存在
os.makedirs(os.path.dirname(png_path), exist_ok=True)

# 转换 SVG 到 PNG，创建多个尺寸
sizes = [16, 32, 48, 64, 128, 256]
images = []

for size in sizes:
    output_png = f'src/sqlexec/resources/icons/app_{size}.png'
    svg2png(url=svg_path, write_to=output_png, output_width=size, output_height=size)
    images.append(Image.open(output_png))
    
# 创建 ICO 文件
images[0].save(ico_path, format='ICO', sizes=[(size, size) for size in sizes], append_images=images[1:])

# 清理临时文件
for size in sizes:
    os.remove(f'src/sqlexec/resources/icons/app_{size}.png') 