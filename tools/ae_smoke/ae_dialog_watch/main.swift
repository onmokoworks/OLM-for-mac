import AppKit
import ApplicationServices
import ScreenCaptureKit
import Vision
import Darwin

let appPath = "/Applications/Adobe After Effects 2026/Adobe After Effects 2026.app"
let fm = FileManager.default
struct Failure: Error, CustomStringConvertible { let description: String; init(_ s: String) { description = s } }
func emit(_ value: Any) throws {
    let data = try JSONSerialization.data(withJSONObject: value, options: [.sortedKeys])
    FileHandle.standardOutput.write(data); FileHandle.standardOutput.write(Data([10]))
}
func pause(_ seconds: Double) { RunLoop.current.run(until: Date().addingTimeInterval(seconds)) }
func windows(_ pid: pid_t) -> [[String: Any]] {
    (CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID)
        as? [[String: Any]] ?? []).filter { ($0[kCGWindowOwnerPID as String] as? Int) == Int(pid) }
}
func bounds(_ row: [String: Any]) -> CGRect {
    CGRect(dictionaryRepresentation: row[kCGWindowBounds as String] as! CFDictionary)!
}
func ownedProcess(_ pid: pid_t) -> Bool {
    var path = [CChar](repeating: 0, count: 4 * Int(MAXPATHLEN))
    guard proc_pidpath(pid, &path, UInt32(path.count)) > 0 else { return false }
    return String(cString: path) == appPath + "/Contents/MacOS/After Effects"
}
func sameApp(_ pid: pid_t) -> NSRunningApplication? {
    guard let app = NSRunningApplication(processIdentifier: pid),
          app.bundleURL?.path == appPath, !app.isTerminated else { return nil }
    return app
}
final class CaptureResult {
    private let lock = NSLock()
    private var result: Result<CGImage, Error>?
    func set(_ value: Result<CGImage, Error>) { lock.lock(); defer { lock.unlock() }; result = value }
    func get() -> Result<CGImage, Error>? { lock.lock(); defer { lock.unlock() }; return result }
}
func snapshot(_ id: CGWindowID, pid: pid_t) throws -> CGImage {
    let captured = CaptureResult()
    SCShareableContent.getExcludingDesktopWindows(true, onScreenWindowsOnly: true) { content, error in
        guard let window = content?.windows.first(where: { $0.windowID == id && $0.owningApplication?.processID == pid }) else {
            captured.set(.failure(error ?? Failure("Target window unavailable"))); return
        }
        let filter = SCContentFilter(desktopIndependentWindow: window)
        let config = SCStreamConfiguration()
        config.width = max(1, Int((filter.contentRect.width * CGFloat(filter.pointPixelScale)).rounded()))
        config.height = max(1, Int((filter.contentRect.height * CGFloat(filter.pointPixelScale)).rounded()))
        config.showsCursor = false
        config.ignoreShadowsSingleWindow = true
        SCScreenshotManager.captureImage(contentFilter: filter, configuration: config) { image, error in
            if let image = image {
                try? emit(["event": "capture", "windowID": id,
                    "pointWidth": filter.contentRect.width, "pointHeight": filter.contentRect.height,
                    "scale": filter.pointPixelScale, "pixelWidth": image.width, "pixelHeight": image.height])
                captured.set(.success(image))
            }
            else { captured.set(.failure(error ?? Failure("Empty capture"))) }
        }
    }
    let deadline = Date().addingTimeInterval(10)
    while captured.get() == nil && Date() < deadline { pause(0.02) }
    guard let result = captured.get() else { throw Failure("ScreenCaptureKit capture timeout; permission loss or window transition not established") }
    do { return try result.get() }
    catch { throw Failure("ScreenCaptureKit capture failed: \(error)") }
}
func recognize(_ image: CGImage) throws -> [TextBox] {
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["ja-JP", "en-US"]
    request.usesLanguageCorrection = false
    try VNImageRequestHandler(cgImage: image).perform([request])
    return (request.results ?? []).compactMap { observation in
        guard let text = observation.topCandidates(1).first else { return nil }
        let r = observation.boundingBox
        return TextBox(text: text.string, box: [r.minX, 1 - r.maxY, r.width, r.height], confidence: text.confidence)
    }
}
func save(_ image: CGImage, _ path: URL) throws {
    // Preserve the native pixels used by Vision so offline OCR is reproducible.
    let bitmap = NSBitmapImageRep(cgImage: image)
    guard let data = bitmap.representation(using: .png, properties: [:]) else {
        throw Failure("Cannot encode evidence")
    }
    try data.write(to: path, options: .atomic)
}

func attr(_ el: AXUIElement, _ name: String) -> CFTypeRef? {
    var value: CFTypeRef?
    guard AXUIElementCopyAttributeValue(el, name as CFString, &value) == .success else { return nil }
    return value
}
func axRect(_ el: AXUIElement) -> CGRect? {
    guard let p = attr(el, kAXPositionAttribute), let s = attr(el, kAXSizeAttribute),
          CFGetTypeID(p) == AXValueGetTypeID(), CFGetTypeID(s) == AXValueGetTypeID() else { return nil }
    var point = CGPoint.zero; var size = CGSize.zero
    guard AXValueGetValue(p as! AXValue, .cgPoint, &point),
          AXValueGetValue(s as! AXValue, .cgSize, &size) else { return nil }
    return CGRect(origin: point, size: size)
}
func isWorkspace(_ pid: pid_t, _ window: [String: Any]) -> Bool {
    let rect = bounds(window)
    let application = AXUIElementCreateApplication(pid)
    AXUIElementSetMessagingTimeout(application, 1)
    let ax = (attr(application, kAXWindowsAttribute) as? [AXUIElement] ?? []).first { axRect($0) == rect }
    return Policy.workspace(title: window[kCGWindowName as String] as? String ?? "", rect: rect,
        role: ax.flatMap { attr($0, kAXRoleAttribute) as? String },
        subrole: ax.flatMap { attr($0, kAXSubroleAttribute) as? String },
        modal: ax.flatMap { attr($0, kAXModalAttribute) as? Bool } ?? false)
}
func axButtons(_ pid: pid_t, _ rect: CGRect) -> [(TextBox, AXUIElement)] {
    var found: [(TextBox, AXUIElement)] = []
    var visited = 0
    let deadline = Date().addingTimeInterval(2)
    func walk(_ el: AXUIElement, _ depth: Int) {
        visited += 1
        guard depth < 20 && visited < 2000 && Date() < deadline else { return }
        if attr(el, kAXRoleAttribute) as? String == kAXButtonRole,
           (attr(el, kAXEnabledAttribute) as? Bool) == true,
           let name = attr(el, kAXTitleAttribute) as? String,
           let r = axRect(el), rect.contains(r), r.width > 0, r.height > 0 {
            found.append((TextBox(text: name, box: [(r.minX-rect.minX)/rect.width,
                (r.minY-rect.minY)/rect.height, r.width/rect.width, r.height/rect.height], confidence: 1), el))
        }
        for child in attr(el, kAXChildrenAttribute) as? [AXUIElement] ?? [] { walk(child, depth+1) }
    }
    let application = AXUIElementCreateApplication(pid)
    AXUIElementSetMessagingTimeout(application, 1)
    for window in attr(application, kAXWindowsAttribute) as? [AXUIElement] ?? [] {
        // Never borrow a button from an overlapping underlying AE window.
        if axRect(window) == rect { walk(window, 0) }
    }
    return found
}
func watch(_ dir: URL) throws {
    guard AXIsProcessTrusted() else { throw Failure("blocked: needs Accessibility permission for Terminal") }
    guard CGPreflightScreenCaptureAccess() else { throw Failure("blocked: needs Screen Recording for Terminal") }
    try Data("ready".utf8).write(to: dir.appendingPathComponent("ready"), options: .atomic)
    let pidFile = dir.appendingPathComponent("pid")
    let stop = dir.appendingPathComponent("stop")
    let deadline = Date().addingTimeInterval(240)
    while !fm.fileExists(atPath: pidFile.path) {
        if fm.fileExists(atPath: stop.path) { return }
        guard Date() < deadline else { throw Failure("No owned AE PID supplied") }
        pause(0.1)
    }
    let pid = pid_t(try String(contentsOf: pidFile, encoding: .utf8).trimmingCharacters(in: .whitespacesAndNewlines))!
    // AppKit registration may lag exec; never discover/adopt an arbitrary AE.
    let registration = Date().addingTimeInterval(10)
    while sameApp(pid) == nil && Date() < registration { pause(0.1) }
    guard sameApp(pid) != nil else { throw Failure("Owned PID has no matching AE 2026 bundle path") }
    var observer: AXObserver?
    let observerResult = AXObserverCreate(pid, { _, _, notification, _ in
        try? emit(["event": "ax-notification", "notification": notification as String])
    }, &observer)
    if let observer = observer {
        let element = AXUIElementCreateApplication(pid)
        AXObserverAddNotification(observer, element, kAXWindowCreatedNotification as CFString, nil)
        AXObserverAddNotification(observer, element, kAXFocusedWindowChangedNotification as CFString, nil)
        CFRunLoopAddSource(CFRunLoopGetCurrent(), AXObserverGetRunLoopSource(observer), .defaultMode)
    }
    try emit(["event": "attached", "pid": pid, "bundle": appPath, "axObserverResult": observerResult.rawValue])
    var clicks = 0
    var firstSeen: [CGWindowID: Date] = [:]
    var seenGeometry: [CGWindowID: CGRect] = [:]
    var registrationMissing: Date?
    while !fm.fileExists(atPath: stop.path) && ownedProcess(pid) {
        guard let app = sameApp(pid) else {
            if registrationMissing == nil { registrationMissing = Date() }
            guard Date().timeIntervalSince(registrationMissing!) < 10 else {
                throw Failure("AE bundle registration unavailable for 10 seconds")
            }
            pause(0.5); continue
        }
        registrationMissing = nil
        for window in windows(pid) {
            let id = window[kCGWindowNumber as String] as! CGWindowID
            let rect = bounds(window)
            if seenGeometry[id] != rect {
                try emit(["event": "window", "pid": pid, "window": window]); seenGeometry[id] = rect
                firstSeen[id] = Date()
            }
            if Policy.scriptProgress(window[kCGWindowName as String] as? String ?? "") {
                continue // Benign script execution: never click Cancel.
            }
            if isWorkspace(pid, window) {
                let ready = dir.appendingPathComponent("workspace-ready")
                if !fm.fileExists(atPath: ready.path) {
                    try Data().write(to: ready, options: .atomic)
                    try emit(["event": "workspace", "pid": pid, "window": window])
                }
                continue
            }
            guard rect.width >= 200, rect.height >= 100 else { continue }
            guard Date().timeIntervalSince(firstSeen[id] ?? Date()) >= 2 else { continue }
            let image: CGImage
            do { image = try snapshot(id, pid: pid) }
            catch {
                // A destroyed splash is a verified transition, not permission loss.
                guard CGPreflightScreenCaptureAccess(),
                      !windows(pid).contains(where: { ($0[kCGWindowNumber as String] as? CGWindowID) == id }) else { throw error }
                try emit(["event": "window-disappeared", "windowID": id])
                continue
            }
            let rows = try recognize(image)
            guard !rows.isEmpty else {
                try save(image, dir.appendingPathComponent("blank-\(id).png"))
                throw Failure("blocked: needs Screen Recording for Terminal (blank/unreadable capture)")
            }
            let ax = axButtons(pid, rect)
            let allRows = rows + ax.map { $0.0 }
            if !Policy.knownDialog(rows) {
                if Policy.splash(rows) { continue }
                try save(image, dir.appendingPathComponent("unknown-\(id).png"))
                try emit(["event": "unknown", "pid": pid, "window": window, "ocr": try jsonRows(rows)])
                throw Failure("Unknown AE dialog; no click")
            }
            try emit(["event": "dialog", "pid": pid, "window": window])
            let layout = Policy.crashRecoveryLayout(rows)
            let recovery = rows.contains { $0.text.contains("クラッシュ修復") ||
                ["プラグインを管理", "環境設定をリセット", "セーフモードで開始"].contains($0.text) }
            let safe = (recovery ? [] : Policy.candidates(allRows)).filter { row in
                row.rect.midY > 0.55 || ax.contains { $0.0.text == row.text && $0.0.rect.intersects(row.rect) }
            }
            guard let selected = layout ?? safe.first else {
                try save(image, dir.appendingPathComponent("no-safe-button-\(id).png"))
                try emit(["event": "no-safe-button", "pid": pid, "window": window, "ocr": try jsonRows(rows)])
                throw Failure("Known dialog has no safe allowlisted button")
            }
            // Optional read-only evidence barrier used by the live crash-state probe.
            if layout != nil && fm.fileExists(atPath: dir.appendingPathComponent("snapshot-hook").path) {
                try Data().write(to: dir.appendingPathComponent("snapshot-request"))
                let until = Date().addingTimeInterval(30)
                while !fm.fileExists(atPath: dir.appendingPathComponent("snapshot-ready").path) && Date() < until { pause(0.1) }
                guard fm.fileExists(atPath: dir.appendingPathComponent("snapshot-ready").path) else {
                    throw Failure("Crash-state snapshot timed out; no click")
                }
            }
            guard clicks < 10 else { throw Failure("10-click limit reached") }
            guard app.activate(options: []) else { throw Failure("AE activation failed") }
            pause(0.3)
            guard sameApp(pid) != nil, NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
                  let current = windows(pid).first(where: { ($0[kCGWindowNumber as String] as? CGWindowID) == id }),
                  bounds(current) == rect else { throw Failure("AE focus/window changed; no click") }
            // Re-recognize immediately before acting, including destructive overlap checks.
            let before = try snapshot(id, pid: pid)
            let fresh = try recognize(before)
            let freshAX = axButtons(pid, rect)
            guard Policy.knownDialog(fresh),
                  let chosen = (layout != nil ? Policy.crashRecoveryLayout(fresh) : Policy.candidates(fresh + freshAX.map { $0.0 }).first(where: {
                      $0.text == selected.text && $0.rect.intersects(selected.rect)
                  })) else { throw Failure("Dialog changed before click") }
            let axTarget = layout != nil ? nil : freshAX.first { $0.0.text == chosen.text && $0.0.rect.intersects(chosen.rect) }
            let method = axTarget == nil ? "OCR" : "AX"
            clicks += 1
            let prefix = String(format: "%02d", clicks)
            try save(before, dir.appendingPathComponent("\(prefix)-before.png"))
            func record(_ phase: String, _ rows: [TextBox], _ verified: Bool) throws {
                try emit(["event": "click", "phase": phase, "time": ISO8601DateFormatter().string(from: Date()),
                    "pid": pid, "window": window, "bounds": [rect.minX, rect.minY, rect.width, rect.height],
                    "ocr": try jsonRows(rows), "rule": layout != nil ? "crash_recovery_layout" : "exact_label", "chosenLabel": chosen.text, "method": method, "verified": verified])
            }
            try record("before", fresh, false)
            if let target = axTarget {
                guard AXUIElementPerformAction(target.1, kAXPressAction as CFString) == .success else {
                    throw Failure("AXPress failed; no fallback/repeated click")
                }
            } else {
                let point = Policy.centre(chosen, window: rect)
                // Reject occlusion and focus races. PID-directed events never target another app.
                let front = (CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []).first {
                    bounds($0).contains(point) && ($0[kCGWindowLayer as String] as? Int ?? 0) >= 0
                }
                guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
                      front?[kCGWindowNumber as String] as? CGWindowID == id else { throw Failure("Click point occluded; no click") }
                guard let down = CGEvent(mouseEventSource: nil, mouseType: .leftMouseDown, mouseCursorPosition: point, mouseButton: .left),
                      let up = CGEvent(mouseEventSource: nil, mouseType: .leftMouseUp, mouseCursorPosition: point, mouseButton: .left) else { throw Failure("Cannot construct mouse events") }
                down.postToPid(pid); up.postToPid(pid)
            }
            pause(1)
            let remaining = windows(pid)
            if let current = remaining.first(where: { ($0[kCGWindowNumber as String] as? CGWindowID) == id }) {
                let after = try snapshot(id, pid: pid)
                try save(after, dir.appendingPathComponent("\(prefix)-after.png"))
                let afterRows = try recognize(after)
                let disappeared = !Policy.knownDialog(afterRows) && !afterRows.isEmpty
                try record("after", afterRows, disappeared)
                guard disappeared else { throw Failure("Dialog still present after click; stop without retry") }
                seenGeometry[id] = bounds(current)
            } else if let next = remaining.first(where: { bounds($0).width >= 200 && bounds($0).height >= 100 }) {
                let after = try snapshot(next[kCGWindowNumber as String] as! CGWindowID, pid: pid)
                try save(after, dir.appendingPathComponent("\(prefix)-after.png"))
                let afterRows = try recognize(after)
                let disappeared = !Policy.knownDialog(afterRows)
                try record("after", afterRows, disappeared)
                guard disappeared else { throw Failure("Dialog moved/reappeared after click") }
            } else {
                // Do not substitute a screenshot of another application.
                try record("after-no-AE-window", [], false)
                throw Failure("Dialog window disappeared but no AE window available for after capture")
            }
        }
        pause(0.5)
    }
    try emit(["event": "stopped", "pid": pid, "clicks": clicks])
}
func jsonRows(_ rows: [TextBox]) throws -> Any { try JSONSerialization.jsonObject(with: JSONEncoder().encode(rows)) }

do {
    let args = CommandLine.arguments
    switch args.dropFirst().first {
    case "permissions":
        try emit(["accessibility": AXIsProcessTrusted(), "screenRecording": CGPreflightScreenCaptureAccess()])
    case "inspect":
        let pid = pid_t(args[2])!
        guard ownedProcess(pid), sameApp(pid) != nil else { throw Failure("Not owned AE 2026 path") }
        let dir = URL(fileURLWithPath: args[3])
        try emit(["event": "inspect", "pid": pid, "windows": windows(pid)])
        for window in windows(pid) where bounds(window).width >= 200 && bounds(window).height >= 100 {
            let id = window[kCGWindowNumber as String] as! CGWindowID
            let shot = try snapshot(id, pid: pid)
            try save(shot, dir.appendingPathComponent("inspect-\(id).png"))
            try emit(["window": window, "ocr": try jsonRows(recognize(shot))])
        }
    case "ocr":
        let url = URL(fileURLWithPath: args[2])
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil), let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { throw Failure("Cannot read image") }
        let rows = try recognize(image)
        try emit(["rows": try jsonRows(rows), "layout": try jsonRows(Policy.crashRecoveryLayout(rows).map { [$0] } ?? []), "knownDialog": Policy.knownDialog(rows), "candidates": try jsonRows(Policy.candidates(rows))])
    case "script-progress":
        let title = String(data: FileHandle.standardInput.readDataToEndOfFile(), encoding: .utf8) ?? ""
        try emit(["scriptProgress": Policy.scriptProgress(title)])
    case "workspace":
        let data = try JSONSerialization.jsonObject(with: FileHandle.standardInput.readDataToEndOfFile()) as! [String: Any]
        let rect = CGRect(x: 0, y: 0, width: data["width"] as! Double, height: data["height"] as! Double)
        try emit(["workspace": Policy.workspace(title: data["title"] as? String ?? "", rect: rect,
            role: data["role"] as? String, subrole: data["subrole"] as? String,
            modal: data["modal"] as? Bool ?? false)])
    case "policy":
        let rows = try JSONDecoder().decode([TextBox].self, from: FileHandle.standardInput.readDataToEndOfFile())
        guard rows.allSatisfy({ $0.box.count == 4 }) else { throw Failure("Invalid box") }
        try emit(["layout": try jsonRows(Policy.crashRecoveryLayout(rows).map { [$0] } ?? []), "knownDialog": Policy.knownDialog(rows), "candidates": try jsonRows(Policy.candidates(rows)),
                  "centres": Policy.candidates(rows).map { row -> [Double] in
                      let p = Policy.centre(row, window: CGRect(x: -100, y: 50, width: 800, height: 600)); return [p.x,p.y]
                  }])
    case "watch": try watch(URL(fileURLWithPath: args[2]))
    default: throw Failure("Usage: ae-dialog-watch permissions | ocr IMAGE | policy | watch DIRECTORY")
    }
} catch {
    try? emit(["event": "blocked", "reason": String(describing: error)])
    exit(2)
}
