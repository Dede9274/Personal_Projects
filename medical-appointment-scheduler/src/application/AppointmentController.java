package application;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;

import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.ChoiceBox;
import javafx.scene.control.DateCell;
import javafx.scene.control.DatePicker;
import javafx.scene.control.Label;
import javafx.scene.control.TextArea;
import javafx.scene.control.TextField;

public class AppointmentController {

	@FXML private Button dashboardButton;
	@FXML private Button appointmentsButton;
	@FXML private Button logoutButton;
	@FXML private TextField firstnameTextField;
	@FXML private TextField lastnameTextField;
	@FXML private TextField phonenrTextField;
	@FXML private TextField idTextField;
	@FXML private TextArea descriptionTextArea;
	@FXML private ChoiceBox<String> timeChooser;
	@FXML private DatePicker dateChooser;
	@FXML private Button placeAppointmentBtn;
	@FXML private Label appointmentMessageLabel;

	@FXML
	public void initialize() {
		SessionManager.requireUserId();
		timeChooser.getItems().addAll(
				"08:00", "09:00", "10:00", "11:00", "12:00",
				"13:00", "14:00", "15:00", "16:00", "17:00");
		timeChooser.getSelectionModel().selectFirst();
		dateChooser.setValue(LocalDate.now().plusDays(1));
		dateChooser.setDayCellFactory(picker -> new DateCell() {
			@Override
			public void updateItem(LocalDate date, boolean empty) {
				super.updateItem(date, empty);
				setDisable(empty || date.isBefore(LocalDate.now()));
			}
		});
		loadPatientName();
	}

	@FXML
	public void gotoMyappointmentsC() throws IOException {
		SceneNavigator.navigate(appointmentsButton, "MyAppointments.fxml", 1000, 680);
	}

	@FXML
	public void gotoLogIn() throws IOException {
		SessionManager.signOut();
		SceneNavigator.navigate(logoutButton, "Log_in.fxml", 900, 620);
	}

	@FXML
	public void gotoMainPage() throws IOException {
		SceneNavigator.navigate(dashboardButton, "Mainpage.fxml", 1000, 680);
	}

	@FXML
	public void placeAppointmentC() {
		String firstName = firstnameTextField.getText().trim();
		String lastName = lastnameTextField.getText().trim();
		String phoneNumber = phonenrTextField.getText().trim();
		String identityNumber = idTextField.getText().trim();
		String description = descriptionTextArea.getText().trim();
		LocalDate date = dateChooser.getValue();
		String time = timeChooser.getValue();

		if (firstName.isBlank() || lastName.isBlank() || phoneNumber.isBlank()
				|| identityNumber.isBlank() || description.isBlank() || date == null || time == null) {
			showStatus("Complete every field before requesting the appointment.", true);
			return;
		}
		if (date.isBefore(LocalDate.now())) {
			showStatus("Choose today or a future date.", true);
			return;
		}

		placeAppointmentBtn.setDisable(true);
		placeAppointmentBtn.setText("Sending request…");
		String insert = "INSERT INTO appointment "
				+ "(user_id, firstname, lastname, phoneNr, IdNr, description, date, time) "
				+ "VALUES (?, ?, ?, ?, ?, ?, ?, ?)";
		try (Connection connection = DatabaseConnection.getConnection();
				PreparedStatement statement = connection.prepareStatement(insert)) {
			statement.setLong(1, SessionManager.requireUserId());
			statement.setString(2, firstName);
			statement.setString(3, lastName);
			statement.setString(4, phoneNumber);
			statement.setString(5, identityNumber);
			statement.setString(6, description);
			statement.setString(7, date.toString());
			statement.setString(8, time);
			statement.executeUpdate();

			showStatus("Appointment requested successfully. Review it in My appointments.", false);
			phonenrTextField.clear();
			idTextField.clear();
			descriptionTextArea.clear();
			dateChooser.setValue(LocalDate.now().plusDays(1));
			timeChooser.getSelectionModel().selectFirst();
		} catch (SQLException | IllegalStateException exception) {
			System.err.println("Appointment creation failed: " + exception.getMessage());
			showStatus("We could not save the appointment. Please try again.", true);
		} finally {
			placeAppointmentBtn.setDisable(false);
			placeAppointmentBtn.setText("Request appointment");
		}
	}

	private void loadPatientName() {
		String query = "SELECT firstname, lastname FROM users WHERE id = ?";
		try (Connection connection = DatabaseConnection.getConnection();
				PreparedStatement statement = connection.prepareStatement(query)) {
			statement.setLong(1, SessionManager.requireUserId());
			try (ResultSet result = statement.executeQuery()) {
				if (result.next()) {
					firstnameTextField.setText(result.getString("firstname"));
					lastnameTextField.setText(result.getString("lastname"));
				}
			}
		} catch (SQLException exception) {
			System.err.println("Could not load patient details: " + exception.getMessage());
		}
	}

	private void showStatus(String message, boolean error) {
		appointmentMessageLabel.getStyleClass().removeAll("status-error", "status-success");
		appointmentMessageLabel.getStyleClass().add(error ? "status-error" : "status-success");
		appointmentMessageLabel.setText(message);
	}
}
