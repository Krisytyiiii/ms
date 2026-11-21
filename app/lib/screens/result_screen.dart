import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../classify/classifier.dart';
import '../data/scan_history.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/aurora_atmosphere.dart';
import '../widgets/aurora_button.dart';
import '../widgets/diamond_grid_background.dart';
import '../widgets/result_header.dart';
import '../widgets/species_detail.dart';
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
    this.history,
    this.record,
  });

  final Uint8List imageBytes;
  final IdentifyResult result;
  final SpeciesCatalog? catalog;

  /// Session scan log, when this result was opened from the scanner.
  final ScanHistoryController? history;

  /// The entry already logged for this result, so "None of these" can drop it.
  final ScanRecord? record;

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

  void _open(Widget page) {
    Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));
  }

  void _reject() {
    final record = widget.record;
    if (record != null) {
      widget.history?.remove(record);
    }
    setState(() => _rejected = true);
  }

  void _restore() {
    final record = widget.record;
    final history = widget.history;
    if (record != null &&
        history != null &&
        !history.records.contains(record)) {
      history.record(record);
    }
    setState(() => _rejected = false);
  }

  @override
  Widget build(BuildContext context) {
    if (_rejected) {
      return _ResultBody(
        imageBytes: widget.imageBytes,
        rejected: true,
        actions: [
          SizedBox(
            width: double.infinity,
            child: AuroraButton(
              label: 'Take another photo',
              icon: Icons.photo_camera_outlined,
              compact: true,
              onPressed: () => Navigator.of(context).pop(),
            ),
          ),
          const SizedBox(height: 8),
          _CompactOutlined(
            icon: Icons.undo,
            label: 'Show the result again',
            onPressed: _restore,
          ),
        ],
      );
    }

    final result = widget.result;
    if (result.slug == null) {
      return _ResultBody(
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
          return _ResultBody(imageBytes: widget.imageBytes, loading: true);
        }
        final species = snapshot.data;
        final low = result.status == IdentifyStatus.lowConfidence;
        final percent = result.confidence == null
            ? null
            : '${(result.confidence! * 100).toStringAsFixed(0)}%';
        return _ResultBody(
          imageBytes: widget.imageBytes,
          species: species,
          headline: species?.scientificName ?? slug.replaceAll('_', ' '),
          percent: percent,
          share: result.confidence,
          low: low,
          notice: low ? (result.message ?? ResultScreen.retakeSentence) : null,
          actions: [
            SizedBox(
              width: double.infinity,
              child: AuroraButton(
                label: 'Open species profile',
                icon: Icons.menu_book_outlined,
                compact: true,
                onPressed: () => _open(SpeciesScreen(slug: slug)),
              ),
            ),
            const SizedBox(height: 14),
            Text(
              ResultScreen.notSeagrassPrompt,
              style: Theme.of(context).textTheme.labelMedium,
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                Expanded(
                  child: _CompactOutlined(
                    icon: Icons.view_in_ar_outlined,
                    label: 'Open 3D',
                    onPressed: () => _open(Viewer3dScreen(slug: slug)),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _CompactOutlined(
                    icon: Icons.search_off,
                    label: 'None of these',
                    onPressed: _reject,
                  ),
                ),
              ],
            ),
          ],
        );
      },
    );
  }
}

/// Shared page frame for every outcome: header, photo, match, actions, notes.
class _ResultBody extends StatelessWidget {
  const _ResultBody({
    required this.imageBytes,
    this.species,
    this.headline,
    this.percent,
    this.share,
    this.low = false,
    this.notice,
    this.error,
    this.loading = false,
    this.rejected = false,
    this.actions = const [],
  });

  final Uint8List imageBytes;
  final Species? species;
  final String? headline;
  final String? percent;
  final double? share;
  final bool low;
  final String? notice;
  final String? error;
  final bool loading;
  final bool rejected;
  final List<Widget> actions;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SkyPalette.lightStatusBar,
      child: Scaffold(
        backgroundColor: Colors.transparent,
        body: Stack(
          fit: StackFit.expand,
          children: [
            const AuroraAtmosphere(),
            const DiamondGridBackground(seed: 314),
            Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                ResultHeader(onBack: () => Navigator.of(context).maybePop()),
                Expanded(
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(
                        maxWidth: AppSpace.maxContent,
                      ),
                      child: ListView(
                        padding: AppSpace.pageInsets(context),
                        children: [
                          _PhotoCard(imageBytes: imageBytes),
                          const SizedBox(height: 14),
                          if (loading)
                            Container(
                              padding: const EdgeInsets.all(20),
                              decoration: BoxDecoration(
                                color: tokens.surfaceHigh,
                                borderRadius: BorderRadius.circular(
                                  AppRadius.md,
                                ),
                                border: Border.all(color: tokens.border),
                              ),
                              child: const Center(
                                child: SizedBox(
                                  width: 24,
                                  height: 24,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.4,
                                  ),
                                ),
                              ),
                            )
                          else ...[
                            if (rejected) const _RejectionCard(),
                            if (headline != null || percent != null)
                              _MatchCard(
                                species: species,
                                headline: headline,
                                percent: percent,
                                share: share,
                                low: low,
                              ),
                            if (error != null)
                              _Notice(
                                message: error!,
                                tone: _NoticeTone.danger,
                              ),
                            if (notice != null) ...[
                              const SizedBox(height: 12),
                              _Notice(
                                message: notice!,
                                tone: _NoticeTone.notice,
                              ),
                            ],
                            if (actions.isNotEmpty) ...[
                              const SizedBox(height: 16),
                              ...actions,
                            ],
                            const SizedBox(height: 12),
                            _CompactOutlined(
                              icon: Icons.refresh,
                              label: 'Try again',
                              onPressed: () => Navigator.of(context).pop(),
                            ),
                            if (species != null) ...[
                              const SizedBox(height: 24),
                              const SpeciesSectionLabel(label: 'SPECIES NOTES'),
                              const SizedBox(height: 10),
                              SpeciesFactCard(
                                index: 1,
                                icon: Icons.spa_outlined,
                                title: 'Botanical characteristics',
                                value: species!.botanicalCharacteristics,
                              ),
                              const SizedBox(height: 10),
                              SpeciesFactCard(
                                index: 2,
                                icon: Icons.water_outlined,
                                title: 'Ecological role',
                                value: species!.ecologicalRole,
                              ),
                              const SizedBox(height: 10),
                              SpeciesFactCard(
                                index: 3,
                                icon: Icons.shield_outlined,
                                title: 'Conservation status',
                                value: species!.conservationStatus,
                              ),
                              const SizedBox(height: 10),
                              SpeciesFactCard(
                                index: 4,
                                icon: Icons.place_outlined,
                                title: 'Habitat',
                                value: species!.habitat,
                              ),
                              const SizedBox(height: 10),
                              SpeciesFactCard(
                                index: 5,
                                icon: Icons.timeline_outlined,
                                title: 'Growth process',
                                value: species!.growthProcess,
                              ),
                              const SizedBox(height: 10),
                              SpeciesSourcesCard(sources: species!.sources),
                            ],
                            if (headline != null && species == null) ...[
                              const SizedBox(height: 16),
                              Text(
                                'This slug is not in the bundled library, so no '
                                'species notes are available.',
                                style: text.bodySmall?.copyWith(
                                  color: tokens.inkMuted,
                                ),
                              ),
                            ],
                          ],
                        ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

/// Photo with a soft mat so portrait and landscape shots both sit calmly.
class _PhotoCard extends StatelessWidget {
  const _PhotoCard({required this.imageBytes});

  final Uint8List imageBytes;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final height = (MediaQuery.sizeOf(context).height * 0.28).clamp(
      170.0,
      240.0,
    );

    return Container(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      clipBehavior: Clip.antiAlias,
      child: ColoredBox(
        // Pale water, not the deep blue mat: the page stays light like every
        // other tab.
        color: SkyPalette.primaryContainer,
        child: SizedBox(
          height: height,
          width: double.infinity,
          child: Image.memory(
            imageBytes,
            fit: BoxFit.contain,
            gaplessPlayback: true,
            semanticLabel: 'Photo used for this identification',
          ),
        ),
      ),
    );
  }
}

/// Match card: common name, scientific name, and the confidence reading.
class _MatchCard extends StatelessWidget {
  const _MatchCard({
    required this.species,
    required this.headline,
    required this.percent,
    required this.share,
    required this.low,
  });

  final Species? species;
  final String? headline;
  final String? percent;
  final double? share;
  final bool low;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final common = species?.commonName;
    final scientific = headline;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      low ? 'LOW CONFIDENCE' : 'BEST MATCH',
                      style: text.labelSmall?.copyWith(
                        color: low ? tokens.danger : SkyPalette.notice,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.2,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      common ?? scientific ?? 'Match',
                      style: text.titleLarge?.copyWith(
                        color: tokens.ink,
                        fontWeight: FontWeight.w700,
                        height: 1.15,
                      ),
                    ),
                    if (common != null && scientific != null) ...[
                      const SizedBox(height: 2),
                      Text(
                        scientific,
                        style: text.bodyLarge?.copyWith(
                          color: tokens.inkMuted,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
              if (percent != null) ...[
                const SizedBox(width: 12),
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 10,
                    vertical: 6,
                  ),
                  decoration: BoxDecoration(
                    color: low
                        ? tokens.danger.withValues(alpha: 0.08)
                        : SkyPalette.goldContainer,
                    borderRadius: BorderRadius.circular(AppRadius.sm),
                    border: Border.all(
                      color: low
                          ? tokens.danger.withValues(alpha: 0.35)
                          : SkyPalette.sandDeep.withValues(alpha: 0.38),
                    ),
                  ),
                  child: Text(
                    percent!,
                    style: text.titleMedium?.copyWith(
                      color: low ? tokens.danger : SkyPalette.notice,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ],
            ],
          ),
          if (share != null) ...[
            const SizedBox(height: 14),
            Text(
              'Confidence',
              style: text.labelSmall?.copyWith(
                color: tokens.inkSubtle,
                fontSize: 10,
                fontWeight: FontWeight.w700,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 6),
            _ConfidenceMeter(share: share!, low: low),
          ],
        ],
      ),
    );
  }
}

class _RejectionCard extends StatelessWidget {
  const _RejectionCard();

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: tokens.danger.withValues(alpha: 0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: tokens.danger.withValues(alpha: 0.3),
                  ),
                ),
                child: Icon(
                  Icons.search_off_rounded,
                  size: 20,
                  color: tokens.danger,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  ResultScreen.rejectedHeadline,
                  style: text.titleMedium?.copyWith(
                    color: tokens.ink,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            ResultScreen.rejectedMessage,
            style: text.bodyMedium?.copyWith(
              color: tokens.inkMuted,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

/// Compact outlined action. 32 px face, shrink-wrapped tap target.
class _CompactOutlined extends StatelessWidget {
  const _CompactOutlined({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return SizedBox(
      width: double.infinity,
      height: 48,
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Icon(icon, size: 18),
        label: Text(label),
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(0, 48),
          padding: const EdgeInsets.symmetric(horizontal: 14),
          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          textStyle: Theme.of(context).textTheme.labelLarge,
          foregroundColor: tokens.ink,
          side: BorderSide(color: tokens.borderStrong),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(AppRadius.sm),
          ),
        ),
      ),
    );
  }
}

enum _NoticeTone { notice, danger }

/// Horizontal confidence bar that fills once. The number is already on screen;
/// this is the glanceable version, animated without delaying the text.
class _ConfidenceMeter extends StatelessWidget {
  const _ConfidenceMeter({required this.share, required this.low});

  final double share;
  final bool low;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final value = share.clamp(0.0, 1.0);
    final reduce = MediaQuery.disableAnimationsOf(context);

    Widget bar(double fill) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(AppRadius.pill),
        child: SizedBox(
          height: 6,
          child: Stack(
            children: [
              Positioned.fill(child: ColoredBox(color: tokens.navy)),
              Align(
                alignment: Alignment.centerLeft,
                child: FractionallySizedBox(
                  widthFactor: fill,
                  heightFactor: 1,
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        colors: low
                            ? [tokens.notice, tokens.danger]
                            : const [SkyPalette.primary, SkyPalette.seagrass],
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (reduce) {
      return bar(value);
    }

    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0, end: value),
      duration: const Duration(milliseconds: 700),
      curve: Curves.easeOutCubic,
      builder: (context, fill, _) => bar(fill),
    );
  }
}

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
                style: Theme.of(
                  context,
                ).textTheme.bodyMedium?.copyWith(color: color),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
