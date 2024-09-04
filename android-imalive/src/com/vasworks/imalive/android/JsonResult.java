package com.vasworks.imalive.android;

import java.io.Serializable;

public class JsonResult implements Serializable {

	/**
	 * 
	 */
	private static final long serialVersionUID = -1792006488075935813L;

	private String JSON;
	
	private String msg;
	
	private String usr;
	
	private String sid;

	public String getJSON() {
		return JSON;
	}

	public void setJSON(String jSON) {
		JSON = jSON;
	}

	public String getMsg() {
		return msg;
	}

	public void setMsg(String msg) {
		this.msg = msg;
	}

	public String getUsr() {
		return usr;
	}

	public void setUsr(String usr) {
		this.usr = usr;
	}

	public String getSid() {
		return sid;
	}

	public void setSid(String sessionId) {
		this.sid = sessionId;
	}

	@Override
	public String toString() {
		StringBuilder builder = new StringBuilder();
		builder.append("JsonResult [JSON=");
		builder.append(JSON);
		builder.append(", msg=");
		builder.append(msg);
		builder.append(", usr=");
		builder.append(usr);
		builder.append(", sid=");
		builder.append(sid);
		builder.append("]");
		return builder.toString();
	}
}
