import 'package:flutter/material.dart';

import '../theme/tokens.dart';
import 'app_photo.dart';

/// Hero banner for the app's main job: identifying a seagrass from a photo.
///
/// A real field photo fills the frame, a deep-water scrim protects the copy,
/// and the three-step flow lives inside the banner above the compact action.
class HomeHeroBanner extends StatelessWidget {
  const HomeHeroBanner({super.key, required this.onScan});

  final VoidCallback onScan;

  static const asset = 'assets/images/onboarding/identify.jpg';

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
            Positioned.fill(
              child: const AppPhoto(
                asset: asset,
                fade: false,
                semanticLabel: 'Seagrass blades on wet sand',
              ),
            ),
            const Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [
                      Color(0x1A023E8A),
                      Color(0xA6023E8A),
                      Color(0xF2023E8A),
                    ],
                    stops: [0.0, 0.46, 1.0],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 14),
                  Text(
                    'Identify a seagrass',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: text.headlineSmall?.copyWith(
                      color: SkyPalette.onHeader,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "One clear photo of a leaf. We'll match it to the nine "
                    'Mati City species.',
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: text.bodyMedium?.copyWith(
                      color: SkyPalette.onHeader.withValues(alpha: 0.84),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Divider(
                    height: 1,
                    thickness: 1,
                    color: SkyPalette.foam.withValues(alpha: 0.18),
                  ),
                  const SizedBox(height: 6),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Expanded(
                        child: _Step(number: '1', label: 'Take a photo'),
                      ),
                      Expanded(
                        child: _Step(number: '2', label: 'See the match'),
                      ),
                      Expanded(
                        child: _Step(number: '3', label: 'Learn more'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          '9 Mati City species',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: text.labelMedium?.copyWith(
                            color: SkyPalette.onHeader.withValues(alpha: 0.68),
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      _ScanPill(onTap: onScan),
                    ],
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

class _Step extends StatelessWidget {
  const _Step({required this.number, required this.label});

  final String number;
  final String label;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return Column(
      children: [
        Container(
          width: 20,
          height: 20,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: SkyPalette.goldDeep.withValues(alpha: 0.92),
            shape: BoxShape.circle,
            border: Border.all(color: SkyPalette.foam.withValues(alpha: 0.3)),
          ),
          child: Text(
            number,
            style: text.labelSmall?.copyWith(
              color: SkyPalette.onGold,
              fontWeight: FontWeight.w700,
              letterSpacing: 0,
            ),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          label,
          textAlign: TextAlign.center,
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: text.labelSmall?.copyWith(
            color: SkyPalette.onHeader.withValues(alpha: 0.88),
            fontWeight: FontWeight.w600,
            letterSpacing: 0.1,
          ),
        ),
      ],
    );
  }
}

/// 32 px gold pill with a 48 px tap target.
class _ScanPill extends StatelessWidget {
  const _ScanPill({required this.onTap});

  final VoidCallback onTap;

  static const _gold = LinearGradient(
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
    colors: [SkyPalette.goldBright, SkyPalette.goldDeep],
  );

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.pill),
          child: Center(
            child: Container(
              height: 32,
              padding: const EdgeInsets.only(left: 14, right: 6),
              decoration: BoxDecoration(
                gradient: _gold,
                borderRadius: BorderRadius.circular(AppRadius.pill),
                border: Border.all(
                  color: SkyPalette.foam.withValues(alpha: 0.42),
                ),
                boxShadow: [
                  BoxShadow(
                    color: SkyPalette.goldDeep.withValues(alpha: 0.32),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    'Scan Seagrass',
                    style: Theme.of(context).textTheme.labelMedium?.copyWith(
                      color: SkyPalette.onGold,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  const SizedBox(width: 6),
                  Container(
                    width: 20,
                    height: 20,
                    alignment: Alignment.center,
                    decoration: BoxDecoration(
                      color: SkyPalette.foam.withValues(alpha: 0.34),
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.arrow_forward_rounded,
                      size: 14,
                      color: SkyPalette.onGold,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
