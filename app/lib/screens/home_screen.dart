import 'package:flutter/material.dart';

import '../data/profile_controller.dart';
import '../widgets/home_app_bar.dart';
import '../widgets/home_hero_banner.dart';
import '../widgets/home_scan_history.dart';
import '../widgets/home_species_deck.dart';
import '../widgets/how_match_works.dart';
import 'shell_scope.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final profile = ProfileScope.of(context);

    return ListView(
      padding: EdgeInsets.zero,
      children: [
        HomeAppBar(
          name: profile.displayName,
          onProfile: () => ShellScope.of(context).select(ShellTab.profile),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: HomeHeroBanner(
            onScan: () => ShellScope.of(context).select(ShellTab.scan),
          ),
        ),
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: HomeScanHistory(),
        ),
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 12, 16, 0),
          child: HomeSpeciesDeck(),
        ),
        const Padding(
          padding: EdgeInsets.fromLTRB(16, 14, 16, 24),
          child: HowMatchWorks(),
        ),
      ],
    );
  }
}
