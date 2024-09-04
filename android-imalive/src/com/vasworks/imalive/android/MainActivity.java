package com.vasworks.imalive.android;

import com.vasworks.android.util.NetworkStatus;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;

public class MainActivity extends Activity {
	private static final String LOG_TAG = "MainActivity";
	private EditText mPinView;
	private EditText mPcodeView;
	
	static String url = "http://146.148.65.163:8069";
//	static String url = "http://192.168.43.99:8069";
	static Integer userId = 5;
	static final String db = "im_alive_pension";
	static String password = "passw0rd123";
	static String pin = null;
	static Long pid = null;
	static boolean pendingMsg;
	static CharSequence pendingMsgTxt;
	static CharSequence pendingMsgTitle;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_main);
		findViewById(R.id.authenticated).setVisibility((pid != null && pin != null) ? View.VISIBLE : View.GONE);
		findViewById(R.id.unauthenticated).setVisibility((pid != null && pin != null) ? View.GONE : View.VISIBLE);
		
		if(pendingMsg) {
			displayAlert(pendingMsgTxt, pendingMsgTitle, false);
			pendingMsg = false;
			pendingMsgTxt = null;
			pendingMsgTitle = null;
		}
	}
	
	public void enroll(View v) {
		if (NetworkStatus.getInstance(this).isOnline(this)) {
			startActivity(new Intent(this, RegisterActivity.class));
		} else {
			this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
		}	
	}
	
	public void loginPrompt(View v) {
		// get prompts.xml view
		LayoutInflater li = LayoutInflater.from(this);
		View promptsView = li.inflate(R.layout.prompt_login, null);

		AlertDialog.Builder alertDialogBuilder = new AlertDialog.Builder(this);

		// set prompts.xml to alertdialog builder
		alertDialogBuilder.setView(promptsView);

		mPinView = (EditText) promptsView.findViewById(R.id.pin);

		// set dialog message
		alertDialogBuilder
				.setCancelable(false)
				.setPositiveButton("OK",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								String pinEntry = mPinView.getText().toString().trim();
								login(pinEntry);
							}
						})
				.setNegativeButton("Cancel",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								dialog.cancel();
							}
						});

		// create alert dialog
		AlertDialog alertDialog = alertDialogBuilder.create();

		// show it
		alertDialog.show();
	}
	
	public void loginVoicePrompt(View v) {
		// get prompts.xml view
		LayoutInflater li = LayoutInflater.from(this);
		View promptsView = li.inflate(R.layout.prompt_login, null);

		AlertDialog.Builder alertDialogBuilder = new AlertDialog.Builder(this);

		// set prompts.xml to alertdialog builder
		alertDialogBuilder.setView(promptsView);

		mPinView = (EditText) promptsView.findViewById(R.id.pin);

		// set dialog message
		alertDialogBuilder
				.setCancelable(false)
				.setPositiveButton("OK",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								String pinEntry = mPinView.getText().toString().trim();
								loginVoice(pinEntry);
							}
						})
				.setNegativeButton("Cancel",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								dialog.cancel();
							}
						});

		// create alert dialog
		AlertDialog alertDialog = alertDialogBuilder.create();

		// show it
		alertDialog.show();
	}
	
	private void loginVoice(String pinEntry) {
		Log.d(LOG_TAG, "login=" + pinEntry);
		if (!TextUtils.isEmpty(pinEntry)) {
			pin = pinEntry;
			Intent intent = new Intent(this, VoiceRecorderActivity.class);
			intent.putExtra("activityType", "Login");
			startActivity(intent);
		} else {
			mPinView.setError(getString(R.string.error_field_required));
			mPinView.requestFocus();
		}
	}
	
	private void login(String pinEntry) {
		Log.d(LOG_TAG, "login=" + pinEntry);
		if (!TextUtils.isEmpty(pinEntry)) {
			pin = pinEntry;
			startActivity(new Intent(this, FacialLoginActivity.class));
		} else {
			mPinView.setError(getString(R.string.error_field_required));
			mPinView.requestFocus();
		}
	}
	
	public void logout(View v) {
		pid = null;
		pin = null;
		startActivity(new Intent(this, MainActivity.class));
		finish();
	}
	
	public void viewPayslips(View v) {
		if (NetworkStatus.getInstance(this).isOnline(this)) {
			startActivity(new Intent(this, PayslipDetailActivity.class));
		} else {
			this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
		}	
	}
	
	public void ddebit(View v) {
		Log.d(LOG_TAG, "ddebit pid=" + MainActivity.pid);
		if (NetworkStatus.getInstance(this).isOnline(this)) {
			startActivity(new Intent(this, DirectDebitActivity.class));
		} else {
			this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
		}	
	}	
	
	private void approval(String paymentCode) {
		Log.d(LOG_TAG, "paymentCode=" + paymentCode);
		if (!TextUtils.isEmpty(paymentCode)) {
			Intent intent = new Intent(this, LifeProofActivity.class);
			intent.putExtra("paymentCode", paymentCode);
			startActivity(intent);
		} else {
			mPcodeView.setError(getString(R.string.error_field_required));
			mPcodeView.requestFocus();
		}
	}
	
	public void approvalPrompt(View v) {
		// get prompts.xml view
		LayoutInflater li = LayoutInflater.from(this);
		View promptsView = li.inflate(R.layout.prompt_paymentcode, null);

		AlertDialog.Builder alertDialogBuilder = new AlertDialog.Builder(this);

		// set prompts.xml to alertdialog builder
		alertDialogBuilder.setView(promptsView);

		mPcodeView = (EditText) promptsView.findViewById(R.id.paymentcode);

		// set dialog message
		alertDialogBuilder
				.setCancelable(false)
				.setPositiveButton("OK",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								String paymentCode = mPcodeView.getText().toString().trim();
								approval(paymentCode);
							}
						})
				.setNegativeButton("Cancel",
						new DialogInterface.OnClickListener() {
							public void onClick(DialogInterface dialog,
									int id) {
								dialog.cancel();
							}
						});

		// create alert dialog
		AlertDialog alertDialog = alertDialogBuilder.create();

		// show it
		alertDialog.show();
	}
	
	public void profile(View v) {
		startActivity(new Intent(this, ProfileActivity.class));
	}
	
	public void settings(View v) {
		startActivity(new Intent(this, SettingActivity.class));
	}
	
	public void displayAlert(CharSequence message, CharSequence title, final boolean exit) {
		AlertDialog.Builder alertDialog = new AlertDialog.Builder(this).setTitle(title).setPositiveButton(android.R.string.ok,
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
		alertDialog.setMessage(message).show();
	}
}
