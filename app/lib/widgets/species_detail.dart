import 'package:flutter/material.dart';

import '../data/model_3d_library.dart';
import '../data/species.dart';
import '../theme/tokens.dart';
import 'app_photo.dart';
import 'icon_well.dart';

/// Full-bleed photo header for one species.
///
/// The photo sits under a top scrim (so the back button and status bar stay
/// readable) and a bottom scrim that carries the names into the notes sheet.
class SpeciesHero extends StatelessWidget {
  const SpeciesHero({super.key, required this.species, this.stillAsset});

  final Species species;
  final String? stillAsset;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final genus = species.scientificName.split(' ').first;

    return Stack(
      fit: StackFit.expand,
      children: [
        if (stillAsset == null)
          const _HeroFallback()
        else
          AppPhoto(
            asset: stillAsset!,
            semanticLabel: '${species.commonName} photo',
          ),
        const DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              colors: [
                Color(0xB3023E8A),
                Color(0x00023E8A),
                Color(0x73023E8A),
                Color(0xFF023E8A),
              ],
              stops: [0.0, 0.30, 0.72, 1.0],
            ),
          ),
        ),
        Positioned(
          left: 16,
          right: 16,
          bottom: 24,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                '${genus.toUpperCase()}  ·  MATI CITY',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: text.labelSmall?.copyWith(
                  color: SkyPalette.goldBright,
                  fontSize: 10.5,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.3,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                species.scientificName,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
                style: text.headlineSmall?.copyWith(
                  color: SkyPalette.onHeader,
                  fontStyle: FontStyle.italic,
                  fontWeight: FontWeight.w700,
                  height: 1.1,
                ),
              ),
              const SizedBox(height: 3),
              Text(
                species.commonName,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: text.titleSmall?.copyWith(
                  color: SkyPalette.onHeader.withValues(alpha: 0.82),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

/// Small media state pill that hangs at the right of the app bar.
class SpeciesMediaChip extends StatelessWidget {
  const SpeciesMediaChip({super.key, required this.media});

  final SpeciesMedia media;

  @override
  Widget build(BuildContext context) {
    final hasClip = media.hasVideo || media.hasLesson;
    final hasModel = media.hasModel;
    final label = hasClip
        ? 'Clip'
        : hasModel
        ? '3D'
        : 'Photo';
    final icon = hasClip
        ? Icons.play_arrow_rounded
        : hasModel
        ? Icons.view_in_ar_outlined
        : Icons.photo_outlined;

    return Container(
      height: 28,
      padding: const EdgeInsets.symmetric(horizontal: 10),
      decoration: BoxDecoration(
        color: SkyPalette.primaryDark.withValues(alpha: 0.62),
        borderRadius: BorderRadius.circular(AppRadius.pill),
        border: Border.all(color: SkyPalette.foam.withValues(alpha: 0.28)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 13, color: SkyPalette.goldBright),
          const SizedBox(width: 5),
          Text(
            label,
            style: Theme.of(context).textTheme.labelSmall?.copyWith(
              color: SkyPalette.onHeader,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.4,
            ),
          ),
        ],
      ),
    );
  }
}

/// Compact card that names the bundled media and opens the viewer.
class SpeciesMediaCard extends StatelessWidget {
  const SpeciesMediaCard({
    super.key,
    required this.media,
    required this.onOpen,
  });

  final SpeciesMedia media;
  final VoidCallback onOpen;

  String get _subtitle {
    if (media.hasModel && media.hasLesson) {
      return 'Rotate the model and play the lesson clip.';
    }
    if (media.hasModel) {
      return 'Rotate the bundled model.';
    }
    if (media.hasVideo) {
      return 'Play the bundled growth clip.';
    }
    if (media.hasStill) {
      return 'Only the reference photo is bundled.';
    }
    return 'No media file is bundled yet.';
  }

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;
    final hasClip = media.hasVideo || media.hasLesson;
    final icon = hasClip
        ? Icons.play_circle_outline_rounded
        : media.hasModel
        ? Icons.view_in_ar_outlined
        : Icons.photo_outlined;

    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              IconWell(icon: icon, size: 44),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      Model3dLibrary.statusLabel(media),
                      style: text.titleSmall?.copyWith(
                        color: tokens.ink,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _subtitle,
                      style: text.bodySmall?.copyWith(color: tokens.inkMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 32,
            child: FilledButton(
              onPressed: onOpen,
              style: FilledButton.styleFrom(
                minimumSize: const Size(0, 32),
                padding: const EdgeInsets.symmetric(horizontal: 16),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('View in 3D'),
            ),
          ),
        ],
      ),
    );
  }
}

/// One numbered note: a short title, a gold index, and the cited text.
class SpeciesFactCard extends StatelessWidget {
  const SpeciesFactCard({
    super.key,
    required this.index,
    required this.icon,
    required this.title,
    required this.value,
  });

  final int index;
  final IconData icon;
  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              _IndexChip(index: index),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  title,
                  style: text.titleSmall?.copyWith(
                    color: tokens.ink,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Icon(icon, size: 18, color: tokens.brand.withValues(alpha: 0.85)),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            value,
            style: text.bodyMedium?.copyWith(
              color: tokens.inkMuted,
              height: 1.55,
            ),
          ),
        ],
      ),
    );
  }
}

/// Sources sit apart from the notes: smaller type, one row per citation.
class SpeciesSourcesCard extends StatelessWidget {
  const SpeciesSourcesCard({super.key, required this.sources});

  final List<String> sources;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _LabelRow(icon: Icons.menu_book_outlined, label: 'SOURCES'),
          const SizedBox(height: 10),
          for (var i = 0; i < sources.length; i++)
            Padding(
              padding: EdgeInsets.only(bottom: i == sources.length - 1 ? 0 : 9),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Container(
                    margin: const EdgeInsets.only(top: 6),
                    width: 5,
                    height: 5,
                    decoration: const BoxDecoration(
                      shape: BoxShape.circle,
                      color: SkyPalette.goldDeep,
                    ),
                  ),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      sources[i],
                      style: text.bodySmall?.copyWith(
                        color: tokens.inkMuted,
                        height: 1.5,
                      ),
                    ),
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

/// The locked narration, reproduced as text for silent reading.
class SpeciesTranscriptCard extends StatelessWidget {
  const SpeciesTranscriptCard({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final body = Theme.of(context).textTheme;

    return _Surface(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _LabelRow(
            icon: Icons.record_voice_over_outlined,
            label: 'WHAT THE LESSON SAYS',
          ),
          const SizedBox(height: 10),
          Text(
            text,
            style: body.bodyMedium?.copyWith(
              color: tokens.inkMuted,
              height: 1.55,
            ),
          ),
        ],
      ),
    );
  }
}

/// Section eyebrow that introduces the numbered notes.
class SpeciesSectionLabel extends StatelessWidget {
  const SpeciesSectionLabel({super.key, required this.label});

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
            fontWeight: FontWeight.w700,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}

class _LabelRow extends StatelessWidget {
  const _LabelRow({required this.icon, required this.label});

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
            fontSize: 10.5,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.1,
          ),
        ),
        const SizedBox(width: 10),
        Expanded(child: Container(height: 1, color: tokens.border)),
      ],
    );
  }
}

class _IndexChip extends StatelessWidget {
  const _IndexChip({required this.index});

  final int index;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: SkyPalette.goldContainer,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: SkyPalette.sandDeep.withValues(alpha: 0.42)),
      ),
      child: Text(
        index.toString().padLeft(2, '0'),
        style: Theme.of(context).textTheme.labelSmall?.copyWith(
          color: SkyPalette.notice,
          fontSize: 9.5,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.6,
        ),
      ),
    );
  }
}

/// Shared white card. Kept local so the profile reads as one system.
class _Surface extends StatelessWidget {
  const _Surface({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return DecoratedBox(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Padding(
        padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
        child: child,
      ),
    );
  }
}

class _HeroFallback extends StatelessWidget {
  const _HeroFallback();

  @override
  Widget build(BuildContext context) {
    return const DecoratedBox(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [SkyPalette.primary, SkyPalette.primaryDark],
        ),
      ),
      child: Center(
        child: Icon(Icons.spa_outlined, size: 56, color: SkyPalette.goldBright),
      ),
    );
  }
}
