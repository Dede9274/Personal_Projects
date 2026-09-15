package application;

import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Button;

import java.io.IOException;
import java.security.NoSuchAlgorithmException;
import java.security.spec.InvalidKeySpecException;
import java.sql.Connection;
import java.sql.Statement;

import javafx.event.ActionEvent;

import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.scene.input.MouseEvent;
import javafx.scene.paint.Color;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

public class Sign_upController {
	@FXML
	private Label XLabel;
	@FXML
	private Label signupMessageLabel;
	@FXML
	private Button gotoLogin;
	@FXML
	private Button CancelBtn;
	@FXML 
	private TextField firstnameinput;
	@FXML 
	private TextField lastnameinput;
	@FXML 
	private TextField usernameinput;
	@FXML 
	private PasswordField passwordinput;
	@FXML 
	private PasswordField confirmpasswordinput;
	@FXML
	private Button signupbutton;
	

	Connection conn = null;

	// Event Listener on Label[#XLabel].onMouseClicked
	@FXML
	public void XLabelClick(MouseEvent event) {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
	}
	
	@FXML
	public void gotoLoginC(ActionEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Log_in.fxml"));
		Stage LogInStage = new Stage();
		LogInStage.setScene(new Scene(root,600,400));
		LogInStage.initStyle(StageStyle.UNDECORATED); 
		LogInStage.show();
	}
	// Event Listener on Button[#CancelBtn].onMouseClicked
	@FXML
	public void CancelBtnClick(MouseEvent event) {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
	}
	
	@FXML
	public void SignUp(MouseEvent event) throws NoSuchAlgorithmException, InvalidKeySpecException {
		
		if(firstnameinput.getText().isBlank() == false && lastnameinput.getText().isBlank() == false
		   && usernameinput.getText().isBlank() == false && passwordinput.getText().isBlank() == false
		   && confirmpasswordinput.getText().isBlank() == false) {
			
			if(passwordinput.getText().equals(confirmpasswordinput.getText())) {
				
				 conn = DatabaseConnection.ConnectDB();
				
				String password_hashed = PasswordEncryptionDecryption.generateStrongPasswordHash(passwordinput.getText());
				
				String sql = "INSERT INTO users (firstname, lastname, username, password)"
						   + "VALUES ('"+firstnameinput.getText() +"','"+ lastnameinput.getText() + "','"
						   + usernameinput.getText() + "','" + password_hashed + "')";
				
				try {
					
					Statement statement = conn.createStatement();
					statement.executeUpdate(sql);
					
					signupMessageLabel.setTextFill(Color.web("#ff0000"));
					signupMessageLabel.setText("Inserted Succesfully!!!");
					
				}catch(Exception e) {
					System.out.println("Exception in Sign Up Controller "+ e);
				}
				
			}else {
				
				signupMessageLabel.setTextFill(Color.web("#ff0000"));
				signupMessageLabel.setText("Passwords dont match!!!");
				
			}
		}
	
	}
}