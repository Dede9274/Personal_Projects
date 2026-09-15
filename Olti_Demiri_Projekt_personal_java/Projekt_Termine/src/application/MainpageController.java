package application;

import java.io.IOException;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.input.MouseEvent;
import javafx.scene.layout.BorderPane;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

public class MainpageController {

	@FXML
	private Label ContactusLabel;
	@FXML
	private Label XLabel;
	@FXML
	private Label MainpageLabel;
	@FXML
	private Label InfoLabel;
	@FXML
	private Label SettingsLabel;
	@FXML
	private Button gotoAppointmensbtn;
	@FXML
	private Button LogOutbtn;
	@FXML
	private Label myappointmentsLabel;
	
	
	@FXML
	public void XLabelClick(MouseEvent event) {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
	}
	
	@FXML
	public void gotoMyappointments(MouseEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("MyAppointments.fxml"));
		Stage LoginStage = new Stage();
		LoginStage.setScene(new Scene(root,700,400));
		LoginStage.show();
		

	}
	
	@FXML
	public void gotoAppointmentsC(ActionEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Appointment.fxml"));
		Stage AppointmentsStage = new Stage();
		AppointmentsStage.setScene(new Scene(root,700,400));
		AppointmentsStage.initStyle(StageStyle.UNDECORATED); 
		AppointmentsStage.show();
	}
	
	@FXML
	public void gotoLogIn(ActionEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Log_in.fxml"));
		Stage LoginStage = new Stage();
		LoginStage.setScene(new Scene(root,600,400));
		LoginStage.initStyle(StageStyle.UNDECORATED); 
		LoginStage.show();
	}
}
