package application;

import java.io.IOException;
import java.net.URL;
import java.sql.Connection;
import java.sql.Date;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.ResourceBundle;
import java.sql.PreparedStatement;
import javafx.collections.FXCollections;
import javafx.collections.ObservableList;
import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.fxml.Initializable;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Label;
import javafx.scene.control.TableColumn;
import javafx.scene.control.TableView;
import javafx.scene.control.cell.PropertyValueFactory;
import javafx.scene.input.MouseEvent;
import javafx.stage.Stage;
import javafx.stage.StageStyle;


public class MyAppointmentsController implements Initializable  {
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
	private Label myappointmentsLabel;
	@FXML
	private TableView<Appointment> AppointmentsTable;
	@FXML
	private TableColumn<Appointment, Integer> phoneNrColumn;
	@FXML
	private TableColumn<Appointment, String> IdnrColumn;
	@FXML
	private TableColumn<Appointment, String> descriptionColumn;
	@FXML
	private TableColumn<Appointment, String> timeColumn;
	@FXML
	private TableColumn<Appointment, Date> dateColumn;
	
	
	Connection conn;
	
	@Override 
	public void initialize(URL arg0, ResourceBundle arg1 ) {
		showAppointments();
	}
	
	@FXML
	public void gotoMainpage(MouseEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Mainpage.fxml"));
		Stage MainStage = new Stage();
		MainStage.setScene(new Scene(root,700,400));
		MainStage.show();
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
	public ObservableList<Appointment> getAppointments() {
		ObservableList<Appointment> appointmentList = FXCollections.observableArrayList();
		conn = DatabaseConnection.ConnectDB();
		String query = "SELECT * FROM appointment";
		Statement statement;
		ResultSet queryResult;
		
		try {
			
			statement = conn.createStatement();
			queryResult = statement.executeQuery(query);
			Appointment appointment;
			while(queryResult.next()) {
				appointment = new Appointment(
						                      queryResult.getInt("phoneNr"),
						                      queryResult.getString("IdNr"),
						                      queryResult.getString("description"),
						                      queryResult.getDate("date"),
						                      queryResult.getString("time"));
				
				appointmentList.add(appointment);
				System.out.println(appointment.getphoneNr());
			}
			
	
		}catch(Exception ex) {
			ex.printStackTrace();
		}
		return appointmentList;
		
	}
	
	@FXML           
	public void showAppointments() {
		ObservableList<Appointment> appointments = getAppointments();
		
		phoneNrColumn.setCellValueFactory(new PropertyValueFactory<Appointment, Integer>("phoneNr"));
		IdnrColumn.setCellValueFactory(new PropertyValueFactory<Appointment, String>("IdNr"));
		descriptionColumn.setCellValueFactory(new PropertyValueFactory<Appointment, String>("description"));
		dateColumn.setCellValueFactory(new PropertyValueFactory<Appointment, Date>("date"));
		timeColumn.setCellValueFactory(new PropertyValueFactory<Appointment, String>("time"));
		
		AppointmentsTable.setItems(appointments);
	}
}
