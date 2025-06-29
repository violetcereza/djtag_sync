import Foundation
import YapDatabase
import SwiftYapDatabase

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
    
    // Enhanced function to show more details about the serialized data
    private func analyzeSerializedData(_ data: Data, forCollection collection: String) -> String {
        var analysis = "Data size: \(data.count) bytes\n"
        
        // First, let's analyze the binary structure
        let binaryAnalysis = analyzeBinaryStructure(data)
        analysis += "Binary analysis: \(binaryAnalysis)\n"
        
        // Try custom TSAF decoder first (appears to be djay's format)
        if let tsafDecoded = decodeTSAF(data) {
            analysis += "Format: TSAF (djay custom format)\n"
            analysis += "Decoded content: \(tsafDecoded)"
            return analysis
        }
        
        // If not TSAF, show hex representation
        let previewBytes = Array(data.prefix(32))
        let hexPreview = previewBytes.map { String(format: "%02x", $0) }.joined(separator: " ")
        analysis += "Format: Binary (unknown)\n"
        analysis += "First 32 bytes: \(hexPreview)"
        
        if data.count > 32 {
            analysis += " ... (truncated)"
        }
        
        return analysis
    }
    
    // Custom decoder for TSAF format (appears to be djay's custom format)
    private func decodeTSAF(_ data: Data) -> String? {
        guard data.count >= 8 else { return nil }
        
        let bytes = Array(data)
        
        // Check for TSAF signature: 54 53 41 46 (ASCII: "TSAF")
        guard bytes[0] == 0x54 && bytes[1] == 0x53 && bytes[2] == 0x41 && bytes[3] == 0x46 else {
            return nil
        }
        
        // Version info: bytes[4] and bytes[5] seem to be version numbers
        let version1 = bytes[4]
        let version2 = bytes[5]
        
        var result = "TSAF Format - Version: \(version1).\(version2)\n"
        
        // Skip the header (first 8 bytes) and parse the content
        let contentData = data.dropFirst(8)
        let parsedData = parseTSAFContentSimple(contentData)
        
        // Display the parsed data in a structured way
        result += "Parsed Properties:\n"
        for (key, value) in parsedData {
            result += "  \(key): \(value)\n"
        }
        
        return result
    }
    
    // Simple TSAF parser based on TracksByBPM.swift approach
    private func parseTSAFContentSimple(_ data: Data) -> [String: String] {
        var properties: [String: String] = [:]
        
        // Convert the BLOB to an ASCII string for easier parsing (like TracksByBPM.swift)
        let asciiString = data.map { $0 >= 32 && $0 < 127 ? Character(UnicodeScalar($0)) : "\0" }.reduce("") { $0 + String($1) }
        
        func valueBefore(field: String) -> String? {
            guard let range = asciiString.range(of: field) else { return nil }
            let before = asciiString[..<range.lowerBound]
            let parts = before.split(separator: "\0").map { String($0) }.filter { !$0.isEmpty }
            return parts.last
        }
        
        // Known field names from djay format
        let knownFields = [
            "title", "artist", "album", "genre", "composer", "year", "trackNumber", 
            "albumTrackNumber", "discNumber", "grouping", "comments", "contentType", 
            "file", "originSourceID", "duration", "sampleRate", "bitRate", "titleID", 
            "artistUUIDs", "albumUUID", "genreUUIDs", "labelUUID", "addedDate", 
            "modifiedDate", "musicalKeySignatureIndex", "uuid"
        ]
        
        // Extract values for each known field
        for field in knownFields {
            if let value = valueBefore(field: field) {
                properties[field] = value
            }
        }
        
        return properties
    }
    
    // Analyze the binary structure of the data
    private func analyzeBinaryStructure(_ data: Data) -> String {
        guard data.count >= 8 else {
            return "Too small to analyze"
        }
        
        var analysis = ""
        
        // Check for common file signatures
        let firstBytes = Array(data.prefix(8))
        let hexSignature = firstBytes.map { String(format: "%02x", $0) }.joined(separator: " ")
        
        analysis += "Signature: \(hexSignature)\n"
        
        // Check for common patterns
        if firstBytes.starts(with: [0x62, 0x70, 0x6c, 0x69, 0x73, 0x74]) {
            analysis += "Detected: Binary Property List\n"
        } else if firstBytes.starts(with: [0x7b, 0x22]) || firstBytes.starts(with: [0x5b]) {
            analysis += "Detected: JSON-like structure\n"
        } else if firstBytes.starts(with: [0x00, 0x00, 0x00, 0x00]) {
            analysis += "Detected: Possible UTF-16 with BOM\n"
        } else if firstBytes.starts(with: [0xff, 0xfe]) {
            analysis += "Detected: UTF-16 Little Endian BOM\n"
        } else if firstBytes.starts(with: [0xfe, 0xff]) {
            analysis += "Detected: UTF-16 Big Endian BOM\n"
        }
        
        // Check for null bytes pattern (common in binary data)
        let nullCount = data.filter { $0 == 0 }.count
        let nullPercentage = Double(nullCount) / Double(data.count) * 100
        analysis += "Null bytes: \(nullCount)/\(data.count) (\(String(format: "%.1f", nullPercentage))%)\n"
        
        // Check for printable ASCII characters
        let printableCount = data.filter { $0 >= 32 && $0 <= 126 }.count
        let printablePercentage = Double(printableCount) / Double(data.count) * 100
        analysis += "Printable ASCII: \(printableCount)/\(data.count) (\(String(format: "%.1f", printablePercentage))%)\n"
        
        return analysis
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
                    if let serializedData = transaction.serializedObject(forKey: key, inCollection: collectionName) {
                        print("  \(index + 1). Key: \(key)")
                        
                        // Use enhanced analysis for better debugging
                        let analysis = analyzeSerializedData(serializedData, forCollection: collectionName)
                        print("     \(analysis.replacingOccurrences(of: "\n", with: "\n     "))")
                        
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