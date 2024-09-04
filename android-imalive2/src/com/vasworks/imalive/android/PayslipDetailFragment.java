package com.vasworks.imalive.android;

import android.os.Bundle;
import android.app.ListFragment;
import android.view.View;
import android.widget.ListView;

import java.util.ArrayList;

import com.vasworks.android.util.KeyValue;
import com.vasworks.android.util.TwoLineKeyValueArrayAdapter;

/**
 * A list fragment representing a list of Payslips. This fragment also supports
 * tablet devices by allowing list items to be given an 'activated' state upon
 * selection. This helps indicate which item is currently being viewed in a
 * {@link PayslipDetailFragment}.
 * <p>
 * Activities containing this fragment MUST implement the {@link Callbacks}
 * interface.
 */
public class PayslipDetailFragment extends ListFragment {
	/**
	 * The fragment argument representing the item ID that this fragment
	 * represents.
	 */
	public static final String ARG_ITEM_ID = "item_id";
	
	/**
	 * The serialization (saved instance state) Bundle key representing the
	 * activated item position. Only used on tablets.
	 */
	private static final String STATE_ACTIVATED_POSITION = "activated_position";

	/**
	 * The current activated item position. Only used on tablets.
	 */
	private int mActivatedPosition = ListView.INVALID_POSITION;
	
	private TwoLineKeyValueArrayAdapter arrayAdapter;

	/**
	 * Mandatory empty constructor for the fragment manager to instantiate the
	 * fragment (e.g. upon screen orientation changes).
	 */
	public PayslipDetailFragment() {
	}

	@Override
	public void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);

		KeyValue dummyKv = new KeyValue("", "");
		arrayAdapter = new TwoLineKeyValueArrayAdapter(getActivity(), new KeyValue[] {dummyKv});
		setListAdapter(arrayAdapter);
	}

	@Override
	public void onViewCreated(View view, Bundle savedInstanceState) {
		super.onViewCreated(view, savedInstanceState);
	}

	@Override
	public void onSaveInstanceState(Bundle outState) {
		super.onSaveInstanceState(outState);
		if (mActivatedPosition != ListView.INVALID_POSITION) {
			// Serialize and persist the activated item position.
			outState.putInt(STATE_ACTIVATED_POSITION, mActivatedPosition);
		}
	}
}
