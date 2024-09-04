package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;

import com.vasworks.android.util.LinkedHashMapAdapter;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.app.AlertDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.os.AsyncTask;
import android.util.Log;
import android.view.View;
import android.widget.BaseAdapter;
import android.widget.Button;
import android.widget.Spinner;

public class InitializeFlexLovTask extends AsyncTask<Void, Void, Object> {
	private static final String LOG_TAG = "InitializeLovTask";
	private final Context context;
	private final View progressDialog;
	private final HashMap<String, Object> paramsMap;
	private final Spinner spinnerView;
	private final String methodName;
	private final Button formButton;

	InitializeFlexLovTask(Context context, String methodName, HashMap<String, Object> paramsMap, Spinner spinnerView, View progressDialog, Button formButton) {
		this.context = context;
		this.spinnerView = spinnerView;
		this.methodName = methodName;
		this.paramsMap = paramsMap;
		this.progressDialog = progressDialog;
		this.formButton = formButton;
	}

	@Override
	protected void onPreExecute() {
		super.onPreExecute();
		progressDialog.setVisibility(View.VISIBLE);
	}
	
	@Override
	protected Object doInBackground(Void... params) {
		// TODO: attempt authentication against a network service.
		XMLRPCClient models;
		Object val = null;
		try {
			ArrayList<Object> methodParams = new ArrayList<>();
			methodParams.add(paramsMap);
		    
			models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
			val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
					methodName, methodParams.toArray());
			
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
			//TODO Load data into spinnerView
				if(val instanceof Object[]) {
					Object[] data = (Object[]) val;
					Object[] item;
					LinkedHashMap<Integer, String> lovData = new LinkedHashMap<Integer, String>();
					for (Object d : data) {
						item = (Object[]) d;
						Log.i(LOG_TAG, "ID=" + item[0] + ", NAME=" + item[1]);
						Log.i(LOG_TAG, "--------------------------------");
						lovData.put((Integer) item[0], (String) item[1]);
					}
				    LinkedHashMapAdapter<Integer, String> adapter = new LinkedHashMapAdapter<Integer, String>(context, android.R.layout.simple_spinner_item, lovData);
				    adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);

				    spinnerView.setAdapter(adapter);
					((BaseAdapter) spinnerView.getAdapter()).notifyDataSetChanged();				
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