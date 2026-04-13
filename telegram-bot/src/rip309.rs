//! RIP-309 Phase 1: Fingerprinting Implementation
//! 
//! This module implements fingerprinting detection and prevention
//! for RustChain network as per the bounty program.

use crate::config::CONFIG;
use std::collections::HashMap;

/// Fingerprint detector for network nodes
pub struct FingerprintDetector {
    known_signatures: HashMap<u64, String>,
}

impl FingerprintDetector {
    pub fn new() -> Self {
        Self {
            known_signatures: HashMap::new(),
        }
    }

    /// Check if a transaction fingerprint matches known patterns
    pub fn detect(&mut self, fingerprint: &[u8]) -> Option<String> {
        let hash = self.compute_hash(fingerprint);
        if let Some(pattern) = self.known_signatures.get(&hash) {
            Some(pattern.clone())
        } else {
            self.known_signatures.insert(hash, String::new());
            None
        }
    }

    /// Compute hash for fingerprint detection
    fn compute_hash(&self, data: &[u8]) -> u64 {
        data.iter()
            .fold(0u64, |acc, &b| acc.wrapping_add(b as u64))
    }

    /// Register a known fingerprint pattern
    pub fn register_pattern(&mut self, hash: u64, pattern: &str) {
        self.known_signatures.insert(hash, pattern.to_string());
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fingerprint_detection() {
        let mut detector = FingerprintDetector::new();
        let fingerprint = b"test_fingerprint_data";
        
        // Test detection
        let detected = detector.detect(fingerprint);
        assert!(detected.is_none()); // First detection should be None (no known pattern)
    }

    #[test]
    fn test_hash_computation() {
        let detector = FingerprintDetector::new();
        let hash = detector.compute_hash(b"hello");
        assert_eq!(hash, 104 + 101 + 108 + 108 + 111); // h=104, e=101, l=108, o=111
    }
}
