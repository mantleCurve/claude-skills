#!/usr/bin/env python3
"""Lift diorama/illustration layers out of a dark poster as alpha WebP files.

Usage: layers.py poster.png out_dir name:x0,y0,x1,y1[:cut;cut...][:keepx0,keepy0,keepx1,keepy1] ...
  cut  = x0,y0,x1,y1 rectangles (poster coords) erased, e.g. printed text
  keep = one rectangle (poster coords); everything outside it is dropped (kills card borders)
Dark pixels (max channel <= LO) become transparent, bright (>= HI) opaque, feathered between.
Optional cut rectangles (poster coords) erase printed text so live HTML can replace it.
Env: LO (default 50), HI (default 95), FEATHER px (default 5).
"""
import os, sys
from PIL import Image, ImageFilter, ImageDraw, ImageChops
LO=int(os.environ.get('LO',50)); HI=int(os.environ.get('HI',95)); F=float(os.environ.get('FEATHER',5))
src=Image.open(sys.argv[1]).convert('RGB'); out=sys.argv[2]; os.makedirs(out,exist_ok=True)
for spec in sys.argv[3:]:
    parts=spec.split(':'); name=parts[0]; box=tuple(int(v) for v in parts[1].split(','))
    cuts=[tuple(int(v) for v in c.split(',')) for c in parts[2].split(';')] if len(parts)>2 and parts[2] else []
    keep=tuple(int(v) for v in parts[3].split(',')) if len(parts)>3 and parts[3] else None
    im=src.crop(box).convert('RGBA'); w,h=im.size
    r,g,b=im.convert('RGB').split(); m=ImageChops.lighter(ImageChops.lighter(r,g),b)
    a=m.point(lambda v: 0 if v<=LO else 255 if v>=HI else int((v-LO)*255/(HI-LO)))
    cut=Image.new('L',(w,h),255); d=ImageDraw.Draw(cut)
    for x0,y0,x1,y1 in cuts: d.rectangle((x0-box[0],y0-box[1],x1-box[0],y1-box[1]),fill=0)
    if keep:
        kx0,ky0,kx1,ky1=keep; d.rectangle((0,0,w,ky0-box[1]),fill=0); d.rectangle((0,ky1-box[1],w,h),fill=0); d.rectangle((0,0,kx0-box[0],h),fill=0); d.rectangle((kx1-box[0],0,w,h),fill=0)
    a=ImageChops.multiply(a,cut.filter(ImageFilter.GaussianBlur(F))).filter(ImageFilter.GaussianBlur(0.7))
    im.putalpha(a); im.save(os.path.join(out,name+'.webp'),quality=86,method=6); print(name,im.size)
