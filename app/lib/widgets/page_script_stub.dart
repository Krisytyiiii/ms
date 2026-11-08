/// Mobile and desktop have no page script. The 3D view uses its own web view.
Future<void> runPageScript(String source) async {}

/// Mobile and desktop cannot read the page. The phone viewer keeps its own camera.
Future<String?> readPageScript(String source) async => null;
