import os

from logai.dataloader.openset_data_loader import OpenSetDataLoader, OpenSetDataLoaderConfig
from logai.preprocess.preprocessor import PreprocessorConfig, Preprocessor
from logai.utils import constants

from logai.information_extraction.log_parser import LogParser, LogParserConfig
from logai.algorithms.parsing_algo.drain import DrainParams

from logai.information_extraction.feature_extractor import FeatureExtractorConfig, FeatureExtractor

from logai.analysis.anomaly_detector import AnomalyDetector, AnomalyDetectionConfig
from sklearn.model_selection import train_test_split
import pandas as pd

from logai.information_extraction.log_vectorizer import VectorizerConfig, LogVectorizer
from logai.information_extraction.categorical_encoder import CategoricalEncoderConfig, CategoricalEncoder

from logai.information_extraction.feature_extractor import FeatureExtractorConfig, FeatureExtractor


from logai.algorithms.anomaly_detection_algo.isolation_forest import IsolationForestParams
from logai.analysis.anomaly_detector import AnomalyDetectionConfig, AnomalyDetector
from sklearn.model_selection import train_test_split


def setup_anomalies(log_file):

    print("Starting logai...")
    # Loading Data
    #File Configuration
    filepath = os.path.join("..", "datasets", log_file) # Point to the target HealthApp.log dataset

    dataset_name = "HealthApp"
    data_loader = OpenSetDataLoader(
        OpenSetDataLoaderConfig(
            dataset_name=dataset_name,
            filepath=filepath)
    )

    logrecord = data_loader.load_data()

    # logrecord.to_dataframe().head(5)

    print("Loaded data...")

    # Preprocess the Data
    loglines = logrecord.body[constants.LOGLINE_NAME]
    attributes = logrecord.attributes

    preprocessor_config = PreprocessorConfig(
        custom_replace_list=[
            [r"\d+\.\d+\.\d+\.\d+", "<IP>"],   # retrieve all IP addresses and replace with <IP> tag in the original string.
        ]
    )

    preprocessor = Preprocessor(preprocessor_config)

    clean_logs, custom_patterns = preprocessor.clean_log(
        loglines
    )

    print("Preprocessed data...")

    # Parsing
    parsing_algo_params = DrainParams(
        sim_th=0.5, depth=5
    )

    log_parser_config = LogParserConfig(
        parsing_algorithm="drain",
        parsing_algo_params=parsing_algo_params
    )

    parser = LogParser(log_parser_config)
    parsed_result = parser.parse(clean_logs)
    parsed_loglines = parsed_result['parsed_logline']

    print("Parsed data...")

    return parsed_loglines, parsed_result, attributes, logrecord, loglines

def get_time_series(logrecord, parsed_result, attributes):
    print("Start time series...")
    # Feature extraction 

    config = FeatureExtractorConfig(
        group_by_time="15min",
        group_by_category=['parsed_logline', 'Action', 'ID'],
    )

    feature_extractor = FeatureExtractor(config)

    timestamps = logrecord.timestamp['timestamp']
    parsed_loglines = parsed_result['parsed_logline']
    counter_vector = feature_extractor.convert_to_counter_vector(
        log_pattern=parsed_loglines,
        attributes=attributes,
        timestamps=timestamps
    )

    print("Time, feature extraction...")

    # Now anomaly detection

    counter_vector["attribute"] = counter_vector.drop(
                    [
                        constants.LOG_COUNTS,
                        constants.LOG_TIMESTAMPS,
                        constants.EVENT_INDEX
                    ],
                    axis=1
                ).apply(
                    lambda x: "-".join(x.astype(str)), axis=1
                )

    attr_list = counter_vector["attribute"].unique()

    anomaly_detection_config = AnomalyDetectionConfig(
        algo_name='dbl'
    )

    res = pd.DataFrame()
    for attr in attr_list:
        temp_df = counter_vector[counter_vector["attribute"] == attr]
        if temp_df.shape[0] >= constants.MIN_TS_LENGTH:
            train, test = train_test_split(
                temp_df[[constants.LOG_TIMESTAMPS, constants.LOG_COUNTS]],
                shuffle=False,
                train_size=0.3
            )
            anomaly_detector = AnomalyDetector(anomaly_detection_config)
            anomaly_detector.fit(train)
            anom_score = anomaly_detector.predict(test)
            res = res._append(anom_score)

    print("Time, did anomaly detecetion...")
    return res

def get_semantic(logrecord, parsed_loglines, attributes):
    print("Start semantic...")
    vectorizer_config = VectorizerConfig(
        algo_name = "word2vec"
    )

    vectorizer = LogVectorizer(
        vectorizer_config
    )

    # Train vectorizer
    vectorizer.fit(parsed_loglines)

    # Transform the loglines into features
    log_vectors = vectorizer.transform(parsed_loglines)
    encoder_config = CategoricalEncoderConfig(name="label_encoder")
    encoder = CategoricalEncoder(encoder_config)
    attributes_encoded = encoder.fit_transform(attributes)

    timestamps = logrecord.timestamp['timestamp']

    config = FeatureExtractorConfig(
        max_feature_len=100
    )

    feature_extractor = FeatureExtractor(config)

    _, feature_vector = feature_extractor.convert_to_feature_vector(log_vectors, attributes_encoded, timestamps)

    print("Semantic, got features...")

    train, test = train_test_split(feature_vector, train_size=0.7, test_size=0.3)

    algo_params = IsolationForestParams(
        n_estimators=10,
        max_features=100
    )
    config = AnomalyDetectionConfig(
        algo_name='isolation_forest',
        algo_params=algo_params
    )

    anomaly_detector = AnomalyDetector(config)
    train[('timestamp')] = train[('timestamp')].values.astype("float64")
    anomaly_detector.fit(train)
    test[('timestamp')] = test[('timestamp')].values.astype("float64")

    res = anomaly_detector.predict(test)
    # obtain the anomalous datapoints
    anomalies = res[res==1]

    print("Semantic, got anomalies...")


    return anomalies

def main():
    parsed_loglines, parsed_result, attributes, logrecord, loglines = setup_anomalies("HealthApp_2000.log")
    time_res = get_time_series(logrecord, parsed_result, attributes)
    sem_res = get_semantic(logrecord, parsed_loglines, attributes)

    # print(time_res)
    # print(sem_res)

    print(loglines.iloc[sem_res.index][:5])
    print(attributes.iloc[sem_res.index][:5])

main()