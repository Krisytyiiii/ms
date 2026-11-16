/// 148-value feature vector, ported from `ml/src/features.py` (feature v2).
///
/// Layout: 102 color, 36 GLCM, 10 shape. Any change here must be mirrored in
/// the Python file and re-checked against `app/test/fixtures/vectors.json`,
/// because the SVM was trained on those exact numbers.
library;

import 'dart:math' as math;
import 'dart:typed_data';

import 'color_space.dart';
import 'image_ops.dart';
import 'leaf_focus.dart';

const int bins = 16;
const int glcmSize = 128;
const int levels = 32;
const List<int> distances = [1, 2, 4];
const List<double> angles = [0.0, math.pi / 4, math.pi / 2, 3 * math.pi / 4];
const int minBlobPx = 20;
const int shapeLen = 10;
const int colorLen = 3 * bins * 2 + 6;
const int glcmLen = 6 * 3 * 2;
const int bladeWidthAt = 6;
const int featureLength = colorLen + glcmLen + shapeLen;

/// `np.histogram(v, bins=16, range=(0, 1))` divided by the value count.
Float64List hsvHistogram(Float64List values, int count) {
  final hist = Float64List(3 * bins);
  if (count == 0) return hist;
  const stride = bins;
  for (var i = 0; i < 3; i++) {
    final channel = values.sublist(i * count, (i + 1) * count);
    for (final v in channel) {
      var idx = (v * bins).floor();
      if (idx >= bins) idx = bins - 1;
      if (idx < 0) continue;
      hist[i * stride + idx] += 1.0;
    }
  }
  for (var i = 0; i < hist.length; i++) {
    hist[i] /= count;
  }
  return hist;
}

Float64List _colorFeatures(RgbImage rgb, Uint8List mask) {
  final hsv = rgbToHsv(rgb);
  final n = rgb.pixelCount;
  final frame = Float64List(n * 3);
  for (var i = 0; i < n; i++) {
    frame[i] = hsv.h[i];
    frame[n + i] = hsv.s[i];
    frame[2 * n + i] = hsv.v[i];
  }

  var plantCount = 0;
  for (final m in mask) {
    if (m != 0) plantCount++;
  }
  final plant = Float64List(plantCount * 3);
  var p = 0;
  for (var i = 0; i < n; i++) {
    if (mask[i] == 0) continue;
    plant[p] = hsv.h[i];
    plant[plantCount + p] = hsv.s[i];
    plant[2 * plantCount + p] = hsv.v[i];
    p++;
  }

  final out = Float64List(colorLen);
  out.setRange(0, 3 * bins, hsvHistogram(frame, n));
  out.setRange(3 * bins, 6 * bins, hsvHistogram(plant, plantCount));

  var o = 6 * bins;
  if (plantCount == 0) {
    for (var i = 0; i < 6; i++) {
      out[o + i] = 0.0;
    }
    return out;
  }
  for (var c = 0; c < 3; c++) {
    var sum = 0.0;
    for (var i = 0; i < plantCount; i++) {
      sum += plant[c * plantCount + i];
    }
    final mean = sum / plantCount;
    var variance = 0.0;
    for (var i = 0; i < plantCount; i++) {
      final d = plant[c * plantCount + i] - mean;
      variance += d * d;
    }
    out[o + c] = mean;
    out[o + 3 + c] = math.sqrt(variance / plantCount);
  }
  return out;
}

/// Quantized 128px gray plane: blur, bilinear to 128, then 32 levels.
Uint8List quantizedGray(Uint8List gray, int w, int h) {
  final plane = Float64List(w * h);
  for (var i = 0; i < plane.length; i++) {
    plane[i] = gray[i].toDouble();
  }
  final blurred = gaussianBlurGray(plane, w, h, 0.5);
  final q = Uint8List(glcmSize * glcmSize);
  // skimage resize samples at output centres: (i + 0.5) * in/out - 0.5.
  final stepX = w / glcmSize;
  final stepY = h / glcmSize;
  for (var y = 0; y < glcmSize; y++) {
    for (var x = 0; x < glcmSize; x++) {
      final v = sampleBilinear(blurred, w, h, (x + 0.5) * stepX - 0.5, (y + 0.5) * stepY - 0.5);
      var vv = v.floor();
      if (vv < 0) vv = 0;
      if (vv > 255) vv = 255;
      var level = (vv * (levels - 1)) ~/ 255;
      if (level > levels - 1) level = levels - 1;
      q[y * glcmSize + x] = level;
    }
  }
  return q;
}

/// skimage offsets: `(round(d*sin(a)), round(d*cos(a)))` per (distance, angle).
///
/// Note the rounding: a "distance 2" diagonal is `(1, 1)`, not `(2, 2)`, and
/// "distance 4" is `(3, 3)`. Hardcoding `(d, d)` skews every d>1 GLCM value.
List<int> _offset(double angle, int distance) {
  final dr = (math.sin(angle) * distance).round();
  final dc = (math.cos(angle) * distance).round();
  return [dr, dc];
}

/// Contrast/dissimilarity/homogeneity/energy/correlation/ASM, angle mean + range.
Float64List _glcmFeatures(Uint8List gray, int w, int h) {
  final q = quantizedGray(gray, w, h);
  final out = Float64List(glcmLen);

  for (var di = 0; di < distances.length; di++) {
    final d = distances[di];
    // props[angle][prop]
    final props = <List<double>>[];
    for (final angle in angles) {
      final matrix = Float64List(levels * levels);
      final offset = _offset(angle, d);
      final dr = offset[0];
      final dc = offset[1];
      for (var y = 0; y < glcmSize; y++) {
        final y2 = y + dr;
        if (y2 < 0 || y2 >= glcmSize) continue;
        for (var x = 0; x < glcmSize; x++) {
          final x2 = x + dc;
          if (x2 < 0 || x2 >= glcmSize) continue;
          final i = q[y * glcmSize + x];
          final j = q[y2 * glcmSize + x2];
          matrix[i * levels + j] += 1.0;
          matrix[j * levels + i] += 1.0; // symmetric=True
        }
      }
      var total = 0.0;
      for (final v in matrix) {
        total += v;
      }
      if (total > 0) {
        for (var i = 0; i < matrix.length; i++) {
          matrix[i] /= total;
        }
      }
      props.add(_glcmProps(matrix));
    }

    for (var prop = 0; prop < 6; prop++) {
      final values = props.map((row) => row[prop]).toList();
      final mean = values.reduce((a, b) => a + b) / values.length;
      final maxV = values.reduce(math.max);
      final minV = values.reduce(math.min);
      // features.py appends all distances' means, then all distances' ranges.
      out[prop * 6 + di] = mean;
      out[prop * 6 + distances.length + di] = maxV - minV;
    }
  }
  return out;
}

List<double> _glcmProps(Float64List m) {
  var contrast = 0.0, dissimilarity = 0.0, homogeneity = 0.0, asm = 0.0;
  var meanI = 0.0, meanJ = 0.0;
  for (var i = 0; i < levels; i++) {
    for (var j = 0; j < levels; j++) {
      final p = m[i * levels + j];
      if (p == 0.0) continue;
      final diff = (i - j).toDouble();
      contrast += p * diff * diff;
      dissimilarity += p * diff.abs();
      homogeneity += p / (1.0 + diff * diff);
      asm += p * p;
      meanI += p * i;
      meanJ += p * j;
    }
  }
  var varI = 0.0, varJ = 0.0, cov = 0.0;
  for (var i = 0; i < levels; i++) {
    for (var j = 0; j < levels; j++) {
      final p = m[i * levels + j];
      if (p == 0.0) continue;
      final di = i - meanI;
      final dj = j - meanJ;
      varI += p * di * di;
      varJ += p * dj * dj;
      cov += p * di * dj;
    }
  }
  final denom = math.sqrt(varI * varJ);
  final correlation = denom == 0.0 ? 0.0 : cov / denom;
  return [
    contrast,
    dissimilarity,
    homogeneity,
    math.sqrt(asm),
    correlation,
    asm,
  ];
}

class _Region {
  _Region(this.area, this.coords);
  final int area;
  final List<int> coords; // packed y*width + x
}

/// 8-connected components, area-filtered, matching `label` + `regionprops`.
List<_Region> _regions(Uint8List mask, int w, int h) {
  final seen = Uint8List(mask.length);
  final regions = <_Region>[];
  final stack = <int>[];
  for (var start = 0; start < mask.length; start++) {
    if (mask[start] == 0 || seen[start] != 0) continue;
    final coords = <int>[];
    stack
      ..clear()
      ..add(start);
    seen[start] = 1;
    while (stack.isNotEmpty) {
      final idx = stack.removeLast();
      coords.add(idx);
      final y = idx ~/ w;
      final x = idx % w;
      for (var dy = -1; dy <= 1; dy++) {
        for (var dx = -1; dx <= 1; dx++) {
          if (dy == 0 && dx == 0) continue;
          final ny = y + dy;
          final nx = x + dx;
          if (ny < 0 || ny >= h || nx < 0 || nx >= w) continue;
          final n = ny * w + nx;
          if (mask[n] == 0 || seen[n] != 0) continue;
          seen[n] = 1;
          stack.add(n);
        }
      }
    }
    if (coords.length >= minBlobPx) {
      regions.add(_Region(coords.length, coords));
    }
  }
  return regions;
}

class _RegionProps {
  _RegionProps(this.area, this.eccentricity, this.solidity, this.extent, this.elongation);
  final int area;
  final double eccentricity;
  final double solidity;
  final double extent;
  final double elongation;
}

_RegionProps _regionProps(_Region region, int w, int h) {
  var sumX = 0.0, sumY = 0.0;
  var minY = h, maxY = -1, minX = w, maxX = -1;
  for (final idx in region.coords) {
    final y = idx ~/ w;
    final x = idx % w;
    sumX += x;
    sumY += y;
    if (y < minY) minY = y;
    if (y > maxY) maxY = y;
    if (x < minX) minX = x;
    if (x > maxX) maxX = x;
  }
  final n = region.area.toDouble();
  final cx = sumX / n;
  final cy = sumY / n;

  var mu20 = 0.0, mu02 = 0.0, mu11 = 0.0;
  for (final idx in region.coords) {
    final y = (idx ~/ w) - cy;
    final x = (idx % w) - cx;
    mu20 += x * x;
    mu02 += y * y;
    mu11 += x * y;
  }
  mu20 /= n;
  mu02 /= n;
  mu11 /= n;

  final common = math.sqrt((mu20 - mu02) * (mu20 - mu02) + 4.0 * mu11 * mu11);
  final majorEig = (mu20 + mu02 + common) / 2.0;
  final minorEig = (mu20 + mu02 - common) / 2.0;
  final major = 4.0 * math.sqrt(math.max(majorEig, 0.0));
  final minor = 4.0 * math.sqrt(math.max(minorEig, 0.0));
  final eccentricity = majorEig <= 0.0
      ? 0.0
      : math.sqrt(math.max(0.0, 1.0 - (minorEig / majorEig)));

  final hullArea = _convexHullArea(region.coords, w);
  final solidity = hullArea == 0 ? 0.0 : region.area / hullArea;
  final bboxArea = (maxY - minY + 1) * (maxX - minX + 1);
  final extent = bboxArea == 0 ? 0.0 : region.area / bboxArea;
  final elongation = math.log(
    1.0 + math.min(major / (minor < 1.0 ? 1.0 : minor), 50.0),
  );

  return _RegionProps(region.area, eccentricity, solidity, extent, elongation);
}

/// Area of the filled convex hull, in pixels (skimage counts hull pixels).
double _convexHullArea(List<int> coords, int w) {
  if (coords.length < 3) return coords.length.toDouble();
  final points = <List<int>>[];
  for (final idx in coords) {
    points.add([idx ~/ w, idx % w]);
  }
  points.sort((a, b) => a[0] != b[0] ? a[0] - b[0] : a[1] - b[1]);
  final lower = <List<int>>[];
  for (final p in points) {
    while (lower.length >= 2 && _cross(lower[lower.length - 2], lower.last, p) <= 0) {
      lower.removeLast();
    }
    lower.add(p);
  }
  final upper = <List<int>>[];
  for (final p in points.reversed) {
    while (upper.length >= 2 && _cross(upper[upper.length - 2], upper.last, p) <= 0) {
      upper.removeLast();
    }
    upper.add(p);
  }
  final hull = [...lower.sublist(0, lower.length - 1), ...upper.sublist(0, upper.length - 1)];

  var count = 0;
  var minY = hull.first[0];
  var maxY = hull.first[0];
  for (final p in hull) {
    minY = math.min(minY, p[0]);
    maxY = math.max(maxY, p[0]);
  }
  for (var y = minY; y <= maxY; y++) {
    var lo = double.infinity;
    var hi = double.negativeInfinity;
    for (var i = 0; i < hull.length; i++) {
      final a = hull[i];
      final b = hull[(i + 1) % hull.length];
      if (a[0] == b[0]) {
        if (y == a[0]) {
          lo = math.min(lo, math.min(a[1], b[1]).toDouble());
          hi = math.max(hi, math.max(a[1], b[1]).toDouble());
        }
        continue;
      }
      final y0 = math.min(a[0], b[0]);
      final y1 = math.max(a[0], b[0]);
      if (y < y0 || y > y1) continue;
      final t = (y - a[0]) / (b[0] - a[0]);
      final x = a[1] + (b[1] - a[1]) * t;
      lo = math.min(lo, x);
      hi = math.max(hi, x);
    }
    if (lo == double.infinity) continue;
    final from = lo.round();
    final to = hi.round();
    if (to >= from) count += to - from + 1;
  }
  return count.toDouble();
}

double _cross(List<int> o, List<int> a, List<int> b) =>
    ((a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])).toDouble();

/// Union of the area-filtered regions, the mask the shape block thins.
///
/// Exposed so the parity diagnostic compares the same intermediate the app
/// uses; `extractVector` calls this indirectly through the same `_regions`.
Uint8List cleanMask(Uint8List mask, int w, int h) {
  final clean = Uint8List(mask.length);
  for (final region in _regions(mask, w, h)) {
    for (final idx in region.coords) {
      clean[idx] = 1;
    }
  }
  return clean;
}

/// Zhang-Suen thinning, matching `skimage.morphology.skeletonize`.
Uint8List skeletonize(Uint8List mask, int w, int h) {
  final img = Uint8List.fromList(mask);
  bool get(int y, int x) {
    if (y < 0 || y >= h || x < 0 || x >= w) return false;
    return img[y * w + x] != 0;
  }

  var changed = true;
  final toClear = <int>[];
  while (changed) {
    changed = false;
    for (var step = 0; step < 2; step++) {
      toClear.clear();
      for (var y = 1; y < h - 1; y++) {
        for (var x = 1; x < w - 1; x++) {
          if (!get(y, x)) continue;
          final p2 = get(y - 1, x);
          final p3 = get(y - 1, x + 1);
          final p4 = get(y, x + 1);
          final p5 = get(y + 1, x + 1);
          final p6 = get(y + 1, x);
          final p7 = get(y + 1, x - 1);
          final p8 = get(y, x - 1);
          final p9 = get(y - 1, x - 1);
          final neighbors = [p2, p3, p4, p5, p6, p7, p8, p9];
          var b = 0;
          for (final v in neighbors) {
            if (v) b++;
          }
          if (b < 2 || b > 6) continue;
          var a = 0;
          for (var i = 0; i < 8; i++) {
            if (!neighbors[i] && neighbors[(i + 1) % 8]) a++;
          }
          if (a != 1) continue;
          if (step == 0) {
            if (p2 && p4 && p6) continue;
            if (p4 && p6 && p8) continue;
          } else {
            if (p2 && p4 && p8) continue;
            if (p2 && p6 && p8) continue;
          }
          toClear.add(y * w + x);
        }
      }
      if (toClear.isNotEmpty) {
        changed = true;
        for (final idx in toClear) {
          img[idx] = 0;
        }
      }
    }
  }
  return img;
}

/// Squared Euclidean distance to the nearest background pixel.
Float64List edtSquared(Uint8List mask, int w, int h) {
  const inf = 1e20;
  final grid = Float64List(w * h);
  for (var i = 0; i < grid.length; i++) {
    grid[i] = mask[i] != 0 ? inf : 0.0;
  }

  List<double> pass1d(List<double> f, int n) {
    final d = Float64List(n);
    final v = Int32List(n);
    final z = Float64List(n + 1);
    var k = 0;
    v[0] = 0;
    z[0] = double.negativeInfinity;
    z[1] = double.infinity;
    for (var q = 1; q < n; q++) {
      while (true) {
        final s = ((f[q] + q * q) - (f[v[k]] + v[k] * v[k])) / (2.0 * q - 2.0 * v[k]);
        if (s <= z[k]) {
          k--;
          if (k < 0) {
            k = 0;
            break;
          }
        } else {
          break;
        }
      }
      k++;
      v[k] = q;
      z[k] = ((f[q] + q * q) - (f[v[k - 1]] + v[k - 1] * v[k - 1])) / (2.0 * q - 2.0 * v[k - 1]);
      z[k + 1] = double.infinity;
    }
    k = 0;
    for (var q = 0; q < n; q++) {
      while (z[k + 1] < q) {
        k++;
      }
      final dq = q - v[k];
      d[q] = dq * dq + f[v[k]];
    }
    return d;
  }

  for (var y = 0; y < h; y++) {
    final row = List<double>.generate(w, (x) => grid[y * w + x]);
    final out = pass1d(row, w);
    for (var x = 0; x < w; x++) {
      grid[y * w + x] = out[x];
    }
  }
  for (var x = 0; x < w; x++) {
    final col = List<double>.generate(h, (y) => grid[y * w + x]);
    final out = pass1d(col, h);
    for (var y = 0; y < h; y++) {
      grid[y * w + x] = out[y];
    }
  }
  return grid;
}

double percentile(List<double> sorted, double p) {
  if (sorted.isEmpty) return 0.0;
  if (sorted.length == 1) return sorted.first;
  final rank = (p / 100.0) * (sorted.length - 1);
  final lo = rank.floor();
  final hi = math.min(lo + 1, sorted.length - 1);
  final frac = rank - lo;
  return sorted[lo] + (sorted[hi] - sorted[lo]) * frac;
}

Float64List _shapeFeatures(Uint8List mask, {required bool usedFallback, required int w, required int h}) {
  final out = Float64List(shapeLen);
  final side = math.max(w, h).toDouble();
  out[0] = maskMean(mask);
  out[9] = usedFallback ? 1.0 : 0.0;

  final regions = _regions(mask, w, h);
  if (regions.isEmpty) return out;

  final clean = Uint8List(mask.length);
  for (final region in regions) {
    for (final idx in region.coords) {
      clean[idx] = 1;
    }
  }

  final props = regions.map((r) => _regionProps(r, w, h)).toList();
  final totalArea = props.fold<double>(0.0, (a, p) => a + p.area);

  out[1] = math.log(1.0 + regions.length);
  out[2] = props.fold<double>(0.0, (a, p) => a + (p.area / totalArea) * p.eccentricity);
  out[3] = props.fold<double>(0.0, (a, p) => a + (p.area / totalArea) * p.solidity);
  out[4] = props.fold<double>(0.0, (a, p) => a + (p.area / totalArea) * p.extent);
  out[5] = props.fold<double>(0.0, (a, p) => a + (p.area / totalArea) * p.elongation);

  final skeleton = skeletonize(clean, w, h);
  var skeletonCount = 0;
  var cleanCount = 0;
  for (var i = 0; i < clean.length; i++) {
    if (skeleton[i] != 0) skeletonCount++;
    if (clean[i] != 0) cleanCount++;
  }
  if (skeletonCount > 0 && cleanCount > 0) {
    final edt = edtSquared(clean, w, h);
    final widths = <double>[];
    for (var i = 0; i < edt.length; i++) {
      if (skeleton[i] != 0) widths.add(2.0 * math.sqrt(edt[i]));
    }
    widths.sort();
    final q25 = percentile(widths, 25);
    final q50 = percentile(widths, 50);
    final q75 = percentile(widths, 75);
    out[bladeWidthAt] = q50 / side;
    out[7] = (q75 - q25) / side;
    out[8] = skeletonCount / cleanCount;
  }
  return out;
}

/// Otsu threshold on a histogram of 256 bins.
int otsuThreshold(Uint8List gray) {
  final hist = Float64List(256);
  for (final v in gray) {
    hist[v] += 1.0;
  }
  final total = gray.length.toDouble();
  var sumAll = 0.0;
  for (var i = 0; i < 256; i++) {
    sumAll += i * hist[i];
  }
  var sumB = 0.0, wB = 0.0, best = 0.0, threshold = 0;
  for (var t = 0; t < 256; t++) {
    wB += hist[t];
    if (wB == 0) continue;
    final wF = total - wB;
    if (wF == 0) break;
    sumB += t * hist[t];
    final mB = sumB / wB;
    final mF = (sumAll - sumB) / wF;
    final between = wB * wF * (mB - mF) * (mB - mF);
    if (between > best) {
      best = between;
      threshold = t;
    }
  }
  return threshold;
}

/// Full v2 vector for a prepared 256px RGB image.
Float64List extractVector(RgbImage rgb, {int width = 256, int height = 256}) {
  final w = rgb.width;
  final h = rgb.height;
  final gray = rgbToGrayU8(rgb);
  final mask = plantMask(rgb);
  final mean = maskMean(mask);
  Uint8List shapeMask;
  var usedFallback = false;
  if (mean >= 0.01) {
    shapeMask = mask;
  } else {
    final t = otsuThreshold(gray);
    var darkCount = 0;
    for (final v in gray) {
      if (v < t) darkCount++;
    }
    final useDark = darkCount / gray.length <= 0.5;
    shapeMask = Uint8List(gray.length);
    for (var i = 0; i < gray.length; i++) {
      shapeMask[i] = ((gray[i] < t) == useDark) ? 1 : 0;
    }
    usedFallback = true;
  }

  final vector = Float64List(featureLength);
  vector.setRange(0, colorLen, _colorFeatures(rgb, mask));
  vector.setRange(colorLen, colorLen + glcmLen, _glcmFeatures(gray, w, h));
  vector.setRange(
    colorLen + glcmLen,
    featureLength,
    _shapeFeatures(shapeMask, usedFallback: usedFallback, w: w, h: h),
  );
  return vector;
}
