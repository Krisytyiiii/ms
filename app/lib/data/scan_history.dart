import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/widgets.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// One identification the SVM has finished.
///
/// The label, the score, and the time are always kept. A small JPEG thumbnail
/// is kept too, so the history thread can show the photo that was scanned.
class ScanRecord {
  const ScanRecord({
    required this.slug,
    required this.at,
    this.confidence,
    this.low = false,
    this.thumb,
  });

  final String slug;
  final double? confidence;
  final DateTime at;
  final bool low;

  /// Base64 JPEG thumbnail, or null for a record saved before thumbnails.
  final String? thumb;

  Map<String, dynamic> toJson() => {
    'slug': slug,
    'confidence': confidence,
    'at': at.toIso8601String(),
    'low': low,
    if (thumb != null) 'thumb': thumb,
  };

  static ScanRecord? fromJson(Object? value) {
    if (value is! Map) {
      return null;
    }
    final slug = value['slug'];
    final at = DateTime.tryParse('${value['at']}');
    if (slug is! String || slug.isEmpty || at == null) {
      return null;
    }
    final confidence = value['confidence'];
    final thumb = value['thumb'];
    return ScanRecord(
      slug: slug,
      confidence: confidence is num ? confidence.toDouble() : null,
      at: at,
      low: value['low'] == true,
      thumb: thumb is String && thumb.isNotEmpty ? thumb : null,
    );
  }
}

/// Decoded thumbnail bytes for a saved scan, or null when none was kept.
Uint8List? scanThumbBytes(ScanRecord record) {
  final thumb = record.thumb;
  if (thumb == null) {
    return null;
  }
  try {
    return base64Decode(thumb);
  } catch (_) {
    return null;
  }
}

/// Saved scanner history, newest first and capped so a long session stays
/// small. Records are mirrored to local storage; if storage is unavailable the
/// log still works for the rest of the session.
class ScanHistoryController extends ChangeNotifier {
  ScanHistoryController({int limit = 20}) : _limit = limit;

  static const storageKey = 'scanner_history_v1';

  final int _limit;
  final List<ScanRecord> _records = [];
  var _loaded = false;

  List<ScanRecord> get records => List.unmodifiable(_records);

  bool get isEmpty => _records.isEmpty;

  bool get isLoaded => _loaded;

  int get count => _records.length;

  ScanRecord? get latest => _records.isEmpty ? null : _records.first;

  Future<void> load() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(storageKey);
      final restored = <ScanRecord>[];
      if (raw != null) {
        final decoded = jsonDecode(raw);
        if (decoded is List) {
          for (final item in decoded) {
            final record = ScanRecord.fromJson(item);
            if (record != null) {
              restored.add(record);
            }
          }
        }
      }
      _records
        ..clear()
        ..addAll(restored.take(_limit));
    } catch (_) {
      // Local storage is best effort; keep the in-memory log.
    }
    _loaded = true;
    notifyListeners();
  }

  void record(ScanRecord record) {
    _records.insert(0, record);
    if (_records.length > _limit) {
      _records.removeRange(_limit, _records.length);
    }
    notifyListeners();
    unawaited(_persist());
  }

  /// Drops a record when the user marks the photo as "None of these".
  void remove(ScanRecord record) {
    if (_records.remove(record)) {
      notifyListeners();
      unawaited(_persist());
    }
  }

  Future<void> _persist() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(
        storageKey,
        jsonEncode([for (final record in _records) record.toJson()]),
      );
    } catch (_) {
      // Nothing to recover; next record tries again.
    }
  }
}

/// Short "2 min ago" label for a saved scan.
String scanRelativeTime(DateTime at) {
  final gap = DateTime.now().difference(at);
  if (gap.inMinutes < 1) {
    return 'just now';
  }
  if (gap.inHours < 1) {
    return '${gap.inMinutes} min ago';
  }
  if (gap.inDays < 1) {
    return '${gap.inHours} hr ago';
  }
  return '${gap.inDays} d ago';
}

/// "62%" for a saved confidence, or null when the scan had no score.
String? scanPercent(double? confidence) =>
    confidence == null ? null : '${(confidence * 100).toStringAsFixed(0)}%';

/// Fallback label when the bundled catalog is still loading.
String prettySlug(String slug) {
  final words = slug.split('_');
  return [
    for (final word in words)
      word.isEmpty ? word : word[0].toUpperCase() + word.substring(1),
  ].join(' ');
}

class ScanHistoryScope extends InheritedNotifier<ScanHistoryController> {
  const ScanHistoryScope({
    super.key,
    required ScanHistoryController controller,
    required super.child,
  }) : super(notifier: controller);

  static ScanHistoryController of(BuildContext context) {
    final scope = context
        .dependOnInheritedWidgetOfExactType<ScanHistoryScope>();
    assert(scope != null, 'ScanHistoryScope not found');
    return scope!.notifier!;
  }
}
