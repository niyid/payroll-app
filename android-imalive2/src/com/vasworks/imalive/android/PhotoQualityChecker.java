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

import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.graphics.PorterDuff;
import android.graphics.Typeface;
import android.util.Log;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import com.google.android.gms.appdatasearch.GetRecentContextCall.Response;
import com.google.android.gms.vision.face.Face;

/**
 * Graphic instance for rendering face position, orientation, and landmarks within an associated
 * graphic overlay view.
 */
class PhotoQualityChecker extends GraphicOverlay.Graphic {
	private static final String LOG_TAG = "PhotoQualityChecker";
	
    private static final float FACE_POSITION_RADIUS = 10.0f;
    private static final float ID_TEXT_SIZE = 40.0f;
    private static final float ID_Y_OFFSET = 50.0f;
    private static final float ID_X_OFFSET = -50.0f;
    private static final float BOX_STROKE_WIDTH = 5.0f;
    private static final float RADIUS = 10.0f;
    private int[] canvasSize = new int[2];

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
    private volatile int mBlinkedTwice = 2;

    PhotoQualityChecker(GraphicOverlay overlay) {
        super(overlay);
        mFacePositionPaint = new Paint();

        mIdPaint = new Paint();
        mIdPaint.setTextSize(ID_TEXT_SIZE);

        mBoxPaint = new Paint();
        mBoxPaint.setStyle(Paint.Style.STROKE);
        mBoxPaint.setStrokeWidth(BOX_STROKE_WIDTH);
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
		canvas.drawText("Straight face", x - ID_X_OFFSET - 270, y - ID_Y_OFFSET + 100, mIdPaint);
		
		boolean blink = face.getIsLeftEyeOpenProbability() < 0.25 || face.getIsRightEyeOpenProbability() < 0.25;
		if(blink && mBlinkedTwice > 0) {
			mBlinkedTwice -= 1;
		}

		// Draws a bounding box around the face.
		float xTopOffset = scaleX(face.getWidth() * 0.5f);
		float yTopOffset = scaleY(face.getHeight() * 0.4f);
		float xBottomOffset = scaleX(face.getWidth() * 0.5f);
		float yBottomOffset = scaleY(face.getHeight() * 0.6f);
		left = x - xTopOffset;
		top = y - yTopOffset;
		right = x + xBottomOffset;
		bottom = y + yBottomOffset;
//		canvas.drawRect(left, top, right, bottom, mBoxPaint);

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
		auxCanvas.drawRect(new RectF(0, 0, bitmap.getWidth(), bitmap.getHeight()), paint);

		// finally, draw the whole thing to the original canvas
		canvas.drawBitmap(bitmap, 0, 0, paint);		
    }
    
    public int[] fetchCanvasSize() {
    	return canvasSize;
    }
    
    public int[] fetchBoundingRect() {
//    	return new int[]{(int) left, (int) top, (int) (right - left), (int) (bottom - top)};
    	return new int[]{(int) scaleX(mFace.getPosition().x), (int) scaleY(mFace.getPosition().y), (int) scaleX(mFace.getWidth()), (int) scaleY(mFace.getHeight())};
    }
    
    public boolean passed() {
    	return mBlinkedTwice == 0;
    }
}
