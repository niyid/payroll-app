package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.Map.Entry;

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

public class InitializeLovTask extends AsyncTask<Void, Void, Object> {
	private static final String LOG_TAG = "InitializeLovTask";
	private final Context context;
	private final View progressDialog;
	private final String entityName;
	private final String methodName;
	private final Spinner spinnerView;
	private final Button formButton;
	private final Object currentEntityId;

	InitializeLovTask(Context context, String entityName, String methodName, Spinner spinnerView, View progressDialog, Object currentEntityId, Button formButton) {
		this.context = context;
		this.entityName = entityName;
		this.methodName = methodName;
		this.spinnerView = spinnerView;
		this.currentEntityId = currentEntityId;
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
			methodParams.add(entityName);
		    
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
					if(currentEntityId != null) {
						spinnerView.setSelection(getIndex((Integer) currentEntityId));
					}
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

	// private method of your class
	@SuppressWarnings("unchecked")
	private int getIndex(Integer key) {
		int index = 0;

		for (int i = 0; i < spinnerView.getCount(); i++) {
			if (((Entry<Integer, String>) spinnerView.getItemAtPosition(i)).getKey() == key) {
				index = i;
				break;
			}
		}
		return index;
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