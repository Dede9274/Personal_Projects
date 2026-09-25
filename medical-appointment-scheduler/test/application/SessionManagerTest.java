package application;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

class SessionManagerTest {

    @AfterEach
    void clearSession() {
        SessionManager.signOut();
    }

    @Test
    void exposesTheAuthenticatedIdentity() {
        SessionManager.signIn(42L, "alex");

        assertTrue(SessionManager.isAuthenticated());
        assertEquals(42L, SessionManager.requireUserId());
        assertEquals("alex", SessionManager.getUsername());
    }

    @Test
    void rejectsAccessWithoutAuthentication() {
        SessionManager.signOut();

        assertFalse(SessionManager.isAuthenticated());
        assertThrows(IllegalStateException.class, SessionManager::requireUserId);
    }
}
