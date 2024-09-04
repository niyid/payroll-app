package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Currency;
import java.util.List;
import java.util.Locale;

import com.vasworks.android.util.KeyValue;
import com.vasworks.android.util.TwoLineKeyValueArrayAdapter;
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
 * An activity representing a single Payslip detail screen. This activity is
 * only used on handset devices. On tablet-size devices, item details are
 * presented side-by-side with a list of items in a {@link PayslipListActivity}.
 * <p>
 * This activity is mostly just a 'shell' activity containing nothing more than
 * a {@link PayslipDetailFragment}.
 */
public class PayslipDetailActivity extends AppCompatActivity {

	public static final String LOG_TAG = "PayslipDetailActivity";
	
	private PayslipDetailTask mPayslipDetailTask;
	private View mProgressView;
	private PayslipDetailFragment mPayslipDetail;
	private ArrayList<String[]> payslipItems = new ArrayList<>();
	private String selectedItemId;
	private NumberFormat format = NumberFormat.getCurrencyInstance(Locale.getDefault());

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_payslip_detail2);

		format.setCurrency(Currency.getInstance("NGN"));

		// Show the Up button in the action bar.
		getSupportActionBar().setDisplayHomeAsUpEnabled(true);

		// savedInstanceState is non-null when there is fragment state
		// saved from previous configurations of this activity
		// (e.g. when rotating the screen from portrait to landscape).
		// In this case, the fragment will automatically be re-added
		// to its container so we don't need to manually add it.
		// For more information, see the Fragments API guide at:
		//
		// http://developer.android.com/guide/components/fragments.html
		//
		selectedItemId = getIntent().getStringExtra(PayslipDetailFragment.ARG_ITEM_ID);
		if (savedInstanceState == null) {
			// Create the detail fragment and add it to the activity
			// using a fragment transaction.
			Bundle arguments = new Bundle();
			arguments.putString(PayslipDetailFragment.ARG_ITEM_ID, selectedItemId);
			PayslipDetailFragment fragment = new PayslipDetailFragment();
			fragment.setArguments(arguments);
//			getFragmentManager().beginTransaction().add(R.id.payslip_detail_container, fragment).commit();
		}

		// In two-pane mode, list items should be given the
		// 'activated' state when touched.
		mPayslipDetail = (PayslipDetailFragment) getFragmentManager().findFragmentById(R.id.payslip_detail);

		mProgressView = findViewById(R.id.payslip_detail_progress);
		mPayslipDetailTask = new PayslipDetailTask(this);
		mPayslipDetailTask.execute((Void) null);
		Log.i(LOG_TAG, "Payslips Items=" + payslipItems);		
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
			NavUtils.navigateUpTo(this, new Intent(this, PayslipListActivity.class));
			return true;
		}
		return super.onOptionsItemSelected(item);
	}

	/**
	 * Represents an asynchronous login/registration task used to authenticate
	 * the user.
	 */
	public class PayslipDetailTask extends AsyncTask<Void, Void, String> {
		
		private PayslipDetailActivity activity;

		public PayslipDetailTask(PayslipDetailActivity activity) {
			super();
			this.activity = activity;
		}

		@Override
		protected String doInBackground(Void... params) {
			// TODO: attempt authentication against a network service.
			mProgressView.setVisibility(View.VISIBLE);
			XMLRPCClient models;
			String msg = null;
			try {
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				Object val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
						"list_payslip_items", new Long[]{MainActivity.pid});

				payslipItems.clear();
				Log.i(LOG_TAG, "Return val=" + val);
				try {
					Object[] data = (Object[]) val;
					Object[] item;
					for (Object d : data) {
						item = (Object[]) d;
						Log.i(LOG_TAG, "ID=" + item[0] + ", NAME=" + item[1]);
						Log.i(LOG_TAG, "--------------------------------");
						payslipItems.add(new String[] { item[0].toString(), format.format(Double.valueOf(item[1].toString())) });
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
			mPayslipDetailTask = null;
			mProgressView.setVisibility(View.GONE);
			
			List<KeyValue> pairs = new ArrayList<>();
			for(String[] item : payslipItems) {
				pairs.add(new KeyValue(item[0], item[1]));
			}
			
			mPayslipDetail.setListAdapter(new TwoLineKeyValueArrayAdapter(activity, pairs.toArray(new KeyValue[pairs.size()])));
			((BaseAdapter) mPayslipDetail.getListAdapter()).notifyDataSetChanged();
		}

		@Override
		protected void onCancelled() {
			mPayslipDetailTask = null;
			mProgressView.setVisibility(View.GONE);
		}
	}
}
