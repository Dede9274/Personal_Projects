package application;

import java.io.IOException;

import javafx.animation.FadeTransition;
import javafx.fxml.FXMLLoader;
import javafx.scene.Node;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.stage.Stage;
import javafx.util.Duration;

public final class SceneNavigator {

	private SceneNavigator() {
	}

	public static void navigate(Node source, String resource, double width, double height)
			throws IOException {
		Parent nextRoot = FXMLLoader.load(SceneNavigator.class.getResource(resource));
		Scene scene = source.getScene();
		if (scene == null) {
			throw new IllegalStateException("The navigation source is not attached to a scene");
		}

		Stage stage = (Stage) scene.getWindow();
		Node currentRoot = scene.getRoot();
		FadeTransition fadeOut = new FadeTransition(Duration.millis(120), currentRoot);
		fadeOut.setFromValue(currentRoot.getOpacity());
		fadeOut.setToValue(0.0);
		fadeOut.setOnFinished(event -> {
			nextRoot.setOpacity(0.0);
			scene.setRoot(nextRoot);
			stage.setTitle(titleFor(resource));
			stage.setMinWidth(width);
			stage.setMinHeight(height);
			stage.setWidth(width);
			stage.setHeight(height);
			stage.centerOnScreen();

			FadeTransition fadeIn = new FadeTransition(Duration.millis(180), nextRoot);
			fadeIn.setFromValue(0.0);
			fadeIn.setToValue(1.0);
			fadeIn.play();
		});
		fadeOut.play();
	}

	private static String titleFor(String resource) {
		if (resource.endsWith("Log_in.fxml")) return "PhysioCare — Sign in";
		if (resource.endsWith("Sign_up.fxml")) return "PhysioCare — Create account";
		if (resource.endsWith("Appointment.fxml")) return "PhysioCare — Book an appointment";
		if (resource.endsWith("MyAppointments.fxml")) return "PhysioCare — My appointments";
		return "PhysioCare — Patient portal";
	}
}
