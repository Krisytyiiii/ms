import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../data/onboarding.dart';
import '../theme/tokens.dart';
import '../widgets/app_logo.dart';
import '../widgets/app_photo.dart';
import '../widgets/aurora_atmosphere.dart';
import '../widgets/aurora_button.dart';
import '../widgets/glass_button.dart';
import '../widgets/wave_edge.dart';
import '../widgets/wave_field.dart';

/// Onboarding sits on a photo, so the status bar needs light icons.
/// The page below is foam, so the navigation bar keeps dark icons.
const _onboardingUi = SystemUiOverlayStyle(
  statusBarColor: Colors.transparent,
  statusBarIconBrightness: Brightness.light,
  statusBarBrightness: Brightness.dark,
  systemNavigationBarColor: SkyPalette.foam,
  systemNavigationBarIconBrightness: Brightness.dark,
);

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.onDone});

  final VoidCallback onDone;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final _pages = PageController();
  var _index = 0;

  bool get _last => _index == onboardingSlides.length - 1;

  void _next() {
    if (_last) {
      HapticFeedback.mediumImpact();
      widget.onDone();
      return;
    }
    HapticFeedback.selectionClick();
    _pages.nextPage(duration: AppMotion.medium, curve: AppMotion.ease);
  }

  void _goTo(int index) {
    if (index == _index) {
      return;
    }
    HapticFeedback.selectionClick();
    _pages.animateToPage(
      index,
      duration: AppMotion.medium,
      curve: AppMotion.ease,
    );
  }

  void _onPageChanged(int value) {
    if (value == _index) {
      return;
    }
    HapticFeedback.selectionClick();
    setState(() => _index = value);
  }

  @override
  void dispose() {
    _pages.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: _onboardingUi,
      child: Stack(
        fit: StackFit.expand,
        children: [
          const AuroraAtmosphere(),
          const WaveField(height: 300),
          LayoutBuilder(
            builder: (context, constraints) {
              final heroHeight = (constraints.maxHeight * 0.55).clamp(
                260.0,
                500.0,
              );

              return Column(
                children: [
                  Expanded(
                    child: PageView.builder(
                      controller: _pages,
                      itemCount: onboardingSlides.length,
                      onPageChanged: _onPageChanged,
                      itemBuilder: (context, index) {
                        return _Slide(
                          slide: onboardingSlides[index],
                          index: index,
                          controller: _pages,
                          heroHeight: heroHeight,
                          active: index == _index,
                        );
                      },
                    ),
                  ),
                  _BottomBar(
                    index: _index,
                    last: _last,
                    onDot: _goTo,
                    onNext: _next,
                  ),
                ],
              );
            },
          ),
          Positioned(
            top: 0,
            left: 0,
            right: 0,
            child: _TopBar(onSkip: widget.onDone),
          ),
        ],
      ),
    );
  }
}

/// Brand mark and Skip, floating over the photo. The photo carries a top
/// scrim so the light text stays readable on bright frames.
class _TopBar extends StatelessWidget {
  const _TopBar({required this.onSkip});

  final VoidCallback onSkip;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;

    return SafeArea(
      bottom: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(20, 10, 16, 0),
        child: Row(
          children: [
            const AppLogo(size: 32),
            const SizedBox(width: 10),
            Expanded(
              child: Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  'MarineSee',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: text.titleMedium?.copyWith(
                    color: SkyPalette.onHeader,
                    fontWeight: FontWeight.w700,
                    letterSpacing: -0.2,
                    shadows: const [
                      Shadow(
                        color: Color(0x4D000000),
                        blurRadius: 10,
                        offset: Offset(0, 1),
                      ),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(width: 12),
            GlassButton(label: 'Skip', onPressed: onSkip),
          ],
        ),
      ),
    );
  }
}

class _Slide extends StatelessWidget {
  const _Slide({
    required this.slide,
    required this.index,
    required this.controller,
    required this.heroHeight,
    required this.active,
  });

  final OnboardingSlide slide;
  final int index;
  final PageController controller;
  final double heroHeight;
  final bool active;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final reduce = MediaQuery.disableAnimationsOf(context);
    final settled = reduce || active;

    return Column(
      children: [
        SizedBox(
          height: heroHeight,
          width: double.infinity,
          child: _HeroPhoto(
            slide: slide,
            index: index,
            controller: controller,
            still: reduce,
          ),
        ),
        Expanded(
          child: SingleChildScrollView(
            padding: const EdgeInsets.fromLTRB(24, 26, 24, 12),
            child: AnimatedSlide(
              offset: settled ? Offset.zero : const Offset(0, 0.06),
              duration: AppMotion.medium,
              curve: AppMotion.ease,
              child: AnimatedOpacity(
                opacity: settled ? 1 : 0,
                duration: AppMotion.medium,
                curve: AppMotion.ease,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _Eyebrow(label: slide.eyebrow),
                    const SizedBox(height: 14),
                    Text(slide.title, style: text.displaySmall),
                    const SizedBox(height: 10),
                    Text(
                      slide.body,
                      style: text.bodyLarge?.copyWith(
                        color: tokens.inkMuted,
                        height: 1.55,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

/// Green rule plus a small blue label. Two accents, one line, no box.
class _Eyebrow extends StatelessWidget {
  const _Eyebrow({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;

    return Row(
      children: [
        Container(
          width: 22,
          height: 2,
          decoration: BoxDecoration(
            color: SkyPalette.seagrass,
            borderRadius: BorderRadius.circular(AppRadius.pill),
          ),
        ),
        const SizedBox(width: 10),
        Text(
          label.toUpperCase(),
          style: text.labelSmall?.copyWith(
            color: tokens.brandDeep,
            fontWeight: FontWeight.w700,
            letterSpacing: 1.6,
          ),
        ),
      ],
    );
  }
}

class _HeroPhoto extends StatelessWidget {
  const _HeroPhoto({
    required this.slide,
    required this.index,
    required this.controller,
    required this.still,
  });

  final OnboardingSlide slide;
  final int index;
  final PageController controller;
  final bool still;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;
    const amplitude = 9.0;

    final photo = ColoredBox(
      color: tokens.surfaceHigh,
      child: Stack(
        fit: StackFit.expand,
        children: [
          AnimatedBuilder(
            animation: controller,
            builder: (context, child) {
              var delta = 0.0;
              if (!still && controller.hasClients) {
                final position = controller.position;
                if (position.hasContentDimensions) {
                  delta =
                      (position.pixels / position.viewportDimension) - index;
                }
              }
              // 6% overscan keeps the frame covered while it drifts.
              return Transform.translate(
                offset: Offset(delta * 22, 0),
                child: Transform.scale(scale: 1.14, child: child),
              );
            },
            child: AppPhoto(
              asset: slide.imageAsset,
              fade: false,
              errorIcon: slide.icon,
            ),
          ),
          const IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Color(0x66000000),
                    Color(0x1F000000),
                    Color(0x00000000),
                  ],
                  stops: [0.0, 0.42, 0.72],
                ),
              ),
            ),
          ),
          // A deep-water wash at the base ties the three photos to one palette.
          const IgnorePointer(
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [Color(0x000077B6), Color(0x330077B6)],
                  stops: [0.55, 1.0],
                ),
              ),
            ),
          ),
        ],
      ),
    );

    return Stack(
      children: [
        Positioned.fill(
          child: ClipPath(
            clipper: const WaveEdgeClipper(amplitude: amplitude),
            child: photo,
          ),
        ),
        const Positioned.fill(child: WaveEdgeLine(amplitude: amplitude)),
      ],
    );
  }
}

class _BottomBar extends StatelessWidget {
  const _BottomBar({
    required this.index,
    required this.last,
    required this.onDot,
    required this.onNext,
  });

  final int index;
  final bool last;
  final ValueChanged<int> onDot;
  final VoidCallback onNext;

  @override
  Widget build(BuildContext context) {
    final text = Theme.of(context).textTheme;
    final tokens = context.tokens;
    final step = (index + 1).toString().padLeft(2, '0');
    final total = onboardingSlides.length.toString().padLeft(2, '0');

    return SafeArea(
      top: false,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(24, 4, 24, 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                for (var i = 0; i < onboardingSlides.length; i++)
                  _ProgressBar(
                    selected: i == index,
                    onTap: () => onDot(i),
                    position: i + 1,
                    total: onboardingSlides.length,
                  ),
                const Spacer(),
                Text(
                  '$step / $total',
                  style: text.labelSmall?.copyWith(
                    color: tokens.inkSubtle,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.2,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            AuroraButton(
              label: last ? 'Get started' : 'Continue',
              onPressed: onNext,
              trailingIcon: last ? Icons.check_rounded : Icons.arrow_forward,
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressBar extends StatelessWidget {
  const _ProgressBar({
    required this.selected,
    required this.onTap,
    required this.position,
    required this.total,
  });

  final bool selected;
  final VoidCallback onTap;
  final int position;
  final int total;

  @override
  Widget build(BuildContext context) {
    final tokens = context.tokens;

    return Semantics(
      button: true,
      selected: selected,
      label: 'Step $position of $total',
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        child: SizedBox(
          height: 44,
          child: Align(
            alignment: Alignment.centerLeft,
            child: AnimatedContainer(
              duration: AppMotion.medium,
              curve: AppMotion.ease,
              margin: const EdgeInsets.only(right: 6),
              width: selected ? 40 : 14,
              height: 3,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: selected
                      ? const [SkyPalette.primary, SkyPalette.seagrass]
                      : [tokens.borderStrong, tokens.borderStrong],
                ),
                borderRadius: BorderRadius.circular(AppRadius.pill),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
