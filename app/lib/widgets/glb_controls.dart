import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// Three canned camera angles for the bundled model.
enum GlbCameraPreset { front, side, top }

extension GlbCameraPresetX on GlbCameraPreset {
  String get label {
    switch (this) {
      case GlbCameraPreset.front:
        return 'Front';
      case GlbCameraPreset.side:
        return 'Side';
      case GlbCameraPreset.top:
        return 'Top';
    }
  }

  IconData get icon {
    switch (this) {
      case GlbCameraPreset.front:
        return Icons.rectangle_outlined;
      case GlbCameraPreset.side:
        return Icons.swap_horiz_rounded;
      case GlbCameraPreset.top:
        return Icons.vertical_align_top_rounded;
    }
  }

  String get orbit {
    switch (this) {
      case GlbCameraPreset.front:
        return '0deg 75deg 105%';
      case GlbCameraPreset.side:
        return '90deg 75deg 105%';
      case GlbCameraPreset.top:
        return '0deg 20deg 105%';
    }
  }
}

/// The glass control deck under the model stage.
///
/// Every control calls straight back into [GlbViewer]; this file holds no
/// viewer state so the stage can stay cheap to rebuild.
class GlbControlDock extends StatelessWidget {
  const GlbControlDock({
    super.key,
    required this.enabled,
    required this.playing,
    required this.spinning,
    required this.rootsClear,
    required this.speed,
    required this.onTogglePlay,
    required this.onToggleSpin,
    required this.onToggleRoots,
    required this.onSpeed,
    required this.onZoomIn,
    required this.onZoomOut,
    required this.onPreset,
    required this.onReset,
  });

  final bool enabled;
  final bool playing;
  final bool spinning;
  final bool rootsClear;
  final double speed;
  final VoidCallback onTogglePlay;
  final VoidCallback onToggleSpin;
  final VoidCallback onToggleRoots;
  final ValueChanged<double> onSpeed;
  final VoidCallback onZoomIn;
  final VoidCallback onZoomOut;
  final ValueChanged<GlbCameraPreset> onPreset;
  final VoidCallback onReset;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Container(
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.lg),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      padding: const EdgeInsets.fromLTRB(14, 14, 14, 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '3D CONTROLS',
                      style: text.labelSmall?.copyWith(
                        color: SkyPalette.notice,
                        fontSize: 10.5,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 1.4,
                      ),
                    ),
                    const SizedBox(height: 3),
                    Row(
                      children: [
                        Icon(
                          Icons.touch_app_rounded,
                          size: 13,
                          color: tokens.inkSubtle,
                        ),
                        const SizedBox(width: 5),
                        Text(
                          'Drag to turn · Pinch to zoom',
                          style: text.bodySmall?.copyWith(
                            color: tokens.inkSubtle,
                            fontSize: 11.5,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              _IconAction(
                icon: Icons.center_focus_strong_rounded,
                tooltip: 'Reset view',
                onTap: enabled ? onReset : null,
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              _DockAction(
                icon: playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
                label: playing ? 'Pause' : 'Play',
                selected: playing,
                onTap: enabled ? onTogglePlay : null,
              ),
              const SizedBox(width: 8),
              _DockAction(
                icon: Icons.threesixty_rounded,
                label: 'Spin',
                selected: spinning,
                onTap: enabled ? onToggleSpin : null,
              ),
              const SizedBox(width: 8),
              _DockAction(
                icon: Icons.zoom_in_rounded,
                label: 'Zoom in',
                onTap: enabled ? onZoomIn : null,
              ),
              const SizedBox(width: 8),
              _DockAction(
                icon: Icons.zoom_out_rounded,
                label: 'Zoom out',
                onTap: enabled ? onZoomOut : null,
              ),
            ],
          ),
          const SizedBox(height: 14),
          _GroupLabel('Playback speed'),
          const SizedBox(height: 7),
          _SpeedSegments(speed: speed, onSelected: enabled ? onSpeed : null),
          const SizedBox(height: 14),
          _GroupLabel('Camera'),
          const SizedBox(height: 7),
          Row(
            children: [
              for (final preset in GlbCameraPreset.values) ...[
                if (preset != GlbCameraPreset.values.first)
                  const SizedBox(width: 8),
                Expanded(
                  child: _PresetChip(
                    preset: preset,
                    onTap: enabled ? () => onPreset(preset) : null,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 10),
          _RootsRow(clear: rootsClear, enabled: enabled, onTap: onToggleRoots),
        ],
      ),
    );
  }
}

class _GroupLabel extends StatelessWidget {
  const _GroupLabel(this.label);

  final String label;

  @override
  Widget build(BuildContext context) {
    return Text(
      label.toUpperCase(),
      style: Theme.of(context).textTheme.labelSmall?.copyWith(
        color: context.tokens.inkSubtle,
        fontSize: 9.5,
        fontWeight: FontWeight.w700,
        letterSpacing: 1.1,
      ),
    );
  }
}

class _DockAction extends StatelessWidget {
  const _DockAction({
    required this.icon,
    required this.label,
    required this.onTap,
    this.selected = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onTap;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final enabled = onTap != null;
    final color = !enabled
        ? tokens.inkSubtle.withValues(alpha: 0.45)
        : selected
        ? SkyPalette.primaryDark
        : tokens.ink;

    return Expanded(
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.md),
          child: AnimatedContainer(
            duration: AppMotion.fast,
            curve: AppMotion.ease,
            height: 62,
            decoration: BoxDecoration(
              color: selected
                  ? SkyPalette.gold
                  : tokens.ocean.withValues(alpha: enabled ? 1 : 0.5),
              borderRadius: BorderRadius.circular(AppRadius.md),
              border: Border.all(
                color: selected ? SkyPalette.goldDeep : tokens.border,
              ),
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                AnimatedSwitcher(
                  duration: AppMotion.fast,
                  child: Icon(
                    icon,
                    key: ValueKey(icon),
                    color: color,
                    size: 22,
                  ),
                ),
                const SizedBox(height: 5),
                Text(
                  label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.labelSmall?.copyWith(
                    color: color,
                    fontSize: 10.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _IconAction extends StatelessWidget {
  const _IconAction({
    required this.icon,
    required this.tooltip,
    required this.onTap,
  });

  final IconData icon;
  final String tooltip;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final enabled = onTap != null;

    return Tooltip(
      message: tooltip,
      child: Material(
        color: tokens.ocean.withValues(alpha: enabled ? 1 : 0.5),
        shape: CircleBorder(side: BorderSide(color: tokens.border)),
        child: InkWell(
          onTap: onTap,
          customBorder: const CircleBorder(),
          child: SizedBox(
            width: 40,
            height: 40,
            child: Icon(
              icon,
              size: 19,
              color: tokens.ink.withValues(alpha: enabled ? 0.9 : 0.35),
            ),
          ),
        ),
      ),
    );
  }
}

class _SpeedSegments extends StatelessWidget {
  const _SpeedSegments({required this.speed, required this.onSelected});

  final double speed;
  final ValueChanged<double>? onSelected;

  static const values = [0.5, 1.0, 1.5, 2.0];

  static String _label(double value) {
    if (value == 0.5) {
      return '0.5×';
    }
    if (value == 1.5) {
      return '1.5×';
    }
    return '${value.round()}×';
  }

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.all(3),
      decoration: BoxDecoration(
        color: tokens.ocean,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
      ),
      child: Row(
        children: [
          for (final value in values)
            Expanded(
              child: _Segment(
                label: _label(value),
                selected: speed == value,
                onTap: onSelected == null ? null : () => onSelected!(value),
              ),
            ),
        ],
      ),
    );
  }
}

class _Segment extends StatelessWidget {
  const _Segment({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Semantics(
      button: true,
      selected: selected,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(AppRadius.sm),
          child: AnimatedContainer(
            duration: AppMotion.fast,
            curve: AppMotion.ease,
            padding: const EdgeInsets.symmetric(vertical: 9),
            decoration: BoxDecoration(
              color: selected ? tokens.brand : Colors.transparent,
              borderRadius: BorderRadius.circular(AppRadius.sm),
            ),
            child: Text(
              label,
              textAlign: TextAlign.center,
              style: Theme.of(context).textTheme.labelMedium?.copyWith(
                color: selected ? tokens.onBrand : tokens.inkMuted,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _PresetChip extends StatelessWidget {
  const _PresetChip({required this.preset, required this.onTap});

  final GlbCameraPreset preset;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final enabled = onTap != null;
    final ink = tokens.ink.withValues(alpha: enabled ? 0.86 : 0.35);

    return Material(
      color: Colors.transparent,
      borderRadius: BorderRadius.circular(AppRadius.sm),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        child: Container(
          height: 42,
          decoration: BoxDecoration(
            color: tokens.ocean.withValues(alpha: enabled ? 1 : 0.5),
            borderRadius: BorderRadius.circular(AppRadius.sm),
            border: Border.all(color: tokens.border),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(preset.icon, size: 15, color: ink),
              const SizedBox(width: 6),
              Flexible(
                child: Text(
                  preset.label,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.labelMedium?.copyWith(
                    color: ink,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _RootsRow extends StatelessWidget {
  const _RootsRow({
    required this.clear,
    required this.enabled,
    required this.onTap,
  });

  final bool clear;
  final bool enabled;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Semantics(
      toggled: clear,
      button: true,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(AppRadius.md),
        child: InkWell(
          onTap: enabled ? onTap : null,
          borderRadius: BorderRadius.circular(AppRadius.md),
          child: Container(
            padding: const EdgeInsets.fromLTRB(12, 10, 12, 10),
            decoration: BoxDecoration(
              color: tokens.ocean.withValues(alpha: enabled ? 1 : 0.5),
              borderRadius: BorderRadius.circular(AppRadius.md),
              border: Border.all(color: tokens.border),
            ),
            child: Row(
              children: [
                Icon(
                  clear
                      ? Icons.visibility_off_rounded
                      : Icons.visibility_rounded,
                  size: 18,
                  color: SkyPalette.goldDeep.withValues(
                    alpha: enabled ? 1 : 0.4,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        clear ? 'Hide roots' : 'See roots',
                        style: text.labelLarge?.copyWith(
                          color: tokens.ink.withValues(
                            alpha: enabled ? 0.92 : 0.4,
                          ),
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Text(
                        'Fade the sand layer to show the buried base.',
                        style: text.bodySmall?.copyWith(
                          color: tokens.inkSubtle,
                          fontSize: 11,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 8),
                AnimatedContainer(
                  duration: AppMotion.fast,
                  curve: AppMotion.ease,
                  width: 42,
                  height: 24,
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    color: clear ? SkyPalette.gold : tokens.abyss,
                    borderRadius: BorderRadius.circular(AppRadius.pill),
                    border: Border.all(
                      color: clear ? SkyPalette.goldDeep : tokens.borderStrong,
                    ),
                  ),
                  child: AnimatedAlign(
                    duration: AppMotion.fast,
                    curve: AppMotion.ease,
                    alignment: clear
                        ? Alignment.centerRight
                        : Alignment.centerLeft,
                    child: Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: clear ? SkyPalette.primaryDark : tokens.abyss,
                        border: Border.all(color: tokens.borderStrong),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
