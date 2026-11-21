import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/app_states.dart';
import '../widgets/glb_viewer.dart';
import '../widgets/species_clip_player.dart';

/// Immersive 3D room for one species: the model stage first, then the lesson.
class Viewer3dScreen extends StatefulWidget {
  const Viewer3dScreen({super.key, required this.slug});

  final String slug;

  static const placeholderCopy =
      '3D model coming — drop a .glb or growth clip here later.';

  @override
  State<Viewer3dScreen> createState() => _Viewer3dScreenState();
}

class _Viewer3dScreenState extends State<Viewer3dScreen> {
  late Future<_OpenedViewer> _future = _open(widget.slug);
  var _videoFailed = false;

  Future<_OpenedViewer> _open(String slug) async {
    final media = await Model3dLibrary.resolve(slug);
    final species = await speciesCatalog.bySlug(slug);
    final transcript = species?.transcript;
    return _OpenedViewer(
      media: media,
      species: species,
      transcript: transcript == null || transcript.isEmpty ? null : transcript,
    );
  }

  @override
  void didUpdateWidget(covariant Viewer3dScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.slug != widget.slug) {
      _future = _open(widget.slug);
      _videoFailed = false;
    }
  }

  void _reload() {
    setState(() {
      Model3dLibrary.resetCache();
      _future = _open(widget.slug);
      _videoFailed = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SkyPalette.lightStatusBar,
      child: Scaffold(
        backgroundColor: context.tokens.abyss,
        body: FutureBuilder<_OpenedViewer>(
          future: _future,
          builder: (context, snapshot) {
            final opened = snapshot.data;
            final species = opened?.species;

            return Column(
              children: [
                _ViewerTopBar(
                  slug: widget.slug,
                  species: species,
                  media: opened?.media,
                  onBack: () => Navigator.of(context).maybePop(),
                ),
                Expanded(child: _body(context, snapshot, opened)),
              ],
            );
          },
        ),
      ),
    );
  }

  Widget _body(
    BuildContext context,
    AsyncSnapshot<_OpenedViewer> snapshot,
    _OpenedViewer? opened,
  ) {
    if (snapshot.hasError) {
      return OceanError(
        message: 'Could not open this species model.',
        onRetry: _reload,
      );
    }
    if (opened == null) {
      return const OceanLoading(label: 'Opening 3D model…');
    }

    final media = opened.media;
    final species = opened.species;

    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 40),
          children: [
            if (media.hasModel)
              GlbViewer(assetPath: media.modelAsset!, label: widget.slug)
            else if (media.hasVideo && !_videoFailed) ...[
              const _SectionLabel('GROWTH CLIP'),
              const SizedBox(height: 10),
              SpeciesClipPlayer(
                assetPath: media.videoAsset!,
                onFailed: () => setState(() => _videoFailed = true),
              ),
            ] else
              SizedBox(
                height: 320,
                child: OceanEmpty(
                  icon: Icons.view_in_ar_outlined,
                  title: Viewer3dScreen.placeholderCopy,
                  message: 'Playback only. Modeling stays outside this repo.',
                ),
              ),
            if (media.hasLesson) ...[
              const SizedBox(height: 26),
              const _SectionLabel('LESSON CLIP'),
              const SizedBox(height: 10),
              SpeciesClipPlayer(
                assetPath: media.lessonAsset!,
                autoPlay: false,
                muted: false,
              ),
              if (opened.transcript != null) ...[
                const SizedBox(height: 12),
                _GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const _GlassLabel(
                        icon: Icons.record_voice_over_outlined,
                        label: 'WHAT THE LESSON SAYS',
                      ),
                      const SizedBox(height: 10),
                      Text(
                        opened.transcript!,
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: context.tokens.inkMuted,
                          height: 1.6,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
            const SizedBox(height: 22),
            _ModelInfoCard(
              species: species,
              media: media,
              clip: !media.hasModel && !media.hasLesson,
            ),
          ],
        ),
      ),
    );
  }
}

class _OpenedViewer {
  const _OpenedViewer({required this.media, this.species, this.transcript});

  final SpeciesMedia media;
  final Species? species;
  final String? transcript;
}

class _ViewerTopBar extends StatelessWidget {
  const _ViewerTopBar({
    required this.slug,
    required this.species,
    required this.media,
    required this.onBack,
  });

  final String slug;
  final Species? species;
  final SpeciesMedia? media;
  final VoidCallback onBack;

  String get _title {
    final name = species?.commonName;
    if (name != null && name.isNotEmpty) {
      return name;
    }
    return slug
        .split('_')
        .map(
          (part) => part.isEmpty
              ? part
              : '${part[0].toUpperCase()}${part.substring(1)}',
        )
        .join(' ');
  }

  String get _subtitle {
    final scientific = species?.scientificName;
    if (scientific != null && scientific.isNotEmpty) {
      return scientific;
    }
    return 'Bundled 3D model';
  }

  String get _badge {
    if (media == null) {
      return '…';
    }
    if (media!.hasModel) {
      return 'GLB';
    }
    if (media!.hasVideo || media!.hasLesson) {
      return 'CLIP';
    }
    if (media!.hasStill) {
      return 'PHOTO';
    }
    return 'NONE';
  }

  IconData get _badgeIcon {
    if (media?.hasModel ?? false) {
      return Icons.view_in_ar_rounded;
    }
    return Icons.play_arrow_rounded;
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: context.tokens.headerGradient,
        border: Border(
          bottom: BorderSide(color: SkyPalette.foam.withValues(alpha: 0.10)),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(12, 10, 16, 12),
          child: Row(
            children: [
              _RoundBackButton(onTap: onBack),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '3D MODEL  ·  MATI CITY',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.labelSmall?.copyWith(
                        color: SkyPalette.goldBright,
                        fontSize: 9.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.3,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Text(
                      _title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.titleLarge?.copyWith(
                        color: SkyPalette.onHeader,
                        fontWeight: FontWeight.w700,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      _subtitle,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.bodySmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.7),
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 10),
              Container(
                height: 28,
                padding: const EdgeInsets.symmetric(horizontal: 10),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                  border: Border.all(
                    color: Colors.white.withValues(alpha: 0.2),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(_badgeIcon, size: 13, color: SkyPalette.goldBright),
                    const SizedBox(width: 5),
                    Text(
                      _badge,
                      style: text.labelSmall?.copyWith(
                        color: SkyPalette.onHeader,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.7,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RoundBackButton extends StatelessWidget {
  const _RoundBackButton({required this.onTap});

  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Tooltip(
      message: 'Back',
      child: Material(
        color: Colors.white.withValues(alpha: 0.14),
        shape: CircleBorder(
          side: BorderSide(color: Colors.white.withValues(alpha: 0.22)),
        ),
        child: InkWell(
          onTap: onTap,
          customBorder: const CircleBorder(),
          child: const SizedBox(
            width: 44,
            height: 44,
            child: Icon(
              Icons.arrow_back_rounded,
              color: SkyPalette.onHeader,
              size: 20,
            ),
          ),
        ),
      ),
    );
  }
}

class _SectionLabel extends StatelessWidget {
  const _SectionLabel(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 18,
          height: 2,
          decoration: BoxDecoration(
            color: SkyPalette.goldDeep,
            borderRadius: BorderRadius.circular(AppRadius.pill),
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: SkyPalette.notice,
            fontSize: 10.5,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}

class _GlassLabel extends StatelessWidget {
  const _GlassLabel({required this.icon, required this.label});

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Row(
      children: [
        Icon(icon, size: 16, color: SkyPalette.notice),
        const SizedBox(width: 7),
        Text(
          label,
          style: Theme.of(context).textTheme.labelSmall?.copyWith(
            color: SkyPalette.notice,
            fontSize: 10,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.1,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(child: Container(height: 1, color: tokens.border)),
      ],
    );
  }
}

class _GlassCard extends StatelessWidget {
  const _GlassCard({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: child,
    );
  }
}

class _ModelInfoCard extends StatelessWidget {
  const _ModelInfoCard({
    required this.species,
    required this.media,
    required this.clip,
  });

  final Species? species;
  final SpeciesMedia media;
  final bool clip;

  String get _bundled {
    if (media.hasModel) {
      return '.glb model';
    }
    if (media.hasVideo) {
      return 'Growth clip';
    }
    if (media.hasLesson) {
      return 'Lesson clip';
    }
    if (media.hasStill) {
      return 'Reference photo';
    }
    return 'Nothing bundled yet';
  }

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final rows = <(String, String, bool)>[
      ('Common name', species?.commonName ?? '—', false),
      ('Scientific name', species?.scientificName ?? '—', true),
      ('Bundled file', _bundled, false),
    ];

    return _GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const _GlassLabel(
            icon: Icons.info_outline_rounded,
            label: 'ABOUT THIS MODEL',
          ),
          const SizedBox(height: 6),
          for (var i = 0; i < rows.length; i++) ...[
            if (i > 0) Divider(height: 1, color: tokens.border),
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 11),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    rows[i].$1,
                    style: text.bodySmall?.copyWith(color: tokens.inkSubtle),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: Text(
                      rows[i].$2,
                      textAlign: TextAlign.end,
                      style: text.bodySmall?.copyWith(
                        color: tokens.ink,
                        fontStyle: rows[i].$3
                            ? FontStyle.italic
                            : FontStyle.normal,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 4),
          Text(
            clip
                ? 'Playback only. This repo does not author models.'
                : 'Playback only. The .glb and lesson clip stay bundled with the app.',
            style: text.bodySmall?.copyWith(
              color: tokens.inkSubtle,
              fontSize: 11,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}
