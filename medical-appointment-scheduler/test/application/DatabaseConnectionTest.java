package application;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Path;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

class DatabaseConnectionTest {

    @TempDir
    Path temporaryDirectory;

    @AfterEach
    void clearDatabaseOverride() {
        System.clearProperty("medical.app.db.url");
    }

    @Test
    void createsSchemaAndEnablesForeignKeys() throws Exception {
        useTemporaryDatabase();

        try (Connection connection = DatabaseConnection.getConnection();
                Statement statement = connection.createStatement()) {
            try (ResultSet result = statement.executeQuery("PRAGMA foreign_keys")) {
                assertTrue(result.next());
                assertEquals(1, result.getInt(1));
            }

            assertTrue(tableExists(connection, "users"));
            assertTrue(tableExists(connection, "appointment"));
        }
    }

    @Test
    void persistsAnAppointmentForItsUser() throws Exception {
        useTemporaryDatabase();

        try (Connection connection = DatabaseConnection.getConnection()) {
            long userId;
            try (PreparedStatement user = connection.prepareStatement(
                    "INSERT INTO users (firstname, lastname, username, password) "
                            + "VALUES (?, ?, ?, ?)")) {
                user.setString(1, "Test");
                user.setString(2, "Patient");
                user.setString(3, "test-patient");
                user.setString(4, "test-hash");
                assertEquals(1, user.executeUpdate());
            }
            try (Statement statement = connection.createStatement();
                    ResultSet result = statement.executeQuery("SELECT last_insert_rowid()")) {
                assertTrue(result.next());
                userId = result.getLong(1);
            }

            try (PreparedStatement appointment = connection.prepareStatement(
                    "INSERT INTO appointment "
                            + "(user_id, firstname, lastname, phoneNr, IdNr, description, date, time) "
                            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?)")) {
                appointment.setLong(1, userId);
                appointment.setString(2, "Test");
                appointment.setString(3, "Patient");
                appointment.setString(4, "0123456789");
                appointment.setString(5, "ID-1");
                appointment.setString(6, "Routine visit");
                appointment.setString(7, "2030-01-02");
                appointment.setString(8, "09:00");
                assertEquals(1, appointment.executeUpdate());
            }

            try (PreparedStatement query = connection.prepareStatement(
                    "SELECT date FROM appointment WHERE user_id = ?")) {
                query.setLong(1, userId);
                try (ResultSet result = query.executeQuery()) {
                    assertTrue(result.next());
                    assertEquals("2030-01-02", result.getString("date"));
                }
            }
        }
    }

    private void useTemporaryDatabase() {
        Path database = temporaryDirectory.resolve("appointments.db");
        System.setProperty("medical.app.db.url", "jdbc:sqlite:" + database);
    }

    private boolean tableExists(Connection connection, String name) throws Exception {
        try (PreparedStatement statement = connection.prepareStatement(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?")) {
            statement.setString(1, name);
            try (ResultSet result = statement.executeQuery()) {
                return result.next();
            }
        }
    }
}
