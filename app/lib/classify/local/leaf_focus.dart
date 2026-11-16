/// Plant mask and plant crop, ported from `ml/src/leaf_focus.py`.
///
/// The mask is a diagnostic plus an optional zoom; it is not the science. The
/// thresholds below must stay in step with the Python file or the crop window
/// moves and every downstream feature changes.
library;

import 'dart:math' as math;
import 'dart:typed_data';

import 'color_space.dart';
import 'image_ops.dart';

const int analyzeMaxSide = 512;

const int _exgMin = 20;
const double _hueLo = 0.16;
const double _hueHi = 0.50;
const double _satMin = 0.12;
const double _valLo = 0.08;
const double _valHi = 0.92;

const double cropPad = 0.15;
const double cropMinArea = 0.02;
const double cropMaxArea = 0.90;
const int cropMinSide = 16;

const int trainImageSize = 256;

/// Green-pixel mask: excess-green cut plus an HSV window.
Uint8List plantMask(RgbImage rgb) {
  final n = rgb.pixelCount;
  final hsv = rgbToHsv(rgb);
  final mask = Uint8List(n);
  for (var i = 0; i < n; i++) {
    final r = rgb.data[i * 3];
    final g = rgb.data[i * 3 + 1];
    final b = rgb.data[i * 3 + 2];
    final exg = 2 * g - r - b;
    final hue = hsv.h[i];
    final sat = hsv.s[i];
    final val = hsv.v[i];
    final greenish =
        hue >= _hueLo &&
        hue <= _hueHi &&
        sat >= _satMin &&
        val >= _valLo &&
        val <= _valHi;
    mask[i] = (exg >= _exgMin && greenish) ? 1 : 0;
  }
  return mask;
}

double maskMean(Uint8List mask) {
  if (mask.isEmpty) return 0.0;
  var sum = 0;
  for (final v in mask) {
    sum += v;
  }
  return sum / mask.length;
}

class _Preview {
  _Preview(this.image, this.scaleX, this.scaleY);
  final RgbImage image;
  final double scaleX;
  final double scaleY;
}

_Preview _forAnalysis(RgbImage rgb) {
  final longest = math.max(rgb.height, rgb.width);
  if (longest <= analyzeMaxSide) {
    return _Preview(rgb, 1.0, 1.0);
  }
  final scale = analyzeMaxSide / longest;
  final newH = math.max(1, (rgb.height * scale).round());
  final newW = math.max(1, (rgb.width * scale).round());
  final preview = resizeRgb(rgb, newW, newH, ResampleFilter.triangle);
  return _Preview(preview, rgb.width / newW, rgb.height / newH);
}

class CropResult {
  CropResult(this.image, this.didCrop);
  final RgbImage image;
  final bool didCrop;
}

/// Zoom to the plant-mask bbox when it is a mid-size region, else the frame.
CropResult cropToPlant(RgbImage rgb) {
  final preview = _forAnalysis(rgb);
  final mask = plantMask(preview.image);
  if (mask.isEmpty) return CropResult(rgb, false);

  var top = preview.image.height, bottom = -1, left = preview.image.width, right = -1;
  for (var y = 0; y < preview.image.height; y++) {
    for (var x = 0; x < preview.image.width; x++) {
      if (mask[y * preview.image.width + x] == 0) continue;
      if (y < top) top = y;
      if (y > bottom) bottom = y;
      if (x < left) left = x;
      if (x > right) right = x;
    }
  }
  if (bottom < 0 || right < 0) return CropResult(rgb, false);

  final y0 = top;
  final y1 = bottom + 1;
  final x0 = left;
  final x1 = right + 1;
  final smallH = preview.image.height;
  final smallW = preview.image.width;
  final areaFrac = ((y1 - y0) * (x1 - x0)) / (smallH * smallW);
  if (areaFrac < cropMinArea || areaFrac > cropMaxArea) {
    return CropResult(rgb, false);
  }

  final padY = ((y1 - y0) * cropPad).round();
  final padX = ((x1 - x0) * cropPad).round();
  final cropTop = math.max(0, ((y0 - padY) * preview.scaleY).floor());
  final cropLeft = math.max(0, ((x0 - padX) * preview.scaleX).floor());
  final cropBottom = math.min(rgb.height, ((y1 + padY) * preview.scaleY).floor());
  final cropRight = math.min(rgb.width, ((x1 + padX) * preview.scaleX).floor());
  if (cropBottom - cropTop < cropMinSide || cropRight - cropLeft < cropMinSide) {
    return CropResult(rgb, false);
  }
  return CropResult(rgb.crop(cropLeft, cropTop, cropRight, cropBottom), true);
}

/// Plant crop when the mask allows it, then a 256px LANCZOS resize.
RgbImage prepareRgb(RgbImage rgb, {int size = trainImageSize}) {
  final cropped = cropToPlant(rgb);
  return resizeRgb(cropped.image, size, size, ResampleFilter.lanczos3);
}
