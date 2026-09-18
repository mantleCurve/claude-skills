#!/usr/bin/env python3
"""Export a pre-laid-out PDF to verified, numerically named 300 DPI JPEGs."""
import argparse
import json
from pathlib import Path
import re
import shutil
import tempfile

import pymupdf as fitz
from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pdf', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--width', type=int, required=True)
    parser.add_argument('--height', type=int, required=True)
    parser.add_argument('--pages', type=int, required=True)
    parser.add_argument('--dpi', type=int, default=300)
    parser.add_argument('--prefix', default='photo_new_ivory')
    parser.add_argument('--uniform-background', action='store_true')
    args = parser.parse_args()
    if min(args.width, args.height, args.pages, args.dpi) <= 0:
        parser.error('Dimensions, page count, and DPI must be positive')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.prefix):
        parser.error('Prefix must contain only letters, digits, underscores or hyphens')
    if args.output.exists():
        parser.error('Output directory already exists; choose a fresh export directory')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.album-export-', dir=args.output.parent))
    try:
        entries = []
        common_bg = None
        with fitz.open(args.pdf) as doc:
            if len(doc) != args.pages:
                raise ValueError(f'Expected {args.pages} PDF pages; found {len(doc)}')
            for i, page in enumerate(doc, 1):
                # Refuse distortion/resampling to conceal a wrongly sized layout.
                expected = (args.width * 72 / args.dpi, args.height * 72 / args.dpi)
                if any(abs(a-b) > .02 for a, b in zip((page.rect.width, page.rect.height), expected)):
                    raise ValueError(f'Page {i} has incorrect physical dimensions; re-layout the PDF')
                pix = page.get_pixmap(dpi=args.dpi, colorspace=fitz.csRGB, alpha=False)
                path = stage / f'{args.prefix}_{i}.jpg'
                pix.pil_save(str(path), format='JPEG', quality=98, subsampling=0,
                             dpi=(args.dpi, args.dpi))
                with Image.open(path) as im:
                    if im.format != 'JPEG' or im.mode != 'RGB':
                        raise ValueError(f'Page {i} is not RGB JPEG')
                    if im.size != (args.width, args.height) or im.info.get('dpi') != (args.dpi, args.dpi):
                        raise ValueError(f'Page {i} has incorrect pixel dimensions or DPI')
                    samples = []
                    if args.uniform_background:
                        # Outer and inner blank paper positions for this profile.
                        # This catches margin differences, not all possible background layers.
                        for x, y in [(0.5,.01),(.01,.5),(.99,.5),(.5,.05),(.04,.5),(.96,.5)]:
                            samples.append(im.getpixel((int(x*im.width), int(y*im.height))))
                        if common_bg is None:
                            common_bg = samples[0]
                        if any(sample != common_bg for sample in samples):
                            raise ValueError(f'Page {i} background samples differ; inspect layers and proof')
                    im.verify()
                entries.append({'page': i, 'filename': path.name})
        report = {'pages': entries, 'width': args.width, 'height': args.height,
                  'dpi': args.dpi, 'sampled_background_rgb': common_bg,
                  'note': 'Pixel samples do not replace full visual and source-coverage checks.'}
        (stage / 'export-verification.json').write_text(json.dumps(report, indent=2) + '\n')
        stage.rename(args.output)
        print(f'Exported and verified {args.pages} JPEGs: {args.output}')
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


if __name__ == '__main__':
    main()
