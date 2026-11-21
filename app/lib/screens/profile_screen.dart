import 'package:flutter/material.dart';

import '../data/profile_controller.dart';
import '../theme/tokens.dart';
import '../widgets/how_match_works.dart';
import '../widgets/profile_avatar.dart';
import '../widgets/profile_header.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  static const purpose =
      'MarineSee identifies and teaches the nine Mati species.';

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _name = TextEditingController();
  var _loaded = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_loaded) {
      return;
    }
    _name.text = ProfileScope.of(context).name;
    _loaded = true;
  }

  @override
  void dispose() {
    _name.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profile = ProfileScope.of(context);
    final text = Theme.of(context).textTheme;
    final displayName = profile.displayName;
    final initial = displayName.isEmpty
        ? 'G'
        : displayName.trim()[0].toUpperCase();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ProfileHeader(initial: initial),
        Expanded(
          child: Align(
            alignment: Alignment.topCenter,
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppSpace.maxContent),
              child: ListView(
                keyboardDismissBehavior:
                    ScrollViewKeyboardDismissBehavior.onDrag,
                padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
                children: [
                  _IdentityCard(initials: initial, name: displayName),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _name,
                    textCapitalization: TextCapitalization.words,
                    textInputAction: TextInputAction.done,
                    decoration: const InputDecoration(
                      labelText: 'Your name',
                      hintText: 'Shown on Home',
                    ),
                    onChanged: profile.setName,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    'Stored on this device only. No account.',
                    style: text.bodySmall,
                  ),
                  const SizedBox(height: 20),
                  const _SectionLabel('ABOUT MARINESEE'),
                  const SizedBox(height: 10),
                  _Surface(
                    child: Text(
                      ProfileScreen.purpose,
                      style: text.bodyMedium?.copyWith(
                        color: context.tokens.inkMuted,
                        height: 1.5,
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                  const _SectionLabel('HOW IT WORKS'),
                  const SizedBox(height: 10),
                  const _Surface(
                    child: Column(
                      children: [
                        _Step(
                          number: '1',
                          label: 'Camera or gallery',
                          detail:
                              'Take one clear photo of a seagrass leaf, '
                              'or pick an existing photo from the gallery.',
                        ),
                        _Divider(),
                        _Step(
                          number: '2',
                          label: 'Read the name and percent',
                          detail:
                              'The result names the closest of the nine '
                              'Mati City species and shows how confident the '
                              'match is.',
                        ),
                        _Divider(),
                        _Step(
                          number: '3',
                          label: 'Open the library and 3D',
                          detail:
                              'Open the species profile for its notes and '
                              'sources, or rotate the bundled 3D model.',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 12),
                  const HowMatchWorks(),
                  const SizedBox(height: 12),
                  _Surface(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'From photo to species',
                          style: text.titleSmall?.copyWith(
                            color: context.tokens.ink,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'A photo becomes colour, texture, and shape '
                          'features. The on-device SVM compares them with '
                          'the nine documented Mati City species, then '
                          'returns the closest match and a percent. A weak '
                          'match asks for a retake. No network is needed.',
                          style: text.bodyMedium?.copyWith(
                            color: context.tokens.inkMuted,
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// Local visitor card: avatar, current name, and the no-account note.
class _IdentityCard extends StatelessWidget {
  const _IdentityCard({required this.initials, required this.name});

  final String initials;
  final String name;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return _Surface(
      child: Row(
        children: [
          ProfileAvatar(initials: initials, size: 64),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: text.titleLarge?.copyWith(
                    color: tokens.ink,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.2,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'Local visitor profile',
                  style: text.bodySmall?.copyWith(color: tokens.inkMuted),
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
    required this.number,
    required this.label,
    required this.detail,
  });

  final String number;
  final String label;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    final text = Theme.of(context).textTheme;

    return ConstrainedBox(
      constraints: const BoxConstraints(minHeight: AppTokens.tapMin),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 32,
            height: 32,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: tokens.brandDeep,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text(
              number,
              style: text.labelLarge?.copyWith(color: tokens.onBrand),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label, style: text.titleMedium),
                const SizedBox(height: 3),
                Text(
                  detail,
                  style: text.bodySmall?.copyWith(
                    color: tokens.inkMuted,
                    height: 1.45,
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

/// Shared white card, matching the species notes and conservation panels.
class _Surface extends StatelessWidget {
  const _Surface({required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Container(
      padding: const EdgeInsets.fromLTRB(16, 15, 16, 16),
      decoration: BoxDecoration(
        color: tokens.surfaceHigh,
        borderRadius: BorderRadius.circular(AppRadius.md),
        border: Border.all(color: tokens.border),
        boxShadow: tokens.cardShadows,
      ),
      child: child,
    );
  }
}

/// Thin divider that matches the profile card spacing.
class _Divider extends StatelessWidget {
  const _Divider();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Divider(height: 1, color: context.tokens.border),
    );
  }
}
