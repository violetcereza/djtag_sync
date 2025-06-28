#!/usr/bin/env swift

import Foundation
import YapDatabase
import SwiftYapDatabase

// MARK: - Command Line Arguments

struct CommandLineArguments {
    let databasePath: String
    let help: Bool
    let collectionName: String?
    let listTracksByBPMWithMetadata: Bool
    
    init() {
        var args = CommandLine.arguments.dropFirst()
        var dbPath: String?
        var showHelp = false
        var collection: String?
        var tracksByBPMWithMetadata = false
        
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
            case "--tracks-by-bpm-with-metadata":
                tracksByBPMWithMetadata = true
                args = args.dropFirst()
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
        self.listTracksByBPMWithMetadata = tracksByBPMWithMetadata
    }
}

// MARK: - Database Operations

class YapDatabaseLister {
    private let database: YapDatabase
    
    init?(path: String) {
        guard let db = YapDatabase(url: URL(fileURLWithPath: path)) else {
            print("Error: Could not open database at path: \(path)")
            return nil
        }
        self.database = db
    }
    
    func listCollections() {
        let connection = database.newConnection()
        
        connection.read { transaction in
            print("Collections in database:")
            print("========================")
            
            let collections = transaction.allCollections()
            
            if collections.isEmpty {
                print("No collections found in the database.")
            } else {
                for (index, collection) in collections.enumerated() {
                    let count = transaction.numberOfKeys(inCollection: collection)
                    print("\(index + 1). \(collection) (\(count) items)")
                }
            }
            
            print("\nTotal collections: \(collections.count)")
        }
    }
    
    func listCollectionDetails(collectionName: String) {
        let connection = database.newConnection()
        
        connection.read { transaction in
            print("Details for collection: \(collectionName)")
            print("================================")
            
            let keys = transaction.allKeys(inCollection: collectionName)
            
            if keys.isEmpty {
                print("No items found in collection '\(collectionName)'")
            } else {
                print("Keys in collection '\(collectionName)' (showing first 20):")
                let keysToShow = Array(keys.prefix(20))
                
                for (index, key) in keysToShow.enumerated() {
                    if let object = transaction.object(forKey: key, inCollection: collectionName) {
                        print("  \(index + 1). Key: \(key)")
                        print("     Value: \(object)")
                    } else {
                        print("  \(index + 1). Key: \(key)")
                        print("     Value: <nil>")
                    }
                    print()
                }
                
                if keys.count > 20 {
                    print("... and \(keys.count - 20) more items")
                }
                print("\nTotal items: \(keys.count)")
            }
        }
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
        --tracks-by-bpm-with-metadata
        -h, --help                Show this help message
    
    Examples:
        swift run YapDatabaseCLI /path/to/database.sqlite
        swift run YapDatabaseCLI -d /path/to/database.sqlite
        swift run YapDatabaseCLI -c "myCollection" /path/to/database.sqlite
        swift run YapDatabaseCLI --collection "myCollection" --database /path/to/database.sqlite
        swift run YapDatabaseCLI --tracks-by-bpm-with-metadata /path/to/database.sqlite
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
    } else if args.listTracksByBPMWithMetadata {
        let tracksByBPM = TracksByBPM(databasePath: args.databasePath)
        tracksByBPM.listTracksByBPMWithMetadata()
    } else {
        lister.listCollections()
    }
}

// Run the main function
main() 