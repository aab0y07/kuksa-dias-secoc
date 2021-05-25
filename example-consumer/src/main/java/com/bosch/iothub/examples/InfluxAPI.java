package com.bosch.iothub.examples;

import java.util.concurrent.TimeUnit;

import org.influxdb.InfluxDB;
import org.influxdb.dto.Point;

public class InfluxAPI {
	
	public void writeMetricDataUnderHost(InfluxDB influxDB, String metric, String value) {
			influxDB.write(Point.measurement(metric)
				    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
				    //.tag("host", host)
				    .addField("SignalValue", value)
				    .build());
	}
}

