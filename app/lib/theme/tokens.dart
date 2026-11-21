import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

enum AppStyle { night, frost }

/// Ocean blue and bright yellow. Blue carries structure, yellow carries action.
/// Widgets read [AppTokens]; these swatches are the roles.
abstract final class SkyPalette {
  static const primary = Color(0xFF0077B6);
  static const onPrimary = Color(0xFFFFFFFF);
  static const primaryDark = Color(0xFF023E8A);
  static const water = Color(0xFF48CAE4);
  static const waterDeep = Color(0xFF00A6D6);
  static const primaryContainer = Color(0xFFD6EEF9);

  static const sky = Color(0xFF48CAE4);
  static const skyDeep = Color(0xFF2FB8D9);
  static const onSky = Color(0xFF04263F);
  static const onHeader = Color(0xFFFFFFFF);
  static const headerTop = Color(0xFF0077B6);
  static const headerMid = Color(0xFF00659D);
  static const headerBottom = Color(0xFF023E8A);

  static const sand = Color(0xFFFFE38A);
  static const sandDeep = Color(0xFFFFC300);
  static const sandLight = Color(0xFFFFF6D6);
  static const onSand = Color(0xFF3A2A0E);
  static const sandContainer = Color(0xFFFFF8E1);

  static const gold = Color(0xFFFFD60A);
  static const goldBright = Color(0xFFFFE45C);
  static const goldDeep = Color(0xFFFFC300);
  static const goldSoft = Color(0xFFFFEB8F);
  static const goldContainer = Color(0xFFFFF7C9);
  static const onGold = Color(0xFF04263F);

  static const mist = Color(0xFFF8FAFC);
  static const mistDeep = Color(0xFFEEF4FA);
  static const foam = Color(0xFFFFFFFF);
  static const seagrass = Color(0xFFFFC300);
  static const onSeagrass = Color(0xFF04263F);

  static const ink = onSky;
  static const inkMuted = Color(0xFF4F6475);
  static const inkSubtle = Color(0xFF7A8B99);
  static const lineOnSand = Color(0xFFE2E8F0);
  static const lineOnSky = Color(0x66FFFFFF);
  static const shadow = Color(0x1A023E8A);

  static const inverse = Color(0xFF0077B6);
  static const inverseContainer = Color(0xFF48CAE4);
  static const onInverse = Color(0xFFFFFFFF);

  static const danger = Color(0xFFB3261E);
  static const dangerFill = Color(0xFFFDECEA);
  static const notice = Color(0xFF8A5A0B);
  static const noticeFill = Color(0xFFFFF7DE);
  static const noticeBorder = Color(0xFFEBD08A);

  static const page = mist;
  static const pageDeep = mistDeep;
  static const ocean = primary;
  static const oceanDeep = primaryDark;
  static const card = foam;
  static const line = lineOnSand;
  static const lineStrong = Color(0xFFC9D6E2);
  static const tileBlue = primary;
  static const tileGreen = seagrass;
  static const scanner = Color(0xFF0077B6);
  static const scannerDeep = Color(0xFF023E8A);

  static const darkStatusBar = SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.dark,
    statusBarBrightness: Brightness.light,
    systemNavigationBarColor: foam,
    systemNavigationBarIconBrightness: Brightness.dark,
  );

  static const lightStatusBar = SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    statusBarBrightness: Brightness.dark,
    systemNavigationBarColor: scannerDeep,
    systemNavigationBarIconBrightness: Brightness.light,
  );

  static const headerStatusBar = SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    statusBarIconBrightness: Brightness.light,
    statusBarBrightness: Brightness.dark,
    systemNavigationBarColor: foam,
    systemNavigationBarIconBrightness: Brightness.dark,
  );
}

/// Color tokens for the teal header and light page.
///
/// [night] and [frost] are the same palette. Primary buttons use [brand].
/// The page below a header is [abyss].
@immutable
class AppTokens extends ThemeExtension<AppTokens> {
  const AppTokens({
    required this.style,
    required this.brightness,
    required this.abyss,
    required this.ocean,
    required this.navy,
    required this.surface,
    required this.surfaceHigh,
    required this.ink,
    required this.inkMuted,
    required this.inkSubtle,
    required this.cyan,
    required this.teal,
    required this.brand,
    required this.brandDeep,
    required this.violet,
    required this.onBrand,
    required this.danger,
    required this.notice,
    required this.noticeFill,
    required this.noticeBorder,
    required this.border,
    required this.borderStrong,
    required this.glowCyan,
    required this.glowTeal,
    required this.shadow,
    required this.depthGradient,
    required this.primaryGradient,
    required this.headerGradient,
    required this.surfaceSheen,
    required this.systemUi,
    required this.auraCyan,
    required this.auraTeal,
    required this.auraViolet,
  });

  final AppStyle style;
  final Brightness brightness;
  final Color abyss;
  final Color ocean;
  final Color navy;
  final Color surface;
  final Color surfaceHigh;
  final Color ink;
  final Color inkMuted;
  final Color inkSubtle;
  final Color cyan;
  final Color teal;
  final Color brand;
  final Color brandDeep;
  final Color violet;
  final Color onBrand;
  final Color danger;
  final Color notice;
  final Color noticeFill;
  final Color noticeBorder;
  final Color border;
  final Color borderStrong;
  final Color glowCyan;
  final Color glowTeal;
  final Color shadow;
  final LinearGradient depthGradient;
  final LinearGradient primaryGradient;
  final LinearGradient headerGradient;
  final LinearGradient surfaceSheen;
  final SystemUiOverlayStyle systemUi;
  final double auraCyan;
  final double auraTeal;
  final double auraViolet;

  static const double tapMin = 48;
  static const Size tapSize = Size(double.infinity, 52);
  static const double radius = 20;

  static const sky = AppTokens(
    style: AppStyle.frost,
    brightness: Brightness.light,
    abyss: SkyPalette.mist,
    ocean: SkyPalette.mistDeep,
    navy: SkyPalette.primaryContainer,
    surface: SkyPalette.foam,
    surfaceHigh: SkyPalette.foam,
    ink: SkyPalette.ink,
    inkMuted: SkyPalette.inkMuted,
    inkSubtle: SkyPalette.inkSubtle,
    cyan: SkyPalette.primary,
    teal: SkyPalette.gold,
    brand: SkyPalette.primary,
    brandDeep: SkyPalette.primaryDark,
    violet: SkyPalette.skyDeep,
    onBrand: SkyPalette.onPrimary,
    danger: SkyPalette.danger,
    notice: SkyPalette.notice,
    noticeFill: SkyPalette.noticeFill,
    noticeBorder: SkyPalette.noticeBorder,
    border: SkyPalette.lineOnSand,
    borderStrong: SkyPalette.lineOnSand,
    glowCyan: Color(0x330077B6),
    glowTeal: Color(0x33FFD60A),
    shadow: SkyPalette.shadow,
    depthGradient: LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [SkyPalette.mist, SkyPalette.mist, SkyPalette.mistDeep],
      stops: [0.0, 0.22, 1.0],
    ),
    primaryGradient: LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [SkyPalette.primary, SkyPalette.primaryDark],
    ),
    headerGradient: LinearGradient(
      begin: Alignment.topCenter,
      end: Alignment.bottomCenter,
      colors: [
        SkyPalette.headerTop,
        SkyPalette.headerMid,
        SkyPalette.headerBottom,
      ],
      stops: [0.0, 0.48, 1.0],
    ),
    surfaceSheen: LinearGradient(
      begin: Alignment.topLeft,
      end: Alignment.bottomRight,
      colors: [SkyPalette.foam, SkyPalette.foam, SkyPalette.goldContainer],
    ),
    systemUi: SkyPalette.darkStatusBar,
    auraCyan: 0.08,
    auraTeal: 0.05,
    auraViolet: 0.04,
  );

  static const night = sky;
  static const frost = sky;

  static AppTokens forStyle(AppStyle style) => sky;

  bool get isLight => brightness == Brightness.light;

  List<BoxShadow> get cardShadows => [
    BoxShadow(color: shadow, blurRadius: 18, offset: const Offset(0, 8)),
  ];

  List<BoxShadow> get cardGlowShadows => [
    BoxShadow(color: glowCyan, blurRadius: 22, offset: const Offset(0, 8)),
    BoxShadow(color: shadow, blurRadius: 12, offset: const Offset(0, 6)),
  ];

  List<BoxShadow> get glowShadows => [
    BoxShadow(color: glowTeal, blurRadius: 16, offset: const Offset(0, 6)),
  ];

  @override
  AppTokens copyWith({AppStyle? style}) => forStyle(style ?? this.style);

  @override
  AppTokens lerp(ThemeExtension<AppTokens>? other, double t) {
    if (other is! AppTokens) {
      return this;
    }
    return t < 0.5 ? this : other;
  }
}

extension MarineSeeThemeX on BuildContext {
  AppTokens get tokens =>
      Theme.of(this).extension<AppTokens>() ?? AppTokens.sky;
}

abstract final class AppSpace {
  static const double xs = 8;
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 32;
  static const double maxContent = 720;
  static const double stackActionsBelow = 300;

  static const double navClearance = 24;

  static EdgeInsets pageInsets(BuildContext context, {double extraBottom = 0}) {
    final width = MediaQuery.sizeOf(context).width;
    final horizontal = width >= 768 ? 32.0 : 20.0;
    return EdgeInsets.fromLTRB(horizontal, 16, horizontal, 28 + extraBottom);
  }

  static EdgeInsets headerInsets(BuildContext context) {
    final width = MediaQuery.sizeOf(context).width;
    final horizontal = width >= 768 ? 32.0 : 20.0;
    return EdgeInsets.fromLTRB(horizontal, 12, horizontal, 20);
  }
}

abstract final class AppRadius {
  static const double sm = 12;
  static const double md = 16;
  static const double lg = 24;
  static const double xl = 28;
  static const double pill = 999;

  static BorderRadius get button => BorderRadius.circular(xl);
  static BorderRadius get card => BorderRadius.circular(lg);
  static BorderRadius get sheet => BorderRadius.circular(xl);
}

abstract final class AppMotion {
  static const Duration fast = Duration(milliseconds: 180);
  static const Duration medium = Duration(milliseconds: 280);
  static const Duration aurora = Duration(seconds: 14);
  static const Curve ease = Curves.easeInOutCubic;
}
