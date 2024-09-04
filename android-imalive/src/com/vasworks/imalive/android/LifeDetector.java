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

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.graphics.Typeface;
import android.util.Log;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.google.android.gms.appdatasearch.GetRecentContextCall.Response;
import com.google.android.gms.vision.face.Face;
import com.google.android.gms.vision.face.Landmark;
import com.vasworks.android.util.PollingNotifierTimerTask;

/**
 * Graphic instance for rendering face position, orientation, and landmarks within an associated
 * graphic overlay view.
 */
class LifeDetector extends GraphicOverlay.Graphic {
	private static final String LOG_TAG = "LifeDetector";
	
    private static final float FACE_POSITION_RADIUS = 10.0f;
    private static final float ID_TEXT_SIZE = 40.0f;
    private static final float ID_Y_OFFSET = 50.0f;
    private static final float ID_X_OFFSET = -50.0f;
    private static final float BOX_STROKE_WIDTH = 5.0f;
    private static final float RADIUS = 10.0f;
    private int[] canvasSize = new int[2];
    
    public static final int TEST_COUNT = 8;

    private static final int COLOR_CHOICES[] = {
        Color.GREEN,
        Color.RED,
        Color.YELLOW
    };

    private Paint mFacePositionPaint;
    private Paint mIdPaint;
    private Paint mBoxPaint;

    private volatile float left;
    private volatile float top;
    private volatile float right;
    private volatile float bottom;
    private volatile Face mFace;
    private int mFaceId;
    private volatile float mFaceHappiness;
	private static List<String> instructions = new ArrayList<>(TEST_COUNT);
	private static List<Boolean> responses = new ArrayList<>(TEST_COUNT);
	private static int idx = 0;
	private volatile int cx;
	private volatile int cy;
	private Paint landmarkPaint;
	
	static {
        initChecks();
	}

    LifeDetector(GraphicOverlay overlay) {
        super(overlay);
        mFacePositionPaint = new Paint();

        mIdPaint = new Paint();
        mIdPaint.setTextSize(ID_TEXT_SIZE);
        mIdPaint.setColor(Color.RED);

        mBoxPaint = new Paint();
        mBoxPaint.setStyle(Paint.Style.STROKE);
        mBoxPaint.setStrokeWidth(BOX_STROKE_WIDTH);

        landmarkPaint = new Paint();
        landmarkPaint.setStyle(Paint.Style.STROKE);
        landmarkPaint.setColor(Color.GREEN);
    }
    
    void setFontColor(int color) {
    	mFacePositionPaint.setColor(color);
    	mIdPaint.setColor(color);
    	mBoxPaint.setColor(color);
    }

    void setId(int id) {
        mFaceId = id;
    }

    /**
     * Updates the face instance from the detection of the most recent frame.  Invalidates the
     * relevant portions of the overlay to trigger a redraw.
     */
    void updateFace(Face face) {
        mFace = face;
        postInvalidate();
    }

    /**
     * Draws the face annotations for position on the supplied canvas.
     */
    @Override
    public void draw(Canvas canvas) {
    	canvasSize[0] = canvas.getWidth();
    	canvasSize[1] = canvas.getHeight();
    	Log.i(LOG_TAG, "Canvas: w=" + canvas.getWidth() + " h=" + canvas.getHeight());
        Face face = mFace;
        if (face == null) {
            return;
        }

        // Draws a circle at the position of the detected face, with the face's track id below.
        float x = translateX(face.getPosition().x + face.getWidth() / 2);
        float y = translateY(face.getPosition().y + face.getHeight() / 2);
//        canvas.drawCircle(x, y, FACE_POSITION_RADIUS, mFacePositionPaint);
//        canvas.drawText("id: " + mFaceId, x + ID_X_OFFSET, y + ID_Y_OFFSET, mIdPaint);
//        canvas.drawText("hapo: " + String.format("%.2f %.2f %.2f", face.getIsSmilingProbability(), face.getEulerY(), face.getEulerZ()), x - ID_X_OFFSET, y - ID_Y_OFFSET, mIdPaint);
//        canvas.drawText("eye2: " + String.format("%.2f", face.getIsRightEyeOpenProbability()), x + ID_X_OFFSET * 2, y + ID_Y_OFFSET * 2, mIdPaint);
//        canvas.drawText("eye1: " + String.format("%.2f", face.getIsLeftEyeOpenProbability()), x - ID_X_OFFSET*2, y - ID_Y_OFFSET*2, mIdPaint);

		mIdPaint.setTextSize(80f);
//		canvas.drawText(LifeProofActivity.instructions.get(LifeProofActivity.currentMode), x - ID_X_OFFSET - 150, y - ID_Y_OFFSET, mIdPaint);
		String txt = "";
		int size = face.getLandmarks().size();
		if(idx < TEST_COUNT) {
			StringBuilder b = new StringBuilder(String.valueOf(idx));
			b.append(") ");
			b.append(instructions.get(idx));
			b.append(" ONLY");
			txt = b.toString();
			canvas.drawText(txt, x - ID_X_OFFSET - 270, y - ID_Y_OFFSET + 100, mIdPaint);
			
			boolean blink = face.getIsLeftEyeOpenProbability() < 0.25 || face.getIsRightEyeOpenProbability() < 0.25;
			boolean smile = face.getIsSmilingProbability() > 0.5;
			if(LifeProofActivity.timerTask.getTime() > 2000 && ("Smile".equals(instructions.get(idx)) && smile && !blink) || ("Blink".equals(instructions.get(idx)) && blink && !smile)) {
				responses.add(true);
				
				Context context = LifeProofActivity.timerTask.getContext();
				LifeProofActivity.timerTask.end();
				LifeProofActivity.timerTask = new PollingNotifierTimerTask(context);
				LifeProofActivity.timerTask.schedule();

				idx++;
			}
		} else {
			if(LifeProofActivity.timerTask != null) {
				LifeProofActivity.timerTask.end();
			}
			if(size < 3) {
				txt = "More LIGHT!";
			}
			else if(size >= 3 && size < 5) {
				txt = "Even More LIGHT!";
			}
			else if(size >= 5 && size < 7) {
				txt = "A bit more LIGHT!";
			} else {
				txt = "Steady & snap!";
			}
			canvas.drawText(txt, x - ID_X_OFFSET - 270, y - ID_Y_OFFSET + 100, mIdPaint);

			// Draws a bounding box around the face.
			float xTopOffset = scaleX(face.getWidth() * 0.5f);
			float yTopOffset = scaleY(face.getHeight() * 0.4f);
			float xBottomOffset = scaleX(face.getWidth() * 0.5f);
			float yBottomOffset = scaleY(face.getHeight() * 0.6f);
			left = x - xTopOffset;
			top = y - yTopOffset;
			right = x + xBottomOffset;
			bottom = y + yBottomOffset;
			
			for (Landmark landmark : face.getLandmarks()) {
				cx = (int) scaleX(landmark.getPosition().x);
				cy = (int) scaleY(landmark.getPosition().y);
				canvas.drawCircle(cx, cy, 10, landmarkPaint);
			}

			// same constants as above except innerRectFillColor is not used. Instead:
			int outerFillColor = 0xCC000000;
			
			// first create an off-screen bitmap and its canvas
			Bitmap bitmap = Bitmap.createBitmap(canvas.getWidth(), canvas.getHeight(), Bitmap.Config.ARGB_8888);
			Canvas auxCanvas = new Canvas(bitmap);

			// then fill the bitmap with the desired outside color
			Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
			paint.setColor(outerFillColor);
			paint.setStyle(Paint.Style.FILL);
			auxCanvas.drawPaint(paint);

			// then punch a transparent hole in the shape of the rect
			paint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.CLEAR));
			auxCanvas.drawRoundRect(new RectF(left, top, right, bottom), RADIUS, RADIUS, paint);

			// then draw the white rect border (being sure to get rid of the xfer mode!)
			paint.setXfermode(null);
			paint.setColor(Color.WHITE);
			paint.setStyle(Paint.Style.STROKE);
			auxCanvas.drawRoundRect(new RectF(0, 0, bitmap.getWidth(), bitmap.getHeight()), RADIUS, RADIUS, paint);

			// finally, draw the whole thing to the original canvas
			canvas.drawBitmap(bitmap, 0, 0, paint);					
		}
    }
    
    public int[] fetchCanvasSize() {
    	return canvasSize;
    }
    
    public int[] fetchBoundingRect() {
//    	return new int[]{(int) left, (int) top, (int) (right - left), (int) (bottom - top)};
    	return new int[]{(int) scaleX(mFace.getPosition().x), (int) scaleY(mFace.getPosition().y), (int) scaleX(mFace.getWidth()), (int) scaleY(mFace.getHeight())};
    }
    
    public boolean passed() {
		return responses.size() == TEST_COUNT;
    }
    
    public static void initChecks() {
    	instructions.clear();
        for(int i = 0; i < TEST_COUNT; i++) {
        	if(Math.random() < 0.5) {
        		instructions.add("Blink");
        	} else {
        		instructions.add("Smile");
        	}
        }
        responses.clear();
        idx = 0;
    }
    
    public static int getIdx() {
    	return idx;
    }
}
