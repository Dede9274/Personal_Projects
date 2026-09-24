import * as Crypto from 'expo-crypto';
import {pbkdf2Async} from '@noble/hashes/pbkdf2.js';
import {sha256} from '@noble/hashes/sha2.js';
import {bytesToHex, hexToBytes, utf8ToBytes} from '@noble/hashes/utils.js';

const PBKDF2_ITERATIONS = 120000;
const KEY_LENGTH = 32;

export const createPasswordSalt = async () => {
  const bytes = await Crypto.getRandomBytesAsync(16);
  return bytesToHex(bytes);
};

export const derivePasswordHash = async (password, salt) => {
  const hash = await pbkdf2Async(
    sha256,
    utf8ToBytes(password),
    hexToBytes(salt),
    {
      c: PBKDF2_ITERATIONS,
      dkLen: KEY_LENGTH,
      asyncTick: 10,
    }
  );

  return bytesToHex(hash);
};

export const hashesMatch = (first, second) => {
  if (first.length !== second.length) {
    return false;
  }

  let difference = 0;

  for (let index = 0; index < first.length; index += 1) {
    difference |= first.charCodeAt(index) ^ second.charCodeAt(index);
  }

  return difference === 0;
};
