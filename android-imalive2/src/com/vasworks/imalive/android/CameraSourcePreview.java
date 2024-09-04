/*
 * Copyright (C) The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.vasworks.imalive.android;

import java.io.ByteArrayInputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.Arrays;

import com.google.android.gms.common.images.Size;
import com.google.android.gms.vision.CameraSource;
import com.google.android.gms.vision.CameraSource.PictureCallback;
import com.google.android.gms.vision.CameraSource.ShutterCallback;
import com.google.android.gms.vision.face.FaceDetector;
import com.vasworks.android.util.FaceCropper;

import android.app.Activity;
import android.content.Context;
import android.content.res.Configuration;
import android.graphics.Bitmap;
import android.graphics.Bitmap.CompressFormat;
import android.graphics.BitmapFactory;
import android.graphics.Matrix;
import android.os.Build;
import android.os.Environment;
import android.util.AttributeSet;
import android.util.DisplayMetrics;
import android.util.Log;
import android.view.Display;
import android.view.SurfaceHolder;
import android.view.SurfaceView;
import android.view.ViewGroup;
import android.view.WindowManager;

public class CameraSourcePreview extends ViewGroup {
	private static final String LOG_TAG = "CameraSourcePreview";

	private Context mContext;
	private SurfaceView mSurfaceView;
	private volatile boolean mStartRequested;
	private volatile boolean mSurfaceAvailable;
	private CameraSource mCameraSource;
	private FaceCropper mFaceCropper = new FaceCropper();
	private BitmapFactory.Options bitmapLoadingOptions = new BitmapFactory.Options();

	private GraphicOverlay mOverlay;

	private File[] photos = new File[1];

	public CameraSourcePreview(Context context, AttributeSet attrs) {
		super(context, attrs);
		mContext = context;
		mStartRequested = false;
		mSurfaceAvailable = false;

		mSurfaceView = new SurfaceView(context);
		mSurfaceView.getHolder().addCallback(new SurfaceCallback());
		addView(mSurfaceView);
		bitmapLoadingOptions.inPreferredConfig = Bitmap.Config.RGB_565;
	}

	public void start(CameraSource cameraSource) throws IOException {
		if (cameraSource == null) {
			stop();
		}

		mCameraSource = cameraSource;

		if (mCameraSource != null) {
			mStartRequested = true;
			startIfReady();
		}
	}

	public void start(CameraSource cameraSource, GraphicOverlay overlay) throws IOException {
		mOverlay = overlay;
		start(cameraSource);
	}

	public void stop() {
		if (mCameraSource != null) {
			mCameraSource.stop();
		}
	}

	public void release() {
		if (mCameraSource != null) {
			mCameraSource.release();
			mCameraSource = null;
		}
	}

	private static Bitmap rotateImage(Bitmap img, int degree) {
		Matrix matrix = new Matrix();
		matrix.postRotate(degree);
		Bitmap rotatedImg = Bitmap.createBitmap(img, 0, 0, img.getWidth(), img.getHeight(), matrix, true);
		img.recycle();
		return rotatedImg;
	}

	public void takePicture(final int[] boundingRect, final int[] canvasSize) {
		if (mCameraSource != null) {
			ShutterCallback shutter = new ShutterCallback() {

				@Override
				public void onShutter() {
					// TODO Auto-generated method stub

				}
			};

			PictureCallback jpeg = new PictureCallback() {

				@Override
				public void onPictureTaken(byte[] data) {
					Bitmap wholePhoto = BitmapFactory.decodeStream(new ByteArrayInputStream(data),null,bitmapLoadingOptions);

					Log.i(LOG_TAG, "Bounds: " + Arrays.toString(boundingRect));
					
					Log.i(LOG_TAG, "Device: " + getDeviceName());
					
					if(getDeviceName().contains("Samsung")) {
			        	wholePhoto = rotateImage(wholePhoto, -90);
					}

					WindowManager w = ((Activity) mContext).getWindowManager();
					Display d = w.getDefaultDisplay();
					DisplayMetrics metrics = new DisplayMetrics();
					d.getMetrics(metrics);
					int xBuffer = 50 * wholePhoto.getWidth() / 1920;
					int yBuffer = 250 * wholePhoto.getHeight() / 2560;
					int heightBuffer = 200 * wholePhoto.getHeight() / 2560;
					Log.i(LOG_TAG, "Screen Size: w=" + metrics.widthPixels + ", h=" + metrics.heightPixels + " density=" + getContext().getResources().getDisplayMetrics().density);
					Log.i(LOG_TAG, "Whole: w=" + wholePhoto.getWidth() + " h=" + wholePhoto.getHeight());
					int cropX = (int) Math.floor(boundingRect[0] * wholePhoto.getWidth() / metrics.widthPixels) + xBuffer;
					int cropY = (int) Math.floor(boundingRect[1] * wholePhoto.getHeight() / metrics.heightPixels) + yBuffer;
					int cropWidth = (int) Math.floor(boundingRect[2] * wholePhoto.getWidth() / metrics.widthPixels);
					int cropHeight = (int) Math.floor(boundingRect[3] * wholePhoto.getHeight() / metrics.heightPixels) + heightBuffer;
					Bitmap croppedBmp = Bitmap.createBitmap(wholePhoto, cropX, cropY, cropWidth, cropHeight);
					double scale = Double.valueOf(croppedBmp.getHeight()) / Double.valueOf(croppedBmp.getWidth());
					double width = 400;
					double height = 400 * scale;

					saveToFile(getSavePath(), "face.png", Bitmap.createScaledBitmap(croppedBmp, (int) Math.floor(width), (int) Math.floor(height), true));
					((PhotoUploader) mContext).upload(photos);
				}
			};
			mCameraSource.takePicture(shutter, jpeg);
		}
	}

	public void saveToFile(File path, String filename, Bitmap bmp) {
		try {
			Log.i(LOG_TAG, "Path=" + path.getAbsolutePath());
			File file = new File(path.getAbsolutePath() + "/" + filename);
			photos[0] = file;
			FileOutputStream out = new FileOutputStream(file);
			bmp.compress(CompressFormat.PNG, 100, out);
			out.flush();
			out.close();
		} catch (Exception e) {
			e.printStackTrace();
		}
	}

	public boolean hasSDCard() {
		String status = Environment.getExternalStorageState();
		return status.equals(Environment.MEDIA_MOUNTED);
	}

	public String getSDCardPath() {
		File path = Environment.getExternalStorageDirectory();
		return path.getAbsolutePath();
	}

	public File getSavePath() {
		return mContext.getCacheDir();
	}

	private void startIfReady() throws IOException {
		if (mStartRequested && mSurfaceAvailable) {
			mCameraSource.start(mSurfaceView.getHolder());
			if (mOverlay != null) {
				Size size = mCameraSource.getPreviewSize();
				int min = Math.min(size.getWidth(), size.getHeight());
				int max = Math.max(size.getWidth(), size.getHeight());
				if (isPortraitMode()) {
					// Swap width and height sizes when in portrait, since it
					// will be rotated by
					// 90 degrees
					mOverlay.setCameraInfo(min, max, mCameraSource.getCameraFacing());
				} else {
					mOverlay.setCameraInfo(max, min, mCameraSource.getCameraFacing());
				}
				mOverlay.clear();
			}
			mStartRequested = false;
		}
	}

	private class SurfaceCallback implements SurfaceHolder.Callback {
		@Override
		public void surfaceCreated(SurfaceHolder surface) {
			mSurfaceAvailable = true;
			try {
				startIfReady();
			} catch (IOException e) {
				Log.e(LOG_TAG, "Could not start camera source.", e);
			}
		}

		@Override
		public void surfaceDestroyed(SurfaceHolder surface) {
			mSurfaceAvailable = false;
		}

		@Override
		public void surfaceChanged(SurfaceHolder holder, int format, int width, int height) {
		}
	}

	@Override
	protected void onLayout(boolean changed, int left, int top, int right, int bottom) {
		int width = 320;
		int height = 240;
		if (mCameraSource != null) {
			Size size = mCameraSource.getPreviewSize();
			if (size != null) {
				width = size.getWidth();
				height = size.getHeight();
			}
		}

		// Swap width and height sizes when in portrait, since it will be
		// rotated 90 degrees
		if (isPortraitMode()) {
			int tmp = width;
			width = height;
			height = tmp;
		}

		final int layoutWidth = right - left;
		final int layoutHeight = bottom - top;

		// Computes height and width for potentially doing fit width.
		int childWidth = layoutWidth;
		int childHeight = (int) (((float) layoutWidth / (float) width) * height);

		// If height is too tall using fit width, does fit height instead.
		if (childHeight > layoutHeight) {
			childHeight = layoutHeight;
			childWidth = (int) (((float) layoutHeight / (float) height) * width);
		}

		for (int i = 0; i < getChildCount(); ++i) {
			getChildAt(i).layout(0, 0, childWidth, childHeight);
		}

		try {
			startIfReady();
		} catch (IOException e) {
			Log.e(LOG_TAG, "Could not start camera source.", e);
		}
	}
	
	public String getDeviceName() {
	    String manufacturer = Build.MANUFACTURER;
	    String model = Build.MODEL;
	    if (model.startsWith(manufacturer)) {
	        return capitalize(model);
	    } else {
	        return capitalize(manufacturer) + " " + model;
	    }
	}

	private String capitalize(String s) {
	    if (s == null || s.length() == 0) {
	        return "";
	    }
	    char first = s.charAt(0);
	    if (Character.isUpperCase(first)) {
	        return s;
	    } else {
	        return Character.toUpperCase(first) + s.substring(1);
	    }
	}
	
	private boolean isPortraitMode() {
		int orientation = mContext.getResources().getConfiguration().orientation;
		if (orientation == Configuration.ORIENTATION_LANDSCAPE) {
			return false;
		}
		if (orientation == Configuration.ORIENTATION_PORTRAIT) {
			return true;
		}

		Log.d(LOG_TAG, "isPortraitMode returning false by default");
		return false;
	}

	public File[] getPhotos() {
		return photos;
	}
}
