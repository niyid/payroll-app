package com.vasworks.android.util;

import java.util.Timer;
import java.util.TimerTask;

import com.vasworks.imalive.android.VoiceRecorderActivity;

import android.content.Context;
import android.os.Handler;
import android.text.SpannableStringBuilder;
import android.text.style.RelativeSizeSpan;
import android.widget.Toast;

public class VoicePromptTimerTask extends TimerTask {
	private Handler handler = new Handler();
	private Timer timer = new Timer();
	private long tStart;
	private String passphrase;
	private int phraseIndex;
	
	private final Context context;

	public VoicePromptTimerTask(Context context, String passphrase) {
		super();
		this.context = context;
		this.passphrase = passphrase;
	}

	public void run() {
		
		handler.post(new Runnable() {
			public void run() {
				if(phraseIndex < passphrase.length()) {
					String text = String.valueOf(passphrase.charAt(phraseIndex));
					SpannableStringBuilder biggerText = new SpannableStringBuilder(text);
					biggerText.setSpan(new RelativeSizeSpan(18f), 0, text.length(), 0);
					Toast.makeText(context, biggerText, Toast.LENGTH_SHORT).show();
					phraseIndex++;
				} else {
					end();
				}
			}
		});
	}
	
	public void schedule() {
		timer.scheduleAtFixedRate(this, 0, 2000);
		tStart = System.currentTimeMillis();
		VoiceRecorderActivity activity = (VoiceRecorderActivity) context;
		activity.startRecording();
	}
	
	public void end() {
		timer.cancel();
		timer.purge();
		handler = null;
		timer = null;
		VoiceRecorderActivity activity = (VoiceRecorderActivity) context;
		activity.stopRecording();
		activity.save();
	}
	
	public long getTime() {
		long tEnd = System.currentTimeMillis();
		return tEnd - tStart;
	}
	
	public Context getContext() {
		return context;
	}
}
