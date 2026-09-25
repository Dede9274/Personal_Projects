package application;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.time.LocalDate;

import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.fxml.FXML;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.cell.PropertyValueFactory;

public class MyAppointmentsController {

	@FXML private Button dashboardButton;
	@FXML private Button newAppointmentButton;
	@FXML private Button logoutButton;
	@FXML private Label appointmentCountLabel;
	@FXML private Label tableMessageLabel;
	@FXML private TableView<Appointment> AppointmentsTable;
	@FXML private TableColumn<Appointment, String> phoneNrColumn;
	@FXML private TableColumn<Appointment, String> IdnrColumn;
	@FXML private TableColumn<Appointment, String> descriptionColumn;
	@FXML private TableColumn<Appointment, String> timeColumn;
	@FXML private TableColumn<Appointment, LocalDate> dateColumn;

	@FXML
	public void initialize() {
		SessionManager.requireUserId();
		AppointmentsTable.setColumnResizePolicy(TableView.CONSTRAINED_RESIZE_POLICY);
		phoneNrColumn.setCellValueFactory(new PropertyValueFactory<>("phoneNr"));
		IdnrColumn.setCellValueFactory(new PropertyValueFactory<>("idNr"));
		descriptionColumn.setCellValueFactory(new PropertyValueFactory<>("description"));
		dateColumn.setCellValueFactory(new PropertyValueFactory<>("date"));
		timeColumn.setCellValueFactory(new PropertyValueFactory<>("time"));
		showAppointments();
	}

	@FXML
	public void gotoMainpage() throws IOException {
		SceneNavigator.navigate(dashboardButton, "Mainpage.fxml", 1000, 680);
	}

	@FXML
	public void gotoNewAppointment() throws IOException {
		SceneNavigator.navigate(newAppointmentButton, "Appointment.fxml", 1000, 720);
	}

	@FXML
	public void gotoLogIn() throws IOException {
		SessionManager.signOut();
		SceneNavigator.navigate(logoutButton, "Log_in.fxml", 900, 620);
	}

	public ObservableList<Appointment> getAppointments() {
		ObservableList<Appointment> appointmentList = FXCollections.observableArrayList();
		String query = "SELECT phoneNr, IdNr, description, date, time "
				+ "FROM appointment WHERE user_id = ? ORDER BY date, time";
		try (Connection connection = DatabaseConnection.getConnection();
				PreparedStatement statement = connection.prepareStatement(query)) {
			statement.setLong(1, SessionManager.requireUserId());
			try (ResultSet result = statement.executeQuery()) {
				while (result.next()) {
					appointmentList.add(new Appointment(
							result.getString("phoneNr"),
							result.getString("IdNr"),
							result.getString("description"),
							LocalDate.parse(result.getString("date")),
							result.getString("time")));
				}
			}
			tableMessageLabel.setText("");
		} catch (SQLException | IllegalStateException exception) {
			System.err.println("Could not load appointments: " + exception.getMessage());
			tableMessageLabel.getStyleClass().removeAll("status-success");
			tableMessageLabel.getStyleClass().add("status-error");
			tableMessageLabel.setText("Appointments could not be loaded. Try refreshing the list.");
		}
		return appointmentList;
	}

	@FXML
	public void showAppointments() {
		ObservableList<Appointment> appointments = getAppointments();
		AppointmentsTable.setItems(appointments);
		int count = appointments.size();
		appointmentCountLabel.setText(count == 1 ? "1 appointment" : count + " appointments");
	}
}
