package application;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Hyperlink;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;

public class Log_inController {

	@FXML private Label loginMessageLabel;
	@FXML private TextField usernameinput;
	@FXML private PasswordField passwordinput;
	@FXML private Button loginbutton;
	@FXML private Hyperlink gotoSignUp;

	@FXML
	public void gotoSignUpC() throws IOException {
		SceneNavigator.navigate(gotoSignUp, "Sign_up.fxml", 900, 680);
	}

	@FXML
	public void SignIn() {
		String username = usernameinput.getText().trim();
		String password = passwordinput.getText();
		if (username.isBlank() || password.isBlank()) {
			showMessage("Enter both your username and password.", true);
			return;
		}

		loginbutton.setDisable(true);
		loginbutton.setText("Signing in…");
		String query = "SELECT id, username, password FROM users WHERE username = ?";
		try (Connection connection = DatabaseConnection.getConnection();
				PreparedStatement statement = connection.prepareStatement(query)) {
			statement.setString(1, username);
			try (ResultSet result = statement.executeQuery()) {
				if (!result.next() || !PasswordHasher.verify(password, result.getString("password"))) {
					showMessage("The username or password is incorrect.", true);
					return;
				}
				long userId = result.getLong("id");
				String storedHash = result.getString("password");
				if (PasswordHasher.needsUpgrade(storedHash)) {
					upgradePasswordHash(connection, userId, password);
				}
				SessionManager.signIn(userId, result.getString("username"));
				openDashboard();
			}
		} catch (SQLException | IllegalStateException exception) {
			System.err.println("Login failed: " + exception.getMessage());
			showMessage("We could not sign you in. Please try again.", true);
		} finally {
			loginbutton.setDisable(false);
			loginbutton.setText("Sign in");
		}
	}

	private void upgradePasswordHash(Connection connection, long userId, String password)
			throws SQLException {
		try (PreparedStatement statement =
				connection.prepareStatement("UPDATE users SET password = ? WHERE id = ?")) {
			statement.setString(1, PasswordHasher.hash(password));
			statement.setLong(2, userId);
			statement.executeUpdate();
		}
	}

	private void openDashboard() {
		try {
			SceneNavigator.navigate(loginbutton, "Mainpage.fxml", 1000, 680);
		} catch (IOException exception) {
			SessionManager.signOut();
			showMessage("The patient portal could not be opened.", true);
		}
	}

	private void showMessage(String message, boolean error) {
		loginMessageLabel.getStyleClass().removeAll("status-error", "status-success");
		loginMessageLabel.getStyleClass().add(error ? "status-error" : "status-success");
		loginMessageLabel.setText(message);
	}
}
