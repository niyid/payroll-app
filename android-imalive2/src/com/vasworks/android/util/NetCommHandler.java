package com.vasworks.android.util;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.UnsupportedEncodingException;

import com.vasworks.android.util.NetworkStateReceiver.NetworkStateReceiverListener;
import com.vasworks.imalive.android.R;

import android.content.Context;
import android.os.Bundle;
import android.widget.AutoCompleteTextView;
import android.widget.EditText;

public class NetCommHandler implements NetworkStateReceiverListener {

	public static final String LOG_TAG = "NetCommHandler";

	public static final String BASE_ACTION_URL = "http://192.168.43.33:8080/dplggr-web/json/";
	
	public static final String ACTION_LOGIN = "authenticate.jspx";
	
	public static final String ACTION_REGISTER = "register.jspx";
	
	public static final String ACTION_SAVE_PHOTOS = "uploadPhoto.jspx";
	
	public static final String ACTION_FETCH_MATCHES = "matches.jspx";
	
	public static final String ACTION_FETCH_RANDOM = "random.jspx";
	
	public static final String ACTION_FETCH_CELEBS = "celebrities.jspx";
	
	public static final String ACTION_SEARCH = "search.jspx";
	
	public static final String ACTION_RATE = "rate.jspx";
	
	private static Context activity;
	
	private static Bundle savedInstanceState;
	
	public NetCommHandler(Context activity, Bundle savedInstanceState) {
		NetCommHandler.activity = activity;
		NetCommHandler.savedInstanceState = savedInstanceState;
	}
	public void sendPendingRequests() {
		for(String key : savedInstanceState.keySet()) {
			if(key.startsWith("params_")) {
				try {
					//TODO Retrieve URLs as well
					savedInstanceState.remove(key);
				} catch (Throwable e) {
					e.printStackTrace();
					ByteArrayOutputStream out = new ByteArrayOutputStream();
					try {
						String aString = new String(out.toByteArray(), "UTF-8");
//						activity.displayAlert(aString, "Error", false);
					} catch (UnsupportedEncodingException e1) {
		
						e1.printStackTrace();
					}
					try {
						out.close();
					} catch (IOException e2) {
						e2.printStackTrace();
					}
				}
			}
		}

	}

	@Override
	public void onNetworkAvailable() {
		if(savedInstanceState != null && !savedInstanceState.isEmpty()) {
			sendPendingRequests();
		}
	}

	@Override
	public void onNetworkUnavailable() {
		//Do nothing
	}

	public int resolveError(String errorCode, AutoCompleteTextView mEmailView, EditText mPasswordView) {
		int resourceId = 0;

		if ("error_invalid_email".equals(errorCode)) {
			resourceId = R.string.error_invalid_email;
			mEmailView.setError(activity.getString(resourceId));
			mEmailView.requestFocus();
		} else if ("error_invalid_password".equals(errorCode)) {
			resourceId = R.string.error_invalid_password;
			mPasswordView.setError(activity.getString(resourceId));
			mPasswordView.requestFocus();
		} else if ("error_mismatch_password".equals(errorCode)) {
			resourceId = R.string.error_mismatch_password;
			mPasswordView.setError(activity.getString(resourceId));
			mPasswordView.requestFocus();
		} else if ("error_incorrect_password".equals(errorCode)) {
			resourceId = R.string.error_incorrect_password;
			mPasswordView.setError(activity.getString(resourceId));
			mPasswordView.requestFocus();
		} else if ("error_user_disabled".equals(errorCode)) {
			resourceId = R.string.error_user_disabled;
			mEmailView.setError(activity.getString(resourceId));
			mEmailView.requestFocus();
		} else if ("error_no_such_user".equals(errorCode)) {
			resourceId = R.string.error_no_such_user;
			mEmailView.setError(activity.getString(resourceId));
			mEmailView.requestFocus();
		} else if ("error_user_exists".equals(errorCode)) {
			resourceId = R.string.error_user_exists;
			mEmailView.setError(activity.getString(resourceId));
			mEmailView.requestFocus();
		} else if ("error_field_required".equals(errorCode)) {
			resourceId = R.string.error_field_required;
			mPasswordView.setError(activity.getString(resourceId));
			mPasswordView.requestFocus();
		}
		
		return resourceId;
	}
}
