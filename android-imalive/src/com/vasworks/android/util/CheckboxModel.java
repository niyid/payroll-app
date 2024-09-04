package com.vasworks.android.util;


public class CheckboxModel {
	
	private Integer id;

	private String label;
	
	private boolean selected;

	public CheckboxModel(Integer id, String label, boolean selected) {
		this.id = id;
		this.label = label;
		this.selected = selected;
	}

	public Integer getId() {
		return id;
	}

	public void setId(Integer id) {
		this.id = id;
	}

	public String getLabel() {
		return label;
	}

	public boolean isSelected() {
		return selected;
	}

	public void setSelected(boolean selected) {
		this.selected = selected;
	}
}
