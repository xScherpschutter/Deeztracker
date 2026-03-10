//! Cryptographic utilities for Deezer audio decryption.

use md5::{Digest, Md5};
use std::fs::File;
use std::io::Write;
use std::path::Path;

use crate::error::Result;

/// Deezer's secret key for Blowfish key derivation.
const SECRET_KEY: &[u8] = b"g4el58wc0zvf9na1";

/// Blowfish initialization vector.
const BLOWFISH_IV: [u8; 8] = [0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07];

/// Block size for audio encryption.
const BLOCK_SIZE: usize = 2048;

/// Blowfish cipher block size.
const BF_BLOCK_SIZE: usize = 8;

pub fn md5_hex(data: &str) -> String {
    let mut hasher = Md5::new();
    hasher.update(data.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}

pub fn calc_blowfish_key(song_id: &str) -> Vec<u8> {
    let hash = md5_hex(song_id);
    let hash_bytes = hash.as_bytes();
    let mut key = Vec::with_capacity(16);
    for i in 0..16 {
        let byte = hash_bytes[i] ^ hash_bytes[i + 16] ^ SECRET_KEY[i];
        key.push(byte);
    }
    key
}

fn decrypt_blowfish_cbc(data: &[u8], key: &[u8]) -> Vec<u8> {
    use blowfish::Blowfish;
    use cipher::generic_array::GenericArray;
    use cipher::BlockDecrypt;
    use cipher::KeyInit;

    let cipher: Blowfish<byteorder::BE> = Blowfish::new_from_slice(key).expect("Invalid key");
    let mut result = data.to_vec();
    let mut prev_block = BLOWFISH_IV.to_vec();

    for chunk in result.chunks_mut(BF_BLOCK_SIZE) {
        if chunk.len() < BF_BLOCK_SIZE { break; }
        let ciphertext = chunk.to_vec();
        let block = GenericArray::from_mut_slice(chunk);
        cipher.decrypt_block(block);
        for (byte, prev) in chunk.iter_mut().zip(prev_block.iter()) {
            *byte ^= prev;
        }
        prev_block = ciphertext;
    }
    result
}

pub fn decrypt_blowfish_chunk(data: &[u8], key: &[u8]) -> Vec<u8> {
    decrypt_blowfish_cbc(data, key)
}

pub fn decrypt_track(encrypted_data: &[u8], song_id: &str, output_path: &Path) -> Result<()> {
    let key = calc_blowfish_key(song_id);
    let mut output = File::create(output_path)?;
    let mut block_count = 0;

    for chunk in encrypted_data.chunks(BLOCK_SIZE) {
        let processed = if block_count % 3 == 0 && chunk.len() == BLOCK_SIZE {
            decrypt_blowfish_chunk(chunk, &key)
        } else {
            chunk.to_vec()
        };
        output.write_all(&processed)?;
        block_count += 1;
    }
    Ok(())
}
