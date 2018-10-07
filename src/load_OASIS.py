#-*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pymongo import MongoClient
from datetime import datetime as dt

#client = MongoClient("localhost", 27017)
#db = client["IDM"]


def load_files(raw_repo_dir):
    fm_programme = pd.read_csv(raw_repo_dir + "fm_programme.csv")
    fm_profile = pd.read_csv(raw_repo_dir + "fm_profile.csv")
    fm_policytc = pd.read_csv(raw_repo_dir + "fm_policytc.csv")
    fm_xref = pd.read_csv(raw_repo_dir + "fm_xref.csv")
    try:
        coverages = pd.read_csv(raw_repo_dir + "coverages.csv")
        coverages.columns = [i.strip(' "') for i in coverages.columns]
    except:
        coverages = []
    
    try:
        items = pd.read_csv(raw_repo_dir + "items.csv")
        items.columns = [i.strip(' "') for i in items.columns]
    except:
        items = []
    
    # clean_strange_column_namesin fm_profile:
    fm_profile.columns = [i.strip(' "') for i in fm_profile.columns]
    return fm_programme, fm_profile, fm_policytc, fm_xref, items, coverages


def terms_dict(profile):
    calcrules = pd.read_csv("../data/calcrules.csv", sep=';')
    deds = []
    if profile["deductible_1"] != 0:
        dedtype = calcrules.loc[calcrules["calcrule_id"] == profile["calcrule_id"], "ded_type"].values[0]
        deds.append({"type": dedtype, "value": float(profile["deductible_1"])})
    if profile["deductible_2"] != 0:
        deds.append({"type": "minimum", "value": float(profile["deductible_2"])})
    if profile["deductible_3"] != 0:
        deds.append({"type": "maximum", "value": float(profile["deductible_3"])})
    
    lims = []
    if profile["limit_1"] != 0:
        limtype = calcrules.loc[calcrules["calcrule_id"] == profile["calcrule_id"], "lim_type"].values[0]      
        lims.append({"type": limtype, "value": float(profile["limit_1"])})
    
    terms = {}
    if deds:
        terms["deductible"] = deds
    if lims:
        terms["limit"] = lims
    if profile["share_1"] != 0:
        terms["share"] = {"type": "% of limit", "value": float(profile["share_1"])}
    if profile["share_2"] != 0: 
        # verify me!!!
        terms["% ceded"] = float(profile["share_2"])
    if profile["share_3"] != 0:
        #verify me!
        terms["% placed"] = float(profile["share_3"])
    if profile["attachment_1"] != 0:
        terms["attachment"] = {"value": float(profile["attachment_1"])}
    return terms

def find_children(programme, fm_policytc, level, agg_id, acc_id):
    agg_ids = list(programme.loc[(programme["level_id"]==level) & (programme["to_agg_id"]==agg_id)]["from_agg_id"])
    if level-1 == 0:
        covers = ["InsObj_{}_{}".format(acc_id, i) for i in agg_ids]
    else:
        covers = []
        for agg in agg_ids:
            layer_ids = list(fm_policytc.loc[(fm_policytc["level_id"]== level-1) \
                                             & (fm_policytc["agg_id"]== agg)]["layer_id"])
            #print(layer_ids)
            covers.extend(["layer_{}_{}_{}".format(level-1, agg, i) for i in layer_ids])
    return covers

def find_parents(programme, fm_policytc, level, agg_id, layer_id):
    agg_ids = list(programme.loc[(programme["level_id"]==level+1) & (programme["from_agg_id"]==agg_id)]["to_agg_id"])
    feeds_into = []
    for agg in agg_ids:
        layer_ids = list(fm_policytc.loc[(fm_policytc["level_id"]== level+1) & (fm_policytc["agg_id"]==agg)]["layer_id"])
        #print(layer_ids)
        feeds_into.extend(["layer_{}_{}_{}".format(level+1, agg, i) for i in layer_ids])
    if len(agg_ids) == 0:
        feeds_into = ["policy_loss"]
    return feeds_into


def find_layer_terms(fm_policytc, level, agg_id, layer_id=1):
    terms = fm_policytc.loc[(fm_policytc["level_id"] == level) \
                            & (fm_policytc["agg_id"]==agg_id) \
                            & (fm_policytc["layer_id"]==layer_id)]["terms"].values
    if len(terms) == 1:
        terms = terms[0]
    elif len(terms) == 0:
        terms = None
    return terms


def make_layer(fm_programme, fm_policytc, acc_id, level, agg_id, layer_id=1):
    layer = {"layer_id": str("layer_{}_{}_{}".format(level, agg_id, layer_id))}
    layer["covers"] = find_children(fm_programme, fm_policytc, level, agg_id, acc_id)
    layer["feeds_into"] = find_parents(fm_programme, fm_policytc, level, agg_id, layer_id)
    layer["terms"] = find_layer_terms(fm_policytc, level, agg_id, layer_id)
    return layer


def remove_empty_layer(empty_layer, layers):
    assert empty_layer["terms"] == {}
    if any([s.startswith("InsObj") for s in empty_layer["covers"]]) and any([s == "policy_loss" for s in empty_layer["feeds_into"]]):
        for layer in layers:
            if layer["layer_id"] == empty_layer["layer_id"]:
                layer["terms"] = None
        return layers
    else:
        for l in layers:
            if empty_layer["layer_id"] in l["feeds_into"]:
                l["feeds_into"].remove(empty_layer["layer_id"])
                l["feeds_into"].extend(empty_layer["feeds_into"])
            if empty_layer["layer_id"] in l["covers"]:
                l["covers"].remove(empty_layer["layer_id"])
                l["covers"].extend(empty_layer["covers"])
    return [i for i in layers if i["layer_id"] != empty_layer["layer_id"]]
    
    
def make_all_layers(fm_programme, fm_policytc, acc_id):
    layers = []
    for i, row in fm_policytc.iterrows():
        layers.append(make_layer(fm_programme, fm_policytc, acc_id, row["level_id"], row["agg_id"], row["layer_id"]))
    empty_layers = True
    while empty_layers:
        for layer in layers:
            empty_layers = False
            if layer["terms"] == {}:
                layers = remove_empty_layer(layer, layers)
                empty_layers = True
                break
    return layers


def make_ins_objs(coverages, items, acc_id):
    ins_objs = coverages.merge(items, on="coverage_id")
    ins_objs["_id"] = ins_objs.apply(lambda row: str("InsObj_{}_{}".format(acc_id, int(row["coverage_id"]))), axis=1)
    ins_objs = ins_objs.drop("coverage_id", axis=1).to_dict("records")
    for i in ins_objs:
        i["acc_id"] = "Acc_%i" % acc_id
        i["location"] = {
                "address": {
                        "country": "Germany",
                        "city": "Lenggries",
                        "street": "Karwendelstr."
                },
                 "geometry": {
                         "type": "Point",
                         "coordinates": [np.random.random()*5+8, np.random.random()*5+49]
                         }
                }
        i["occupancy"] = {
                "classification": "ATC",
                "class": 1,
                "desc": "Single Family housing"
                }
        i["construction"] = {
                "classification": "ATC",
                "class": 5,
                "desc": "Masonry",
                "year_built": 1978,
                "height": 2,
                "basement": "True"
                }        
    return ins_objs


def load_ktest_example(acc_id):
    fp = "https://raw.githubusercontent.com/OasisLMF/ktest/master/ftest/data/fm{}/input/".format(acc_id)
    try:
        fm_programme, fm_profile, fm_policytc, fm_xref, items, coverages = load_files(fp)
    except:
        print("can't find: ", fp)
    fm_profile["terms"] = fm_profile.apply(terms_dict, axis=1)
    fm_policytc = fm_policytc.merge(fm_profile[["profile_id", "terms"]], left_on="policytc_id", right_on="profile_id").drop("profile_id", axis=1)
    
    layers = make_all_layers(fm_programme, fm_policytc, acc_id)
    
    policy = {"_id": "Acc{}_Pol{}".format(acc_id, 1),
              "acc_id": "Acc_%i" % (acc_id),
              "inception_date": dt(2018,1,1),
              "expiration_date": dt(2018,12,31),
              "covered_perils": ["EQ", "FL", "WS", "FI"],
              "layers": layers}
    
    if len(coverages) > 0:
        ins_objs = make_ins_objs(coverages, items, acc_id)
    
    account = {
            "_id": "Acc_%i" % acc_id,
            "name": "account_{}".format(acc_id),
            "address": {
                    "country": "US",
                    "city": "New York",
                    "street": "37 N Ave",
                    },
            "email": "acc_{}@idm.com".format(acc_id),
            "policies": policy["_id"],
            "insured_objects": [i["_id"] for i in ins_objs]
            }
    return account, policy, ins_objs
    
    
    
def insert_all_ktest_examples(db):
    for acc_id in range(38):
        account, policy, ins_objs = load_ktest_example(acc_id)
        if account != None:
            print("loading, converting, and inserting fm%i into MongoDB" % acc_id)
            db.accounts.insert_one(account)
            db.insured_objects.insert_many(ins_objs)
            db.policies.insert_one(policy)


