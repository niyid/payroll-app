package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map.Entry;

import com.vasworks.android.util.NetCommHandler;
import com.vasworks.android.util.NetworkStateReceiver;
import com.vasworks.android.util.NetworkStatus;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.annotation.TargetApi;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.os.AsyncTask;
import android.os.Build;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.AdapterView;
import android.widget.AdapterView.OnItemSelectedListener;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;

/**
 * A login screen that offers login via email/password.
 * 
 */
public class DdInstructionAddActivity extends Activity {

	private static final String LOG_TAG = "DdInstructionAddActivity";

	// UI references.
	private EditText mNameView;
	private EditText mAmountView;
	private Spinner mRecipientView;
	private Spinner mServiceView;
	private Spinner mCalendarView;
	private CheckBox mRecurrentView;
	private View mProgressView;
	private NetCommHandler netHandler;

	private NetworkStateReceiver networkStateReceiver;

	@Override
	protected void onStop() {
		unregisterReceiver(networkStateReceiver);
		super.onStop();
	}
	
	@Override
	public void onBackPressed() {
		Intent intent = new Intent(this, DirectDebitActivity.class);
		startActivity(intent);
		finish();
	}

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_instruction_add);
		
		Log.d(LOG_TAG, "savedInstanceState=" + savedInstanceState);

		netHandler = new NetCommHandler(this, savedInstanceState);
		networkStateReceiver = new NetworkStateReceiver(this);
		networkStateReceiver.addListener(netHandler);
		this.registerReceiver(networkStateReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));
		
		mCalendarView = (Spinner) findViewById(R.id.calendar);
		
		mAmountView = (EditText) findViewById(R.id.amount);
		
		mNameView = (EditText) findViewById(R.id.narration);
		
		mRecipientView = (Spinner) findViewById(R.id.recipient);
		
		mServiceView = (Spinner) findViewById(R.id.service);
		mServiceView.setOnItemSelectedListener(new OnItemSelectedListener() {

			@Override
			public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
				mAmountView.setVisibility(View.GONE);
			}

			@Override
			public void onNothingSelected(AdapterView<?> parent) {
				mAmountView.setVisibility(View.VISIBLE);
			}
		});
		
		mRecurrentView = (CheckBox) findViewById(R.id.recurrent);

		mProgressView = findViewById(R.id.instruction_progress);
		
		final Button saveButton = (Button) findViewById(R.id.instruction_add_button);
		saveButton.setOnClickListener(new OnClickListener() {
			@Override
			public void onClick(View view) {
				submit();
			}
		});

		HashMap<String, Object> paramMap = new HashMap<>();
		paramMap.put("table_name", "imalive_pension_ddebit_recipient");
		paramMap.put("field_name", "pensioner_id");
		paramMap.put("field_value", MainActivity.pid);
		new InitializeFlexLovTask(this, "list_recipient_items", paramMap, mRecipientView, mProgressView, saveButton).execute();
		
		new InitializeLovTask(this, "imalive_pension_calendar", "list_items", mCalendarView, mProgressView, null, saveButton).execute();

		//TODO Task to list services owned by recipient if any launched at recipient onChange.
		mRecipientView.setOnItemSelectedListener(new OnItemSelectedListener() {

			@SuppressWarnings("unchecked")
			@Override
			public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
				Entry<String, Object> pair = (Entry<String, Object>) mRecipientView.getItemAtPosition(position);
				HashMap<String, Object> paramMap = new HashMap<>();
				paramMap.put("table_name", "imalive_pension_ddebit_service");
				paramMap.put("field_name", "recipient_id");
				paramMap.put("field_value", pair.getKey());
				new InitializeSlaveLovTask(DdInstructionAddActivity.this, "list_slave_items", paramMap, mServiceView, mProgressView, saveButton).execute();
			}

			@Override
			public void onNothingSelected(AdapterView<?> parent) {
				mServiceView.setAdapter(null);
			}
		});

	}

	@SuppressWarnings("unchecked")
	public void submit() {
		Log.d(LOG_TAG, "submit()");

		// Reset errors.
		mAmountView.setError(null);
		mNameView.setError(null);
		TextView errorTextRecipient = (TextView) mRecipientView.getSelectedView();
		errorTextRecipient.setError("");
		errorTextRecipient.setTextColor(Color.BLACK);//just to highlight that this is an error
		errorTextRecipient.setText("");//changes the selected item text to this

		TextView errorTextService = (TextView) mServiceView.getSelectedView();
		errorTextService.setError("");
		errorTextService.setTextColor(Color.BLACK);//just to highlight that this is an error
		errorTextService.setText("");//changes the selected item text to this

		TextView errorTextCalendar = (TextView) mCalendarView.getSelectedView();
		errorTextCalendar.setError("");
		errorTextCalendar.setTextColor(Color.BLACK);//just to highlight that this is an error
		errorTextCalendar.setText("");//changes the selected item text to this
		
		String name = mNameView.getText().toString();
		String amount = mAmountView.getText().toString();
		String narration = mNameView.getText().toString();
		Object recipientId = ((Entry<Long, String>) mRecipientView.getSelectedItem()).getKey();
		Object serviceId = ((Entry<Long, String>) mServiceView.getSelectedItem()).getKey();
		Object calendarId = ((Entry<Long, String>) mCalendarView.getSelectedItem()).getKey();
		Boolean recurrent = mRecurrentView.isChecked();

		boolean cancel = false;
		View focusView = null;

		if (serviceId == null && TextUtils.isEmpty(amount)) {
			mAmountView.setError(getString(R.string.error_field_required));
			focusView = mAmountView;
			cancel = true;
		}
		if (serviceId == null && TextUtils.isEmpty(amount)) {
			errorTextService = (TextView) mServiceView.getSelectedView();
			errorTextService.setError("");
			errorTextService.setTextColor(Color.RED);//just to highlight that this is an error
			errorTextService.setText("Service is required when no amount is entered");//changes the selected item text to this
			focusView = mServiceView;
			cancel = true;
		}
		if (TextUtils.isEmpty(narration)) {
			mNameView.setError(getString(R.string.error_field_required));
			focusView = mNameView;
			cancel = true;
		}

		if (recipientId == null) {
			errorTextRecipient = (TextView) mRecipientView.getSelectedView();
			errorTextRecipient.setError("");
			errorTextRecipient.setTextColor(Color.RED);//just to highlight that this is an error
			errorTextRecipient.setText("Recipient is required");//changes the selected item text to this
			focusView = mRecipientView;
			cancel = true;
		}

		if (cancel) {
			focusView.requestFocus();
		} else {
			showProgress(true);
			HashMap<String, Object> instructionData = new HashMap<>();
			instructionData.put("pensioner_id", MainActivity.pid);
			instructionData.put("name", name);
			instructionData.put("amount", amount);
			instructionData.put("recipient_id", recipientId);
			instructionData.put("service_id", serviceId);
			instructionData.put("calendar_id", calendarId);
			instructionData.put("recurrent", recurrent);
			if (NetworkStatus.getInstance(DdInstructionAddActivity.this).isOnline(DdInstructionAddActivity.this)) {
				new DdInstructionAddTask(this, instructionData).execute();
			} else {
				DdInstructionAddActivity.this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
			}
		}
	}

	/**
	 * Shows the progress UI and hides the login form.
	 */
	@TargetApi(Build.VERSION_CODES.HONEYCOMB_MR2)
	public void showProgress(final boolean show) {
		// On Honeycomb MR2 we have the ViewPropertyAnimator APIs, which allow
		// for very easy animations. If available, use these APIs to fade-in
		// the progress spinner.
		if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.HONEYCOMB_MR2) {
			int shortAnimTime = getResources().getInteger(android.R.integer.config_shortAnimTime);

			mProgressView.setVisibility(show ? View.VISIBLE : View.GONE);
			mProgressView.animate().setDuration(shortAnimTime).alpha(show ? 1 : 0).setListener(new AnimatorListenerAdapter() {
				@Override
				public void onAnimationEnd(Animator animation) {
					mProgressView.setVisibility(show ? View.VISIBLE : View.GONE);
				}
			});
		} else {
			// The ViewPropertyAnimator APIs are not available, so simply show
			// and hide the relevant UI components.
			mProgressView.setVisibility(show ? View.VISIBLE : View.GONE);
		}
	}

	public void displayAlert(CharSequence charSequence, CharSequence charSequence2, final boolean exit) {
		AlertDialog.Builder alertDialog = new AlertDialog.Builder(this).setTitle(charSequence2).setPositiveButton(android.R.string.ok,
				new DialogInterface.OnClickListener() {
					@Override
					public void onClick(DialogInterface dialog, int arg1) {
						if (exit) {
							finish();
						} else {
							dialog.cancel();
						}
					}
				});
		alertDialog.setMessage(charSequence).show();
	}
	
	public class DdInstructionAddTask extends AsyncTask<Void, Void, Object> {

		private final DdInstructionAddActivity activity;
		private final HashMap<String, Object> instructionData;

		DdInstructionAddTask(DdInstructionAddActivity activity, HashMap<String, Object> instructionData) {
			this.activity = activity;
			this.instructionData = instructionData;
		}

		@Override
		protected void onPreExecute() {
			super.onPreExecute();
			mProgressView.setVisibility(View.VISIBLE);
		}
		
		@Override
		protected Object doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			XMLRPCClient models;
			Object msg = null;
			try {
				ArrayList<Object> methodParams = new ArrayList<>();

				methodParams.add(instructionData);
			    
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				msg = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "imalive.pension.ddebit",
						"create", methodParams.toArray());
				
				Log.i(LOG_TAG, "Return val=" + msg);

			} catch (MalformedURLException e) {
				e.printStackTrace();
				msg = e.getMessage();
			} catch (XMLRPCException e) {
				e.printStackTrace();
				msg = e.getMessage();
			} catch (Exception e) {
				e.printStackTrace();
				msg = e.getMessage();
			}

			return msg;
		}
		
		@Override
		protected void onPostExecute(final Object msg) {
			mProgressView.setVisibility(View.GONE);
			Log.i(LOG_TAG, "" + msg);
			if(msg != null) {
				try {
					Long.parseLong(msg.toString());
					instructionData.clear();
					DirectDebitActivity.pendingMsg = true;
					DirectDebitActivity.pendingMsgTxt = "You have successfully added a new Direct Debit instruction.";
					DirectDebitActivity.pendingMsgTitle = "Success";
					Intent intent = new Intent(DdInstructionAddActivity.this, DirectDebitActivity.class);
					DdInstructionAddActivity.this.startActivity(intent);
					finish();
				} catch(NumberFormatException e) {
					displayAlert(msg.toString(), "Error", true);
				}
			} else {
				displayAlert("Server is down; try again later.", "Error", true);
			}
		}

		@Override
		protected void onCancelled() {
			mProgressView.setVisibility(View.GONE);
		}
	}
}
