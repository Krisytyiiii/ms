import 'package:image_picker/image_picker.dart';

enum IdentifyStatus { stub, ok, lowConfidence, error }

/// Shown when the SVM answer is under the exported retake threshold.
///
/// The model has no "none of the nine" class, so a low score is the only hint it
/// can give that the photo may not be a target seagrass. The sentence names that
/// possibility instead of promising a species. `ResultScreen` also offers the
/// user-driven "None of these" control; see `docs/22-accuracy-plan.md`.
const String lowConfidenceRetakeSentence =
    'Low confidence — this may not be one of the nine species. '
    'Retake closer to a leaf.';

class IdentifyResult {
  const IdentifyResult({
    this.slug,
    this.confidence,
    required this.status,
    this.message,
  });

  final String? slug;
  final double? confidence;
  final IdentifyStatus status;
  final String? message;
}

abstract class Classifier {
  Future<IdentifyResult> identify(XFile image);
}
