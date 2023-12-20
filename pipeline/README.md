## Pipeline Folder

The pipeline folder contains a gradle project with 4 classes:
[BonsaiConfig](#BonsaiConfig), [KafkaConfig](#KafkaConfig), [HealthAppConsumer](#HealthAppConsumer), and [HealthAppProducer](#HealthAppProducer). 
The purpose of the project is to send health app log entries to a Kafka cluster
using the HealthAppProducer class, and then process the messages
and insert them into a Bonsai Open Search database using the HealthAppConsumer class.

#### BonsaiConfig

used for parsing a text file containing Bonsai credentials,
used for avoiding exposing secrets in plain text.

#### KafkaConfig

similar to BonsaiConfig, parses a Kafka config file and stores
secrets in private attributes to avoid exposing them in plain text.

#### HealthAppProducer

Contains two private attributes: a log object, and a string
of arrays that includes all fields from the health app log files.

The createKafkaProducer method configures and returns a Kafka producer.
It first reads in the Kafka credentials using the KafkaConfig class
and uses them to establish a connection with our Upstash.io Kafka cluster.
Both key and values serializers are set as Strings, and the producer is then
configured to compress and batch messages to optimize throughput. The messages
are compressed using the snappy algorithm, which has historically been championed
by Kafka, though LZ4 would be an equally appropriate choice. “LINGER_MS_CONFIG”
is set to 20, so that message batches are only sent every 20ms, and the batch size
increased to 32kb so that the producer batches messages targeting the same partition
by default.

The main method first initializes variables representing the config filepaths and the
topic which the producer will write to. A producer is then initialized using the
createKafkaProducer method described above. A log file is read in to simulate an API call
that would read streaming log information in an enterprise program. Each entry is used
to initialize a JSON object. Note that about a dozen entries out of over 250k included
extra fields, and these are ignored in this case as such a small number of affected entries
would not have a significant impact on the logAI models. The log JSON object is then used
to initialize a producer record, which is sent to the Kafka cluster. The onCompletion method
is overridden to log record data on successful sends, as well as to log any failures. The producer
is closed in a finally block in order to ensure that it is correctly flushed and shut down.


#### HealthAppConsumer 

