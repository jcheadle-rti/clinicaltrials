import json
import csv
import requests
import collections

def main():
    input_filepath = "inputs/heal_clintrials_cleaned.csv"
    output_path = "outputs"
    nctid_dict = create_nctid_dict(input_filepath)
    results = get_request(nctid_dict)
    
    # Export JSON (if not already done)
    #clintrials_file = f"{output_path}/heal_clintrials.json"
    #with open(clintrials_file, 'w') as jsonfile:
    #    json.dump(results, indent=2, fp=jsonfile)

    # Flatten and Export CSV
    results_flat,fieldnames = flatten_results(results)

    # Write flattened results dicts to CSV
    clintrials_file = f"{output_path}/heal_clintrials2.csv"
    with open(clintrials_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for result in results_flat:
            writer.writerow(result)

def create_nctid_dict(filepath):
    '''
    given a filepath to a CSV, returns a list of dictionaries
    '''
    nctids = []
    with open(filepath) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            nctids.append(dict(row))

    return(nctids)

def get_request(nctid_dict):
    # Initialize Results List
    results_list = []

    # Request Details (hardcoded for now)
    headers = {
        'Content-Type': 'application/json',
        'accept': 'application/json'
        }
    base_url = "https://clinicaltrials.gov/api/query/"
    endpoint = "full_studies"  
    search_area = "AREA[NCTIdSearch]"
    min_rnk = 1
    max_rnk = 100
    fmt = "json"
    
    # 10 IDs at a time to keep URL short
    for i in range(0, len(nctid_dict), 10):
        dicts = nctid_dict[i:i+10]
        expr = " OR ".join([a['nctid'] for a in dicts])
        search = requests.utils.quote(f"{search_area}{expr}") # make it URL accessible
        request_url = f"{base_url}{endpoint}?expr={search}&min_rnk={min_rnk}&max_rnk={max_rnk}&fmt={fmt}"
    
        # Request Object:
        req = requests.request(method = "GET",
                            url = request_url,
                            headers = headers)
        
        # What happens when we fail
        if req.status_code is not 200:
            print("UH OH!")

        results_obj = req.json()['FullStudiesResponse']['FullStudies']
        
        # Re-attach appl_id and project to results_obj
        # TODO: Check for whether returned ID is accurate
        studies = [s['Study'] for s in results_obj]
        for i in range(0, len(studies), 1):
            study = studies[i]
            nctid = study['ProtocolSection']['IdentificationModule']['NCTId']
            dict = [d for d in dicts if d['nctid'] == nctid]
            if not dict:
               studies.pop(i) 
               continue
            else:
                dict = dict.pop()
            study['appl_id'] = dict['appl_id']
            study['project'] = dict['project']

        # Add studies to list of dicts
        results_list.extend(studies)

    return(results_list)

def merge_dict(dict_list):
    '''
    Merges dictionaries in a list by turning values of same keys into a 
    list of values in the target dictionary.
    '''
    d_new = {}
    for d in dict_list:
        for k,v in d.items():
            if k in d_new:
                d_new[k].append(v)
            else:
                d_new[k] = [v]
    return(d_new)

def flatten_json(dictionary, parent_key=False, separator='.'):
    # https://github.com/ScriptSmith/socialreaper/blob/master/socialreaper/tools.py
    '''
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key: The string to prepend to dictionary's keys
    :param separator: The string used to separate flattened keys
    :return: A flattened dictionary
    '''

    items = []
    for key, value in dictionary.items():
        if value==None: # skip if None
            continue
        new_key = str(parent_key) + separator + key if parent_key else key

        if isinstance(value, collections.MutableMapping):
            items.extend(flatten_json(value, new_key, separator).items()) #recurse

        elif isinstance(value, list):
            if not value: #skip list if empty
                continue
            elif isinstance(value[0], dict):
                items.extend(flatten_json(merge_dict(value), new_key, separator).items()) #recurse
            else:
                value = ';'.join(map(str,value))
                items.append((new_key, str(value))) # append as tuple
            
        else:
            items.append((new_key, value)) # append as tuple
    return dict(items)

def flatten_json_2(d, sep="."):

    obj = collections.OrderedDict()

    def recurse(t,parent_key=""):
        
        if isinstance(t,list):
            for i in range(len(t)):
                recurse(t[i],parent_key + sep + str(i) if parent_key else str(i))
        elif isinstance(t,dict):
            for k,v in t.items():
                recurse(v,parent_key + sep + k if parent_key else k)
        else:
            obj[parent_key] = t

    recurse(d)

    return obj

def flatten_results(results_list):
    # Map flatten function to results
    results_flat = list(map(flatten_json_2, results_list))
    fieldnames = []
    for result in results_flat:
        fieldnames.extend(list(result.keys()))
    fieldnames = list(set(fieldnames))
    fieldnames.sort() # sort alphabetically
    return(results_flat,fieldnames)

if __name__ == "__main__":
    main()