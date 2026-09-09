"""Compose delivery previews and package the verified Blender model with its sources."""

import hashlib
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageStat

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'/'leopard2'
OUT=ROOT/'models'/'leopard2'
font_path=Path('C:/Windows/Fonts/arial.ttf')
font_bold=Path('C:/Windows/Fonts/arialbd.ttf')
title_font=ImageFont.truetype(str(font_bold),44)
label_font=ImageFont.truetype(str(font_bold),23)
small_font=ImageFont.truetype(str(font_path),20)
background=(239,242,242)
ink=(37,46,44)


def add_view(sheet, name, label, rect):
    x,y,w,h=rect
    source=Image.open(ASSETS/f'{name}.png').convert('RGB')
    source.thumbnail((w,h-43),Image.Resampling.LANCZOS)
    sheet.paste(source,(x+(w-source.width)//2,y+43+(h-43-source.height)//2))
    ImageDraw.Draw(sheet).text((x+8,y+8),label,font=label_font,fill=ink)


sheet=Image.new('RGB',(2200,1740),background)
draw=ImageDraw.Draw(sheet)
draw.text((46,32),'LEOPARD 2  /  EARLY PROTOTYPE',font=title_font,fill=ink)
draw.text((48,91),'Reference reconstruction  |  Editable exterior  |  1 unit = 1 meter',font=small_font,fill=ink)
add_view(sheet,'hero','01  FRONT THREE-QUARTER',(38,139,1048,732))
add_view(sheet,'rear','02  REAR THREE-QUARTER',(1114,139,1048,732))
add_view(sheet,'side','03  SIDE ORTHOGRAPHIC',(38,894,1352,391))
add_view(sheet,'top','04  TOP ORTHOGRAPHIC',(38,1305,1352,391))
add_view(sheet,'front','05  FRONT',(1450,894,683,391))
add_view(sheet,'back','06  REAR',(1450,1305,683,391))
sheet.save(ASSETS/'model_contact_sheet.jpg',quality=94)

report=json.loads((OUT/'validation_report.json').read_text(encoding='utf-8'))
if not report['passed']:
    raise RuntimeError('Refusing to package an unvalidated model')
preview_checks=[]
for name in ('hero','rear','side','top','front','back'):
    image=Image.open(ASSETS/f'{name}.png').convert('RGB')
    stat=ImageStat.Stat(image)
    center=image.crop((image.width//5,image.height//5,image.width*4//5,image.height*4//5))
    central_stat=ImageStat.Stat(center)
    ok=min(image.size)>=700 and sum(stat.stddev)>30 and sum(central_stat.stddev)>20
    preview_checks.append({'name':name,'size':image.size,'stddev':stat.stddev,'nonblank':ok})
if not all(p['nonblank'] for p in preview_checks):
    raise RuntimeError('A preview failed nonblank pixel verification')
(OUT/'preview_checks.json').write_text(json.dumps(preview_checks,indent=2),encoding='utf-8')

files=[]
for directory in (OUT,ASSETS,ROOT/'references'/'leopard2',ROOT/'docs'/'leopard2'):
    files.extend(p for p in directory.rglob('*') if p.is_file() and p.suffix not in ('.blend1','.zip','.log'))
files.extend(ROOT/'scripts'/name for name in (
    'build_leopard2_reference.py','tank_common.py','tank_running_gear.py',
    'validate_leopard2_model.py','package_leopard2.py'))
bundle=OUT/'Leopard_2_editable_model_bundle.zip'
with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for path in files:
        archive.write(path,path.relative_to(ROOT).as_posix())
with zipfile.ZipFile(bundle) as archive:
    assert archive.testzip() is None
print(json.dumps({'bundle':str(bundle),'files':len(files),'bytes':bundle.stat().st_size,
                  'sha256':hashlib.sha256(bundle.read_bytes()).hexdigest(),
                  'geometry_checks':len(report['checks']),
                  'preview_checks':preview_checks},indent=2))
