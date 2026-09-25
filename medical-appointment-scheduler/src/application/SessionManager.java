package application;

/** Holds the authenticated identity for the lifetime of this desktop process. */
public final class SessionManager {

	private static Long userId;
	private static String username;

	private SessionManager() {
	}

	public static synchronized void signIn(long authenticatedUserId, String authenticatedUsername) {
		if (authenticatedUserId <= 0) {
			throw new IllegalArgumentException("User id must be positive");
		}
		userId = authenticatedUserId;
		username = authenticatedUsername;
	}

	public static synchronized long requireUserId() {
		if (userId == null) {
			throw new IllegalStateException("Authentication is required");
		}
		return userId;
	}

	public static synchronized boolean isAuthenticated() {
		return userId != null;
	}

	public static synchronized String getUsername() {
		return username;
	}

	public static synchronized void signOut() {
		userId = null;
		username = null;
	}
}
