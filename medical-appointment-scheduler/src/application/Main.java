package application;

import javafx.application.Application;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;

public class Main extends Application {

	@Override
	public void start(Stage primaryStage) {
		try {
			Parent root = FXMLLoader.load(getClass().getResource("Log_in.fxml"));
			Scene scene = new Scene(root, 900, 620);
			primaryStage.setTitle("PhysioCare — Sign in");
			primaryStage.setMinWidth(900);
			primaryStage.setMinHeight(620);
			primaryStage.setScene(scene);
			primaryStage.show();
		} catch (Exception exception) {
			exception.printStackTrace();
		}
	}

	public static void main(String[] args) {
		launch(args);
	}
}
