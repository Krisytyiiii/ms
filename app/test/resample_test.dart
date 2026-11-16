/// Lock the resampler to Pillow.
///
/// The feature fixtures start from an already-prepared 256px PNG, so they run
/// the resampler in its identity fast path and cannot see a resampling bug. A
/// wrong row stride here once shipped: the plant crop masked it, `flutter test`
/// stayed green, and every on-device feature vector drifted. These vectors come
/// from `PIL.Image.resize(..., Image.Resampling.LANCZOS)` and
/// `...BILINEAR` on the same 7x5 source, so any drift fails here instead.
library;

import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:marine_see/classify/local/image_ops.dart';

/// 7x5, asymmetric per row so a wrong row stride cannot hide.
const List<List<int>> _source = [
  [0, 0, 0, 37, 13, 91, 74, 26, 182, 111, 39, 17, 148, 52, 108, 185, 65, 199, 222, 78, 34],
  [11, 61, 7, 48, 74, 98, 85, 87, 189, 122, 100, 24, 159, 113, 115, 196, 126, 206, 233, 139, 41],
  [22, 122, 14, 59, 135, 105, 96, 148, 196, 133, 161, 31, 170, 174, 122, 207, 187, 213, 244, 200, 48],
  [33, 183, 21, 70, 196, 112, 107, 209, 203, 144, 222, 38, 181, 235, 129, 218, 248, 220, 255, 5, 55],
  [44, 244, 28, 81, 1, 119, 118, 14, 210, 155, 27, 45, 192, 40, 136, 229, 53, 227, 10, 66, 62],
];

const List<List<int>> _lanczos4x3 = [
  [18, 23, 53, 80, 42, 117, 149, 65, 102, 209, 98, 120],
  [36, 135, 65, 99, 167, 129, 166, 195, 114, 240, 173, 132],
  [54, 162, 77, 115, 90, 141, 196, 136, 126, 165, 81, 144],
];

const List<List<int>> _bilinear4x3 = [
  [24, 33, 51, 82, 53, 121, 150, 77, 104, 208, 97, 111],
  [41, 129, 62, 99, 149, 132, 167, 173, 115, 225, 163, 122],
  [58, 155, 73, 116, 99, 143, 184, 123, 126, 166, 85, 133],
];

RgbImage _flatten(List<List<int>> rows) {
  final data = Uint8List(7 * 5 * 3);
  for (var i = 0; i < rows.length; i++) {
    data.setRange(i * 21, (i + 1) * 21, rows[i]);
  }
  return RgbImage(7, 5, data);
}

void main() {
  test('Lanczos3 matches Pillow', () {
    final out = resizeRgb(_flatten(_source), 4, 3, ResampleFilter.lanczos3);
    expect(out.width, 4);
    expect(out.height, 3);
    for (var y = 0; y < 3; y++) {
      expect(
        out.data.sublist(y * 12, (y + 1) * 12),
        _lanczos4x3[y],
        reason: 'row $y',
      );
    }
  });

  test('bilinear matches Pillow', () {
    final out = resizeRgb(_flatten(_source), 4, 3, ResampleFilter.triangle);
    for (var y = 0; y < 3; y++) {
      expect(
        out.data.sublist(y * 12, (y + 1) * 12),
        _bilinear4x3[y],
        reason: 'row $y',
      );
    }
  });
}
