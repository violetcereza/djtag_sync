// swift-tools-version: 5.9
// The swift-tools-version declares the minimum version of Swift required to build this package.

import PackageDescription

let package = Package(
    name: "YapDatabaseCLI",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        .package(url: "https://github.com/mickeyl/SwiftYapDatabase.git", from: "2.9.0")
    ],
    targets: [
        .executableTarget(
            name: "YapDatabaseCLI",
            dependencies: [
                .product(name: "SwiftYapDatabase", package: "swiftyapdatabase"),
                .product(name: "YapDatabase", package: "swiftyapdatabase")
            ],
            path: "Sources/YapDatabaseCLI"
        )
    ]
) 