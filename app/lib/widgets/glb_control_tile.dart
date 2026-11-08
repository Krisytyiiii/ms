import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// One tappable control under the 3D viewer.
class GlbControlTile extends StatelessWidget {
  const GlbControlTile({
    super.key,
    required this.icon,
    required this.label,
    required this.onPressed,
    this.selected = false,
  });

  final IconData icon;
  final String label;
  final VoidCallback? onPressed;
  final bool selected;

  @override
  Widget build(BuildContext context) {
    final enabled = onPressed != null;
    final color = enabled ? Colors.white : Colors.white38;

    return Expanded(
      child: Material(
        color: Colors.white.withValues(alpha: selected ? 0.22 : 0.08),
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          onTap: onPressed,
          borderRadius: BorderRadius.circular(16),
          child: ConstrainedBox(
            constraints: const BoxConstraints(minHeight: AppTokens.tapMin),
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 10),
              child: Column(
                children: [
                  Icon(icon, color: color),
                  const SizedBox(height: 4),
                  Text(
                    label,
                    textAlign: TextAlign.center,
                    style: Theme.of(
                      context,
                    ).textTheme.labelMedium?.copyWith(color: color),
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

/// Playback speed for the growth clip: half, normal, and two faster steps.
class GlbSpeedRow extends StatelessWidget {
  const GlbSpeedRow({
    super.key,
    required this.speed,
    required this.onSelected,
  });

  final double speed;
  final ValueChanged<double>? onSelected;

  static const speeds = [0.5, 1.0, 1.5, 2.0];

  static String labelFor(double value) {
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
    return Row(
      children: [
        for (final value in speeds) ...[
          if (value != speeds.first) const SizedBox(width: 8),
          GlbControlTile(
            icon: Icons.speed,
            label: labelFor(value),
            selected: speed == value,
            onPressed: onSelected == null ? null : () => onSelected!(value),
          ),
        ],
      ],
    );
  }
}
