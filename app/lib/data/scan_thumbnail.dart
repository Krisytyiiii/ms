import 'dart:convert';
import 'dart:typed_data';

import 'package:image/image.dart' as img;

/// Builds a small JPEG for the history thread.
///
/// The thumbnail is capped at 360 px wide and quality 66, which keeps a saved
/// scan around 10–20 KB. It is best effort: an unreadable image simply gets no
/// thumbnail, and the history row shows a placeholder instead.
Future<String?> makeScanThumb(Uint8List bytes) async {
  try {
    final decoded = img.decodeImage(bytes);
    if (decoded == null) {
      return null;
    }
    final resized = decoded.width > 360
        ? img.copyResize(
            decoded,
            width: 360,
            interpolation: img.Interpolation.average,
          )
        : decoded;
    return base64Encode(img.encodeJpg(resized, quality: 66));
  } catch (_) {
    return null;
  }
}
