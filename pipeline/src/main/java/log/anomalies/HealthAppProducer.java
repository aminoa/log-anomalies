package log.anomalies;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileNotFoundException;
import java.io.IOException;

public class HealthAppProducer {
    private static final String[] KEYS = {"Time", "Component", "PID", "Content"};

    public static void main(String[] args) {
        String filepath = "src/main/resources/HealthApp.log";

        try {
            File health_app_file = new File(filepath);
            FileReader health_app_fr = new FileReader(health_app_file);
            BufferedReader health_app_br = new BufferedReader((health_app_fr));
            String line;

            int j = 0;
            // read in file, parse every log line and create JSON object
            while ((line = health_app_br.readLine()) != null && j < 5) {
                String[] vals = line.split("\\|");
                JSONObject logJSON = new JSONObject();

                int i = 0;
                // iterate through vals array, use KEYS array to put key:value pairs into logJSON object
                for (String val : vals) {
                    logJSON.put(KEYS[i], val);
                    i++;
                }
                System.out.println(logJSON);
                j++;
            }
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
