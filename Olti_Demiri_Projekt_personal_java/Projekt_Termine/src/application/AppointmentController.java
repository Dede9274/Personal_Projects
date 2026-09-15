package application;

import java.io.IOException;
import java.util.*;



import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Alert;
import javafx.scene.control.Button;
import javafx.scene.control.ChoiceBox;
import javafx.scene.control.DatePicker;
import javafx.scene.control.Label;
import javafx.scene.control.Labeled;
import javafx.scene.control.TextField;
import javafx.scene.input.MouseEvent;
import javafx.scene.media.AudioClip;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.Time;
import java.sql.Timestamp;
import java.time.LocalDate;

public class AppointmentController {
	
	@FXML
	private Label XLabel;
	@FXML
	private Label ContactusLabel;
	@FXML
	private Label mainpageLabel;
	@FXML
	private Label AboutLabel;
	@FXML
	private Label SettingsLabel;
	@FXML
	private Button LogOutBtn;
	@FXML
	private Label MyappointmentsLabel;
	@FXML
    private TextField firstnameTextField;
    @FXML
    private TextField lastnameTextField;
    @FXML
    private TextField phonenrTextField;
    @FXML
    private TextField idTextField;
    @FXML
    private TextField descriptionTextField;
    @FXML
    private ChoiceBox<String> timeChooser;
    @FXML
    private DatePicker dateChooser;
    @FXML
    private Button placeAppointmentBtn;
    @FXML

    private ArrayList<Appointment> existingAppointments;
	Connection conn;

    
	
	@FXML
	public void initialize() {
		timeChooser.getItems().addAll("8:00", "9:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00");
	
	        
		
	}
	
	@FXML
	public void gotoMyappointmentsC(MouseEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("MyAppointments.fxml"));
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
	
	@FXML
	public void gotoMainPage(MouseEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Mainpage.fxml"));
		Stage LoginStage = new Stage();
		LoginStage.setScene(new Scene(root,700,400));
		LoginStage.initStyle(StageStyle.UNDECORATED); 
		LoginStage.show();
	}
	
	public void placeAppointmentC(ActionEvent event) {
		conn = DatabaseConnection.ConnectDB();                               
		String query = "INSERT INTO appointment (firstname, lastname, phoneNr, IdNr, description, date, time) VALUES (?,?,?,?,?,?,?)";
		
		
	    
			
		try {
			
			PreparedStatement preparedStmt = conn.prepareStatement(query);
			
			int phoneNr = Integer.parseInt(phonenrTextField.getText());
			String firstname = firstnameTextField.getText();
			String lastname = lastnameTextField.getText();
			String IdNr = idTextField.getText();
			String description = descriptionTextField.getText();
			LocalDate date = dateChooser.getValue();
			String time = timeChooser.getValue();
			
			preparedStmt.setString(1, firstname);
			preparedStmt.setString(2, lastname);
			preparedStmt.setInt(3, phoneNr);
			preparedStmt.setString(4, IdNr);
			preparedStmt.setString(5, description);
			preparedStmt.setDate(6, java.sql.Date.valueOf(date) );
			preparedStmt.setString(7, time);
			
			preparedStmt.execute();
			 Alert alertPart = new Alert(Alert.AlertType.INFORMATION);
			
	            alertPart.setTitle("Appointment");
	            alertPart.setContentText("Your appointment has been requested!"
	            		+ " Please check the details on the \"Appointmens\" page. "
	            		+ "You will recieve a SMS within 24h to tell you if your appointment has been aproved.");
	            
	            
	            alertPart.showAndWait();
			
		}catch(Exception exc) {
		  exc.printStackTrace();
		}
	}
	
}


