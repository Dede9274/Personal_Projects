package application;


import java.io.IOException;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.Statement;

import javafx.event.ActionEvent;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.Button;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.scene.input.MouseEvent;
import javafx.scene.paint.Color;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

public class Log_inController {
	
	@FXML
	private Label XLabel;
	
	@FXML
	private Label loginMessageLabel;
	
	@FXML 
	private TextField usernameinput;
	
	@FXML 
	private PasswordField passwordinput;
	@FXML
	private Button gotoSignUp;
	@FXML
	private Button CancelBtn;
	
	
	Connection conn = null;
	
	@FXML
	public void CancelBtnClick(MouseEvent event) {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
	}
	
	@FXML
	public void XLabelClick(MouseEvent event) {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
	}	
	
	@FXML
	public void gotoSignUpC(ActionEvent event) throws IOException {
		Stage stage = (Stage) XLabel.getScene().getWindow();
		stage.close();
		Parent root = FXMLLoader.load(getClass().getResource("Sign_up.fxml"));
		Stage LoginStage = new Stage();
		LoginStage.setScene(new Scene(root,600,400));
		LoginStage.initStyle(StageStyle.UNDECORATED); 
		LoginStage.show();
	}
	
	@FXML 
	public void SignIn() {
		
		if(usernameinput.getText().isBlank() == false && passwordinput.getText().isBlank() == false) {
			
			conn = DatabaseConnection.ConnectDB();
			
			String sql = "SELECT * FROM users WHERE username = '" + usernameinput.getText()+ "'";
			
			try {
				
				Statement statement = conn.createStatement();
				ResultSet queryResult = statement.executeQuery(sql);
					
					if(queryResult.next()) {
						
						String storedPassword = queryResult.getString("password");
						
						if(PasswordEncryptionDecryption.validatePassword(passwordinput.getText(), storedPassword)) {
							
							Stage stage = (Stage) XLabel.getScene().getWindow();
							stage.close();
							Parent root = FXMLLoader.load(getClass().getResource("Mainpage.fxml"));
							Stage dashboardStage = new Stage();
							dashboardStage.setScene(new Scene(root,700,400));
							dashboardStage.show();

						}else {
							
							loginMessageLabel.setTextFill(Color.web("#ff0000"));
							loginMessageLabel.setText("Invalid username or password!!!");
							
						}
						
						
					}else {
						
						loginMessageLabel.setTextFill(Color.web("#ff0000"));
						loginMessageLabel.setText("Invalid Sign in!!!");
						
					}
					
				
				
					
			}catch(Exception ex) {
				System.out.println("Exception in Login Controller "+ex);
			}
			
			
		}else {
			
			loginMessageLabel.setTextFill(Color.web("#ff0000"));
			loginMessageLabel.setText("Please type your username and password!!!");
			
		}
		
	}

}
