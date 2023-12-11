package log.anomalies;

import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.util.Properties;

public class HealthAppProducer {
    // HealthApp log fields to be used as keys in JSON objects
    private static final String[] KEYS = {"Time", "Component", "PID", "Content"};

    // Method for creating and returning Kafka producer
    private static KafkaProducer<String, String> createKafkaProducer(String configFilepath){
        // custom class for reading in data from Kafka config file
        KafkaConfig kc = new KafkaConfig(configFilepath);

        //  define properties for connecting to Kafka cluster
        var props = new Properties();
        props.put("bootstrap.servers", kc.getBootstrapServer());
        props.put("sasl.mechanism", kc.getSaslMechanism());
        props.put("security.protocol", kc.getSecurityProtocol());
        props.put("sasl.jaas.config", kc.getSaslJaasConfig());

        props.put("key.serializer", "org.apache.kafka.common.serialization.StringSerializer");
        props.put("value.serializer", "org.apache.kafka.common.serialization.StringSerializer");

        // set file compression in producer for efficient batch processing, increase linger  to 20ms
        // and batch size to 32kb to send larger compressed messages
        props.put(ProducerConfig.COMPRESSION_TYPE_CONFIG, "snappy");
        props.put(ProducerConfig.LINGER_MS_CONFIG, 20);
        props.put(ProducerConfig.BATCH_SIZE_CONFIG, Integer.toString(32*1024));

        return new KafkaProducer<String, String>(props);
    }

    public static void main(String[] args) {
        String healthLogsFilepath = "src/main/resources/HealthApp.log";
        String configFilepath = "src/main/resources/kafka_config.txt";
        KafkaProducer<String, String> healthAppProducer = createKafkaProducer(configFilepath);

        try {
            File health_app_file = new File(healthLogsFilepath);
            FileReader health_app_fr = new FileReader(health_app_file);
            BufferedReader health_app_br = new BufferedReader(health_app_fr);
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
