package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Arrays;

import com.vasworks.android.util.CheckboxListAdapter;
import com.vasworks.android.util.CheckboxModel;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.AsyncTask;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.HeaderViewListAdapter;
import android.widget.ListView;
import android.widget.TextView;

public class InitializeCheckboxListTask extends AsyncTask<Void, Void, Object> {
	private static final String LOG_TAG = "InitializeLovTask";
	private final Context context;
	private final View progressDialog;
	private final String entityName;
	private final ListView spinnerView;
	private final String title;
	private final Button formButton;
	private final ArrayList<Object> selectedIds = new ArrayList<>();

	InitializeCheckboxListTask(Context context, String entityName, ListView spinnerView, Object selectedIds, View progressDialog, Button formButton, String title) {
		this.context = context;
		this.entityName = entityName;
		this.spinnerView = spinnerView;
		this.progressDialog = progressDialog;
		this.title = title;
		this.formButton = formButton;
		
		if(selectedIds != null) {
			String selection = (String) selectedIds;
			
			for(String token : selection.replace(" ", "").replace("[", "").replace("]", "").split(",")) {
				this.selectedIds.add(Integer.parseInt(token));
			}
		}
	}

	@Override
	protected void onPreExecute() {
		super.onPreExecute();
		progressDialog.setVisibility(View.VISIBLE);
	}
	
	@Override
	protected Object doInBackground(Void... params) {
		XMLRPCClient models;
		Object val = null;
		try {
			ArrayList<Object> methodParams = new ArrayList<>();
			methodParams.add(entityName);
		    
			models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
			val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
					"list_items", methodParams.toArray());
			
			Log.i(LOG_TAG, "Return val=" + val);

		} catch (MalformedURLException e) {
			e.printStackTrace();
			val = e.getMessage();
		} catch (XMLRPCException e) {
			e.printStackTrace();
			val = e.getMessage();
		} catch (Exception e) {
			e.printStackTrace();
			val = e.getMessage();
		}

		return val;
	}
	
	@Override
	protected void onPostExecute(final Object val) {
		progressDialog.setVisibility(View.GONE);
		Log.i(LOG_TAG, "" + val);
		if(val != null) {
			try {
				if(val instanceof Object[]) {
					Object[] data = (Object[]) val;
					Object[] item;
					for (Object d : data) {
						item = (Object[]) d;
						Log.i(LOG_TAG, "ID=" + item[0] + ", NAME=" + item[1]);
						Log.i(LOG_TAG, "--------------------------------");
					}
					ArrayList<CheckboxModel> models = new ArrayList<>();
					Object[] keyValue;
					for(Object pair : data) {
						keyValue = (Object[]) pair;
						models.add(new CheckboxModel((Integer) keyValue[0], (String) keyValue[1], selectedIds != null ? selectedIds.contains(keyValue[0]) : false));
					}
				    CheckboxListAdapter adapter = new CheckboxListAdapter(context, models.toArray(new CheckboxModel[models.size()]));
				    TextView headerView = new TextView(context);
				    headerView.setText(title);
				    spinnerView.addHeaderView(headerView);
				    spinnerView.setAdapter(adapter);
				    ((CheckboxListAdapter)((HeaderViewListAdapter) spinnerView.getAdapter()).getWrappedAdapter()).notifyDataSetChanged();
				} else if(val instanceof String) {
					formButton.setEnabled(false);
					this.displayAlert("An error occurred - possible no Internet access or connection to server.", "Error");
				}
			} catch(NumberFormatException e) {
				displayAlert(val.toString(), "Error");
			}
		} else {
			displayAlert("Server is down; try again later.", "Error");
		}
	}

	@Override
	protected void onCancelled() {
		progressDialog.setVisibility(View.GONE);
	}

	public void displayAlert(CharSequence charSequence, CharSequence charSequence2) {
		AlertDialog.Builder alertDialog = new AlertDialog.Builder(context).setTitle(charSequence2).setPositiveButton(android.R.string.ok,
				new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int arg1) {
						dialog.cancel();
					}
				});
		alertDialog.setMessage(charSequence).show();
	}
}