package com.vasworks.android.util;

import android.content.Context;

/**
 * Key and Value Array Adapter
 * 
 * @param <T>
 */
public class TwoLineKeyValueArrayAdapter extends TwoLineArrayAdapter<KeyValue> {
    
    public TwoLineKeyValueArrayAdapter(Context context, KeyValue[] pairs) {
        super(context, pairs);
    }

    @Override
    public String lineOneText(KeyValue e) {
        return e.key;
    }

    @Override
    public String lineTwoText(KeyValue e) {
        return e.value;
    }
}