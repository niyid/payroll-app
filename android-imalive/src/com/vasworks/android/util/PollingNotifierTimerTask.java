package com.vasworks.android.util;

import java.util.Timer;
import java.util.TimerTask;

import android.content.Context;
import android.os.Handler;
import android.widget.Toast;

public class PollingNotifierTimerTask extends TimerTask {
	private Handler handler = new Handler();
	private Timer timer = new Timer();
	private long tStart;
	
	private final Context context;

	public PollingNotifierTimerTask(Context context) {
		super();
		this.context = context;
	}

	public void run() {
		
		handler.post(new Runnable() {
			public void run() {
				Toast.makeText(context, "It appears you are experiencing problems; please contact a customer representative if the problems persist.", Toast.LENGTH_LONG).show();
			}
		});
	}
	
	public void schedule() {
		timer.scheduleAtFixedRate(this, 60000, 60000);
		tStart = System.currentTimeMillis();
	}
	
	public void end() {
		if(timer != null) {
			timer.cancel();
			timer.purge();
			handler = null;
			timer = null;
		}
	}
	
	public long getTime() {
		long tEnd = System.currentTimeMillis();
		return tEnd - tStart;
	}
	
	public Context getContext() {
		return context;
	}
}
