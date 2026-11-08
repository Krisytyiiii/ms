import 'dart:js_interop';

@JS('eval')
external JSAny? _eval(JSString source);

/// Runs a script in the browser page, where the 3D viewer element lives.
Future<void> runPageScript(String source) async {
  _eval(source.toJS);
}

/// Runs a script and returns the string it evaluates to.
Future<String?> readPageScript(String source) async {
  final value = _eval(source.toJS)?.dartify();
  if (value is String && value.isNotEmpty) {
    return value;
  }
  return null;
}
