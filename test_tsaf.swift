#!/usr/bin/env swift

import Foundation
import SQLite3

// Simple test script to dump TSAF blobs for analysis
let databasePath = "TEST djay Media Library.djayMediaLibrary/MediaLibrary.db"

// Import the TracksByBPM functionality
// Note: This is a simplified version for testing
func dumpTSAFBlob(forRowId rowid: Int64, databasePath: String) {
    print("Dumping TSAF blob for track rowid: \(rowid)")
    print("==========================================")
    
    var db: OpaquePointer?
    let result = sqlite3_open(databasePath, &db)
    
    guard result == SQLITE_OK, let database = db else {
        print("Error: Could not open database: \(result)")
        return
    }
    
    // First, get the key from mediaItemAnalyzedData collection
    let keyQuery = "SELECT key FROM database2 WHERE rowid = ? AND collection = 'mediaItemAnalyzedData'"
    var keyStatement: OpaquePointer?
    let keyResult = sqlite3_prepare_v2(database, keyQuery, -1, &keyStatement, nil)
    
    guard keyResult == SQLITE_OK else {
        print("Error preparing key query: \(keyResult)")
        sqlite3_close(database)
        return
    }
    
    sqlite3_bind_int64(keyStatement, 1, rowid)
    
    guard sqlite3_step(keyStatement) == SQLITE_ROW else {
        print("No mediaItemAnalyzedData found for rowid: \(rowid)")
        sqlite3_finalize(keyStatement)
        sqlite3_close(database)
        return
    }
    
    let key = String(cString: sqlite3_column_text(keyStatement, 0))
    print("Found key: \(key)")
    print("Key length: \(key.count)")
    print("Key hex: \(key.utf8.map { String(format: "%02x", $0) }.joined(separator: " "))")
    
    sqlite3_finalize(keyStatement)
    
    // Now get the corresponding mediaItems entry
    let mediaQuery = "SELECT rowid FROM database2 WHERE collection = 'mediaItems' AND key = ?"
    var mediaStatement: OpaquePointer?
    let mediaResult = sqlite3_prepare_v2(database, mediaQuery, -1, &mediaStatement, nil)
    
    guard mediaResult == SQLITE_OK else {
        print("Error preparing media query: \(mediaResult)")
        sqlite3_close(database)
        return
    }
    
    // Debug: print the key being bound
    print("Binding key to mediaItems query: \(key)")
    print("Binding key length: \(key.count)")
    print("Binding key hex: \(key.utf8.map { String(format: "%02x", $0) }.joined(separator: " "))")
    
    // Try binding as C string with explicit length
    key.withCString { cstr in
        sqlite3_bind_text(mediaStatement, 1, cstr, Int32(strlen(cstr)), nil)
    }
    
    // Direct query for comparison
    let directQuery = "SELECT rowid FROM database2 WHERE collection = 'mediaItems' AND key = '" + key + "'"
    var directStatement: OpaquePointer?
    let directResult = sqlite3_prepare_v2(database, directQuery, -1, &directStatement, nil)
    if directResult == SQLITE_OK, sqlite3_step(directStatement) == SQLITE_ROW {
        let foundRowid = sqlite3_column_int64(directStatement, 0)
        print("Direct query found rowid: \(foundRowid)")
    } else {
        print("Direct query did not find the key either!")
    }
    sqlite3_finalize(directStatement)
    
    guard sqlite3_step(mediaStatement) == SQLITE_ROW else {
        print("No mediaItems found for key: \(key)")
        sqlite3_finalize(mediaStatement)
        sqlite3_close(database)
        return
    }
    
    let mediaRowId = sqlite3_column_int64(mediaStatement, 0)
    print("Found mediaItems rowid: \(mediaRowId)")
    
    sqlite3_finalize(mediaStatement)
    
    // Get the BLOB data
    let blobQuery = "SELECT data FROM database2 WHERE rowid = ?"
    var blobStatement: OpaquePointer?
    let blobResult = sqlite3_prepare_v2(database, blobQuery, -1, &blobStatement, nil)
    
    guard blobResult == SQLITE_OK else {
        print("Error preparing blob query: \(blobResult)")
        sqlite3_close(database)
        return
    }
    
    sqlite3_bind_int64(blobStatement, 1, mediaRowId)
    
    guard sqlite3_step(blobStatement) == SQLITE_ROW else {
        print("No BLOB data found for mediaItems rowid: \(mediaRowId)")
        sqlite3_finalize(blobStatement)
        sqlite3_close(database)
        return
    }
    
    let blobData = sqlite3_column_blob(blobStatement, 0)
    let blobSize = sqlite3_column_bytes(blobStatement, 0)
    
    guard let data = blobData, blobSize > 0 else {
        print("Empty or null BLOB data")
        sqlite3_finalize(blobStatement)
        sqlite3_close(database)
        return
    }
    
    let dataPointer = data.bindMemory(to: UInt8.self, capacity: Int(blobSize))
    let dataArray = Array(UnsafeBufferPointer(start: dataPointer, count: Int(blobSize)))
    
    print("BLOB size: \(blobSize) bytes")
    print("First 64 bytes (hex): \(dataArray.prefix(64).map { String(format: "%02x", $0) }.joined(separator: " "))")
    
    // Save to file
    let outputPath = "/tmp/tsaf_blob_\(rowid).bin"
    let url = URL(fileURLWithPath: outputPath)
    do {
        try Data(dataArray).write(to: url)
        print("BLOB saved to: \(outputPath)")
    } catch {
        print("Error saving BLOB to file: \(error)")
    }
    
    // Try to interpret as string (might reveal text content)
    if let stringData = String(data: Data(dataArray), encoding: .utf8) {
        print("As UTF-8 string (first 200 chars): \(String(stringData.prefix(200)))")
    } else {
        print("Not valid UTF-8 string")
    }
    
    // Try to interpret as ASCII
    if let asciiData = String(data: Data(dataArray), encoding: .ascii) {
        print("As ASCII string (first 200 chars): \(String(asciiData.prefix(200)))")
    }
    
    sqlite3_finalize(blobStatement)
    sqlite3_close(database)
}

// Test with tracks that have matching keys
print("Testing TSAF blob extraction...")
dumpTSAFBlob(forRowId: 27305, databasePath: databasePath)  // This should have key 000617ad30343a70eeed9bb9481a7789
print("\n" + String(repeating: "=", count: 80) + "\n")
dumpTSAFBlob(forRowId: 55025, databasePath: databasePath)  // This should have key 0030880edcbdd5d74d9d279cd0819037
print("\n" + String(repeating: "=", count: 80) + "\n")
dumpTSAFBlob(forRowId: 55022, databasePath: databasePath)  // This should have key 0051a1ec8d6ac6fbc8c9cd36fc9205cc 