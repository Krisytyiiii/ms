import 'dart:ui';

import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// One destination in [MarineNavBar].
class MarineNavItem {
  const MarineNavItem({
    required this.tab,
    required this.label,
    required this.icon,
    required this.activeIcon,
  });

  /// Index in `ShellTab`.
  final int tab;
  final String label;
  final IconData icon;
  final IconData activeIcon;
}

/// Floating glass pill plus a separate Scan action.
///
/// The pill holds the four browse tabs; Scan sits outside it as its own round
/// button. The active tab is gold with dark navy type, so yellow carries the
/// selection while blue stays the quiet, resting color.
class MarineNavBar extends StatelessWidget {
  const MarineNavBar({
    super.key,
    required this.index,
    required this.items,
    required this.scan,
    required this.onSelect,
  });

  final int index;
  final List<MarineNavItem> items;
  final MarineNavItem scan;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      top: false,
      minimum: const EdgeInsets.fromLTRB(16, 0, 16, 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          Expanded(
            child: _NavPill(index: index, items: items, onSelect: onSelect),
          ),
          const SizedBox(width: 10),
          _ScanButton(
            item: scan,
            selected: index == scan.tab,
            onTap: () => onSelect(scan.tab),
          ),
        ],
      ),
    );
  }
}

class _NavPill extends StatelessWidget {
  const _NavPill({
    required this.index,
    required this.items,
    required this.onSelect,
  });

  final int index;
  final List<MarineNavItem> items;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(AppRadius.pill),
        boxShadow: [
          BoxShadow(
            color: tokens.shadow,
            blurRadius: 26,
            offset: const Offset(0, 10),
          ),
          BoxShadow(
            color: SkyPalette.primary.withValues(alpha: 0.10),
            blurRadius: 14,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(AppRadius.pill),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
          child: DecoratedBox(
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(AppRadius.pill),
              gradient: LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  SkyPalette.foam.withValues(alpha: 0.94),
                  SkyPalette.mistDeep.withValues(alpha: 0.90),
                  SkyPalette.primaryContainer.withValues(alpha: 0.86),
                ],
                stops: const [0.0, 0.55, 1.0],
              ),
              border: Border.all(
                color: SkyPalette.foam.withValues(alpha: 0.85),
              ),
            ),
            child: Padding(
              padding: const EdgeInsets.all(6),
              child: Row(
                children: [
                  for (final item in items)
                    Expanded(
                      child: _NavTab(
                        item: item,
                        selected: item.tab == index,
                        onTap: () => onSelect(item.tab),
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

class _NavTab extends StatelessWidget {
  const _NavTab({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  final MarineNavItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final color = selected ? SkyPalette.onGold : SkyPalette.inkMuted;

    return Semantics(
      selected: selected,
      button: true,
      label: item.label,
      child: Tooltip(
        message: item.label,
        child: AnimatedContainer(
          duration: AppMotion.fast,
          curve: AppMotion.ease,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppRadius.pill),
            gradient: selected
                ? const LinearGradient(
                    begin: Alignment.topCenter,
                    end: Alignment.bottomCenter,
                    colors: [SkyPalette.goldBright, SkyPalette.goldDeep],
                  )
                : null,
            border: selected
                ? Border.all(color: SkyPalette.sandDeep.withValues(alpha: 0.55))
                : null,
            boxShadow: selected
                ? [
                    BoxShadow(
                      color: SkyPalette.goldDeep.withValues(alpha: 0.32),
                      blurRadius: 12,
                      offset: const Offset(0, 4),
                    ),
                  ]
                : null,
          ),
          child: Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: onTap,
              borderRadius: BorderRadius.circular(AppRadius.pill),
              splashColor: SkyPalette.goldDeep.withValues(alpha: 0.16),
              highlightColor: SkyPalette.goldDeep.withValues(alpha: 0.10),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 2, vertical: 8),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      selected ? item.activeIcon : item.icon,
                      size: 22,
                      color: color,
                    ),
                    const SizedBox(height: 3),
                    FittedBox(
                      fit: BoxFit.scaleDown,
                      child: Text(
                        item.label,
                        maxLines: 1,
                        style: text.labelSmall?.copyWith(
                          fontSize: 11,
                          height: 1.1,
                          letterSpacing: 0.1,
                          fontWeight: selected
                              ? FontWeight.w700
                              : FontWeight.w500,
                          color: color,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Round Scan action docked beside the pill. Gold when the scanner is open.
class _ScanButton extends StatelessWidget {
  const _ScanButton({
    required this.item,
    required this.selected,
    required this.onTap,
  });

  final MarineNavItem item;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final icon = selected ? item.activeIcon : item.icon;
    final foreground = selected ? SkyPalette.onGold : SkyPalette.primaryDark;

    return Semantics(
      selected: selected,
      button: true,
      label: item.label,
      child: Tooltip(
        message: item.label,
        child: AnimatedContainer(
          duration: AppMotion.fast,
          curve: AppMotion.ease,
          width: 62,
          height: 62,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: selected
                ? const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [SkyPalette.goldBright, SkyPalette.goldDeep],
                  )
                : const LinearGradient(
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                    colors: [SkyPalette.foam, SkyPalette.mistDeep],
                  ),
            border: Border.all(
              color: selected
                  ? SkyPalette.sandDeep.withValues(alpha: 0.55)
                  : SkyPalette.foam.withValues(alpha: 0.9),
            ),
            boxShadow: [
              BoxShadow(
                color: selected
                    ? SkyPalette.goldDeep.withValues(alpha: 0.38)
                    : context.tokens.shadow,
                blurRadius: selected ? 18 : 20,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: Material(
            color: Colors.transparent,
            shape: const CircleBorder(),
            child: InkWell(
              onTap: onTap,
              customBorder: const CircleBorder(),
              splashColor: SkyPalette.goldDeep.withValues(alpha: 0.20),
              highlightColor: SkyPalette.goldDeep.withValues(alpha: 0.12),
              child: Icon(icon, size: 26, color: foreground),
            ),
          ),
        ),
      ),
    );
  }
}
