from larva_service.models import task, run

def remove_mongo_keys(d):

    remove_keys = ['_id','_collection','_database','_keywords']

    if d is not None:
        if isinstance(d, list):
            for sublist in d:
                remove_mongo_keys(sublist)
        elif isinstance(d, dict):
            for key in d.keys():
                try:
                    remove_keys.index(key)
                    del(d[key])
                except:
                    remove_mongo_keys(d[key])

    return