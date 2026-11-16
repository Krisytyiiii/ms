import 'dart:typed_data';

import 'package:image_picker/image_picker.dart';

import 'classifier.dart';
import 'local/features.dart';
import 'local/image_ops.dart';
import 'local/leaf_focus.dart';
import 'local/svm_model.dart';

/// On-device SVM. No network: image bytes go straight through the training
/// preprocess and feature path, then the bundled `svm_mobile` weights.
///
/// Contract: `ml/src/preprocess.py` + `features.py` must stay in step with
/// `local/leaf_focus.dart` and `local/features.dart`. The parity test is
/// `test/local_parity_test.dart`, checked against `test/fixtures/vectors.json`.
class LocalClassifier implements Classifier {
  LocalClassifier({SvmModel? model}) : _model = model;

  SvmModel? _model;

  @override
  Future<IdentifyResult> identify(XFile image) async {
    final bytes = await image.readAsBytes();
    if (bytes.isEmpty) {
      return const IdentifyResult(
        status: IdentifyStatus.error,
        message: 'That photo is empty.',
      );
    }

    try {
      final model = _model ??= await SvmModel.load();
      final vector = featureVectorFromBytes(bytes);
      final prediction = model.predict(vector);
      return IdentifyResult(
        slug: prediction.slug,
        confidence: prediction.confidence,
        status: prediction.lowConfidence
            ? IdentifyStatus.lowConfidence
            : IdentifyStatus.ok,
        message: prediction.lowConfidence
            ? lowConfidenceRetakeSentence
            : null,
      );
    } on FormatException catch (e) {
      return IdentifyResult(
        status: IdentifyStatus.error,
        message: e.message.isEmpty
            ? 'That photo could not be read.'
            : e.message,
      );
    } catch (_) {
      return const IdentifyResult(
        status: IdentifyStatus.error,
        message: 'The on-device model could not read that photo.',
      );
    }
  }
}

/// Decode → plant crop → 256px → 148 features. Used by the app and the test.
Float64List featureVectorFromBytes(Uint8List bytes) {
  final decoded = decodeToRgb(bytes);
  final prepared = prepareRgb(decoded);
  return extractVector(prepared);
}
