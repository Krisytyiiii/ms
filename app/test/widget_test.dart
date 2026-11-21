import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:image_picker/image_picker.dart';
import 'package:marine_see/app.dart';
import 'package:marine_see/classify/classifier.dart';
import 'package:marine_see/classify/stub_classifier.dart';
import 'package:marine_see/data/scan_history.dart';
import 'package:marine_see/screens/history_screen.dart';
import 'package:marine_see/screens/result_screen.dart';
import 'package:marine_see/theme/theme.dart';
import 'package:marine_see/theme/tokens.dart';
import 'package:marine_see/widgets/library_deck.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  test('StubClassifier does not invent a species or confidence', () async {
    final result = await StubClassifier().identify(XFile('dummy.jpg'));
    expect(result.status, IdentifyStatus.stub);
    expect(result.slug, isNull);
    expect(result.confidence, isNull);
    expect(result.message, StubClassifier.notConnectedMessage);
  });

  test('scan history persists between controller instances', () async {
    SharedPreferences.setMockInitialValues({});
    final first = ScanHistoryController();
    await first.load();
    first.record(
      ScanRecord(
        slug: 'enhalus_acoroides',
        confidence: 0.74,
        at: DateTime(2026, 11, 21, 10),
        thumb: 'dGh1bWI=',
      ),
    );
    await Future<void>.delayed(const Duration(milliseconds: 20));
    first.dispose();

    final second = ScanHistoryController();
    await second.load();
    expect(second.records, hasLength(1));
    expect(second.records.first.slug, 'enhalus_acoroides');
    expect(second.records.first.confidence, 0.74);
    expect(second.records.first.thumb, 'dGh1bWI=');
    second.dispose();
  });

  testWidgets('tab screens fit a 375-wide phone', (tester) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MarineSeeApp());
    await tester.pump();

    expect(find.text('Identify seagrass'), findsOneWidget);
    await tester.tap(find.text('Skip'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('MarineSee').hitTestable(), findsOneWidget);
    expect(find.text('Identify a seagrass').hitTestable(), findsOneWidget);
    expect(find.text('Scan Seagrass').hitTestable(), findsOneWidget);
    expect(find.text('How the match is made').hitTestable(), findsOneWidget);
    expect(find.byTooltip('Scan'), findsOneWidget);
    expect(find.byTooltip('Library'), findsOneWidget);
    expect(find.byTooltip('Conserve'), findsOneWidget);
    expect(find.byTooltip('Profile'), findsOneWidget);
    expect(find.text('Your Impact'), findsNothing);
    expect(find.textContaining('71%'), findsNothing);
    expect(find.text('CNN Model Active'), findsNothing);

    await tester.tap(find.byTooltip('Scan'));
    await tester.pump();
    expect(find.text('No photo yet').hitTestable(), findsOneWidget);
    expect(find.text('Camera').hitTestable(), findsOneWidget);
    expect(find.text('Gallery').hitTestable(), findsOneWidget);
    expect(find.text('Identify').hitTestable(), findsOneWidget);

    await tester.tap(find.byTooltip('Library'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Showing 9 species').hitTestable(), findsOneWidget);
    expect(find.text('Cymodocea rotundata').hitTestable(), findsWidgets);

    await tester.enterText(find.byType(TextField), 'no such seagrass');
    await tester.pump();
    expect(find.text('No matching species').hitTestable(), findsOneWidget);
    expect(find.text('Cymodocea rotundata'), findsNothing);

    await tester.tap(find.text('Show all species'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));
    expect(find.text('Showing 9 species').hitTestable(), findsOneWidget);
    expect(find.text('Cymodocea rotundata').hitTestable(), findsWidgets);

    await tester.drag(find.byType(LibraryDeck), const Offset(0, 240));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.text('Cymodocea serrulata').hitTestable(), findsWidgets);

    await tester.tap(find.byTooltip('Conserve'));
    await tester.pump();
    expect(find.text('Why seagrass matters').hitTestable(), findsOneWidget);
    expect(find.text('TBD — adviser source').hitTestable(), findsOneWidget);

    await tester.tap(find.byTooltip('Profile'));
    await tester.pump();
    expect(
      find
          .text('MarineSee identifies and teaches the nine Mati species.')
          .hitTestable(),
      findsOneWidget,
    );
    expect(find.text('Camera or gallery').hitTestable(), findsOneWidget);
  });

  testWidgets('species profile opens from the deck at 375 wide', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MarineSeeApp());
    await tester.pump();
    await tester.tap(find.text('Skip'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    await tester.tap(find.byTooltip('Library'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    await tester.tap(find.byType(LibraryDeck));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));

    expect(find.text('Cymodocea rotundata'), findsWidgets);
    expect(find.text('Botanical characteristics'), findsOneWidget);
    expect(find.text('View in 3D'), findsOneWidget);

    await tester.scrollUntilVisible(
      find.text('SOURCES'),
      400,
      scrollable: find.descendant(
        of: find.byType(CustomScrollView),
        matching: find.byType(Scrollable),
      ),
    );
    expect(find.text('SOURCES'), findsOneWidget);
  });

  testWidgets('home card tap cycles the deck without opening a profile', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MarineSeeApp());
    await tester.pump();
    await tester.tap(find.text('Skip'));
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(milliseconds: 200));
    }

    final card = find.text('Smooth ribbon seagrass');
    await tester.scrollUntilVisible(card, 200);
    expect(card, findsOneWidget);

    await tester.tap(card);
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 700));

    expect(find.text('Serrated ribbon seagrass'), findsOneWidget);
    expect(find.text('Smooth ribbon seagrass'), findsNothing);
    expect(find.text('Botanical characteristics'), findsNothing);
  });

  testWidgets('identify error shows the error and Try again', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildMarineSeeTheme(AppTokens.sky),
        home: ResultScreen(
          imageBytes: _png,
          result: const IdentifyResult(
            status: IdentifyStatus.error,
            message: 'Cannot reach the identify API.',
          ),
        ),
      ),
    );
    await tester.pump();

    expect(find.text('Cannot reach the identify API.'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
    expect(find.text('Open species profile'), findsNothing);
    expect(find.text('Open 3D'), findsNothing);
    expect(find.textContaining('Cymodocea'), findsNothing);
  });

  testWidgets('a finished identify shows the name and percent', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildMarineSeeTheme(AppTokens.sky),
        home: ResultScreen(
          imageBytes: _png,
          result: const IdentifyResult(
            slug: 'enhalus_acoroides',
            confidence: 0.62,
            status: IdentifyStatus.ok,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Enhalus acoroides'), findsOneWidget);
    expect(find.text('62%'), findsOneWidget);
    expect(find.text(ResultScreen.retakeSentence), findsNothing);
    expect(find.text('Open species profile'), findsOneWidget);
    await tester.scrollUntilVisible(find.text('Try again'), 200);
    expect(find.text('Open 3D'), findsOneWidget);
  });

  testWidgets('low confidence shows the name, percent, and retake notice', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(400, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildMarineSeeTheme(AppTokens.sky),
        home: ResultScreen(
          imageBytes: _png,
          result: const IdentifyResult(
            slug: 'cymodocea_rotundata',
            confidence: 0.42,
            status: IdentifyStatus.lowConfidence,
            message: ResultScreen.retakeSentence,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Cymodocea rotundata'), findsOneWidget);
    expect(find.text('42%'), findsOneWidget);
    expect(find.text(ResultScreen.retakeSentence), findsOneWidget);
    expect(find.text('Open species profile'), findsOneWidget);
    expect(find.text('Open 3D'), findsOneWidget);
    expect(find.text('None of these'), findsOneWidget);
    expect(find.text('Try again'), findsOneWidget);
  });

  testWidgets('None of these replaces the species call with an abstention', (
    tester,
  ) async {
    tester.view.physicalSize = const Size(400, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(
      MaterialApp(
        theme: buildMarineSeeTheme(AppTokens.sky),
        home: ResultScreen(
          imageBytes: _png,
          result: const IdentifyResult(
            slug: 'enhalus_acoroides',
            confidence: 0.62,
            status: IdentifyStatus.ok,
          ),
        ),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Enhalus acoroides'), findsOneWidget);
    await tester.tap(find.text('None of these'));
    await tester.pump();

    expect(find.text(ResultScreen.rejectedHeadline), findsOneWidget);
    expect(find.text(ResultScreen.rejectedMessage), findsOneWidget);
    expect(find.text('Take another photo'), findsOneWidget);
    expect(find.text('Enhalus acoroides'), findsNothing);
    expect(find.text('62%'), findsNothing);
    expect(find.text('Open species profile'), findsNothing);
    expect(find.text('Open 3D'), findsNothing);

    await tester.tap(find.text('Show the result again'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('Enhalus acoroides'), findsOneWidget);
    expect(find.text(ResultScreen.rejectedHeadline), findsNothing);
  });

  testWidgets('home history banner opens the dedicated history page', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    tester.view.physicalSize = const Size(375, 812);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const MarineSeeApp());
    await tester.pump();
    await tester.tap(find.text('Skip'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('SCANNER HISTORY').hitTestable(), findsOneWidget);
    await tester.tap(find.text('SCANNER HISTORY'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));

    expect(find.text('Scanner history').hitTestable(), findsOneWidget);
    expect(find.text('Nothing saved yet').hitTestable(), findsOneWidget);
  });

  testWidgets('history page shows a cited answer and opens the evidence', (
    tester,
  ) async {
    SharedPreferences.setMockInitialValues({});
    tester.view.physicalSize = const Size(400, 1400);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    final history = ScanHistoryController();
    addTearDown(history.dispose);
    await history.load();
    history.record(
      ScanRecord(
        slug: 'cymodocea_rotundata',
        confidence: 0.62,
        at: DateTime.now(),
      ),
    );

    await tester.pumpWidget(
      MaterialApp(
        theme: buildMarineSeeTheme(AppTokens.sky),
        home: HistoryScreen(history: history),
      ),
    );
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 400));

    expect(find.text('MarineSee agent'), findsWidgets);
    expect(find.text('Reviewed 1 scan on this phone'), findsOneWidget);
    expect(find.text('Fair'), findsOneWidget);
    expect(find.text('Species profile'), findsOneWidget);
    expect(find.text('3 tool calls'), findsOneWidget);
    expect(
      find.textContaining('Cymodocea rotundata', findRichText: true),
      findsWidgets,
    );

    await tester.tap(find.text('Species profile'));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));

    expect(find.text('FROM THE SPECIES PROFILE'), findsOneWidget);
    expect(find.text('Profile'), findsOneWidget);
    expect(find.text('3D'), findsOneWidget);
    expect(find.textContaining('Scanned'), findsOneWidget);
  });
}

final _png = base64Decode(
  'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII=',
);
