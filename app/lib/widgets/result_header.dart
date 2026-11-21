import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Gradient header for the identify result.
///
/// Pushed over the scanner, so it keeps a back control. The right chip names
/// what the page is about without repeating the species name.
class ResultHeader extends StatelessWidget {
  const ResultHeader({super.key, required this.onBack});

  final VoidCallback onBack;

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
              Tooltip(
                message: 'Back',
                child: Material(
                  color: SkyPalette.foam.withValues(alpha: 0.14),
                  shape: CircleBorder(
                    side: BorderSide(
                      color: SkyPalette.foam.withValues(alpha: 0.26),
                    ),
                  ),
                  child: InkWell(
                    onTap: onBack,
                    customBorder: const CircleBorder(),
                    child: const SizedBox(
                      width: 48,
                      height: 48,
                      child: Icon(
                        Icons.arrow_back_rounded,
                        color: SkyPalette.onHeader,
                        size: 22,
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Result',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.titleLarge?.copyWith(
                        color: SkyPalette.onHeader,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.2,
                      ),
                    ),
                    const SizedBox(height: 1),
                    Text(
                      'Mati City · nine species',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: text.bodySmall?.copyWith(
                        color: SkyPalette.onHeader.withValues(alpha: 0.72),
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
                  color: SkyPalette.foam.withValues(alpha: 0.14),
                  borderRadius: BorderRadius.circular(AppRadius.pill),
                  border: Border.all(
                    color: SkyPalette.foam.withValues(alpha: 0.26),
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(
                      Icons.center_focus_strong_rounded,
                      size: 13,
                      color: SkyPalette.goldBright,
                    ),
                    const SizedBox(width: 5),
                    Text(
                      'SVM',
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
