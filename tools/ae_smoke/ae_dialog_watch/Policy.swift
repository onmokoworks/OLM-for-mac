import Foundation
import CoreGraphics

struct TextBox: Codable {
    let text: String
    let box: [Double] // normalized top-left x,y,width,height
    let confidence: Float
    var rect: CGRect { CGRect(x: box[0], y: box[1], width: box[2], height: box[3]) }
}

struct Policy {
    static let allowed = ["OK", "続行", "Continue", "閉じる", "Close", "後で", "Later",
                          "スキップ", "Skip", "今はしない", "Not Now"]
    static let forbidden = ["削除", "Delete", "保存しない", "Don't Save", "Don’t Save",
                            "置き換え", "Replace", "リセット", "Reset", "アンインストール",
                            "Uninstall", "購入", "Purchase", "Buy", "サインアウト", "Sign Out",
                            "セーフモード", "Safe Mode", "プラグインを管理", "Manage Plugins"]
    static func normalized(_ text: String) -> String {
        text.precomposedStringWithCompatibilityMapping.trimmingCharacters(in: .whitespacesAndNewlines)
    }
    static func dangerous(_ text: String) -> Bool {
        forbidden.contains { normalized(text).localizedCaseInsensitiveContains($0) }
    }
    static func knownDialog(_ rows: [TextBox]) -> Bool {
        let text = rows.map(\.text).joined(separator: " ").lowercased()
        // Context allowlist, not just a generic OK in an arbitrary window.
        return ["クラッシュ修復オプション", "crash repair options", "crash recovery",
                "プラグインが見つかりません", "missing plug-in", "duplicate plug-in",
                "重複するプラグイン", "preview controls", "プレビューコントロール",
                "what’s new", "what's new", "新機能", "アップデート", "update available",
                "after effects へようこそ", "welcome to after effects"].contains { text.contains($0) }
    }
    static func candidates(_ rows: [TextBox]) -> [TextBox] {
        rows.filter { candidate in
            allowed.contains(normalized(candidate.text)) && candidate.confidence >= 0.8 &&
            candidate.box.count == 4 && candidate.box.allSatisfy(\.isFinite) &&
            candidate.rect.width > 0 && candidate.rect.height > 0 &&
            CGRect(x: 0, y: 0, width: 1, height: 1).contains(candidate.rect) &&
            !rows.contains { dangerous($0.text) && $0.rect.intersects(candidate.rect) }
        }
    }
    static func centre(_ row: TextBox, window: CGRect) -> CGPoint {
        CGPoint(x: window.minX + row.rect.midX * window.width,
                y: window.minY + row.rect.midY * window.height)
    }
}
