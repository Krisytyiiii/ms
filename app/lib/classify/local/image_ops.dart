/// RGB image ops matching the Python training path.
///
/// The training code resizes twice and crops once: a 512px BILINEAR preview for
/// the plant mask, a crop of the original, then a 256px LANCZOS resize. The
/// resampling weights follow Pillow's separable filter so the pixel values
/// match `ml/src/preprocess.py` and `ml/src/leaf_focus.py`.
library;

import 'dart:math' as math;
import 'dart:typed_data';

import 'package:image/image.dart' as img;

/// Packed 8-bit RGB, row major: 3 bytes per pixel.
class RgbImage {
  RgbImage(this.width, this.height, this.data)

    : assert(data.length == width * height * 3);

  final int width;
  final int height;
  final Uint8List data;

  int get pixelCount => width * height;

  int red(int i) => data[i * 3];

  int green(int i) => data[i * 3 + 1];

  int blue(int i) => data[i * 3 + 2];

  RgbImage crop(int left, int top, int right, int bottom) {
    final w = right - left;
    final h = bottom - top;
    final out = Uint8List(w * h * 3);
    for (var y = 0; y < h; y++) {
      final srcStart = ((top + y) * width + left) * 3;
      out.setRange(y * w * 3, (y + 1) * w * 3, data, srcStart);
    }
    return RgbImage(w, h, out);
  }
}

/// Decode bytes to RGB, applying EXIF orientation like `ImageOps.exif_transpose`.
RgbImage decodeToRgb(Uint8List bytes) {
  final decoded = img.decodeImage(bytes);
  if (decoded == null) {
    throw const FormatException('Unsupported or corrupt image.');
  }
  final oriented = img.bakeOrientation(decoded);
  final w = oriented.width;
  final h = oriented.height;
  final out = Uint8List(w * h * 3);
  var o = 0;
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      final p = oriented.getPixel(x, y);
      out[o++] = p.r.toInt();
      out[o++] = p.g.toInt();
      out[o++] = p.b.toInt();
    }
  }
  return RgbImage(w, h, out);
}

enum ResampleFilter { triangle, lanczos3 }

/// Pillow-compatible separable resample.
///
/// Pillow converts each pass back to 8 bits, so this does too; skipping that
/// would make the result subtly brighter and drift the GLCM block.
RgbImage resizeRgb(RgbImage src, int outW, int outH, ResampleFilter filter) {
  if (src.width == outW && src.height == outH) {
    return RgbImage(src.width, src.height, Uint8List.fromList(src.data));
  }
  final horizontal = _resampleAxis(
    src,
    outW,
    axisX: true,
    filter: filter,
  );
  return _resampleAxis(horizontal, outH, axisX: false, filter: filter);
}

double _kernel(ResampleFilter filter, double x) {
  switch (filter) {
    case ResampleFilter.triangle:
      final ax = x.abs();
      return ax < 1.0 ? 1.0 - ax : 0.0;
    case ResampleFilter.lanczos3:
      final ax = x.abs();
      if (ax == 0.0) return 1.0;
      if (ax >= 3.0) return 0.0;
      final pix = math.pi * x;
      return (3.0 * math.sin(pix) * math.sin(pix / 3.0)) / (pix * pix);
  }
}

class _Weights {
  _Weights(this.start, this.weights);
  final int start;
  final Float64List weights;
}

_Weights _weightsFor(
  int outIndex,
  int inSize,
  int outSize,
  ResampleFilter filter,
) {
  final supportBase = filter == ResampleFilter.triangle ? 1.0 : 3.0;
  final scale = inSize / outSize;
  final filterscale = math.max(scale, 1.0);
  final support = supportBase * filterscale;
  final center = (outIndex + 0.5) * scale;

  var start = (center - support + 0.5).floor();
  if (start < 0) start = 0;
  var end = (center + support + 0.5).floor();
  if (end > inSize) end = inSize;
  if (end <= start) end = math.min(inSize, start + 1);

  final weights = Float64List(end - start);
  var total = 0.0;
  for (var i = 0; i < weights.length; i++) {
    final w = _kernel(filter, (i + start - center + 0.5) / filterscale);
    weights[i] = w;
    total += w;
  }
  if (total != 0.0) {
    for (var i = 0; i < weights.length; i++) {
      weights[i] /= total;
    }
  }
  return _Weights(start, weights);
}

RgbImage _resampleAxis(
  RgbImage src,
  int outSize, {
  required bool axisX,
  required ResampleFilter filter,
}) {
  final inSize = axisX ? src.width : src.height;
  final outW = axisX ? outSize : src.width;
  final outH = axisX ? src.height : outSize;
  final out = Uint8List(outW * outH * 3);
  final inStride = src.width * 3;
  final outStride = outW * 3;
  final cache = List<_Weights?>.filled(outSize, null);
  for (var y = 0; y < outH; y++) {
    final outRow = y * outStride;
    // The horizontal pass reads source row `y`, whose stride is the *input*
    // width; using the output stride here shifts every row after the first.
    final inRow = y * inStride;
    for (var x = 0; x < outW; x++) {
      final index = axisX ? x : y;
      final w = cache[index] ??= _weightsFor(index, inSize, outSize, filter);
      var r = 0.0, g = 0.0, b = 0.0;
      if (axisX) {
        for (var k = 0; k < w.weights.length; k++) {
          final p = inRow + (w.start + k) * 3;
          final wt = w.weights[k];
          r += wt * src.data[p];
          g += wt * src.data[p + 1];
          b += wt * src.data[p + 2];
        }
      } else {
        for (var k = 0; k < w.weights.length; k++) {
          final sy = w.start + k;
          final p = sy * inStride + x * 3;
          final wt = w.weights[k];
          r += wt * src.data[p];
          g += wt * src.data[p + 1];
          b += wt * src.data[p + 2];
        }
      }
      final o = outRow + x * 3;
      out[o] = _clip8(r);
      out[o + 1] = _clip8(g);
      out[o + 2] = _clip8(b);
    }
  }
  return RgbImage(outW, outH, out);
}

int _clip8(double v) {
  if (v <= 0.0) return 0;
  if (v >= 255.0) return 255;
  return (v + 0.5).floor();
}

/// Separable Gaussian used before the GLCM downsample (`anti_aliasing=True`).
Float64List gaussianBlurGray(Float64List gray, int w, int h, double sigma) {
  final radius = (4.0 * sigma).ceil();
  final kernel = Float64List(radius * 2 + 1);
  var total = 0.0;
  for (var i = -radius; i <= radius; i++) {
    final v = math.exp(-(i * i) / (2.0 * sigma * sigma));
    kernel[i + radius] = v;
    total += v;
  }
  for (var i = 0; i < kernel.length; i++) {
    kernel[i] /= total;
  }

  final tmp = Float64List(w * h);
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      var acc = 0.0;
      for (var k = -radius; k <= radius; k++) {
        var sx = x + k;
        if (sx < 0 || sx >= w) sx = sx < 0 ? -sx - 1 : 2 * w - sx - 1;
        acc += kernel[k + radius] * gray[y * w + sx];
      }
      tmp[y * w + x] = acc;
    }
  }
  final out = Float64List(w * h);
  for (var y = 0; y < h; y++) {
    for (var x = 0; x < w; x++) {
      var acc = 0.0;
      for (var k = -radius; k <= radius; k++) {
        var sy = y + k;
        if (sy < 0 || sy >= h) sy = sy < 0 ? -sy - 1 : 2 * h - sy - 1;
        acc += kernel[k + radius] * tmp[sy * w + x];
      }
      out[y * w + x] = acc;
    }
  }
  return out;
}

/// Bilinear sample of a float plane at `(x, y)` in *pixel index* coordinates.
double sampleBilinear(Float64List plane, int w, int h, double x, double y) {
  if (x < 0) x = 0;
  if (y < 0) y = 0;
  if (x > w - 1) x = (w - 1).toDouble();
  if (y > h - 1) y = (h - 1).toDouble();
  final x0 = x.floor();
  final y0 = y.floor();
  final x1 = math.min(x0 + 1, w - 1);
  final y1 = math.min(y0 + 1, h - 1);
  final fx = x - x0;
  final fy = y - y0;
  final p00 = plane[y0 * w + x0];
  final p10 = plane[y0 * w + x1];
  final p01 = plane[y1 * w + x0];
  final p11 = plane[y1 * w + x1];
  final top = p00 + (p10 - p00) * fx;
  final bottom = p01 + (p11 - p01) * fx;
  return top + (bottom - top) * fy;
}
