package application;

import java.sql.Date;

public class Appointment {


	private int phoneNr;
	private String IdNr;
	private String description;
	private Date date;
	private String time;
	
	public Appointment( int phoneNr,String IdNr, String description, Date date, String time) {
		super();
		this.setphoneNr(phoneNr);
		this.setIdNr(IdNr);
		this.setDescription(description);
		this.setDate(date);
		this.setTime(time);
	}

	

	public int getphoneNr() {
		return phoneNr;
	}

	public void setphoneNr(int phoneNr) {
		this.phoneNr = phoneNr;
	}

	public String getIdNr() {
		return IdNr;
	}

	public void setIdNr(String IdNr) {
		this.IdNr = IdNr;
	}

	public String getDescription() {
		return description;
	}

	public void setDescription(String description) {
		this.description = description;
	}

	public Date getDate() {
		return date;
	}

	public void setDate(Date date) {
		this.date = date;
		
	}
	
	public String getTime() {
		return time;
	}
	
	public void setTime(String time) {
		this.time = time;
	}

}
