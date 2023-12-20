# Pipeline Folder

The pipeline folder contains a gradle project with 4 classes:
BonsaiConfig, KafkaConfig, HealthAppConsumer, and HealthAppProducer. 
The purpose of the project is to send health app log entries to a Kafka cluster
using the HealthAppProducer class, and then process the messages
for insertion into a Bonsai Open Search database using the HealthAppConsumer class.

BonsaiConfig: used for parsing a text file containing Bonsai credentials,
used for avoiding exposing secrets in plain text.

KafkaConfig: similar to BonsaiConfig, parses a Kafka config file and stores
secrets in private attributes to avoid exposing them in plain text.

