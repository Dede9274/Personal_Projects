package application;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;

import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Hyperlink;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;

public class Sign_upController {

	private static final int SQLITE_CONSTRAINT = 19;

	@FXML private Label signupMessageLabel;
	@FXML private Hyperlink gotoLogin;
	@FXML private TextField firstnameinput;
	@FXML private TextField lastnameinput;
	@FXML private TextField usernameinput;
	@FXML private PasswordField passwordinput;
	@FXML private PasswordField confirmpasswordinput;
	@FXML private Button signupbutton;

	@FXML
	public void gotoLoginC() throws IOException {
		SceneNavigator.navigate(gotoLogin, "Log_in.fxml", 900, 620);
	}

	@FXML
	public void SignUp() {
		String firstName = firstnameinput.getText().trim();
		String lastName = lastnameinput.getText().trim();
		String username = usernameinput.getText().trim();
		String password = passwordinput.getText();
		if (firstName.isBlank() || lastName.isBlank() || username.isBlank()
				|| password.isBlank() || confirmpasswordinput.getText().isBlank()) {
			showMessage("Complete every field to create your account.", true);
			return;
		}
		if (!password.equals(confirmpasswordinput.getText())) {
			showMessage("The passwords do not match.", true);
			return;
		}
		if (password.length() < 15) {
			showMessage("Use a password with at least 15 characters.", true);
			return;
		}

		signupbutton.setDisable(true);
		signupbutton.setText("Creating account…");
		String insert = "INSERT INTO users (firstname, lastname, username, password) VALUES (?, ?, ?, ?)";
		try (Connection connection = DatabaseConnection.getConnection();
				PreparedStatement statement = connection.prepareStatement(insert)) {
			statement.setString(1, firstName);
			statement.setString(2, lastName);
			statement.setString(3, username);
			statement.setString(4, PasswordHasher.hash(password));
			statement.executeUpdate();
			showMessage("Account created. You can now return to sign in.", false);
			passwordinput.clear();
			confirmpasswordinput.clear();
		} catch (SQLException exception) {
			if (exception.getErrorCode() == SQLITE_CONSTRAINT) {
				showMessage("That username is already in use.", true);
			} else {
				System.err.println("Sign up failed: " + exception.getMessage());
				showMessage("We could not create your account. Please try again.", true);
			}
		} catch (IllegalStateException exception) {
			System.err.println("Sign up failed: " + exception.getMessage());
			showMessage("We could not create your account. Please try again.", true);
		} finally {
			signupbutton.setDisable(false);
			signupbutton.setText("Create account");
		}
	}

	private void showMessage(String message, boolean error) {
		signupMessageLabel.getStyleClass().removeAll("status-error", "status-success");
		signupMessageLabel.getStyleClass().add(error ? "status-error" : "status-success");
		signupMessageLabel.setText(message);
	}
}
