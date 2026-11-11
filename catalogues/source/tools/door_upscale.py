"""The website's Wellup Door Hall: the small price-list door pictures, made four times larger without losing the
photograph.

Five models (PT 109, 409, 709, 809 and 909) have no shop photograph: their only pictures are the price list's own, 165
to 307 px wide. Shown on the Door Hall's stage, about 900 px tall on a laptop, they were blown up about five times and
looked soft. This makes each four times larger:
  · Real-ESRGAN (x4plus, run on the CPU with ncnn) draws the fine edges — the louvres, the handle, the frame;
  · the photograph itself gives every tone and colour: the result is the photograph enlarged smoothly and blurred to its
    own sharpness (sigma 2.5 px at the new size), plus k = 0.6 of the finer detail Real-ESRGAN adds (what blurring its
    picture by the same takes away). So nothing is recoloured or darkened, and brought back to the photograph's size
    it matches it closely; the louvres' lines keep the photograph's soft grey rather than Real-ESRGAN's ink.
It writes <photos dir>/x4/<slug>.jpg (JPEG, quality 95), which door_leaves.py then reads in place of its own 2x
enlargement. Real-ESRGAN draws what it judges the edges to be; it cannot add what the small picture does not show.

    pip install ncnn pillow numpy
    models: realesrgan-x4plus.param and .bin, from the release zip
      https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip
    python3 door_upscale.py <photos dir> <model base, e.g. models/realesrgan-x4plus> [slug ...]"""
import glob
import os
import sys

import numpy as np
from PIL import Image, ImageFilter

SMALL = ("pt-109-", "pt-409-", "pt-709-", "pt-809-", "pt-909-")
SIGMA, K = 2.5, 0.6


def esrgan_x4(base, im, tile=192, pad=12):
    """Real-ESRGAN x4 on the CPU (ncnn), in tiles with a margin, so a picture of any size fits."""
    import ncnn
    net = ncnn.Net()
    net.opt.use_vulkan_compute = False
    net.opt.num_threads = os.cpu_count() or 4
    net.load_param(base + ".param")
    net.load_model(base + ".bin")
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255.0
    h, w, _ = a.shape
    out = np.zeros((h * 4, w * 4, 3), np.float32)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            y1, x1 = min(h, y0 + tile), min(w, x0 + tile)
            ya, xa, yb, xb = max(0, y0 - pad), max(0, x0 - pad), min(h, y1 + pad), min(w, x1 + pad)
            # (ncnn reads the array where it lies, without copying it: it is kept until the network has run)
            t = np.ascontiguousarray(a[ya:yb, xa:xb].transpose(2, 0, 1))
            mat = ncnn.Mat(t)
            ex = net.create_extractor()
            ex.input("data", mat)
            _, m = ex.extract("output")
            o = np.array(m).transpose(1, 2, 0)
            oy, ox = (y0 - ya) * 4, (x0 - xa) * 4
            out[y0 * 4:y1 * 4, x0 * 4:x1 * 4] = o[oy:oy + (y1 - y0) * 4, ox:ox + (x1 - x0) * 4]
    return Image.fromarray(np.clip(out * 255 + 0.5, 0, 255).astype(np.uint8))


def merge(photo, sr, sigma=SIGMA, k=K):
    """The photograph's own tones and colours (enlarged smoothly, at its own sharpness), and k of the finer detail of the
    super-resolved picture."""
    big = photo.convert("RGB").resize(sr.size, Image.LANCZOS)
    lo_p = np.asarray(big.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)
    s = np.asarray(sr.convert("RGB")).astype(np.float32)
    lo_s = np.asarray(sr.convert("RGB").filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)
    return Image.fromarray(np.clip(lo_p + k * (s - lo_s) + 0.5, 0, 255).astype(np.uint8))


def main(src, base, names):
    os.makedirs(os.path.join(src, "x4"), exist_ok=True)
    names = names or sorted(os.path.basename(f)[:-4] for f in glob.glob(os.path.join(src, "pt-*.jpg"))
                            if os.path.basename(f).startswith(SMALL))
    for n in names:
        photo = Image.open(os.path.join(src, n + ".jpg"))
        out = merge(photo, esrgan_x4(base, photo))
        out.save(os.path.join(src, "x4", n + ".jpg"), quality=95, subsampling=0, optimize=True)
        print(f"{n:24s} {photo.size[0]} x {photo.size[1]} -> {out.size[0]} x {out.size[1]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
