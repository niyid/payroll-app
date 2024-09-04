package com.vasworks.imalive.android;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.List;

import com.vasworks.android.util.VoicePromptTimerTask;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.ProgressDialog;
import android.content.DialogInterface;
import android.content.Intent;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.AsyncTask;
import android.os.Bundle;
import android.os.Environment;
import android.text.TextUtils;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;

public class VoiceRecorderActivity extends Activity {
	private static final String LOG_TAG = "VoiceRecorderActivity";
	private static final int RECORDER_BPP = 16;
	private static final String AUDIO_RECORDER_FILE_EXT_WAV = ".wav";
	private static final String AUDIO_RECORDER_FOLDER = "AudioRecorder";
	private static final String AUDIO_RECORDER_TEMP_FILE = "record_temp.raw";
	private static final int RECORDER_SAMPLERATE = 44100;
	private static final int RECORDER_CHANNELS = AudioFormat.CHANNEL_IN_STEREO;
	private static final int RECORDER_AUDIO_ENCODING = AudioFormat.ENCODING_PCM_16BIT;

	private AudioRecord recorder = null;
	private int bufferSize = 0;
	private Thread recordingThread = null;
	private boolean isRecording = false;
	private String activityType;
	private EditText mPassphraseView;
	private VoicePromptTimerTask voicePromptTimerTask;

	private ProgressDialog progressDialog;

	// TODO Change to display passphrase 1 at a time (every second). User must
	// recite as they appear on the screen
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_record_audio);

		activityType = getIntent().getStringExtra("activityType");

		enableButtons(false);

		bufferSize = AudioRecord.getMinBufferSize(8000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);

		mPassphraseView = (EditText) findViewById(R.id.passphrase);

		progressDialog = new ProgressDialog(this);
	}

	private void enableButton(int id, boolean isEnable) {
		((Button) findViewById(id)).setEnabled(isEnable);
	}

	private void enableButtons(boolean isRecording) {
		enableButton(R.id.btnStart, !isRecording);
	}

	private String getFilename() {
		String filepath = getExternalCacheDir().getAbsolutePath();
		File file = new File(filepath, AUDIO_RECORDER_FOLDER);

		if (!file.exists()) {
			file.mkdirs();
		}

		return (file.getAbsolutePath() + "/voice" + AUDIO_RECORDER_FILE_EXT_WAV);
	}

	private String getTempFilename() {
		String filepath = Environment.getExternalStorageDirectory().getPath();
		File file = new File(filepath, AUDIO_RECORDER_FOLDER);

		if (!file.exists()) {
			file.mkdirs();
		}

		File tempFile = new File(filepath, AUDIO_RECORDER_TEMP_FILE);

		if (tempFile.exists())
			tempFile.delete();

		return (file.getAbsolutePath() + "/" + AUDIO_RECORDER_TEMP_FILE);
	}

	public void startVoice(View v) {
		String passphrase = mPassphraseView.getText().toString();
		if (TextUtils.isEmpty(passphrase)) {
			mPassphraseView.setError(getString(R.string.error_field_required));
			mPassphraseView.requestFocus();
		} else {
			voicePromptTimerTask = new VoicePromptTimerTask(this, mPassphraseView.getText().toString());
			voicePromptTimerTask.schedule();
		}
	}

	public void startRecording() {
		recorder = new AudioRecord(MediaRecorder.AudioSource.MIC, RECORDER_SAMPLERATE, RECORDER_CHANNELS, RECORDER_AUDIO_ENCODING, bufferSize);

		int i = recorder.getState();
		if (i == 1)
			recorder.startRecording();

		isRecording = true;

		recordingThread = new Thread(new Runnable() {

			@Override
			public void run() {
				writeAudioDataToFile();
			}
		}, "AudioRecorder Thread");

		// TODO Thread to cycle through the passphrase and display one character
		// at a time. Once last character displayed, save recording.
		// TODO Display characters with a second delay between each display
		recordingThread.start();
	}

	private void writeAudioDataToFile() {
		byte data[] = new byte[bufferSize];
		String filename = getTempFilename();
		FileOutputStream os = null;

		try {
			os = new FileOutputStream(filename);
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		}

		int read = 0;

		if (null != os) {
			while (isRecording) {
				read = recorder.read(data, 0, bufferSize);

				if (AudioRecord.ERROR_INVALID_OPERATION != read) {
					try {
						os.write(data);
					} catch (IOException e) {
						e.printStackTrace();
					}
				}
			}

			try {
				os.close();
			} catch (IOException e) {
				e.printStackTrace();
			}
		}
	}

	public void stopRecording() {
		if (null != recorder) {
			isRecording = false;

			int i = recorder.getState();
			if (i == 1)
				recorder.stop();
			recorder.release();

			recorder = null;
			recordingThread = null;
		}

		copyWaveFile(getTempFilename(), getFilename());
		deleteTempFile();
	}

	private void deleteTempFile() {
		File file = new File(getTempFilename());

		file.delete();
	}

	private void copyWaveFile(String inFilename, String outFilename) {
		FileInputStream in = null;
		FileOutputStream out = null;
		long totalAudioLen = 0;
		long totalDataLen = totalAudioLen + 36;
		long longSampleRate = RECORDER_SAMPLERATE;
		int channels = 2;
		long byteRate = RECORDER_BPP * RECORDER_SAMPLERATE * channels / 8;

		byte[] data = new byte[bufferSize];

		try {
			in = new FileInputStream(inFilename);
			out = new FileOutputStream(outFilename);
			totalAudioLen = in.getChannel().size();
			totalDataLen = totalAudioLen + 36;

			Log.d(LOG_TAG, "File size: " + totalDataLen);

			WriteWaveFileHeader(out, totalAudioLen, totalDataLen, longSampleRate, channels, byteRate);

			while (in.read(data) != -1) {
				out.write(data);
			}

			in.close();
			out.close();
		} catch (FileNotFoundException e) {
			e.printStackTrace();
		} catch (IOException e) {
			e.printStackTrace();
		}
	}

	private void WriteWaveFileHeader(FileOutputStream out, long totalAudioLen, long totalDataLen, long longSampleRate, int channels, long byteRate)
			throws IOException {

		byte[] header = new byte[44];

		header[0] = 'R'; // RIFF/WAVE header
		header[1] = 'I';
		header[2] = 'F';
		header[3] = 'F';
		header[4] = (byte) (totalDataLen & 0xff);
		header[5] = (byte) ((totalDataLen >> 8) & 0xff);
		header[6] = (byte) ((totalDataLen >> 16) & 0xff);
		header[7] = (byte) ((totalDataLen >> 24) & 0xff);
		header[8] = 'W';
		header[9] = 'A';
		header[10] = 'V';
		header[11] = 'E';
		header[12] = 'f'; // 'fmt ' chunk
		header[13] = 'm';
		header[14] = 't';
		header[15] = ' ';
		header[16] = 16; // 4 bytes: size of 'fmt ' chunk
		header[17] = 0;
		header[18] = 0;
		header[19] = 0;
		header[20] = 1; // format = 1
		header[21] = 0;
		header[22] = (byte) channels;
		header[23] = 0;
		header[24] = (byte) (longSampleRate & 0xff);
		header[25] = (byte) ((longSampleRate >> 8) & 0xff);
		header[26] = (byte) ((longSampleRate >> 16) & 0xff);
		header[27] = (byte) ((longSampleRate >> 24) & 0xff);
		header[28] = (byte) (byteRate & 0xff);
		header[29] = (byte) ((byteRate >> 8) & 0xff);
		header[30] = (byte) ((byteRate >> 16) & 0xff);
		header[31] = (byte) ((byteRate >> 24) & 0xff);
		header[32] = (byte) (2 * 16 / 8); // block align
		header[33] = 0;
		header[34] = RECORDER_BPP; // bits per sample
		header[35] = 0;
		header[36] = 'd';
		header[37] = 'a';
		header[38] = 't';
		header[39] = 'a';
		header[40] = (byte) (totalAudioLen & 0xff);
		header[41] = (byte) ((totalAudioLen >> 8) & 0xff);
		header[42] = (byte) ((totalAudioLen >> 16) & 0xff);
		header[43] = (byte) ((totalAudioLen >> 24) & 0xff);

		out.write(header, 0, 44);
	}

	public void save() {
		try {
			File audio = new File(getFilename());
			ArrayList<Object> methodParams = new ArrayList<>();
			byte bytes[] = new byte[(int) audio.length()];
			BufferedInputStream bis = new BufferedInputStream(new FileInputStream(audio));
			DataInputStream dis = new DataInputStream(bis);
			dis.readFully(bytes);
			dis.close();
			if ("Login".equals(activityType)) {
				methodParams.add(MainActivity.pin);
				methodParams.add(Base64.encodeToString(bytes, Base64.URL_SAFE));

				new UploadVoiceTask("login_voice", methodParams).execute();
			} else if ("Save".equals(activityType)) {

				boolean cancel = false;
				View focusView = null;
				String passphrase = mPassphraseView.getText().toString();
				// Check for a valid PIN.
				if (TextUtils.isEmpty(passphrase)) {
					mPassphraseView.setError(getString(R.string.error_field_required));
					focusView = mPassphraseView;
					cancel = true;
				}
				methodParams.add(MainActivity.pid);
				methodParams.add(passphrase);
				methodParams.add(Base64.encodeToString(bytes, Base64.URL_SAFE));

				if (cancel) {
					focusView.requestFocus();
				} else {
					new UploadVoiceTask("register_voice", methodParams).execute();
				}
			}
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
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

	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class UploadVoiceTask extends AsyncTask<Void, Void, String> {
		private final String functionName;
		private final List<Object> methodParams;

		UploadVoiceTask(String functionName, List<Object> methodParams) {
			this.functionName = functionName;
			this.methodParams = methodParams;
		}

		@Override
		protected void onPreExecute() {
			super.onPreExecute();

			progressDialog.setMessage("Working...");
			progressDialog.show();

		}

		@Override
		protected String doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			XMLRPCClient models;
			String msg = null;
			try {

				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				Object val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee", functionName,
						methodParams.toArray());

				if (val != null) {
					msg = val.toString();
				} else {
					msg = null;
				}

				Log.i(LOG_TAG, "Return val=" + val);

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
		protected void onPostExecute(final String msg) {
			progressDialog.dismiss();
			Log.i(LOG_TAG, "" + msg);
			if (msg != null) {
				if ("Save".equals(activityType)) {
					boolean success = Boolean.parseBoolean(msg);
					if (success) {
						Intent intent = new Intent(VoiceRecorderActivity.this, SettingActivity.class);
						SettingActivity.pendingMsg = true;
						SettingActivity.pendingMsgTitle = "Success";
						SettingActivity.pendingMsgTxt = "Voice activation completed.";
						VoiceRecorderActivity.this.startActivity(intent);
						finish();
					} else {
						displayAlert("Voice operation failed. Contact the administrator for more information", "Error", true);
					}
				} else {
					try {
						MainActivity.pid = Long.parseLong(msg);
						Intent intent = new Intent(VoiceRecorderActivity.this, MainActivity.class);
						VoiceRecorderActivity.this.startActivity(intent);
						finish();
					} catch (NumberFormatException e) {
						displayAlert(msg, "Error", true);
					}

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
