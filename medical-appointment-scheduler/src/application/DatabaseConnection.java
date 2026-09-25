package application;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;

public final class DatabaseConnection {

	private static final String DEFAULT_URL = "jdbc:sqlite:medical_appointment_scheduler.db";

	private DatabaseConnection() {
	}

	public static Connection getConnection() throws SQLException {
		Connection connection = DriverManager.getConnection(databaseUrl());
		try {
			configure(connection);
			initializeSchema(connection);
			return connection;
		} catch (SQLException exception) {
			connection.close();
			throw exception;
		}
	}

	private static String databaseUrl() {
		String url = System.getProperty("medical.app.db.url");
		if (url == null || url.isBlank()) {
			url = System.getenv("MEDICAL_APP_DB_URL");
		}
		if (url == null || url.isBlank()) {
			url = DEFAULT_URL;
		}
		if (!url.startsWith("jdbc:sqlite:")) {
			throw new IllegalStateException("MEDICAL_APP_DB_URL must be a SQLite JDBC URL");
		}
		return url;
	}

	private static void configure(Connection connection) throws SQLException {
		try (Statement statement = connection.createStatement()) {
			statement.execute("PRAGMA foreign_keys = ON");
			statement.execute("PRAGMA busy_timeout = 5000");
		}
	}

	private static void initializeSchema(Connection connection) throws SQLException {
		try (Statement statement = connection.createStatement()) {
			statement.execute("CREATE TABLE IF NOT EXISTS users ("
					+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
					+ "firstname TEXT NOT NULL, "
					+ "lastname TEXT NOT NULL, "
					+ "username TEXT NOT NULL UNIQUE, "
					+ "password TEXT NOT NULL"
					+ ")");
			statement.execute("CREATE TABLE IF NOT EXISTS appointment ("
					+ "id INTEGER PRIMARY KEY AUTOINCREMENT, "
					+ "user_id INTEGER NOT NULL, "
					+ "firstname TEXT NOT NULL, "
					+ "lastname TEXT NOT NULL, "
					+ "phoneNr TEXT NOT NULL, "
					+ "IdNr TEXT NOT NULL, "
					+ "description TEXT NOT NULL, "
					+ "date DATE NOT NULL, "
					+ "time TEXT NOT NULL, "
					+ "FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE"
					+ ")");
			statement.execute("CREATE INDEX IF NOT EXISTS idx_appointment_user_date "
					+ "ON appointment (user_id, date, time)");
		}
	}
}
