import CoreGraphics
import Foundation

func listWindows() {
    let options: CGWindowListOption = [.optionOnScreenOnly, .excludeDesktopElements]
    let raw = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] ?? []
    let windows: [[String: Any]] = raw.compactMap { item in
        guard let layer = item[kCGWindowLayer as String] as? Int, layer == 0,
              let number = item[kCGWindowNumber as String] as? Int,
              let ownerPID = item[kCGWindowOwnerPID as String] as? Int,
              let owner = item[kCGWindowOwnerName as String] as? String,
              let rect = item[kCGWindowBounds as String] as? [String: Any],
              let x = rect["X"] as? Double, let y = rect["Y"] as? Double,
              let width = rect["Width"] as? Double, let height = rect["Height"] as? Double else { return nil }
        return [
            "id": number,
            "pid": ownerPID,
            "owner": owner,
            "title": item[kCGWindowName as String] as? String ?? "",
            "x": x, "y": y, "width": width, "height": height
        ]
    }
    let data = try! JSONSerialization.data(withJSONObject: windows, options: [.sortedKeys])
    print(String(decoding: data, as: UTF8.self))
}

listWindows()
