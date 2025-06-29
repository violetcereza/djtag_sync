#!/usr/bin/env swift

import Foundation
import YapDatabase
import SwiftYapDatabase

// MARK: - Command Line Arguments

struct CommandLineArguments {
    let databasePath: String
    let help: Bool
    let collectionName: String?
    
    init() {
        var args = CommandLine.arguments.dropFirst()
        var dbPath: String?
        var showHelp = false
        var collection: String?
        
        while let arg = args.first {
            switch arg {
            case "-h", "--help":
                showHelp = true
                args = args.dropFirst()
            case "-d", "--database":
                args = args.dropFirst()
                if let path = args.first {
                    dbPath = path
                    args = args.dropFirst()
                } else {
                    print("Error: Database path required after -d/--database")
                    exit(1)
                }
            case "-c", "--collection":
                args = args.dropFirst()
                if let name = args.first {
                    collection = name
                    args = args.dropFirst()
                } else {
                    print("Error: Collection name required after -c/--collection")
                    exit(1)
                }
            default:
                if dbPath == nil {
                    dbPath = arg
                    args = args.dropFirst()
                } else {
                    print("Error: Unexpected argument: \(arg)")
                    exit(1)
                }
            }
        }
        
        self.databasePath = dbPath ?? ""
        self.help = showHelp
        self.collectionName = collection
    }
}

// MARK: - Help and Usage

func printUsage() {
    print("""
    YapDatabase CLI - List collections in a YapDatabase
    
    Usage: swift run YapDatabaseCLI [options] <database-path>
    
    Arguments:
        <database-path>    Path to the YapDatabase file
    
    Options:
        -d, --database <path>     Specify database path (alternative to positional argument)
        -c, --collection <name>   Specify collection name to list details for
        -h, --help                Show this help message
    
    Examples:
        swift run YapDatabaseCLI /path/to/database.sqlite
        swift run YapDatabaseCLI -d /path/to/database.sqlite
        swift run YapDatabaseCLI -c "myCollection" /path/to/database.sqlite
        swift run YapDatabaseCLI --collection "myCollection" --database /path/to/database.sqlite
        swift run YapDatabaseCLI --help
    """)
}

// MARK: - Main Execution

func main() {
    let args = CommandLineArguments()
    
    if args.help {
        printUsage()
        return
    }
    
    if args.databasePath.isEmpty {
        print("Error: Database path is required")
        print("Use --help for usage information")
        exit(1)
    }
    
    guard let lister = YapDatabaseLister(path: args.databasePath) else {
        exit(1)
    }
    
    if let collectionName = args.collectionName {
        lister.listCollectionDetails(collectionName: collectionName)
    } else {
        lister.listCollections()
    }
}

// Run the main function
main() 
