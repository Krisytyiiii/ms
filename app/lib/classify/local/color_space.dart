/// Color conversions matching `skimage.color` and the training thresholds.
///
/// `rgb2hsv` here follows skimage's branch order: the hue branch is chosen by
/// which channel equals the maximum, and channels are divided by `delta` only
/// when `delta != 0`. Gray pixels (all channels equal) land on hue 0, which is
/// what skimage produces because `red == maxc` is true first.
library;

import 'dart:typed_data';

import 'image_ops.dart';

/// skimage's RGB-to-gray weights, applied in [0, 1] then scaled back to 0..255.
const double _wr = 0.2125;
const double _wg = 0.7154;
const double _wb = 0.0721;

/// `skimage.color.rgb2gray` then `* 255` and truncate to uint8.
Uint8List rgbToGrayU8(RgbImage image) {
  final out = Uint8List(image.pixelCount);
  for (var i = 0; i < out.length; i++) {
    final r = image.data[i * 3] / 255.0;
    final g = image.data[i * 3 + 1] / 255.0;
    final b = image.data[i * 3 + 2] / 255.0;
    final v = (r * _wr + g * _wg + b * _wb) * 255.0;
    out[i] = v <= 0.0 ? 0 : (v >= 255.0 ? 255 : v.floor());
  }
  return out;
}

/// HSV planes for every pixel, each value in [0, 1].
class HsvPlanes {
  HsvPlanes(this.h, this.s, this.v, this.count);
  final Float64List h;
  final Float64List s;
  final Float64List v;
  final int count;
}

HsvPlanes rgbToHsv(RgbImage image) {
  final n = image.pixelCount;
  final h = Float64List(n);
  final s = Float64List(n);
  final v = Float64List(n);
  for (var i = 0; i < n; i++) {
    final r = image.data[i * 3] / 255.0;
    final g = image.data[i * 3 + 1] / 255.0;
    final b = image.data[i * 3 + 2] / 255.0;
    final maxc = r > g ? (r > b ? r : b) : (g > b ? g : b);
    final minc = r < g ? (r < b ? r : b) : (g < b ? g : b);
    final delta = maxc - minc;
    s[i] = maxc != 0.0 ? delta / maxc : 0.0;
    v[i] = maxc;
    final rc = delta != 0.0 ? (maxc - r) / delta : 0.0;
    final gc = delta != 0.0 ? (maxc - g) / delta : 0.0;
    final bc = delta != 0.0 ? (maxc - b) / delta : 0.0;
    double hue;
    if (r == maxc) {
      hue = bc - gc;
    } else if (g == maxc) {
      hue = 2.0 + rc - bc;
    } else {
      hue = 4.0 + gc - rc;
    }
    hue = (hue / 6.0) % 1.0;
    if (hue < 0.0) hue += 1.0;
    h[i] = hue;
  }
  return HsvPlanes(h, s, v, n);
}
