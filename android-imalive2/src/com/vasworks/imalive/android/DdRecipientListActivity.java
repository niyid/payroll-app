package com.vasworks.imalive.android;

import java.net.MalformedURLException;
import java.net.URL;
import java.text.NumberFormat;
import java.util.ArrayList;
import java.util.Currency;
import java.util.Locale;

import com.vasworks.android.util.KeyValue;
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
import android.widget.ArrayAdapter;
import android.widget.BaseAdapter;

/**
 * An activity representing a single Payslip detail screen. This activity is
 * only used on handset devices. On tablet-size devices, item details are
 * presented side-by-side with a list of items in a {@link PayslipListActivity}.
 * <p>
 * This activity is mostly just a 'shell' activity containing nothing more than
 * a {@link PayslipDetailFragment}.
 */
public class DdRecipientListActivity extends AppCompatActivity implements DdRecipientListFragment.Callbacks {

	public static final String LOG_TAG = "DdRecipientListActivity";
	
	private DdRecipientListTask mRecipientListTask;
	private View mProgressView;
	private DdRecipientListFragment mRecipientList;
	private ArrayList<KeyValue> recipientItems = new ArrayList<>();
	private String selectedItemId;
	private NumberFormat format = NumberFormat.getCurrencyInstance(Locale.getDefault());

	@Override
	protected void onCreate(Bundle savedInstanceState) {
		super.onCreate(savedInstanceState);
		setContentView(R.layout.activity_recipient_list);

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
		mRecipientList = (DdRecipientListFragment) getFragmentManager().findFragmentById(R.id.recipient_list);

		mProgressView = findViewById(R.id.recipient_list_progress);
		mRecipientListTask = new DdRecipientListTask(this);
		mRecipientListTask.execute((Void) null);
		Log.i(LOG_TAG, "Payslips Items=" + recipientItems);		
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
	public class DdRecipientListTask extends AsyncTask<Void, Void, String> {
		
		private DdRecipientListActivity activity;

		public DdRecipientListTask(DdRecipientListActivity activity) {
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
				ArrayList<Object> methodParams = new ArrayList<>();
				methodParams.add(MainActivity.pid);
				methodParams.add("imalive_pension_ddebit_recipient");
				
				models = new XMLRPCClient(new URL(String.format("%s/xmlrpc/2/object", MainActivity.url)));
				Object val = models.call("execute_kw", MainActivity.db, MainActivity.userId, MainActivity.password, "hr.employee",
						"list_pensioner_items", methodParams.toArray());

				recipientItems.clear();
				Log.i(LOG_TAG, "Return val=" + val);
				try {
					Object[] data = (Object[]) val;
					Object[] item;
					for (Object d : data) {
						item = (Object[]) d;
						Log.i(LOG_TAG, "ID=" + item[0] + ", NAME=" + item[1]);
						Log.i(LOG_TAG, "--------------------------------");
						recipientItems.add(new KeyValue(item[0].toString(), item[1].toString()));
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
			mRecipientListTask = null;
			mProgressView.setVisibility(View.GONE);
			
			mRecipientList.setListAdapter(new ArrayAdapter<>(activity, android.R.layout.simple_list_item_1, recipientItems.toArray(new KeyValue[recipientItems.size()])));
			((BaseAdapter) mRecipientList.getListAdapter()).notifyDataSetChanged();
		}

		@Override
		protected void onCancelled() {
			mRecipientListTask = null;
			mProgressView.setVisibility(View.GONE);
		}
	}

	@Override
	public void onItemSelected(String id) {
		Log.i(LOG_TAG, "Selected ID=" + id);
		
	}
}
