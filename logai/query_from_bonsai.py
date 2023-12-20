import os
import time
from elasticsearch import Elasticsearch
from examples.jupyter_notebook.logs_healthapp import main as logs_driver

class bonsai2logai:
    def __init__(self):
        # init logai
        self.es = Elasticsearch(os.environ['BONSAI_URL'])
        print("Connected to Bonsai",self.es.ping())
        pass

    def start_new_scroll(self, index_name,from_time,query,sort_key,query_continue_sort,size_per_batch):
        '''
        from_time : timestamp
        query : sample es query {"match_all": {}}
        sort_key: keys by which to sort the scroll [{"Time": "asc"}]
        query_continue_sort: query to continue the scrolling from a point {"range": {"Time": {"gt": from_time}}}
        '''
        scroll_time = '5m'
        query_body = {
            "query": query,  # 
            "sort": sort_key # Sorting by Time
        }
        if from_time:
            # Start from documents added after this timestamp
            query_body["query"] = query_continue_sort
    
        response = self.es.search(
            index=index_name,
            scroll=scroll_time,
            size=size_per_batch,
            body=query_body
        )
        return response['_scroll_id'], response['hits']['hits'],len(response['hits']['hits'])
    
    def write_tologfile(self,resp,file_operation_type='w'):
        with open('formatted_data.log', file_operation_type) as log_file:
            for item in resp:
                source = item['_source']
                formatted_line = f"{source['Time']}|{source['Component']}|{source['PID']}|{source['Content']}\n"
                log_file.write(formatted_line)
        loglines, attributes, time_res, sem_res = logs_driver("/Users/ajay/Documents/NYU/Notes/BigData/Project/log-anomalies/logai/formatted_data.log")
        print(loglines.iloc[sem_res.index][:5])
        return loglines, attributes, time_res, sem_res
    
    def query_streaming(self,
                        index_name,
                        from_time=None,
                        query={"match_all": {}},
                        sort_key=[{"Time": "asc"}],
                        query_continue_sort={"range": {"Time": {"gt": None}}},
                        size_per_batch=10000,
                        wait_before_poll=1):
        totalhits = 0
        scroll_time = '5m'
        scroll_id, hits, totalhits = self.start_new_scroll(index_name,from_time,query,sort_key,query_continue_sort,size_per_batch)
        self.write_tologfile(hits)
        
        while True:
            try:
                if scroll_id:
                    response = self.es.scroll(scroll_id=scroll_id, scroll=scroll_time)
                    scroll_id = response['_scroll_id']
                    hits = response['hits']['hits']
                    totalhits += len(hits) # stream here to logai
                    self.write_tologfile(hits)
                    if not hits:
                        # not doing the reinit part cuz you can just use retrieve the last time and use
                        # Reinitialize the scroll for new data
                        # print("Reinit at",tothits)
                        # scroll_id, hits, total_new_hits = self.start_new_scroll(last_time,query,sort_key,query_continue_sort)
                        # totalhits += len(new_hits) # stream here to logai
                        # write_tologfile(hits)
                        # continue 
                        return last_time
        
                    # Update last_time with the Time of the last document
                    if hits:
                        last_time = hits[-1]['_source']['Time']
        
                    # Process hits here
                    print(f"Retrieved {len(hits)} documents, Total: {totalhits}")
                    # After updating last_time in your script
                    print(f"Last timestamp: {last_time}, Hits in batch: {len(hits)}")
        
                print("polling for more")
                time.sleep(wait_before_poll)  # Adjust as needed

            except Exception as e:
                print("An error occurred:", e)
                break

    def query_normal(self, index_name, query):
        response = self.es.search(index=index_name, body=query)
        # stream here to logai 
        loglines, attributes, time_res, sem_res = self.write_tologfile(response['hits']['hits'])
        return response['hits']['hits'], loglines, attributes, time_res, sem_res
