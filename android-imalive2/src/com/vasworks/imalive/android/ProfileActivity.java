package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Map.Entry;

import com.vasworks.android.util.CheckboxModel;
import com.vasworks.android.util.NetCommHandler;
import com.vasworks.android.util.NetworkStateReceiver;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.annotation.TargetApi;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
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
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.DatePicker;
import android.widget.EditText;
import android.widget.HeaderViewListAdapter;
import android.widget.ListView;
import android.widget.Spinner;
import android.widget.TextView;

/**
 * A login screen that offers login via email/password.
 * 
 */
public class ProfileActivity extends Activity {

	private static final String LOG_TAG = "ProfileActivity";

	// UI references.
	private AutoCompleteTextView mCellphoneView;
	private AutoCompleteTextView mEmailView;
	private AutoCompleteTextView mHomephoneView;
	private AutoCompleteTextView mFullNameView;
	private EditText mPinView;
	private EditText mBankAccountView;
//	private EditText mPassphraseView;
	private Spinner mBankView;
	private Spinner mGenderView;
	private Spinner mTitleView;
	private EditText mBirthday;
	private ListView mDisabilityView;
	private View mProgressView;
	private View mLoginFormView;
	private NetCommHandler netHandler;

	private ProgressDialog progressDialog;
	private NetworkStateReceiver networkStateReceiver;
	private HashMap<String, Object> profileData;
	private Button registerButton;

	@Override
	protected void onStop() {
		try {
			unregisterReceiver(networkStateReceiver);
		} catch(IllegalArgumentException e) {
			
		}
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
		setContentView(R.layout.activity_profile);
		
		Log.d(LOG_TAG, "savedInstanceState=" + savedInstanceState);

		progressDialog = new ProgressDialog(this);
		
		netHandler = new NetCommHandler(this, savedInstanceState);
		networkStateReceiver = new NetworkStateReceiver(this);
		networkStateReceiver.addListener(netHandler);
		this.registerReceiver(networkStateReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

		mFullNameView = (AutoCompleteTextView) findViewById(R.id.full_name);
		
		mGenderView = (Spinner) findViewById(R.id.gender);

		mCellphoneView = (AutoCompleteTextView) findViewById(R.id.cellphone);

		mEmailView = (AutoCompleteTextView) findViewById(R.id.email);

		mHomephoneView = (AutoCompleteTextView) findViewById(R.id.homephone);
		
		mPinView = (EditText) findViewById(R.id.pension_code);
		
		mBankAccountView = (EditText) findViewById(R.id.bank_account);
		
//		mPassphraseView = (EditText) findViewById(R.id.passphrase);
		
		mBankView = (Spinner) findViewById(R.id.bank);
		
		mTitleView = (Spinner) findViewById(R.id.title);
		
		mBirthday = (EditText) findViewById(R.id.birthday);
		
		mDisabilityView = (ListView) findViewById(R.id.disabilities);

		mProgressView = findViewById(R.id.register_progress);

		registerButton = (Button) findViewById(R.id.save_button);
		registerButton.setOnClickListener(new OnClickListener() {
			@Override
			public void onClick(View view) {
				saveProfile();
			}
		});
		
		new FetchProfileTask().execute();

		mLoginFormView = findViewById(R.id.register_form);
	}

	/**
	 * Attempts to sign in or register the account specified by the login form.
	 * If there are form errors (invalid email, missing fields, etc.), the
	 * errors are presented and no actual login attempt is made.
	 */
	@SuppressWarnings("unchecked")
	public void saveProfile() {
		Log.d(LOG_TAG, "saveProfile()");

		// Reset errors.
		mCellphoneView.setError(null);
		mHomephoneView.setError(null);
		mFullNameView.setError(null);
		mPinView.setError(null);
		mBankAccountView.setError(null);
		TextView errorTextBank = (TextView) mBankView.getSelectedView();
		errorTextBank.setError("");
		errorTextBank.setTextColor(Color.BLACK);//just to highlight that this is an error
		errorTextBank.setText("");//changes the selected item text to this
		
		String fullName = mFullNameView.getText().toString();
		String pin = mPinView.getText().toString();
		String cellPhone = mCellphoneView.getText().toString();
		String homePhone = mHomephoneView.getText().toString();
		String bankAccountNo = mBankAccountView.getText().toString();
		Object bankId = ((Entry<Long, String>) mBankView.getSelectedItem()).getKey();
		Object titleId = mTitleView.getSelectedItem() != null ? ((Entry<Integer, String>) mTitleView.getSelectedItem()).getKey() : null;
		String birthday = mBirthday.getText().toString();

		Object gender = mGenderView.getSelectedItem();

		boolean cancel = false;
		View focusView = null;

		// Check for a valid PIN.
		if (TextUtils.isEmpty(pin)) {
			mCellphoneView.setError(getString(R.string.error_field_required));
			focusView = mCellphoneView;
			cancel = true;
		}
		// Check for a valid cellphone.
		if (TextUtils.isEmpty(cellPhone)) {
			mCellphoneView.setError(getString(R.string.error_field_required));
			focusView = mCellphoneView;
			cancel = true;
		}
		// Check for a valid home phone.
		if (TextUtils.isEmpty(homePhone)) {
			mHomephoneView.setError(getString(R.string.error_field_required));
			focusView = mHomephoneView;
			cancel = true;
		}
		// Check for a valid bank account no.
		if (TextUtils.isEmpty(bankAccountNo)) {
			mBankAccountView.setError(getString(R.string.error_field_required));
			focusView = mBankAccountView;
			cancel = true;
		}
		// Check for a valid name.
		if (TextUtils.isEmpty(fullName)) {
			mFullNameView.setError(getString(R.string.error_field_required));
			focusView = mFullNameView;
			cancel = true;
		} 
//		else if (!isPersonNameValid(fullName)) {
//			mFullNameView.setError(getString(R.string.error_invalid_person_name));
//			focusView = mFullNameView;
//			cancel = true;
//		}
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
//			String passphrase = mPassphraseView.getText().toString();
			showProgress(true);
			HashMap<String, Object> regData = new HashMap<>();
			regData.put("sinid", pin.trim());
			regData.put("mobile_phone", cellPhone);
			regData.put("home_phone", homePhone);
			regData.put("name_related", fullName.trim());
			regData.put("bank_account_no", bankAccountNo);
			regData.put("bank_id", bankId);
			if(titleId != null) {
				regData.put("title_id", titleId);
			}
			regData.put("gender", gender);
			if(!birthday.isEmpty()) {
				regData.put("birthday", birthday);
			}
//			regData.put("passphrase", passphrase);
			
			ArrayList<Object> disabilityIds = new ArrayList<>();
			HeaderViewListAdapter adapter = (HeaderViewListAdapter) mDisabilityView.getAdapter();
			CheckboxModel model;
			for (int i = 0; i < adapter.getCount(); i++) {
				model = (CheckboxModel) adapter.getItem(i);
				if(model != null && model.isSelected()) {
					disabilityIds.add(model.getId());
				}
			}

			if(disabilityIds.size() > 0) {
				Log.d(LOG_TAG, "disability_ids=" + disabilityIds.toString());
				regData.put("disability_ids", disabilityIds.toString());
			}
			new SaveProfileTask(regData).execute();
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

			mLoginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
			mLoginFormView.animate().setDuration(shortAnimTime).alpha(show ? 0 : 1).setListener(new AnimatorListenerAdapter() {
				@Override
				public void onAnimationEnd(Animator animation) {
					mLoginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
				}
			});

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
			mLoginFormView.setVisibility(show ? View.GONE : View.VISIBLE);
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
	
	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class FetchProfileTask extends AsyncTask<Void, Void, Object> {

		@Override
		protected void onPreExecute() {
			super.onPreExecute();

			progressDialog.setMessage("Working...");
			progressDialog.show();

		}
		
		@Override
		protected Object doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			XMLRPCClient models;
			Object msg = null;
			try {
				ArrayList<Object> methodParams = new ArrayList<>();
				methodParams.add(MainActivity.pid);
			    
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				msg = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
						"fetch_profile", methodParams.toArray());
				
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
		
		@SuppressWarnings("unchecked")
		@Override
		protected void onPostExecute(final Object msg) {
			progressDialog.dismiss();
			Log.i(LOG_TAG, "" + msg);
			if(msg != null) {
				if(msg instanceof Map) {
					profileData = (HashMap<String, Object>) msg;
					
					mFullNameView.setText((CharSequence) profileData.get("name_related"));
					mCellphoneView.setText((CharSequence) profileData.get("mobile_phone"));
					if(profileData.get("work_email") != null) {
						mEmailView.setText((CharSequence) profileData.get("work_email"));
					}
					if(profileData.get("home_phone") != null) {
						if(profileData.get("home_phone") instanceof Boolean) {
							mHomephoneView.setText("");
						} else {
							mHomephoneView.setText((CharSequence) profileData.get("home_phone"));
						}
					}
					mPinView.setText((CharSequence) profileData.get("sinid"));
					mBankAccountView.setText((CharSequence) profileData.get("bank_account_no"));
					mBankView.setSelection(getIndex(mBankView, (Integer) EnrollActivity.regData.get("bank_id")));
					mGenderView.setSelection(getIndex(mGenderView, (String) EnrollActivity.regData.get("gender")));

					new InitializeLovTask(ProfileActivity.this, "res_bank", "list_items", mBankView, mProgressView, (Integer) profileData.get("bank_id"), registerButton).execute();
					
					new InitializeLovTask(ProfileActivity.this, "res_partner_title", "list_items", mTitleView, mProgressView, (Integer) profileData.get("title_id"), registerButton).execute();
					
					new InitializeCheckboxListTask(ProfileActivity.this, "imalive_pension_disability", mDisabilityView, profileData.get("disability_ids"), mProgressView, registerButton, "Disabilities").execute();

				} else {
					displayAlert(msg.toString(), "Error", true);
				}
			} else {
				displayAlert("Server is down; try again later.", "Error", true);
			}
		}

		private int getIndex(Spinner spinner, Object value) {
			int index = 0;

			for (int i = 0; i < spinner.getCount(); i++) {
				if (spinner.getItemAtPosition(i).equals(value)) {
					index = i;
					break;
				}
			}
			return index;
		}

		@Override
		protected void onCancelled() {
			progressDialog.dismiss();
		}
	}
	
	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class SaveProfileTask extends AsyncTask<Void, Void, Object> {

		private final HashMap<String, Object> regData;

		SaveProfileTask(HashMap<String, Object> regData) {
			this.regData = regData;
		}

		@Override
		protected void onPreExecute() {
			super.onPreExecute();

			progressDialog.setMessage("Working...");
			progressDialog.show();

		}
		
		@Override
		protected Object doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			XMLRPCClient models;
			Object msg = null;
			try {
				ArrayList<Object> methodParams = new ArrayList<>();
				methodParams.add(MainActivity.pid);
				methodParams.add(regData);
			    
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				msg = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
						"update_profile", methodParams.toArray());
				
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
			progressDialog.dismiss();
			Log.i(LOG_TAG, "" + msg);
			if(msg != null) {
				try {
					Long.parseLong(msg.toString());
					regData.clear();
					MainActivity.pendingMsg = true;
					MainActivity.pendingMsgTxt = "Your profile was successfully updated.";
					MainActivity.pendingMsgTitle = "Success";
					Intent intent = new Intent(ProfileActivity.this, MainActivity.class);
					ProfileActivity.this.startActivity(intent);
					finish();
				} catch(NumberFormatException e) {
					MainActivity.pendingMsg = true;
					MainActivity.pendingMsgTxt = msg.toString();
					MainActivity.pendingMsgTitle = "Error";
					Intent intent = new Intent(ProfileActivity.this, MainActivity.class);
					ProfileActivity.this.startActivity(intent);
					finish();
				}
			} else {
				displayAlert("Server is down; try again later.", "Error", true);
			}
		}

		@Override
		protected void onCancelled() {
			progressDialog.dismiss();
		}
	}
}
