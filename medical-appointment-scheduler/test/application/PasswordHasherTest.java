package application;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.security.MessageDigest;
import java.util.HexFormat;

import javax.crypto.SecretKeyFactory;
import javax.crypto.spec.PBEKeySpec;

import org.junit.jupiter.api.Test;

class PasswordHasherTest {

    @Test
    void hashesAndVerifiesPasswords() {
        String hash = PasswordHasher.hash("a sufficiently long password");

        assertTrue(PasswordHasher.verify("a sufficiently long password", hash));
        assertFalse(PasswordHasher.verify("wrong password", hash));
        assertFalse(PasswordHasher.needsUpgrade(hash));
    }

    @Test
    void acceptsLegacyHashAndMarksItForUpgrade() throws Exception {
        String legacyHash = legacyHash("legacy password", "0123456789abcdef".getBytes(), 1_000);

        assertTrue(PasswordHasher.verify("legacy password", legacyHash));
        assertFalse(PasswordHasher.verify("wrong password", legacyHash));
        assertTrue(PasswordHasher.needsUpgrade(legacyHash));
    }

    @Test
    void rejectsMalformedHashes() {
        assertFalse(PasswordHasher.verify("password", "not-a-password-hash"));
        assertFalse(PasswordHasher.verify("password", null));
    }

    private String legacyHash(String password, byte[] salt, int iterations) throws Exception {
        PBEKeySpec specification = new PBEKeySpec(password.toCharArray(), salt, iterations, 512);
        byte[] hash = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA1")
                .generateSecret(specification)
                .getEncoded();
        return iterations + ":" + HexFormat.of().formatHex(salt) + ":"
                + HexFormat.of().formatHex(hash);
    }
}
