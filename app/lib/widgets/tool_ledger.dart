import 'package:flutter/material.dart';

import '../theme/tokens.dart';

/// The three on-device steps that turn a photo into a species call.
///
/// Folded by default so the answer stays the first thing a reader sees. The
/// labels match the real pipeline: leaf focus, the 148-value feature vector,
/// and the bundled SVM.
class ToolLedger extends StatefulWidget {
  const ToolLedger({super.key, this.initiallyOpen = false});

  final bool initiallyOpen;

  @override
  State<ToolLedger> createState() => _ToolLedgerState();
}

class _ToolLedgerState extends State<ToolLedger> {
  late bool _open = widget.initiallyOpen;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Container(
      decoration: BoxDecoration(
        color: tokens.abyss,
        borderRadius: BorderRadius.circular(AppRadius.sm),
        border: Border.all(color: tokens.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          InkWell(
            onTap: () => setState(() => _open = !_open),
            borderRadius: BorderRadius.circular(AppRadius.sm),
            child: Padding(
              padding: const EdgeInsets.fromLTRB(10, 8, 8, 8),
              child: Row(
                children: [
                  Icon(
                    Icons.build_circle_outlined,
                    size: 15,
                    color: tokens.inkSubtle,
                  ),
                  const SizedBox(width: 6),
                  Text(
                    '3 tool calls',
                    style: text.labelSmall?.copyWith(
                      color: tokens.inkMuted,
                      fontWeight: FontWeight.w700,
                      letterSpacing: 0.1,
                    ),
                  ),
                  const SizedBox(width: 7),
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 6,
                      vertical: 1,
                    ),
                    decoration: BoxDecoration(
                      color: tokens.navy,
                      borderRadius: BorderRadius.circular(AppRadius.pill),
                    ),
                    child: Text(
                      'SVM',
                      style: text.labelSmall?.copyWith(
                        color: tokens.brandDeep,
                        fontSize: 9,
                        fontWeight: FontWeight.w800,
                        letterSpacing: 0.3,
                      ),
                    ),
                  ),
                  const Spacer(),
                  AnimatedRotation(
                    turns: _open ? 0.5 : 0,
                    duration: AppMotion.fast,
                    child: Icon(
                      Icons.keyboard_arrow_down_rounded,
                      size: 18,
                      color: tokens.inkSubtle,
                    ),
                  ),
                ],
              ),
            ),
          ),
          if (_open)
            Padding(
              padding: const EdgeInsets.fromLTRB(10, 0, 10, 8),
              child: Column(
                children: const [
                  _Step(
                    icon: Icons.crop_free_rounded,
                    name: 'leaf focus',
                    meta: 'preprocess · cropped to leaf',
                  ),
                  _Step(
                    icon: Icons.functions_rounded,
                    name: 'features',
                    meta: '148 values · colour, texture, shape',
                  ),
                  _Step(
                    icon: Icons.memory_rounded,
                    name: 'svm_mobile',
                    meta: '9 species · on-device',
                    last: true,
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }
}

class _Step extends StatelessWidget {
  const _Step({
    required this.icon,
    required this.name,
    required this.meta,
    this.last = false,
  });

  final IconData icon;
  final String name;
  final String meta;
  final bool last;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Padding(
      padding: EdgeInsets.only(bottom: last ? 0 : 8),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 22,
                height: 22,
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  color: tokens.surfaceHigh,
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: SkyPalette.primary.withValues(alpha: 0.28),
                  ),
                ),
                child: Icon(icon, size: 11, color: tokens.brandDeep),
              ),
              if (!last)
                Container(
                  width: 1,
                  height: 12,
                  margin: const EdgeInsets.only(top: 2),
                  color: tokens.border,
                ),
            ],
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: text.labelSmall?.copyWith(
                    color: tokens.ink,
                    fontFamily: 'monospace',
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    height: 1.4,
                  ),
                ),
                Text(
                  meta,
                  style: text.labelSmall?.copyWith(
                    color: tokens.inkSubtle,
                    fontSize: 10,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
          Icon(
            Icons.check_rounded,
            size: 14,
            color: SkyPalette.primary.withValues(alpha: 0.75),
          ),
        ],
      ),
    );
  }
}
