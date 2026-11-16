/// Grading test for the Dart port.
///
/// `ml/src/mobile_fixtures.py` writes prepared 256px PNGs, the exact vector
/// `ml/src/features.py` computes for them, and sklearn's prediction. The Dart
/// extractor and predictor must reproduce those.
///
/// Block offsets: 0-101 color, 102-137 GLCM, 138-147 shape.
///
/// Measured tolerances are bounded by two known, documented gaps: the 128px
/// GLCM resize differs from `skimage.transform.resize` by one grey level on a
/// few dozen pixels, and `skimage.morphology.skeletonize` uses a compiled
/// lookup table that cannot be inspected. Both are bounded by the decision
/// parity check below, which is the check that matters.
library;

import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:marine_see/classify/local/features.dart';
import 'package:marine_see/classify/local/image_ops.dart';
import 'package:marine_see/classify/local/svm_model.dart';
import 'package:marine_see/classify/local_classifier.dart';

const _colorEnd = 102;
const _glcmEnd = 138;

void main() {
  final fixtureFile = File('test/fixtures/vectors.json');
  final manifest = jsonDecode(fixtureFile.readAsStringSync()) as Map<String, dynamic>;
  final items = (manifest['items'] as List).cast<Map<String, dynamic>>();

  Float64List expectedVector(Map<String, dynamic> item) => Float64List.fromList(
    (item['vector'] as List).cast<num>().map((e) => e.toDouble()).toList(),
  );

  group('feature parity with ml/src/features.py', () {
    for (final item in items) {
      test(item['id'] as String, () {
        final id = item['id'] as String;
        final png = File('test/fixtures/${item['prepared_png']}').readAsBytesSync();
        final image = decodeToRgb(png);
        expect(image.width, 256);
        expect(image.height, 256);

        final vector = extractVector(image);
        final expected = expectedVector(item);
        expect(vector.length, expected.length);

        final diffs = <double>[
          for (var i = 0; i < expected.length; i++) (vector[i] - expected[i]).abs(),
        ];
        double blockMax(int from, int to) =>
            diffs.sublist(from, to).reduce((a, b) => a > b ? a : b);

        // ignore: avoid_print
        print(
          '$id color=${blockMax(0, _colorEnd).toStringAsFixed(4)} '
          'glcm=${blockMax(_colorEnd, _glcmEnd).toStringAsFixed(4)} '
          'shape=${blockMax(_glcmEnd, expected.length).toStringAsFixed(4)}',
        );

        expect(blockMax(0, _colorEnd), lessThan(0.02), reason: 'color block');
        expect(blockMax(_colorEnd, _glcmEnd), lessThan(0.05), reason: 'glcm block');
        expect(blockMax(_glcmEnd, expected.length), lessThan(0.05), reason: 'shape block');
      });
    }
  });

  group('decision parity with sklearn', () {
    late SvmModel model;

    setUpAll(() {
      final meta =
          jsonDecode(File('assets/ml/svm_mobile.json').readAsStringSync())
              as Map<String, dynamic>;
      final raw = File('assets/ml/svm_mobile.bin').readAsBytesSync();
      final flat = raw.buffer.asFloat32List(raw.offsetInBytes, raw.lengthInBytes ~/ 4);
      model = SvmModel.fromParts(meta, flat);
    });

    test('weights load as exported', () {
      expect(model.classes.length, 8);
      expect(model.nFeatures, 148);
      expect(model.supportVectorCount, 1200);
    });

    test('retake threshold is the frozen study value', () {
      // docs/14-open-questions.md item 14 freezes 0.44 on the curated
      // validation pass. v1's metrics.json has no retake_threshold, so the
      // export has to be run with `--threshold 0.44`; without this lock it
      // silently ships the 0.20 fallback and never asks for a retake.
      expect(model.threshold, 0.44);
    });

    for (final item in items) {
      test('${item['id']} matches sklearn', () {
        final recorded = item['sklearn_prediction'] as Map<String, dynamic>?;
        if (recorded == null) {
          markTestSkipped('no sklearn prediction in fixtures');
          return;
        }
        final prediction = model.predict(expectedVector(item));
        expect(prediction.slug, recorded['slug']);
        // Confidence is the probability of the *vote* winner, as
        // `ml/src/identify.py` reports it. `predict` and `predict_proba` can
        // name different classes, so `proba.max()` is not comparable here.
        expect(
          (prediction.confidence - (recorded['confidence'] as num)).abs(),
          lessThan(0.02),
        );
      });
    }
  });

  group('offline path on the bundled originals', () {
    // This is the path the phone actually runs: raw JPEG/PNG bytes from the
    // camera or gallery -> decode -> plant crop -> 256px -> features -> SVM.
    // The fixture group above starts from an already-prepared PNG, so only
    // this group proves FS-4 (a name and a percent with no server) and FS-5
    // (the retake notice is reachable at the frozen 0.44).
    late SvmModel model;
    final images = Directory('assets/images/species')
        .listSync()
        .whereType<File>()
        .where((f) => RegExp(r'\.(png|jpe?g)$', caseSensitive: false).hasMatch(f.path))
        .toList()
      ..sort((a, b) => a.path.compareTo(b.path));

    setUpAll(() {
      final meta =
          jsonDecode(File('assets/ml/svm_mobile.json').readAsStringSync())
              as Map<String, dynamic>;
      final raw = File('assets/ml/svm_mobile.bin').readAsBytesSync();
      final flat = raw.buffer.asFloat32List(raw.offsetInBytes, raw.lengthInBytes ~/ 4);
      model = SvmModel.fromParts(meta, flat);
    });

    test('every bundled species photo yields a slug and a percent', () {
      expect(images.length, 9);

      final slugs = model.classes.toSet();
      var lowConfidenceSeen = 0;

      for (final file in images) {
        final prediction = model.predict(featureVectorFromBytes(file.readAsBytesSync()));
        final name = file.uri.pathSegments.last;
        // ignore: avoid_print
        print(
          '$name -> ${prediction.slug} '
          '${(prediction.confidence * 100).toStringAsFixed(1)}%'
          '${prediction.lowConfidence ? ' (retake)' : ''}',
        );

        expect(slugs, contains(prediction.slug), reason: '$name slug');
        expect(prediction.confidence, greaterThan(0));
        expect(prediction.confidence, lessThanOrEqualTo(1));
        expect(prediction.top, isNotEmpty);
        if (prediction.lowConfidence) lowConfidenceSeen++;
      }

      // FS-5 needs the retake branch to be reachable, not just coded.
      expect(
        lowConfidenceSeen,
        greaterThan(0),
        reason: 'no photo fell below the 0.44 retake threshold',
      );
    });
  });
}
