package com.vasworks.android.util;

import com.vasworks.imalive.android.R;

import android.app.Activity;
import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.CheckBox;
import android.widget.CompoundButton;
import android.widget.TextView;

public class CheckboxListAdapter extends ArrayAdapter<CheckboxModel> {
	CheckboxModel[] modelItems = null;
	Context context;

	public CheckboxListAdapter(Context context, CheckboxModel[] modelItems) {
		super(context, R.layout.checkbox_row, modelItems);
		this.context = context;
		this.modelItems = modelItems;
	}

	static class ViewHolder {
		protected TextView text;
		protected CheckBox checkbox;
	}

	@Override
	public View getView(int position, View convertView, ViewGroup parent) {

		ViewHolder viewHolder = null;
		if (convertView == null) {
			LayoutInflater inflator = ((Activity) context).getLayoutInflater();
			convertView = inflator.inflate(R.layout.checkbox_row, parent, false);
			viewHolder = new ViewHolder();
			viewHolder.text = (TextView) convertView.findViewById(R.id.textView1);
			viewHolder.checkbox = (CheckBox) convertView.findViewById(R.id.checkBox1);
			viewHolder.checkbox.setOnCheckedChangeListener(new CompoundButton.OnCheckedChangeListener() {

				@Override
				public void onCheckedChanged(CompoundButton buttonView, boolean isChecked) {
					int buttonViewPosition = (Integer) buttonView.getTag();
					modelItems[buttonViewPosition].setSelected(buttonView.isChecked());
				}
			});
			convertView.setTag(viewHolder);
			convertView.setTag(R.id.textView1, viewHolder.text);
			convertView.setTag(R.id.checkBox1, viewHolder.checkbox);
		} else {
			viewHolder = (ViewHolder) convertView.getTag();
		}
		viewHolder.checkbox.setTag(position);

		viewHolder.text.setText(modelItems[position].getLabel());
		viewHolder.checkbox.setChecked(modelItems[position].isSelected());

		return convertView;
	}

}