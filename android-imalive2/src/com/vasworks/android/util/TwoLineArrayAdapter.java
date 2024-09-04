package com.vasworks.android.util;

import com.vasworks.imalive.android.R.id;
import com.vasworks.imalive.android.R.layout;

import android.content.Context;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.TextView;

public abstract class TwoLineArrayAdapter<T> extends ArrayAdapter<T> {
    private int mListItemLayoutResId;

    public TwoLineArrayAdapter(Context context, T[] ts) {
        this(context, layout.detail_row, ts);
    }

    public TwoLineArrayAdapter(
            Context context, 
            int listItemLayoutResourceId,
            T[] ts) {
        super(context, listItemLayoutResourceId, ts);
        mListItemLayoutResId = listItemLayoutResourceId;
    }

    @Override
    public android.view.View getView(
            int position, 
            View convertView,
            ViewGroup parent) {


        LayoutInflater inflater = (LayoutInflater)getContext()
            .getSystemService(Context.LAYOUT_INFLATER_SERVICE);

        View listItemView = convertView;
        if (null == convertView) { 
            listItemView = inflater.inflate(
                mListItemLayoutResId, 
                parent, 
                false);
        }

        // The ListItemLayout must use the standard text item IDs.
        TextView lineOneView = (TextView)listItemView.findViewById(
            id.description);
        TextView lineTwoView = (TextView)listItemView.findViewById(
            id.amount);

        T t = (T)getItem(position); 
        lineOneView.setText(lineOneText(t));
        lineTwoView.setText(lineTwoText(t));

        return listItemView;
    }

    public abstract String lineOneText(T t);

    public abstract String lineTwoText(T t);
}