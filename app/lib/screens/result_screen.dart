import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';

import '../classify/classifier.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/aurora_button.dart';
import '../widgets/ocean_layout.dart';
import '../widgets/ocean_surface.dart';
import 'species_screen.dart';
import 'viewer_3d_screen.dart';

/// Identify result: species, confidence, profile and 3D, the retake notice, and
/// the app's one abstention control.
///
/// The SVM has **no "none of the nine" class**, so a photo of sand, a hand, or a
/// different plant still comes back with a species name. "None of these" lets
/// the user correct that. It records the user's judgement, not a model
/// rejection: no claim is made that the app detects non-seagrass.
/// See `docs/22-accuracy-plan.md` and `docs/08-modules-and-business-logic.md`.
class ResultScreen extends StatefulWidget {
  const ResultScreen({
    super.key,
    required this.imageBytes,
    required this.result,
    this.catalog,
  });

  final Uint8List imageBytes;
  final IdentifyResult result;
  final SpeciesCatalog? catalog;

  static const retakeSentence = lowConfidenceRetakeSentence;

  static const rejectedHeadline = 'Not one of the nine species';
  static const rejectedMessage =
      'You marked this photo as none of the nine Mati seagrasses. MarineSee '
      'only names those nine, so it has no answer for this one. The model '
      'cannot refuse a photo by itself — this call came from you.';
  static const notSeagrassPrompt = 'Wrong species, or not a seagrass at all?';

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _rejected = false;

  @override
  Widget build(BuildContext context) {
    if (_rejected) {
      return _ResultScaffold(
        imageBytes: widget.imageBytes,
        headline: ResultScreen.rejectedHeadline,
        notice: ResultScreen.rejectedMessage,
        actions: [
          AuroraButton(
            label: 'Take another photo',
            icon: Icons.photo_camera_outlined,
            onPressed: () => Navigator.of(context).pop(),
          ),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => setState(() => _rejected = false),
            icon: const Icon(Icons.undo),
            label: const Text('Show the result again'),
          ),
        ],
      );
    }

    final result = widget.result;
    if (result.slug == null) {
      return _ResultScaffold(
        imageBytes: widget.imageBytes,
        error: result.message ?? 'Identification did not finish.',
      );
    }

    final slug = result.slug!;
    return FutureBuilder<Species?>(
      future: (widget.catalog ?? speciesCatalog).bySlug(slug),
      builder: (context, snapshot) {
        if (!snapshot.hasData &&
            snapshot.connectionState != ConnectionState.done) {
          return _ResultScaffold(imageBytes: widget.imageBytes, loading: true);
        }
        final species = snapshot.data;
        final low = result.status == IdentifyStatus.lowConfidence;
        final percent = result.confidence == null
            ? null
            : '${(result.confidence! * 100).toStringAsFixed(0)}%';
        return _ResultScaffold(
          imageBytes: widget.imageBytes,
          headline: species?.scientificName ?? slug.replaceAll('_', ' '),
          italicHeadline: true,
          percent: percent,
          notice: low ? (result.message ?? ResultScreen.retakeSentence) : null,
          actions: [
            AuroraButton(
              label: 'Open species profile',
              icon: Icons.menu_book_outlined,
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => SpeciesScreen(slug: slug),
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            OutlinedButton.icon(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder: (_) => Viewer3dScreen(slug: slug),
                  ),
                );
              },
              icon: const Icon(Icons.view_in_ar_outlined),
              label: const Text('Open 3D'),
            ),
            const SizedBox(height: 20),
            Text(
              ResultScreen.notSeagrassPrompt,
              style: Theme.of(context).textTheme.labelMedium,
            ),
            const SizedBox(height: 6),
            OutlinedButton.icon(
              onPressed: () => setState(() => _rejected = true),
              icon: const Icon(Icons.search_off),
              label: const Text('None of these'),
            ),
          ],
        );
      },
    );
  }
}

class _ResultScaffold extends StatelessWidget {
  const _ResultScaffold({
    required this.imageBytes,
    this.headline,
    this.italicHeadline = false,
    this.percent,
    this.notice,
    this.error,
    this.loading = false,
    this.actions = const [],
  });

  final Uint8List imageBytes;
  final String? headline;
  final bool italicHeadline;
  final String? percent;
  final String? notice;
  final String? error;
  final bool loading;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return OceanScaffold(
      title: 'Result',
      body: OceanPage(
        children: [
          OceanSurface(
            padding: EdgeInsets.zero,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxHeight: 280),
              child: Image.memory(
                imageBytes,
                fit: BoxFit.contain,
                width: double.infinity,
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (loading)
            const OceanSurface(
              child: Center(child: CircularProgressIndicator(strokeWidth: 2.4)),
            )
          else
            OceanSurface(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (headline != null) ...[
                    Text(
                      headline!,
                      style: text.headlineSmall?.copyWith(
                        fontStyle: italicHeadline ? FontStyle.italic : null,
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],
                  if (percent != null) ...[
                    Text('Confidence', style: text.labelMedium),
                    const SizedBox(height: 4),
                    Text(percent!, style: text.headlineSmall),
                  ],
                  if (notice != null) ...[
                    const SizedBox(height: 14),
                    _Notice(message: notice!, tone: _NoticeTone.notice),
                  ],
                  if (error != null)
                    _Notice(message: error!, tone: _NoticeTone.danger),
                ],
              ),
            ),
          const SizedBox(height: 16),
          ...actions,
          if (actions.isNotEmpty) const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () => Navigator.of(context).pop(),
            icon: const Icon(Icons.refresh),
            label: const Text('Try again'),
          ),
        ],
      ),
    );
  }
}

enum _NoticeTone { notice, danger }

class _Notice extends StatelessWidget {
  const _Notice({required this.message, required this.tone});

  final String message;
  final _NoticeTone tone;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final color = tone == _NoticeTone.danger ? tokens.danger : tokens.notice;
    final fill = tone == _NoticeTone.danger
        ? tokens.danger.withValues(alpha: 0.08)
        : tokens.noticeFill;
    final border = tone == _NoticeTone.danger
        ? tokens.danger.withValues(alpha: 0.35)
        : tokens.noticeBorder;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: fill,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Icon(
              tone == _NoticeTone.danger
                  ? Icons.error_outline
                  : Icons.info_outline,
              color: color,
              size: 20,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Text(
                message,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: color,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
