package com.vasworks.imalive.android;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;

import com.google.android.gms.common.ConnectionResult;
import com.google.android.gms.common.GoogleApiAvailability;
import com.google.android.gms.vision.CameraSource;
import com.google.android.gms.vision.MultiProcessor;
import com.google.android.gms.vision.Tracker;
import com.google.android.gms.vision.face.Face;
import com.google.android.gms.vision.face.FaceDetector;
import com.google.android.gms.vision.face.FaceDetector.Builder;
import com.vasworks.android.util.NetCommHandler;
import com.vasworks.android.util.NetworkStateReceiver;
import com.vasworks.android.util.NetworkStatus;
import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.Manifest;
import android.annotation.SuppressLint;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.Dialog;
import android.app.ProgressDialog;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.hardware.Camera.Parameters;
import android.hardware.Camera;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.design.widget.Snackbar;
import android.support.v4.app.ActivityCompat;
import android.support.v7.app.AppCompatActivity;
import android.util.Base64;
import android.util.Log;
import android.view.View;
import android.widget.Button;

/**
 * Activity for the face tracker app. This app detects faces with the rear
 * facing camera, and draws overlay graphics to indicate the position, size, and
 * ID of each face.
 */
public final class FacialLoginActivity extends AppCompatActivity implements SensorEventListener, PhotoUploader {
	private static final String LOG_TAG = "FacialLoginActivity";

	private CustomCameraSource mCameraSource = null;

	private CameraSourcePreview mPreview;
	private GraphicOverlay mGraphicOverlay;

	private Button statusButton;

	private static final int RC_HANDLE_GMS = 9001;
	// permission request codes need to be < 256
	private static final int RC_HANDLE_CAMERA_PERM = 2;

	private SensorManager sensorMan;
	private Sensor accelerometer;
	private Sensor mProximity;
	private Sensor mLightSensor;

	private volatile float[] mGravity;
	private volatile float mAccel;
	private volatile float mAccelCurrent;
	private volatile float mAccelLast;
	private volatile float mDistance;
	private volatile float mLightQuantity;

	private ProgressDialog progressDialog;

	private NetworkStateReceiver networkStateReceiver;

	private PhotoQualityChecker mFaceGraphic;

	private int[] bounds = new int[4];

	private double rating;

	private NetCommHandler netHandler;

	public boolean photoTaken = false;

	@Override
	public void onBackPressed() {
		Intent intent = new Intent(this, MainActivity.class);
		startActivity(intent);
		finish();
	}

	@Override
	protected void onStop() {
		try {
			unregisterReceiver(networkStateReceiver);
		} catch (IllegalArgumentException e) {

		}
		super.onStop();
	}

	/**
	 * Initializes the UI and initiates the creation of a face detector.
	 */
	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.main);

		netHandler = new NetCommHandler(this, savedInstanceState);

		networkStateReceiver = new NetworkStateReceiver(this);
		networkStateReceiver.addListener(netHandler);
		this.registerReceiver(networkStateReceiver, new IntentFilter(android.net.ConnectivityManager.CONNECTIVITY_ACTION));

		progressDialog = new ProgressDialog(this);

		sensorMan = (SensorManager) getSystemService(SENSOR_SERVICE);
		accelerometer = sensorMan.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
		mProximity = sensorMan.getDefaultSensor(Sensor.TYPE_PROXIMITY);
		mLightSensor = sensorMan.getDefaultSensor(Sensor.TYPE_LIGHT);
		if (mLightSensor == null) {
			displayAlert("Your device does not have a Light Sensor.", "Error", true);
		}
		mAccel = 0.00f;
		mAccelCurrent = SensorManager.GRAVITY_EARTH;
		mAccelLast = SensorManager.GRAVITY_EARTH;

		mPreview = (CameraSourcePreview) findViewById(R.id.preview);
		mGraphicOverlay = (GraphicOverlay) findViewById(R.id.faceOverlay);

		statusButton = (Button) findViewById(R.id.button1);

		sensorMan.registerListener(this, mLightSensor, SensorManager.SENSOR_DELAY_UI);

		// Check for the camera permission before accessing the camera. If the
		// permission is not granted yet, request permission.
		int rc = ActivityCompat.checkSelfPermission(this, Manifest.permission.CAMERA);
		if (rc == PackageManager.PERMISSION_GRANTED) {
			createCameraSource();
		} else {
			requestCameraPermission();
		}
	}

	/**
	 * Handles the requesting of the camera permission. This includes showing a
	 * "Snackbar" message of why the permission is needed then sending the
	 * request.
	 */
	private void requestCameraPermission() {
		Log.w(LOG_TAG, "Camera permission is not granted. Requesting permission");

		final String[] permissions = new String[] { Manifest.permission.CAMERA };

		if (!ActivityCompat.shouldShowRequestPermissionRationale(this, Manifest.permission.CAMERA)) {
			ActivityCompat.requestPermissions(this, permissions, RC_HANDLE_CAMERA_PERM);
			return;
		}

		final Activity thisActivity = this;

		View.OnClickListener listener = new View.OnClickListener() {
			@Override
			public void onClick(View view) {
				ActivityCompat.requestPermissions(thisActivity, permissions, RC_HANDLE_CAMERA_PERM);
			}
		};

		Snackbar.make(mGraphicOverlay, R.string.permission_camera_rationale, Snackbar.LENGTH_INDEFINITE).setAction(R.string.ok, listener).show();
	}

	@Override
	public void onSensorChanged(SensorEvent event) {
		if (event.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
			mGravity = event.values.clone();
			// Shake detection
			float x = mGravity[0];
			float y = mGravity[1];
			float z = mGravity[2];
			mAccelLast = mAccelCurrent;
			mAccelCurrent = (float) Math.sqrt(x * x + y * y + z * z);
			float delta = mAccelCurrent - mAccelLast;
			mAccel = mAccel * 0.9f + delta;
			// Make this higher or lower according to how much
			// motion you want to detect
		}

		if (event.sensor.getType() == Sensor.TYPE_PROXIMITY) {
			mDistance = event.values[0];
		}

		if (event.sensor.getType() == Sensor.TYPE_LIGHT) {
			mLightQuantity = event.values[0];
		}
	}

	@Override
	public void onAccuracyChanged(Sensor sensor, int accuracy) {
		// required method
	}

	/**
	 * Creates and starts the camera. Note that this uses a higher resolution in
	 * comparison to other detection examples to enable the barcode detector to
	 * detect small barcodes at long distances.
	 */
	private void createCameraSource() {

		Context context = getApplicationContext();
		FaceDetector detector = new Builder(context).setLandmarkType(FaceDetector.ALL_LANDMARKS).setMode(FaceDetector.ACCURATE_MODE).setProminentFaceOnly(true).build();

		detector.setProcessor(new MultiProcessor.Builder<>(new GraphicFaceTrackerFactory()).build());

		if (!detector.isOperational()) {
			// Note: The first time that an app using face API is installed on a
			// device, GMS will
			// download a native library to the device in order to do detection.
			// Usually this
			// completes before the app is run for the first time. But if that
			// download has not yet
			// completed, then the above call will not detect any faces.
			//
			// isOperational() can be used to check if the required native
			// library is currently
			// available. The detector will automatically become operational
			// once the library
			// download completes on device.
			Log.w(LOG_TAG, "Face detector dependencies are not yet available.");
		}

		mCameraSource = new CustomCameraSource.Builder(context, detector).setRequestedPreviewSize(640, 480).setFacing(CameraSource.CAMERA_FACING_FRONT)
				.setRequestedFps(30.0f).setFlashMode(Camera.Parameters.FOCUS_MODE_CONTINUOUS_PICTURE).build();
	}

	/**
	 * Restarts the camera.
	 */
	@Override
	protected void onResume() {
		super.onResume();

		startCameraSource();

		Log.d(LOG_TAG, "SENSOR_ACCELEROMETER: " + accelerometer);
		Log.d(LOG_TAG, "SENSOR_PROXIMITY: " + mProximity);
		Log.d(LOG_TAG, "SENSOR_LIGHT: " + mLightSensor);

		sensorMan.registerListener(this, accelerometer, SensorManager.SENSOR_DELAY_UI);
		sensorMan.registerListener(this, mProximity, SensorManager.SENSOR_DELAY_NORMAL);
		sensorMan.registerListener(this, mLightSensor, SensorManager.SENSOR_DELAY_UI);
	}

	/**
	 * Stops the camera.
	 */
	@Override
	protected void onPause() {
		super.onPause();
		mPreview.stop();
		sensorMan.unregisterListener(this);
	}

	/**
	 * Releases the resources associated with the camera source, the associated
	 * detector, and the rest of the processing pipeline.
	 */
	@Override
	protected void onDestroy() {
		super.onDestroy();
		if (mCameraSource != null) {
			mCameraSource.release();
		}
	}

	/**
	 * Callback for the result from requesting permissions. This method is
	 * invoked for every call on {@link #requestPermissions(String[], int)}.
	 * <p>
	 * <strong>Note:</strong> It is possible that the permissions request
	 * interaction with the user is interrupted. In this case you will receive
	 * empty permissions and results arrays which should be treated as a
	 * cancellation.
	 * </p>
	 *
	 * @param requestCode
	 *            The request code passed in
	 *            {@link #requestPermissions(String[], int)}.
	 * @param permissions
	 *            The requested permissions. Never null.
	 * @param grantResults
	 *            The grant results for the corresponding permissions which is
	 *            either {@link PackageManager#PERMISSION_GRANTED} or
	 *            {@link PackageManager#PERMISSION_DENIED}. Never null.
	 * @see #requestPermissions(String[], int)
	 */
	@SuppressLint("NewApi")
	@Override
	public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
		if (requestCode != RC_HANDLE_CAMERA_PERM) {
			Log.d(LOG_TAG, "Got unexpected permission result: " + requestCode);
			super.onRequestPermissionsResult(requestCode, permissions, grantResults);
			return;
		}

		if (grantResults.length != 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
			Log.d(LOG_TAG, "Camera permission granted - initialize the camera source");
			// we have permission, so create the camerasource
			createCameraSource();
			return;
		}

		Log.e(LOG_TAG,
				"Permission not granted: results len = " + grantResults.length + " Result code = " + (grantResults.length > 0 ? grantResults[0] : "(empty)"));

		DialogInterface.OnClickListener listener = new DialogInterface.OnClickListener() {
			public void onClick(DialogInterface dialog, int id) {
				finish();
			}
		};

		AlertDialog.Builder builder = new AlertDialog.Builder(this);
		builder.setTitle("Face Tracker sample").setMessage(R.string.no_camera_permission).setPositiveButton(R.string.ok, listener).show();
	}

	/**
	 * Starts or restarts the camera source, if it exists. If the camera source
	 * doesn't exist yet (e.g., because onResume was called before the camera
	 * source was created), this will be called again when the camera source is
	 * created.
	 */
	private void startCameraSource() {

		// check that the device has play services available.
		int code = GoogleApiAvailability.getInstance().isGooglePlayServicesAvailable(getApplicationContext());
		if (code != ConnectionResult.SUCCESS) {
			Dialog dlg = GoogleApiAvailability.getInstance().getErrorDialog(this, code, RC_HANDLE_GMS);
			dlg.show();
		}

		if (mCameraSource != null) {
			try {
				mPreview.start(mCameraSource, mGraphicOverlay);
			} catch (IOException e) {
				Log.e(LOG_TAG, "Unable to start camera source.", e);
				mCameraSource.release();
				mCameraSource = null;
			}
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
	 * Factory for creating a face tracker to be associated with a new face. The
	 * multiprocessor uses this factory to create face trackers as needed -- one
	 * for each individual.
	 */
	private class GraphicFaceTrackerFactory implements MultiProcessor.Factory<Face> {
		@Override
		public Tracker<Face> create(Face face) {
			return new GraphicFaceTracker(mGraphicOverlay);
		}
	}

	/**
	 * Face tracker for each detected individual. This maintains a face graphic
	 * within the app's associated face overlay.
	 */
	private class GraphicFaceTracker extends Tracker<Face> {
		private GraphicOverlay mOverlay;

		GraphicFaceTracker(GraphicOverlay overlay) {
			mOverlay = overlay;
			mFaceGraphic = new PhotoQualityChecker(overlay);
		}

		/**
		 * Start tracking the detected face instance within the face overlay.
		 */
		@Override
		public void onNewItem(int faceId, Face item) {
			mFaceGraphic.setId(faceId);
		}

		/**
		 * Update the position/characteristics of the face within the overlay.
		 */
		@Override
		public void onUpdate(FaceDetector.Detections<Face> detectionResults, Face face) {
			mOverlay.add(mFaceGraphic);
			mFaceGraphic.updateFace(face);

			if (mFaceGraphic.passed()) {
				rating = computeEigenfaceInput(face);
				statusButton.post(new UpdateStatusButtonColor(statusButton, null));
			}
		}

		/**
		 * Hide the graphic when the corresponding face was not detected. This
		 * can happen for intermediate frames temporarily (e.g., if the face was
		 * momentarily blocked from view).
		 */
		@Override
		public void onMissing(FaceDetector.Detections<Face> detectionResults) {
			mOverlay.remove(mFaceGraphic);
		}

		/**
		 * Called when the face is assumed to be gone for good. Remove the
		 * graphic annotation from the overlay.
		 */
		@Override
		public void onDone() {
			mOverlay.remove(mFaceGraphic);
		}

		public double computeEigenfaceInput(Face face) {
			float lightQuality = mLightQuantity > 250 ? 250 : mLightQuantity;
			return ((float) face.getLandmarks().size() / 8.0);			
//			return (face.getIsLeftEyeOpenProbability() + face.getIsRightEyeOpenProbability() + (1 - face.getEulerY()) + (1 - face.getEulerZ())
//					+ (lightQuality / 250)) * ((float) face.getLandmarks().size() / 8.0) / 5;
		}
	}

	public void snapPhoto(View v) {
		if (rating >= 0 && rating <= 1 && bounds[0] >= 0 && bounds[1] >= 0) {
			if (!photoTaken && rating >= 0.80) {
				photoTaken = true;
				statusButton.setEnabled(false);
				mPreview.takePicture(mFaceGraphic.fetchBoundingRect(), mFaceGraphic.fetchCanvasSize());
			}
		}
	}

	private class UpdateStatusButtonColor implements Runnable {

		private Button button;

		private Integer mode;

		public UpdateStatusButtonColor(Button button, Integer mode) {
			super();
			this.button = button;
			this.mode = mode;
		}

		@Override
		public void run() {
			int color = Color.RED;
			String ratingTxt = "";
			boolean enabled = false;
			if (rating >= 0 && rating <= 0.39999999999999) {
				ratingTxt = "Very Poor";
				color = Color.RED;
			} else if (rating >= 0.4 && rating <= 0.49999999999999) {
				ratingTxt = "Poor";
				color = Color.RED;
			} else if (rating >= 0.5 && rating <= 0.59999999999999) {
				ratingTxt = "Fair";
				color = Color.YELLOW;
			} else if (rating >= 0.6 && rating <= 0.69999999999999) {
				ratingTxt = "Good";
				color = Color.YELLOW;
			} else if (rating >= 0.7 && rating <= 0.69999999999999) {
				ratingTxt = "Very Good";
				color = Color.GREEN;
			} else if (rating >= 0.8) {
				ratingTxt = "Snap Photo";
				color = Color.GREEN;
				enabled = mFaceGraphic.passed();
			}
			button.setText(ratingTxt);
			button.setBackgroundColor(color);
			button.setEnabled(enabled);
			mFaceGraphic.setFontColor(color);
		}

		public int computePowerMeterColor(double value) {
			return android.graphics.Color.HSVToColor(new float[] { (float) value * 120f, 1f, 1f });
		}
	}

	public void upload(File[] photos) {
		if (NetworkStatus.getInstance(FacialLoginActivity.this).isOnline(FacialLoginActivity.this)) {
			new FaceLoginTask(MainActivity.pin, photos).execute();
		} else {
			photoTaken = false;
			FacialLoginActivity.this.displayAlert("There is no connection to the server - You do not have Internet access.", "Error", false);
		}
	}

	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class FaceLoginTask extends AsyncTask<Void, Void, String> {

		private final String mPin;
		private final File[] photos;

		FaceLoginTask(String mPin, File[] photos) {
			this.mPin = mPin;
			this.photos = photos;
		}

		@Override
		protected void onPreExecute() {
			super.onPreExecute();

			progressDialog.setMessage("Working...");
			progressDialog.show();
			mPreview.stop();

		}

		@Override
		protected String doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			XMLRPCClient models;
			String msg = null;
			try {
				ArrayList<Object> methodParams = new ArrayList<>();
				methodParams.add(mPin);
				byte bytes[] = new byte[(int) photos[0].length()];
				BufferedInputStream bis = new BufferedInputStream(new FileInputStream(photos[0]));
				DataInputStream dis = new DataInputStream(bis);
				dis.readFully(bytes);
				dis.close();
				methodParams.add(Base64.encodeToString(bytes, Base64.URL_SAFE));

				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				Object val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee", "login",
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
				try {
					MainActivity.pid = Long.parseLong(msg);
					Intent intent = new Intent(FacialLoginActivity.this, MainActivity.class);
					FacialLoginActivity.this.startActivity(intent);
					finish();
				} catch (NumberFormatException e) {
					displayAlert(msg, "Error", true);
				}
			} else {
				displayAlert("Server is down; try again later.", "Error", true);
			}
			LifeDetector.initChecks();
			photoTaken = false;
		}

		@Override
		protected void onCancelled() {
			progressDialog.dismiss();
		}
	}
}
