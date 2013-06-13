from larva_service.models import run, dataset, shoreline

def remove_mongo_keys(d, extra=None):

    remove_keys = ['_id','_collection','_database','_keywords']

    if isinstance(extra, list):
        remove_keys = list(set(remove_keys + extra))

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
