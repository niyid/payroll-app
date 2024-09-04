package com.vasworks.imalive.android;

import android.app.Application;

import org.acra.ACRA;
import org.acra.annotation.ReportsCrashes;
import org.acra.sender.HttpSender;

@ReportsCrashes(
	    httpMethod = HttpSender.Method.PUT,
	    reportType = HttpSender.Type.JSON,
//	    formUri = "http://192.168.43.99:5984/acra-myapp/_design/acra-storage/_update/report",
	    formUri = "http://acra-fb8fd1.smileupps.com/acra-myapp-54d26f/_design/acra-storage/_update/report",
	    formUriBasicAuthLogin = "reporter",
	    formUriBasicAuthPassword = "passw0rd123"
	)
public class MainApplication extends Application {
    @Override
    public void onCreate() {
        super.onCreate();
        ACRA.init(this);
    }

}
