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
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;

/**
 * A login screen that offers login via email/password.
 * 
 */
public class DdRecipientAddActivity extends Activity {

	private static final String LOG_TAG = "DdRecipientAddActivity";

	// UI references.
	private EditText mNameView;
	private EditText mBankAccountView;
	private Spinner mBankView;
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
		Intent intent = new Intent(this, MainActivity.class);
		startActivity(intent);
		finish();
	}

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_recipient_add);
		
		Log.d(LOG_TAG, "savedInstanceState=" + savedInstanceState);

		netHandler = new NetCommHandler(this, savedInstanceState);
		networkStateReceiver = new NetworkStateReceiver(this);
		networkStateReceiver.addListener(netHandler);
		this.registerReceiver(networkStateReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

		mNameView = (EditText) findViewById(R.id.full_name);
		
		mBankAccountView = (EditText) findViewById(R.id.bank_account);
		
		mBankView = (Spinner) findViewById(R.id.bank);

		mProgressView = findViewById(R.id.register_progress);

		Button saveButton = (Button) findViewById(R.id.recipient_add_button);
		saveButton.setOnClickListener(new OnClickListener() {
			@Override
			public void onClick(View view) {
				saveRecipient();
			}
		});

		new InitializeLovTask(this, "res_bank", "list_items", mBankView, mProgressView, null, saveButton).execute();
	}

	/**
	 * Attempts to sign in or register the account specified by the login form.
	 * If there are form errors (invalid email, missing fields, etc.), the
	 * errors are presented and no actual login attempt is made.
	 */
	@SuppressWarnings("unchecked")
	public void saveRecipient() {
		Log.d(LOG_TAG, "saveRecipient()");

		// Reset errors.
		mNameView.setError(null);
		mBankAccountView.setError(null);
		TextView errorTextBank = (TextView) mBankView.getSelectedView();
		errorTextBank.setError("");
		errorTextBank.setTextColor(Color.BLACK);//just to highlight that this is an error
		errorTextBank.setText("");//changes the selected item text to this
		
		String name = mNameView.getText().toString();
		String bankAccountNo = mBankAccountView.getText().toString();
		Object bankId = ((Entry<Long, String>) mBankView.getSelectedItem()).getKey();

		boolean cancel = false;
		View focusView = null;

		// Check for a valid bank account no.
		if (TextUtils.isEmpty(bankAccountNo)) {
			mBankAccountView.setError(getString(R.string.error_field_required));
			focusView = mBankAccountView;
			cancel = true;
		}
		// Check for a valid name.
		if (TextUtils.isEmpty(name)) {
			mNameView.setError(getString(R.string.error_field_required));
			focusView = mNameView;
			cancel = true;
		}
		
		// Check bank not null.
		if (bankId == null) {
			errorTextBank = (TextView) mBankView.getSelectedView();
			errorTextBank.setError("");
			errorTextBank.setTextColor(Color.RED);//just to highlight that this is an error
			errorTextBank.setText("Bank is required");//changes the selected item text to this
			focusView = mBankView;
			cancel = true;
		}

		if (cancel) {
			// There was an error; don't attempt login and focus the first
			// form field with an error.
			focusView.requestFocus();
		} else {
			// Show a progress spinner, and kick off a background task to
			// perform the user login attempt.
			showProgress(true);
			HashMap<String, Object> recipientData = new HashMap<>();
			recipientData.put("name", name);
			recipientData.put("bank_account_no", bankAccountNo);
			recipientData.put("bank_id", bankId);
			recipientData.put("pensioner_id", MainActivity.pid);
			if (NetworkStatus.getInstance(DdRecipientAddActivity.this).isOnline(DdRecipientAddActivity.this)) {
				new DdRecipientAddTask(this, recipientData).execute();
			} else {
				DdRecipientAddActivity.this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
			}
		}
	}

	private boolean isEmailValid(String email) {
		// TODO: Replace this with your own logic
		return email.contains("@");
	}

	private boolean isPersonNameValid(String personName) {
		return personName.matches("[A-Z][a-zA-Z]*\\s[a-zA-z]+([ '-][a-zA-Z]+)*");
	}

	private boolean isPasswordValid(String password) {
		// TODO: Replace this with your own logic
		return password.length() > 4;
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
	
	public class DdRecipientAddTask extends AsyncTask<Void, Void, Object> {

		private final DdRecipientAddActivity activity;
		private final HashMap<String, Object> recipientData;

		DdRecipientAddTask(DdRecipientAddActivity activity, HashMap<String, Object> recipientData) {
			this.activity = activity;
			this.recipientData = recipientData;
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

				methodParams.add(recipientData);
			    
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				msg = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "imalive.pension.ddebit.recipient",
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
					recipientData.clear();
					DirectDebitActivity.pendingMsg = true;
					DirectDebitActivity.pendingMsgTxt = "You have successfully added a new Direct Debit instruction.";
					DirectDebitActivity.pendingMsgTitle = "Success";
					Intent intent = new Intent(DdRecipientAddActivity.this, DirectDebitActivity.class);
					DdRecipientAddActivity.this.startActivity(intent);
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
