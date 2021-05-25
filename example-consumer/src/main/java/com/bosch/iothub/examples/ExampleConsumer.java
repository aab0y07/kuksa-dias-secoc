/*
 * Copyright 2020 Bosch.IO GmbH. All rights reserved.
 */
package com.bosch.iothub.examples;

import io.vertx.core.Future;
import io.vertx.core.Vertx;


import org.apache.qpid.proton.amqp.messaging.Data;
import org.apache.qpid.proton.message.Message;
import org.eclipse.hono.client.ApplicationClientFactory;
import org.eclipse.hono.client.DisconnectListener;
import org.eclipse.hono.client.HonoConnection;
import org.eclipse.hono.client.MessageConsumer;
import org.eclipse.hono.util.MessageHelper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.influxdb.InfluxDB;
import org.influxdb.InfluxDBFactory;
import org.influxdb.dto.Point;
import org.influxdb.dto.Query;
import org.influxdb.dto.QueryResult;
import org.json.JSONObject;

import java.util.concurrent.TimeUnit;

import javax.annotation.PostConstruct;

@Component
public class ExampleConsumer {
    private static final Logger LOG = LoggerFactory.getLogger(ExampleConsumer.class);
    private static final int RECONNECT_INTERVAL_MILLIS = 1000;

    @Value(value = "${tenant.id:t23dc7c7e760340cdaea5f60e38af23d9}")
    protected String tenantId;
    
    void setTenantId(String tenantId) {
        this.tenantId = tenantId;
    }
    
    @Value("${server.url:http://localhost:8086}")
    protected String serverURL;

    void setServerURL(String serverURL) {
        this.serverURL = serverURL;
    }
    
    @Value("${username:admin}")
	protected String username;
	
	void setUserName(String username) {
		this.username = username;
	}
	
	@Value("${password:admin}")
	protected String password;

	void setPassWord(String password) {
		this.password = password;
	}
	
	@Value("${database:dias_kuksa_secoc}")
	protected String database;

	void setDatabase(String database) {
		this.database = database;
	}

	@Value("${eval.point:50}")
	protected int evalPoint;

	void setEvalPoint(int evalPoint) {
		this.evalPoint = evalPoint;
	}

    @Autowired
    private Vertx vertx;

    @Autowired
    private ApplicationClientFactory clientFactory;

    private long reconnectTimerId = -1;

    void setClientFactory(ApplicationClientFactory clientFactory) {
        this.clientFactory = clientFactory;
    }

   
    private InfluxDB influxDB;
	private InfluxAPI influxAPI;

    @PostConstruct
    private void start() {
        initialize();
    	connectWithRetry();
    }
    
    private void initialize() {
    	// influxService = new InfluxService();
    	
    	System.out.println("00");
    	System.out.println("serverURL: " + serverURL);
    	
    	
		influxDB = InfluxDBFactory.connect(serverURL, username, password); // connectInfluxDBDatabase
		
		System.out.println("0");
		System.out.println("database: " + database);
		influxDB.query(new Query("CREATE DATABASE " + database));
		
		influxDB.setDatabase(database);
		/*influxDB.write(Point.measurement("kuksa_dias_secoc")
				.time(System.currentTimeMillis(), TimeUnit.MILLISECONDS)
				.tag());*/
		
		//System.out.println("Before MEthod: ");
		//influxAPI.writeMetricDataUnderHost(influxDB, "signalTable", "value");
		
		//System.out.println("After Method: ");
		/*influxService.writeSingleMetricToInfluxDB(influxDB, "eval_point", "eval", evalPoint + "");
		int mapCode = 0;
		if (noxMapMode.compareTo("tscr_bad") == 0) {
			mapCode = 0;
		} else if (noxMapMode.compareTo("tscr_intermediate") == 0) {
			mapCode = 1;
		} else if (noxMapMode.compareTo("tscr_good") == 0) {
			mapCode = 2;
		} else if (noxMapMode.compareTo("old_good") == 0) {
			mapCode = 3;
		} else if (noxMapMode.compareTo("pems_cold") == 0) {
			mapCode = 4;
		} else if (noxMapMode.compareTo("pems_hot") == 0) {
			mapCode = 5;
		} else {
			System.out.println("ERROR: Wrong NOx Map Mode Value! Proceed as \"tscr_bad\".");
		}
		influxService.writeSingleMetricToInfluxDB(influxDB, "nox_map_mode", "eval", mapCode + ""); */
    }

    /**
     * Try to connect Hono client infinitely regardless of errors which may occur,
     * even if the Hono client itself is incorrectly configured (e.g. wrong credentials).
     * This is to ensure that client tries to re-connect in unforeseen situations.
     */
    private void connectWithRetry() {
    	
        clientFactoryConnect(this::onDisconnect).compose(connection -> {
            LOG.info("Connected to IoT Hub messaging endpoint.");
            System.out.println("Before createTelemetryConsumer");
            return createTelemetryConsumer().compose(createdConsumer -> {
                LOG.info("Consumer ready [tenant: {}, type: telemetry]. Hit ctrl-c to exit...", tenantId);
                return Future.succeededFuture();
            });
        }).otherwise(connectException -> {
            LOG.info("Connecting or creating a consumer failed with an exception: ", connectException);
            LOG.info("Reconnecting in {} ms...", RECONNECT_INTERVAL_MILLIS);

            // As timer could be triggered by detach or disconnect we need to ensure here that timer runs only once
            vertx.cancelTimer(reconnectTimerId);
            reconnectTimerId = vertx.setTimer(RECONNECT_INTERVAL_MILLIS, timerId -> connectWithRetry());
            return null;
        });
        System.out.println("After createTelemetryConsumer");
    }

    Future<HonoConnection> clientFactoryConnect(DisconnectListener<HonoConnection> disconnectHandler) {
        LOG.info("Connecting to IoT Hub messaging endpoint...");
        System.out.println("Before cleintFactoryConnect");
        clientFactory.addDisconnectListener(disconnectHandler);
        System.out.println("After cleintFactoryConnect");
        return clientFactory.connect();
    }

    Future<MessageConsumer> createTelemetryConsumer() {
    	System.out.println("Start createTelemetryConsumer");
    	LOG.info("Creating telemetry consumer...");
        return clientFactory.createTelemetryConsumer(tenantId, this::handleMessage, this::onDetach);
        
    }

    private void onDisconnect(final HonoConnection connection) {
    	System.out.println("Before connectWithRetry");
        LOG.info("Client got disconnected. Reconnecting...");
        connectWithRetry();
        System.out.println("After connectWithRetry");
    }

    private void onDetach(Void event) {
    	System.out.println("Before onDetach");
        LOG.info("Client got detached. Reconnecting...");
        connectWithRetry();
        System.out.println("After onDetach");
    }

    private void handleMessage(final Message msg) {
        final String deviceId = MessageHelper.getDeviceId(msg);
        String content = ((Data) msg.getBody()).getValue().toString();
        JSONObject jsonObject = new JSONObject(content);
        System.out.println("Before Content: " + jsonObject.get("Aftrtrtmnt1SCRCtlystIntkGasTemp").toString());
        int signal = Integer.valueOf(jsonObject.get("Aftrtrtmnt1SCRCtlystIntkGasTemp").toString());
        System.out.println("Before Write Content: " );
		//JSONObject rates = jsonObject.getJSONObject("rates");
        //influxAPI.writeMetricDataUnderHost(influxDB, "signalTable", jsonObject.get("Aftrtrtmnt1SCRCtlystIntkGasTemp").toString());
        influxDB.write(Point.measurement("signalTable")
			    .time(System.currentTimeMillis() * 1000000, TimeUnit.NANOSECONDS)
			    //.tag("host", host)
			    .addField("SignalValue", jsonObject.get("Aftrtrtmnt1SCRCtlystIntkGasTemp").toString())
			    .build());
        System.out.println("After Write Content: " );
        //Thread.sleep(5_000L);

        // Query your data using InfluxQL.
        // https://docs.influxdata.com/influxdb/v1.7/query_language/data_exploration/#the-basic-select-statement
        QueryResult queryResult = influxDB.query(new Query("SELECT * FROM signalTable"));

        System.out.println("Result of the query: " + queryResult);
        LOG.info("Received message [device: {}, content-type: {}]: {}", deviceId, msg.getContentType(), jsonObject);
        LOG.info("... with application properties: {}", msg.getApplicationProperties());
    }


}
