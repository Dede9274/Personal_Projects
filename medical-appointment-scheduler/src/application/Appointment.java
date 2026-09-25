package application;

import java.time.LocalDate;

public class Appointment {

	private String phoneNr;
	private String IdNr;
	private String description;
	private LocalDate date;
	private String time;

	public Appointment(String phoneNr, String IdNr, String description, LocalDate date, String time) {
		this.phoneNr = phoneNr;
		this.IdNr = IdNr;
		this.description = description;
		this.date = date;
		this.time = time;
	}

	public String getPhoneNr() {
		return phoneNr;
	}

	public void setPhoneNr(String phoneNr) {
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

	public LocalDate getDate() {
		return date;
	}

	public void setDate(LocalDate date) {
		this.date = date;
	}

	public String getTime() {
		return time;
	}

	public void setTime(String time) {
		this.time = time;
	}
}
