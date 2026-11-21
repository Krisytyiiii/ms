import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Genus filters for the species library: one scrolling row of pill choices.
///
/// Gold marks the active filter; the rest stay white so the row reads as a
/// quiet shelf, not a second header.
class LibraryFilterBar extends StatelessWidget {
  const LibraryFilterBar({
    super.key,
    required this.labels,
    required this.selected,
    required this.onSelected,
  });

  final List<String> labels;
  final String selected;
  final ValueChanged<String> onSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: AppTokens.tapMin,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: labels.length,
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final label = labels[index];
          return _GenusPill(
            label: label,
            selected: label == selected,
            onTap: () => onSelected(label),
          );
        },
      ),
    );
  }
}

class _GenusPill extends StatelessWidget {
  const _GenusPill({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return Semantics(
      button: true,
      selected: selected,
      label: label == 'All' ? 'Show all species' : 'Show $label only',
      child: Center(
        child: AnimatedContainer(
          duration: AppMotion.fast,
          curve: AppMotion.ease,
          height: 38,
          decoration: BoxDecoration(
            gradient: selected
                ? const LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [SkyPalette.goldBright, SkyPalette.goldDeep],
                  )
                : null,
            color: selected ? null : tokens.surfaceHigh,
            borderRadius: BorderRadius.circular(AppRadius.pill),
            border: Border.all(
              color: selected
                  ? SkyPalette.sandDeep.withValues(alpha: 0.55)
                  : tokens.border,
            ),
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: SkyPalette.goldDeep.withValues(alpha: 0.28),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : null,
          ),
          child: Material(
            color: Colors.transparent,
            borderRadius: BorderRadius.circular(AppRadius.pill),
            child: InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(AppRadius.pill),
              splashColor: SkyPalette.goldDeep.withValues(alpha: 0.16),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 15),
                child: Center(
                  child: Text(
                    label,
                    maxLines: 1,
                    style: text.labelMedium?.copyWith(
                      color: selected ? SkyPalette.onGold : tokens.inkMuted,
                      fontWeight: selected ? FontWeight.w700 : FontWeight.w600,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
