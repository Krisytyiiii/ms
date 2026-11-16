/// On-device SVM prediction from `svm_mobile.bin` + `svm_mobile.json`.
///
/// The math mirrors `ml/src/export_mobile.py`, which is checked against
/// scikit-learn in `ml/src/test_export_mobile.py` to ~1e-14. The slug comes
/// from one-vs-one votes (sklearn `predict`); the percent comes from coupled
/// Platt probabilities (sklearn `predict_proba`). They can disagree, so both
/// are kept.
library;

import 'dart:convert';
import 'dart:math' as math;
import 'dart:typed_data';

import 'package:flutter/services.dart';

class SvmPrediction {
  const SvmPrediction({
    required this.slug,
    required this.confidence,
    required this.top,
    required this.lowConfidence,
    required this.threshold,
  });

  final String slug;
  final double confidence;
  final List<MapEntry<String, double>> top;
  final bool lowConfidence;
  final double threshold;
}

class SvmModel {
  SvmModel._({
    required this.classes,
    required this.pairs,
    required this.nFeatures,
    required this.gamma,
    required this.threshold,
    required Float64List scalerMean,
    required Float64List scalerScale,
    required Float64List supportVectors,
    required Float64List dualCoef,
    required Float64List intercept,
    required Float64List probA,
    required Float64List probB,
    required Int32List nSupport,
  }) : _mean = scalerMean,
       _scale = scalerScale,
       _supportVectors = supportVectors,
       _dualCoef = dualCoef,
       _intercept = intercept,
       _probA = probA,
       _probB = probB,
       _nSupport = nSupport;

  final List<String> classes;
  final int pairs;
  final int nFeatures;
  final double gamma;
  final double threshold;

  final Float64List _mean;
  final Float64List _scale;
  final Float64List _supportVectors;
  final Float64List _dualCoef;
  final Float64List _intercept;
  final Float64List _probA;
  final Float64List _probB;
  final Int32List _nSupport;

  int get supportVectorCount => _supportVectors.length ~/ nFeatures;

  /// Loads `assets/ml/svm_mobile.json` and its sibling `.bin`.
  static Future<SvmModel> load({
    String jsonAsset = 'assets/ml/svm_mobile.json',
    String binAsset = 'assets/ml/svm_mobile.bin',
  }) async {
    final meta = jsonDecode(await rootBundle.loadString(jsonAsset)) as Map<String, dynamic>;
    final bytes = await rootBundle.load(binAsset);
    final flat = bytes.buffer.asFloat32List(
      bytes.offsetInBytes,
      bytes.lengthInBytes ~/ 4,
    );
    return fromParts(meta, flat);
  }

  static SvmModel fromParts(Map<String, dynamic> meta, Float32List flat) {
    final scaler = meta['scaler'] as Map<String, dynamic>;
    final svm = meta['svm'] as Map<String, dynamic>;
    final nFeatures = scaler['n_features'] as int;
    final nSupportVectors = svm['n_support_vectors'] as int;
    final nClasses = svm['n_classes'] as int;
    final nPairs = svm['n_pairs'] as int;
    final nSupport = Int32List.fromList(
      (svm['n_support'] as List).cast<int>(),
    );

    var offset = 0;
    Float64List take(int count) {
      final out = Float64List(count);
      for (var i = 0; i < count; i++) {
        out[i] = flat[offset + i];
      }
      offset += count;
      return out;
    }

    final mean = take(nFeatures);
    final scale = take(nFeatures);
    final support = take(nSupportVectors * nFeatures);
    final dual = take((nClasses - 1) * nSupportVectors);
    final intercept = take(nPairs);
    final probA = take(nPairs);
    final probB = take(nPairs);

    return SvmModel._(
      classes: (meta['classes'] as List).cast<String>(),
      pairs: nPairs,
      nFeatures: nFeatures,
      gamma: (svm['gamma'] as num).toDouble(),
      threshold: (meta['retake_threshold'] as num?)?.toDouble() ?? 0.20,
      scalerMean: mean,
      scalerScale: scale,
      supportVectors: support,
      dualCoef: dual,
      intercept: intercept,
      probA: probA,
      probB: probB,
      nSupport: nSupport,
    );
  }

  SvmPrediction predict(Float64List features) {
    if (features.length != nFeatures) {
      throw ArgumentError('expected $nFeatures features, got ${features.length}');
    }
    final scaled = Float64List(nFeatures);
    for (var i = 0; i < nFeatures; i++) {
      scaled[i] = (features[i] - _mean[i]) / _scale[i];
    }

    final svs = supportVectorCount;
    final kernel = Float64List(svs);
    for (var s = 0; s < svs; s++) {
      var dist = 0.0;
      final base = s * nFeatures;
      for (var f = 0; f < nFeatures; f++) {
        final d = scaled[f] - _supportVectors[base + f];
        dist += d * d;
      }
      kernel[s] = math.exp(-gamma * dist);
    }

    final starts = List<int>.filled(classes.length + 1, 0);
    for (var i = 0; i < classes.length; i++) {
      starts[i + 1] = starts[i] + _nSupport[i];
    }

    final decision = Float64List(pairs);
    final votes = List<int>.filled(classes.length, 0);
    var pair = 0;
    for (var i = 0; i < classes.length; i++) {
      for (var j = i + 1; j < classes.length; j++) {
        var value = _intercept[pair];
        for (var k = starts[i]; k < starts[i + 1]; k++) {
          value += kernel[k] * _dualCoef[(j - 1) * svs + k];
        }
        for (var k = starts[j]; k < starts[j + 1]; k++) {
          value += kernel[k] * _dualCoef[i * svs + k];
        }
        decision[pair] = value;
        if (value > 0) {
          votes[i]++;
        } else {
          votes[j]++;
        }
        pair++;
      }
    }

    var best = 0;
    for (var i = 1; i < votes.length; i++) {
      if (votes[i] > votes[best]) best = i;
    }

    final pairwise = Float64List(pairs);
    for (var p = 0; p < pairs; p++) {
      pairwise[p] = 1.0 / (1.0 + math.exp(_probA[p] * decision[p] + _probB[p]));
    }
    final probability = _ushapedCoupling(pairwise, classes.length);

    final indexed = List<int>.generate(classes.length, (i) => i)
      ..sort((a, b) => probability[b].compareTo(probability[a]));
    final top = indexed
        .take(3)
        .map((i) => MapEntry(classes[i], probability[i]))
        .toList();

    final confidence = probability[best];
    return SvmPrediction(
      slug: classes[best],
      confidence: confidence,
      top: top,
      lowConfidence: confidence < threshold,
      threshold: threshold,
    );
  }

  /// Wu-Lin-Weng coupling, as implemented by libsvm.
  Float64List _ushapedCoupling(Float64List pairwise, int n) {
    final r = List.generate(n, (_) => Float64List(n));
    var p = 0;
    for (var i = 0; i < n; i++) {
      for (var j = i + 1; j < n; j++) {
        r[i][j] = pairwise[p];
        r[j][i] = 1.0 - pairwise[p];
        p++;
      }
    }
    final q = List.generate(n, (_) => Float64List(n));
    for (var t = 0; t < n; t++) {
      for (var j = 0; j < t; j++) {
        q[t][t] += r[j][t] * r[j][t];
        q[t][j] = q[j][t];
      }
      for (var j = t + 1; j < n; j++) {
        q[t][t] += r[j][t] * r[j][t];
        q[t][j] = -r[j][t] * r[t][j];
      }
    }

    final prob = Float64List(n)..fillRange(0, n, 1.0 / n);
    final qp = Float64List(n);
    final eps = 0.005 / n;
    final maxIter = math.max(100, n);

    for (var iter = 0; iter < maxIter; iter++) {
      var pQp = 0.0;
      for (var t = 0; t < n; t++) {
        var acc = 0.0;
        for (var j = 0; j < n; j++) {
          acc += q[t][j] * prob[j];
        }
        qp[t] = acc;
        pQp += prob[t] * qp[t];
      }
      var maxError = 0.0;
      for (var t = 0; t < n; t++) {
        maxError = math.max(maxError, (qp[t] - pQp).abs());
      }
      if (maxError < eps) break;

      for (var t = 0; t < n; t++) {
        final diff = (-qp[t] + pQp) / q[t][t];
        prob[t] += diff;
        pQp = (pQp + diff * (diff * q[t][t] + 2.0 * qp[t])) / (1.0 + diff) / (1.0 + diff);
        for (var j = 0; j < n; j++) {
          qp[j] = (qp[j] + diff * q[t][j]) / (1.0 + diff);
          prob[j] /= 1.0 + diff;
        }
      }
    }

    var total = 0.0;
    for (var i = 0; i < n; i++) {
      if (prob[i] < 0) prob[i] = 0;
      total += prob[i];
    }
    if (total > 0) {
      for (var i = 0; i < n; i++) {
        prob[i] /= total;
      }
    }
    return prob;
  }
}
