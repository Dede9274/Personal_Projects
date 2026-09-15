package application;

import java.sql.Connection;
import java.sql.DriverManager;

public class DatabaseConnection {
	public static Connection ConnectDB() {
		
		try {
			Connection conn;
			conn = DriverManager.getConnection("jdbc:mysql://localhost:3306/javapr", "root", "");
			return conn;
		
		} catch (Exception ex) {
			System.out.println("Error:" + ex.getMessage());
			return null;
		}
	}
	
		
}
