package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;

import com.vasworks.xmlrpc.XMLRPCClient;
import com.vasworks.xmlrpc.XMLRPCException;

import android.content.Intent;
import android.os.AsyncTask;
import android.os.Bundle;
import android.support.v4.app.NavUtils;
import android.support.v7.app.AppCompatActivity;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.BaseAdapter;

/**
 * An activity representing a list of Payslips. This activity has different
 * presentations for handset and tablet-size devices. On handsets, the activity
 * presents a list of items, which when touched, lead to a
 * {@link PayslipDetailActivity} representing item details. On tablets, the
 * activity presents the list of items and item details side-by-side using two
 * vertical panes.
 * <p>
 * The activity makes heavy use of fragments. The list of items is a
 * {@link PayslipListFragment} and the item details (if present) is a
 * {@link PayslipDetailFragment}.
 * <p>
 * This activity also implements the required
 * {@link PayslipListFragment.Callbacks} interface to listen for item
 * selections.
 */
public class PayslipListActivity extends AppCompatActivity implements PayslipListFragment.Callbacks {

	public static final String LOG_TAG = "PayslipListActivity";

	private PayslipListTask mPayslipListTask = null;
	private View mProgressView;
	private PayslipListFragment mPayslipList;
	private ArrayList<String[]> payslipData = new ArrayList<>();

	/**
	 * Whether or not the activity is in two-pane mode, i.e. running on a tablet
	 * device.
	 */
	private boolean mTwoPane;

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_payslip_list);
		// Show the Up button in the action bar.
		getSupportActionBar().setDisplayHomeAsUpEnabled(true);

		if (findViewById(R.id.payslip_detail_container) != null) {
			// The detail container view will be present only in the
			// large-screen layouts (res/values-large and
			// res/values-sw600dp). If this view is present, then the
			// activity should be in two-pane mode.
			mTwoPane = true;
		}
		// In two-pane mode, list items should be given the
		// 'activated' state when touched.
		mPayslipList = (PayslipListFragment) getFragmentManager().findFragmentById(R.id.payslip_list);

		mProgressView = findViewById(R.id.payslip_list_progress);
		mPayslipListTask = new PayslipListTask();
		mPayslipListTask.execute((Void) null);
		Log.i(LOG_TAG, "Payslips=" + payslipData);
	}

	@Override
	public boolean onOptionsItemSelected(MenuItem item) {
		int id = item.getItemId();
		if (id == android.R.id.home) {
			// This ID represents the Home or Up button. In the case of this
			// activity, the Up button is shown. Use NavUtils to allow users
			// to navigate up one level in the application structure. For
			// more details, see the Navigation pattern on Android Design:
			//
			// http://developer.android.com/design/patterns/navigation.html#up-vs-back
			//
			NavUtils.navigateUpFromSameTask(this);
			return true;
		}
		return super.onOptionsItemSelected(item);
	}

	/**
	 * Callback method from {@link PayslipListFragment.Callbacks} indicating
	 * that the item with the given ID was selected.
	 */
	@Override
	public void onItemSelected(String id) {
		Log.i(LOG_TAG, "Selected ID=" + id);

	}

	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class PayslipListTask extends AsyncTask<Void, Void, String> {

		@Override
		protected String doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			mProgressView.setVisibility(View.VISIBLE);
			XMLRPCClient models;
			String msg = null;
			try {
				ArrayList<Object> methodParams = new ArrayList<>();
				methodParams.add(MainActivity.pid);
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				Object val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
						"list_payslip_items", methodParams);

				payslipData.clear();
				Log.i(LOG_TAG, "Return val=" + val);
				try {
					Object[] data = (Object[]) val;
					Object[] item;
					for (Object d : data) {
						item = (Object[]) d;
						Log.i(LOG_TAG, "ID=" + item[0] + ", NAME=" + item[1]);
						Log.i(LOG_TAG, "--------------------------------");
						payslipData.add(new String[] { item[0].toString(), item[1].toString() });
					}
				} catch (Exception e) {
					Log.e(LOG_TAG, e.getMessage());
					e.printStackTrace();
					msg = e.getMessage();
				}
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
			mPayslipListTask = null;
			mProgressView.setVisibility(View.GONE);
			
			mPayslipList.setPayslipData(payslipData);
			((BaseAdapter) mPayslipList.getListAdapter()).notifyDataSetChanged();
		}

		@Override
		protected void onCancelled() {
			mPayslipListTask = null;
			mProgressView.setVisibility(View.GONE);
		}
	}

}
