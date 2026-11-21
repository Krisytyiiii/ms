import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../classify/local_classifier.dart';
import '../data/scan_history.dart';
import '../theme/tokens.dart';
import '../widgets/aurora_atmosphere.dart';
import '../widgets/diamond_grid_background.dart';
import '../widgets/floating_nav_bar.dart';
import 'conservation_screen.dart';
import 'home_screen.dart';
import 'identify_screen.dart';
import 'library_screen.dart';
import 'profile_screen.dart';
import 'shell_scope.dart';

/// The five destinations share one stack. A floating pill nav holds Home,
/// Library, Conservation and Profile, with Scan as a separate round button
/// beside it. Gold marks the active destination. Home stays the hub that opens
/// Scan, Library, Conservation and Profile.
class AppShell extends StatefulWidget {
  const AppShell({super.key});

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  static const _destinations = [
    MarineNavItem(
      tab: ShellTab.home,
      label: 'Home',
      icon: Icons.home_outlined,
      activeIcon: Icons.home_rounded,
    ),
    MarineNavItem(
      tab: ShellTab.library,
      label: 'Library',
      icon: Icons.menu_book_outlined,
      activeIcon: Icons.menu_book_rounded,
    ),
    MarineNavItem(
      tab: ShellTab.conservation,
      label: 'Conserve',
      icon: Icons.eco_outlined,
      activeIcon: Icons.eco_rounded,
    ),
    MarineNavItem(
      tab: ShellTab.profile,
      label: 'Profile',
      icon: Icons.person_outline_rounded,
      activeIcon: Icons.person_rounded,
    ),
  ];

  static const _scanDestination = MarineNavItem(
    tab: ShellTab.scan,
    label: 'Scan',
    icon: Icons.center_focus_strong_outlined,
    activeIcon: Icons.center_focus_strong,
  );

  var _index = ShellTab.home;
  final _classifier = LocalClassifier();
  final _history = ScanHistoryController();

  @override
  void initState() {
    super.initState();
    _history.load();
  }

  @override
  void dispose() {
    _history.dispose();
    super.dispose();
  }

  void _select(int index) => setState(() => _index = index);

  @override
  Widget build(BuildContext context) {
    final pages = [
      const HomeScreen(),
      IdentifyScreen(classifier: _classifier, history: _history),
      const LibraryScreen(),
      const ConservationScreen(),
      const ProfileScreen(),
    ];

    return ScanHistoryScope(
      controller: _history,
      child: ShellScope(
        select: _select,
        child: AnnotatedRegion<SystemUiOverlayStyle>(
          value: SkyPalette.headerStatusBar,
          child: Stack(
            fit: StackFit.expand,
            children: [
              const AuroraAtmosphere(),
              const DiamondGridBackground(),
              Scaffold(
                backgroundColor: Colors.transparent,
                resizeToAvoidBottomInset: !kIsWeb,
                body: IndexedStack(
                  index: _index,
                  children: [
                    for (var i = 0; i < pages.length; i++)
                      TickerMode(enabled: i == _index, child: pages[i]),
                  ],
                ),
                bottomNavigationBar: MarineNavBar(
                  index: _index,
                  items: _destinations,
                  scan: _scanDestination,
                  onSelect: _select,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
