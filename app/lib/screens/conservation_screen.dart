import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import '../widgets/app_photo.dart';
import '../widgets/conservation_header.dart';
import 'shell_scope.dart';

/// Short FR-7 note. Uncited claims stay with the adviser.
class ConservationScreen extends StatelessWidget {
  const ConservationScreen({super.key});

  static const whyItMatters =
      'Learning the nine documented Mati City seagrass species supports local marine-biodiversity awareness.';

  static const uncited = 'TBD — adviser source';

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        const ConservationHeader(),
        Expanded(
          child: Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
              child: ListView(
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                children: [
                  const _MattersHero(),
                  const SizedBox(height: 18),
                  const _SectionLabel('CONSERVATION NOTES'),
                  const SizedBox(height: 10),
                  const _SourceCard(),
                  const SizedBox(height: 14),
                  const _LibraryCard(),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// Field photo with the deep-water scrim used by the home hero.
class _MattersHero extends StatelessWidget {
  const _MattersHero();

  static const asset = 'assets/images/species/halophila_ovalis.jpeg';

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(8),
        boxShadow: tokens.cardShadows,
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(8),
        child: Stack(
          children: [
            const Positioned.fill(
              child: AppPhoto(
                asset: asset,
                fade: false,
                semanticLabel: 'Seagrass leaves on a sandy seabed',
              ),
            ),
            const Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Color(0x33023E8A),
                      Color(0xB3023E8A),
                      Color(0xF2023E8A),
                    ],
                    stops: [0.0, 0.52, 1.0],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'WHY IT MATTERS',
                    style: text.labelSmall?.copyWith(
                      color: SkyPalette.goldBright,
                      fontSize: 10,
                      fontWeight: FontWeight.w800,
                      letterSpacing: 1.2,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Why seagrass matters',
                    style: text.headlineSmall?.copyWith(
                      color: SkyPalette.onHeader,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    ConservationScreen.whyItMatters,
                    style: text.bodyMedium?.copyWith(
                      color: SkyPalette.onHeader.withValues(alpha: 0.86),
                      height: 1.45,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

/// White note card that names the claims still waiting on a citation.
class _SourceCard extends StatelessWidget {
  const _SourceCard();

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

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
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: SkyPalette.goldContainer,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: SkyPalette.sandDeep.withValues(alpha: 0.38),
                  ),
                ),
                child: const Icon(
                  Icons.menu_book_outlined,
                  size: 20,
                  color: SkyPalette.notice,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Claims waiting on a source',
                      style: text.titleSmall?.copyWith(
                        color: tokens.ink,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Habitat, sediment, and nursery claims',
                      style: text.bodySmall?.copyWith(color: tokens.inkMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: SkyPalette.goldContainer,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: SkyPalette.sandDeep.withValues(alpha: 0.38),
              ),
            ),
            child: Row(
              children: [
                const Icon(
                  Icons.info_outline_rounded,
                  size: 18,
                  color: SkyPalette.notice,
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    ConservationScreen.uncited,
                    style: text.labelLarge?.copyWith(
                      color: SkyPalette.notice,
                      fontWeight: FontWeight.w600,
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

/// Bridge back into the species library.
class _LibraryCard extends StatelessWidget {
  const _LibraryCard();

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Container(
                width: 40,
                height: 40,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: tokens.brand,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  Icons.menu_book_rounded,
                  size: 20,
                  color: tokens.onBrand,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '9 documented species',
                      style: text.titleSmall?.copyWith(
                        color: tokens.ink,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'See the seagrasses recorded for Mati City.',
                      style: text.bodySmall?.copyWith(color: tokens.inkMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          SizedBox(
            height: 36,
            child: FilledButton(
              onPressed: () => ShellScope.of(context).select(ShellTab.library),
              style: FilledButton.styleFrom(
                minimumSize: const Size(0, 36),
                padding: const EdgeInsets.symmetric(horizontal: 16),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: const Text('Open the species library'),
            ),
          ),
        ],
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
            fontWeight: FontWeight.w700,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}
