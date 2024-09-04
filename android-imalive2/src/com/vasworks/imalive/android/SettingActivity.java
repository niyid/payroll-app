package com.vasworks.imalive.android;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;
import android.view.View;

public class SettingActivity extends Activity {
	private static final String LOG_TAG = "SettingActivity";
	static boolean pendingMsg;
	static CharSequence pendingMsgTxt;
	static CharSequence pendingMsgTitle;
	
	@Override
	protected void onCreate(Bundle savedInstanceState) {
		Log.d(LOG_TAG, "SettingActivity pid=" + MainActivity.pid);
		
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_setting);
		
		if(pendingMsg) {
			displayAlert(pendingMsgTxt, pendingMsgTitle, false);
			pendingMsg = false;
			pendingMsgTxt = null;
			pendingMsgTitle = null;
		}
	}
	
	public void recordVoice(View v) {
		Intent intent = new Intent(this, VoiceRecorderActivity.class);
		intent.putExtra("activityType", "Save");
		startActivity(intent);
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
