package com.vasworks.android.util;

import android.content.Context;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.util.Log;

public class NetworkStatus {
	private static final String LOG_TAG = "NetworkStatus";

	private static NetworkStatus instance = new NetworkStatus();
	
	ConnectivityManager connectivityManager;
	
	NetworkInfo wifiInfo, mobileInfo;
	
	static Context context;
	
	boolean connected = false;

	public static NetworkStatus getInstance(Context ctx) {

		context = ctx;
		return instance;
	}

	public Boolean isOnline(Context con) {

		try {
			connectivityManager = (ConnectivityManager) con.getSystemService(Context.CONNECTIVITY_SERVICE);
			
			Log.v(LOG_TAG, "Conn Manager: " + connectivityManager);

			NetworkInfo networkInfo = connectivityManager.getActiveNetworkInfo();
			
			connected = networkInfo != null && networkInfo.isAvailable() && networkInfo.isConnected();
			
			Log.v(LOG_TAG, "Active Network: " + networkInfo);
			
			if(networkInfo != null) {
				Log.v(LOG_TAG, "Network Available: " + networkInfo.isAvailable());
				Log.v(LOG_TAG, "Network Connected: " + networkInfo.isConnected());
			}
			
			return connected;

		} catch (Exception e) {
			System.out
					.println("CheckConnectivity Exception: " + e.getMessage());
			Log.v(LOG_TAG, e.toString());
		}

		return connected;
	}
	
	
}