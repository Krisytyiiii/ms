import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data/model_3d_library.dart';
import '../data/species_catalog.dart';
import '../theme/tokens.dart';
import '../widgets/app_states.dart';
import '../widgets/glb_viewer.dart';
import '../widgets/species_clip_player.dart';

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
      backgroundColor: const Color(0xFF1E8C98),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        foregroundColor: Colors.white,
        systemOverlayStyle: SkyPalette.lightStatusBar,
        iconTheme: const IconThemeData(color: Colors.white),
        titleTextStyle: Theme.of(context).textTheme.titleLarge?.copyWith(
          color: Colors.white,
          fontWeight: FontWeight.w700,
        ),
        centerTitle: true,
        title: const Text('3D Viewer'),
      ),
      body: FutureBuilder<_OpenedViewer>(
        future: _future,
        builder: (context, snapshot) {
          if (snapshot.hasError) {
            return OceanError(
              message: 'Could not open this species model.',
              onRetry: _reload,
            );
          }
          final opened = snapshot.data;
          if (opened == null) {
            return const OceanLoading(label: 'Opening 3D…');
          }
          final media = opened.media;
          if (media.hasModel) {
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 28),
              children: [
                GlbViewer(assetPath: media.modelAsset!, label: widget.slug),
                if (media.hasLesson) ...[
                  const SizedBox(height: 16),
                  Text(
                    'Lesson',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  SpeciesClipPlayer(
                    assetPath: media.lessonAsset!,
                    autoPlay: false,
                    muted: false,
                  ),
                  if (opened.transcript != null) ...[
                    const SizedBox(height: 12),
                    _Transcript(text: opened.transcript!),
                  ],
                ],
                const SizedBox(height: 12),
                _ModelNote(slug: widget.slug),
              ],
            );
          }
          if (media.hasVideo && !_videoFailed) {
            return ListView(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 28),
              children: [
                SpeciesClipPlayer(
                  assetPath: media.videoAsset!,
                  onFailed: () => setState(() => _videoFailed = true),
                ),
                const SizedBox(height: 16),
                _ModelNote(slug: widget.slug, clip: true),
              ],
            );
          }
          return Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const OceanEmpty(
                  icon: Icons.view_in_ar_outlined,
                  title: Viewer3dScreen.placeholderCopy,
                  message: 'Playback only. Modeling stays outside this repo.',
                ),
                const SizedBox(height: 12),
                _ModelNote(slug: widget.slug),
              ],
            ),
          );
        },
      ),
      ),
    );
  }
}

class _OpenedViewer {
  const _OpenedViewer({required this.media, this.transcript});

  final SpeciesMedia media;
  final String? transcript;
}

class _Transcript extends StatelessWidget {
  const _Transcript({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final style = Theme.of(context).textTheme;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: SkyPalette.scanner.withValues(alpha: 0.55),
        borderRadius: AppRadius.card,
        border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Transcript',
              style: style.titleMedium?.copyWith(color: Colors.white),
            ),
            const SizedBox(height: 8),
            Text(
              text,
              style: style.bodyMedium?.copyWith(
                color: Colors.white70,
                height: 1.45,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ModelNote extends StatelessWidget {
  const _ModelNote({required this.slug, this.clip = false});

  final String slug;
  final bool clip;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final name = slug.replaceAll('_', ' ');

    return DecoratedBox(
      decoration: BoxDecoration(
        color: SkyPalette.scanner.withValues(alpha: 0.55),
        borderRadius: AppRadius.card,
        border: Border.all(color: Colors.white.withValues(alpha: 0.16)),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Model information',
              style: text.titleMedium?.copyWith(color: Colors.white),
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Text(
                  'Species',
                  style: text.bodyMedium?.copyWith(color: Colors.white70),
                ),
                const Spacer(),
                Flexible(
                  child: Text(
                    name,
                    textAlign: TextAlign.end,
                    style: text.bodyMedium?.copyWith(
                      color: Colors.white,
                      fontStyle: FontStyle.italic,
                    ),
                  ),
                ),
              ],
            ),
            if (clip) ...[
              const SizedBox(height: 8),
              Text(
                'Growth clip. Playback only — this repo does not author models.',
                style: text.bodySmall?.copyWith(color: Colors.white70),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
