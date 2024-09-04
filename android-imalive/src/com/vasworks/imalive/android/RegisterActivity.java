package com.vasworks.imalive.android;

import java.util.ArrayList;
import java.util.Map.Entry;

import com.vasworks.android.util.CheckboxModel;
import com.vasworks.android.util.NetCommHandler;
import com.vasworks.android.util.NetworkStateReceiver;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.annotation.TargetApi;
import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.View;
import android.view.View.OnClickListener;
import android.widget.AutoCompleteTextView;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HeaderViewListAdapter;
import android.widget.ListView;
import android.widget.Spinner;
import android.widget.TextView;

/**
 * A login screen that offers login via email/password.
 * 
 */
public class RegisterActivity extends Activity {

	private static final String LOG_TAG = "RegisterActivity";

	// UI references.
	private AutoCompleteTextView mCellphoneView;
	private AutoCompleteTextView mEmailView;
	private AutoCompleteTextView mHomephoneView;
	private AutoCompleteTextView mFullNameView;
	private EditText mPinView;
	private EditText mBankAccountView;
	// private EditText mPassphraseView;
	private Spinner mBankView;
	private Spinner mGenderView;
	private ListView mDisabilityView;
	private View mProgressView;
	private View mLoginFormView;
	private NetCommHandler netHandler;
	static boolean pendingMsg;
	static CharSequence pendingMsgTxt;
	static CharSequence pendingMsgTitle;

	private NetworkStateReceiver networkStateReceiver;

	@Override
	protected void onStop() {
		try {
			unregisterReceiver(networkStateReceiver);
		} catch (IllegalArgumentException e) {

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
		setContentView(R.layout.activity_register);

		Log.d(LOG_TAG, "savedInstanceState=" + savedInstanceState);

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

		// mPassphraseView = (EditText) findViewById(R.id.passphrase);

		mBankView = (Spinner) findViewById(R.id.bank);

		mDisabilityView = (ListView) findViewById(R.id.disabilities);

		mProgressView = findViewById(R.id.register_progress);

		Button registerButton = (Button) findViewById(R.id.email_register_button);
		registerButton.setOnClickListener(new OnClickListener() {
			@Override
			public void onClick(View view) {
				attemptRegistration();
			}
		});

		if (pendingMsg) {
			displayAlert(pendingMsgTxt, pendingMsgTitle, false);
			pendingMsg = false;
			pendingMsgTxt = null;
			pendingMsgTitle = null;
		}

		if (!EnrollActivity.regData.isEmpty()) {
			mFullNameView.setText((CharSequence) EnrollActivity.regData.get("name_related"));
			mCellphoneView.setText((CharSequence) EnrollActivity.regData.get("mobile_phone"));
			mEmailView.setText((CharSequence) EnrollActivity.regData.get("work_email"));
			mHomephoneView.setText((CharSequence) EnrollActivity.regData.get("home_phone"));
			mPinView.setText((CharSequence) EnrollActivity.regData.get("sinid"));
			mBankAccountView.setText((CharSequence) EnrollActivity.regData.get("bank_account_no"));
			mBankView.setSelection(getIndex(mBankView, (Integer) EnrollActivity.regData.get("bank_id")));
			mGenderView.setSelection(getIndex(mGenderView, (String) EnrollActivity.regData.get("gender")));
		}
		new InitializeLovTask(this, "res_bank", "list_items", mBankView, mProgressView, EnrollActivity.regData.get("bank_id"), registerButton).execute();

		new InitializeCheckboxListTask(this, "imalive_pension_disability", mDisabilityView, EnrollActivity.regData.get("disability_ids"), mProgressView, registerButton, "Disabilities").execute();

		mLoginFormView = findViewById(R.id.register_form);
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

	/**
	 * Attempts to sign in or register the account specified by the login form.
	 * If there are form errors (invalid email, missing fields, etc.), the
	 * errors are presented and no actual login attempt is made.
	 */
	@SuppressWarnings("unchecked")
	public void attemptRegistration() {
		Log.d(LOG_TAG, "attemptRegistration()");

		// Reset errors.
		mCellphoneView.setError(null);
		mHomephoneView.setError(null);
		mFullNameView.setError(null);
		mPinView.setError(null);
		mBankAccountView.setError(null);
		TextView errorTextBank = (TextView) mBankView.getSelectedView();
		errorTextBank.setError("");
		errorTextBank.setTextColor(Color.BLACK);// just to highlight that this
												// is an error
		errorTextBank.setText("");// changes the selected item text to this

		String fullName = mFullNameView.getText().toString();
		String pin = mPinView.getText().toString();
		String cellPhone = mCellphoneView.getText().toString();
		String email = mEmailView.getText().toString();
		String homePhone = mHomephoneView.getText().toString();
		String bankAccountNo = mBankAccountView.getText().toString();
		Object bankId = ((Entry<Integer, String>) mBankView.getSelectedItem()).getKey();

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
		// else if (!isPersonNameValid(fullName)) {
		// mFullNameView.setError(getString(R.string.error_invalid_person_name));
		// focusView = mFullNameView;
		// cancel = true;
		// }
		// Check bank not null.
		if (bankId == null) {
			errorTextBank = (TextView) mBankView.getSelectedView();
			errorTextBank.setError("");
			errorTextBank.setTextColor(Color.RED);// just to highlight that this
													// is an error
			errorTextBank.setText("Bank is required");// changes the selected
														// item text to this
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
			// String passphrase = mPassphraseView.getText().toString();
			showProgress(true);
			EnrollActivity.regData.put("sinid", pin.trim());
			EnrollActivity.regData.put("mobile_phone", cellPhone);
			if (!email.isEmpty()) {
				EnrollActivity.regData.put("work_email", email);
			}
			EnrollActivity.regData.put("home_phone", homePhone);
			EnrollActivity.regData.put("name_related", fullName.trim());
			EnrollActivity.regData.put("bank_account_no", bankAccountNo);
			EnrollActivity.regData.put("bank_id", bankId);
			EnrollActivity.regData.put("gender", gender);
			// EnrollActivity.regData.put("passphrase", passphrase);

			ArrayList<Object> disabilityIds = new ArrayList<>();
			HeaderViewListAdapter adapter = (HeaderViewListAdapter) mDisabilityView.getAdapter();
			CheckboxModel model;
			for (int i = 0; i < adapter.getCount(); i++) {
				model = (CheckboxModel) adapter.getItem(i);
				if (model != null && model.isSelected()) {
					disabilityIds.add(model.getId());
				}
			}

			if (disabilityIds.size() > 0) {
				Log.d(LOG_TAG, "disability_ids=" + disabilityIds.toString());
				EnrollActivity.regData.put("disability_ids", disabilityIds.toString());
			}

			// Start enrollment photo capture activity
			Intent intent = new Intent(this, EnrollActivity.class);
			startActivity(intent);
			finish();
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

}
