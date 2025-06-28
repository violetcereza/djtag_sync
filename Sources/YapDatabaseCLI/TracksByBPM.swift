import Foundation
import SQLite3

public class TracksByBPM {
    let databasePath: String
    
    public init(databasePath: String) {
        self.databasePath = databasePath
    }
    
    public func listTracksByBPMWithMetadata(limit: Int = 50) {
        print("Tracks sorted by BPM (with metadata):")
        print("=====================================")
        
        var db: OpaquePointer?
        let result = sqlite3_open(databasePath, &db)
        
        guard result == SQLITE_OK, let database = db else {
            print("Error: Could not open database: \(result)")
            return
        }
        
        let query = """
            SELECT rowid, bpm, manualBPM, keySignatureIndex 
            FROM secondaryIndex_mediaItemAnalyzedDataIndex 
            WHERE bpm IS NOT NULL 
            ORDER BY bpm 
            LIMIT \(limit)
            """
        
        var statement: OpaquePointer?
        let prepareResult = sqlite3_prepare_v2(database, query, -1, &statement, nil)
        
        if prepareResult == SQLITE_OK {
            var trackCount = 0
            
            while sqlite3_step(statement) == SQLITE_ROW {
                trackCount += 1
                let rowid = sqlite3_column_int64(statement, 0)
                let bpm = sqlite3_column_double(statement, 1)
                let manualBPM = sqlite3_column_double(statement, 2)
                let keySignatureIndex = sqlite3_column_int(statement, 3)
                
                // Get metadata for this track
                let (title, artist, _, _) = getTrackMetadata(forRowId: rowid, database: database)
                
                print("\(trackCount). Track rowid: \(rowid)")
                print("   BPM: \(String(format: "%.1f", bpm))")
                if manualBPM > 0 {
                    print("   Manual BPM: \(String(format: "%.1f", manualBPM))")
                }
                if let title = title {
                    print("   Title: \(title)")
                }
                if let artist = artist {
                    print("   Artist: \(artist)")
                }
                print("   Key Signature Index: \(keySignatureIndex)")
                print()
            }
            
            if trackCount == 0 {
                print("No tracks with BPM data found.")
            } else if trackCount == limit {
                print("... showing first \(limit) tracks. Use a higher limit to see more.")
            }
            
            // Get total count
            sqlite3_finalize(statement)
            let countQuery = "SELECT COUNT(*) as total FROM secondaryIndex_mediaItemAnalyzedDataIndex WHERE bpm IS NOT NULL"
            var countStatement: OpaquePointer?
            let countResult = sqlite3_prepare_v2(database, countQuery, -1, &countStatement, nil)
            
            if countResult == SQLITE_OK && sqlite3_step(countStatement) == SQLITE_ROW {
                let total = sqlite3_column_int64(countStatement, 0)
                print("Total tracks with BPM data: \(total)")
            }
            
            sqlite3_finalize(countStatement)
        } else {
            print("Error querying BPM data: \(prepareResult)")
        }
        
        sqlite3_close(database)
    }
    
    public func parseTSAFBlob(_ data: [UInt8]) -> (title: String?, artist: String?, duration: Float?, bpm: Float?) {
        // Convert the BLOB to an ASCII string for easier parsing
        let asciiString = data.map { $0 >= 32 && $0 < 127 ? Character(UnicodeScalar($0)) : "\0" }.reduce("") { $0 + String($1) }
        
        func valueBefore(field: String) -> String? {
            guard let range = asciiString.range(of: field) else { return nil }
            let before = asciiString[..<range.lowerBound]
            let parts = before.split(separator: "\0").map { String($0) }.filter { !$0.isEmpty }
            return parts.last
        }
        
        let title = valueBefore(field: "title")
        let artist = valueBefore(field: "artist")
        let duration: Float? = nil
        let bpm: Float? = nil
        return (title, artist, duration, bpm)
    }
    
    private func getTrackMetadata(forRowId rowid: Int64, database: OpaquePointer) -> (title: String?, artist: String?, duration: Float?, bpm: Float?) {
        // Get the key from mediaItemAnalyzedData collection
        let keyQuery = "SELECT key FROM database2 WHERE rowid = ? AND collection = 'mediaItemAnalyzedData'"
        var keyStatement: OpaquePointer?
        let keyResult = sqlite3_prepare_v2(database, keyQuery, -1, &keyStatement, nil)
        
        guard keyResult == SQLITE_OK else {
            sqlite3_finalize(keyStatement)
            return (nil, nil, nil, nil)
        }
        
        sqlite3_bind_int64(keyStatement, 1, rowid)
        
        guard sqlite3_step(keyStatement) == SQLITE_ROW else {
            sqlite3_finalize(keyStatement)
            return (nil, nil, nil, nil)
        }
        
        let key = String(cString: sqlite3_column_text(keyStatement, 0))
        sqlite3_finalize(keyStatement)
        
        // Get the corresponding mediaItems entry
        let mediaQuery = "SELECT rowid FROM database2 WHERE collection = 'mediaItems' AND key = ?"
        var mediaStatement: OpaquePointer?
        let mediaResult = sqlite3_prepare_v2(database, mediaQuery, -1, &mediaStatement, nil)
        
        guard mediaResult == SQLITE_OK else {
            sqlite3_finalize(mediaStatement)
            return (nil, nil, nil, nil)
        }
        
        key.withCString { cstr in
            sqlite3_bind_text(mediaStatement, 1, cstr, Int32(strlen(cstr)), nil)
        }
        
        guard sqlite3_step(mediaStatement) == SQLITE_ROW else {
            sqlite3_finalize(mediaStatement)
            return (nil, nil, nil, nil)
        }
        
        let mediaRowId = sqlite3_column_int64(mediaStatement, 0)
        sqlite3_finalize(mediaStatement)
        
        // Get the BLOB data
        let blobQuery = "SELECT data FROM database2 WHERE rowid = ?"
        var blobStatement: OpaquePointer?
        let blobResult = sqlite3_prepare_v2(database, blobQuery, -1, &blobStatement, nil)
        
        guard blobResult == SQLITE_OK else {
            sqlite3_finalize(blobStatement)
            return (nil, nil, nil, nil)
        }
        
        sqlite3_bind_int64(blobStatement, 1, mediaRowId)
        
        guard sqlite3_step(blobStatement) == SQLITE_ROW else {
            sqlite3_finalize(blobStatement)
            return (nil, nil, nil, nil)
        }
        
        let blobData = sqlite3_column_blob(blobStatement, 0)
        let blobSize = sqlite3_column_bytes(blobStatement, 0)
        
        guard let data = blobData, blobSize > 0 else {
            sqlite3_finalize(blobStatement)
            return (nil, nil, nil, nil)
        }
        
        let dataPointer = data.bindMemory(to: UInt8.self, capacity: Int(blobSize))
        let dataArray = Array(UnsafeBufferPointer(start: dataPointer, count: Int(blobSize)))
        
        sqlite3_finalize(blobStatement)
        
        return parseTSAFBlob(dataArray)
    }
} 