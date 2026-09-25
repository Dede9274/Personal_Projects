package application;

import java.security.MessageDigest;
import java.security.SecureRandom;
import java.security.spec.InvalidKeySpecException;
import java.util.Arrays;
import java.util.Base64;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

/** Hashes passwords and verifies both current and legacy password records. */
public final class PasswordHasher {

	private static final String FORMAT = "pbkdf2-sha256";
	private static final String ALGORITHM = "PBKDF2WithHmacSHA256";
	private static final int ITERATIONS = 600_000;
	private static final int SALT_BYTES = 16;
	private static final int HASH_BITS = 256;
	private static final SecureRandom SECURE_RANDOM = new SecureRandom();

	private PasswordHasher() {
	}

	public static String hash(String password) {
		if (password == null || password.isEmpty()) {
			throw new IllegalArgumentException("Password must not be empty");
		}

		byte[] salt = new byte[SALT_BYTES];
		SECURE_RANDOM.nextBytes(salt);
		byte[] hash = derive(password, salt, ITERATIONS, HASH_BITS, ALGORITHM);

		return FORMAT + "$" + ITERATIONS + "$"
				+ Base64.getEncoder().encodeToString(salt) + "$"
				+ Base64.getEncoder().encodeToString(hash);
	}

	public static boolean verify(String password, String storedHash) {
		if (password == null || storedHash == null) {
			return false;
		}

		try {
			if (storedHash.startsWith(FORMAT + "$")) {
				return verifyCurrent(password, storedHash);
			}
			return verifyLegacy(password, storedHash);
		} catch (IllegalArgumentException | InvalidKeySpecException
				| java.security.NoSuchAlgorithmException exception) {
			return false;
		}
	}

	public static boolean needsUpgrade(String storedHash) {
		if (storedHash == null || !storedHash.startsWith(FORMAT + "$")) {
			return true;
		}

		String[] parts = storedHash.split("\\$", -1);
		if (parts.length != 4) {
			return true;
		}

		try {
			return Integer.parseInt(parts[1]) < ITERATIONS;
		} catch (NumberFormatException exception) {
			return true;
		}
	}

	private static boolean verifyCurrent(String password, String storedHash)
			throws java.security.NoSuchAlgorithmException, InvalidKeySpecException {
		String[] parts = storedHash.split("\\$", -1);
		if (parts.length != 4 || !FORMAT.equals(parts[0])) {
			return false;
		}

		int iterations = Integer.parseInt(parts[1]);
		if (iterations <= 0) {
			return false;
		}

		byte[] salt = Base64.getDecoder().decode(parts[2]);
		byte[] expectedHash = Base64.getDecoder().decode(parts[3]);
		byte[] actualHash = deriveChecked(password, salt, iterations,
				expectedHash.length * Byte.SIZE, ALGORITHM);
		return MessageDigest.isEqual(expectedHash, actualHash);
	}

	/** Supports the original iterations:salt:hash PBKDF2-HMAC-SHA1 records. */
	private static boolean verifyLegacy(String password, String storedHash)
			throws java.security.NoSuchAlgorithmException, InvalidKeySpecException {
		String[] parts = storedHash.split(":", -1);
		if (parts.length != 3) {
			return false;
		}

		int iterations = Integer.parseInt(parts[0]);
		byte[] salt = decodeHex(parts[1]);
		byte[] expectedHash = decodeHex(parts[2]);
		byte[] actualHash = deriveChecked(password, salt, iterations,
				expectedHash.length * Byte.SIZE, "PBKDF2WithHmacSHA1");
		return MessageDigest.isEqual(expectedHash, actualHash);
	}

	private static byte[] derive(String password, byte[] salt, int iterations,
			int hashBits, String algorithm) {
		try {
			return deriveChecked(password, salt, iterations, hashBits, algorithm);
		} catch (java.security.NoSuchAlgorithmException | InvalidKeySpecException exception) {
			throw new IllegalStateException("Password hashing is unavailable", exception);
		}
	}

	private static byte[] deriveChecked(String password, byte[] salt, int iterations,
			int hashBits, String algorithm)
			throws java.security.NoSuchAlgorithmException, InvalidKeySpecException {
		char[] passwordCharacters = password.toCharArray();
		PBEKeySpec specification = new PBEKeySpec(passwordCharacters, salt, iterations, hashBits);
		try {
			return SecretKeyFactory.getInstance(algorithm).generateSecret(specification).getEncoded();
		} finally {
			specification.clearPassword();
			Arrays.fill(passwordCharacters, '\0');
		}
	}

	private static byte[] decodeHex(String hex) {
		if (hex.length() % 2 != 0) {
			throw new IllegalArgumentException("Invalid legacy password hash");
		}

		byte[] bytes = new byte[hex.length() / 2];
		for (int index = 0; index < bytes.length; index++) {
			int high = Character.digit(hex.charAt(index * 2), 16);
			int low = Character.digit(hex.charAt(index * 2 + 1), 16);
			if (high < 0 || low < 0) {
				throw new IllegalArgumentException("Invalid legacy password hash");
			}
			bytes[index] = (byte) ((high << 4) + low);
		}
		return bytes;
	}
}
