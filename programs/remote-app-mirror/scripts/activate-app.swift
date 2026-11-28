import AppKit
import Foundation

guard CommandLine.arguments.count == 2, let pid = Int32(CommandLine.arguments[1]),
      let app = NSRunningApplication(processIdentifier: pid) else {
    fputs("Could not find the selected app process.\n", stderr)
    exit(1)
}

guard app.activate(options: []) else {
    fputs("Could not activate the selected app.\n", stderr)
    exit(1)
}
