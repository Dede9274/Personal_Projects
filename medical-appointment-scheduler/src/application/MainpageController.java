package application;

import java.io.IOException;

import javafx.fxml.FXML;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.Label;

public class MainpageController {

	@FXML private Label welcomeLabel;
	@FXML private Button bookAppointmentButton;
	@FXML private Button myAppointmentsButton;
	@FXML private Button logoutButton;

	@FXML
	public void initialize() {
		SessionManager.requireUserId();
		welcomeLabel.setText("Signed in as " + SessionManager.getUsername());
	}

	@FXML
	public void gotoMyappointments() throws IOException {
		SceneNavigator.navigate(myAppointmentsButton, "MyAppointments.fxml", 1000, 680);
	}

	@FXML
	public void gotoAppointmentsC() throws IOException {
		SceneNavigator.navigate(bookAppointmentButton, "Appointment.fxml", 1000, 720);
	}

	@FXML
	public void gotoLogIn() throws IOException {
		SessionManager.signOut();
		SceneNavigator.navigate(logoutButton, "Log_in.fxml", 900, 620);
	}

	@FXML
	public void showContact() {
		showInformation("Contact reception", "Need help with an appointment?",
				"Call reception at +49 30 555 0142\nMonday–Friday, 08:00–17:00\n\n"
						+ "For urgent medical concerns, contact your local emergency service.");
	}

	@FXML
	public void showPrivacy() {
		showInformation("Your privacy", "Your appointment information stays private",
				"Appointments are stored locally on this device and are shown only for "
						+ "the account that created them. Sign out when using a shared computer.");
	}

	private void showInformation(String title, String header, String content) {
		Alert alert = new Alert(Alert.AlertType.INFORMATION);
		alert.setTitle(title);
		alert.setHeaderText(header);
		alert.setContentText(content);
		alert.showAndWait();
	}
}
