package com.vasworks.imalive.android;

import com.vasworks.android.util.NetworkStatus;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.text.method.ScrollingMovementMethod;
import android.util.Log;
import android.view.LayoutInflater;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;

public class WelcomeActivity extends Activity {
	private static final String LOG_TAG = "WelcomeActivity";
	private TextView welcomeTextView;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_welcome);

		welcomeTextView = (TextView) findViewById(R.id.welcome);
		welcomeTextView.setMovementMethod(new ScrollingMovementMethod());

	}
	
	public void next(View v) {
		if (NetworkStatus.getInstance(this).isOnline(this)) {
			startActivity(new Intent(this, MainActivity.class));
		} else {
			this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
		}	
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
