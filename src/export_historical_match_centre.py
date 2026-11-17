"""Build a validated match-centre export from frozen final-test artifacts.
Predictions are copied only from saved predictions.csv rows with period=final_test.
"""
from __future__ import annotations
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT=ROOT/"data/exports/historical_match_centre.json"
CLASS_ORDER=["H","D","A"]; MODEL_IDS=["Baseline","Model A","Model B","Model C"]
FORBIDDEN={"match_id","season","date","stage","competition_phase","format_era","home_team","away_team","home_key","away_key","outcome_90m","regulation_home_goals","regulation_away_goals","source_file","source_line"}
def _sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def _clean(v):
 if isinstance(v,dict): return {str(k):_clean(x) for k,x in v.items()}
 if isinstance(v,(list,tuple)): return [_clean(x) for x in v]
 if isinstance(v,np.generic): v=v.item()
 if isinstance(v,(pd.Timestamp,datetime)): return v.isoformat()
 if v is None or pd.isna(v): return None
 return v
def ensure_match_id(matches):
 if "match_id" in matches.columns: return matches.copy()
 if not {"source_file","source_line"}.issubset(matches.columns): raise ValueError("Match table needs match_id or source_file/source_line")
 out=matches.copy(); out["match_id"]=out.source_file.astype(str).str.replace(".txt","",regex=False)+":"+out.source_line.astype(int).astype(str)
 return out
def build_payload(predictions:pd.DataFrame,matches:pd.DataFrame,features:pd.DataFrame,model_config:dict[str,Any],*,generated_at_utc=None,source_hashes=None):
 matches=ensure_match_id(matches)
 pc={"period","model","match_id","season","date","competition_phase","format_era","actual","predicted","p_H","p_D","p_A"}
 mc={"match_id","season","date","stage","home_team","away_team","regulation_home_goals","regulation_away_goals","outcome_90m","competition_phase","format_era"}
 if missing:=pc-set(predictions.columns): raise ValueError(f"Prediction table missing columns: {sorted(missing)}")
 if missing:=mc-set(matches.columns): raise ValueError(f"Match table missing columns: {sorted(missing)}")
 if "match_id" not in features: raise ValueError("Historical feature table must include match_id")
 p=predictions.loc[predictions.period.eq("final_test")].copy()
 if p.empty: raise ValueError("No saved final_test predictions found")
 if set(p.model)!=set(MODEL_IDS): raise ValueError("Final-test predictions do not contain all four required models")
 if p.duplicated(["model","match_id"]).any(): raise ValueError("Duplicate saved prediction for model/match_id")
 counts=p.groupby("model").match_id.nunique().to_dict(); mids=set(p.match_id)
 if len(mids)!=503 or any(counts.get(m)!=503 for m in MODEL_IDS): raise ValueError(f"Expected 503 matches and predictions per model; matches={len(mids)}, counts={counts}")
 if matches.match_id.duplicated().any(): raise ValueError("Match table contains duplicate match_id values")
 if features.match_id.duplicated().any(): raise ValueError("Historical feature table contains duplicate match_id values")
 if not mids.issubset(set(matches.match_id)): raise ValueError("Some predictions have no matching actual match row")
 if not mids.issubset(set(features.match_id)): raise ValueError("Some predictions have no historical feature row")
 names={"Baseline":[]}; names.update(model_config.get("feature_sets",{}))
 if set(names)!=set(MODEL_IDS): raise ValueError("model_config.json does not define feature sets for A/B/C")
 for model,cols in names.items():
  if len(cols)!=len(set(cols)): raise ValueError(f"Duplicate feature names for {model}")
  if bad:=FORBIDDEN.intersection(cols): raise ValueError(f"Target/identity fields in {model}: {sorted(bad)}")
  if missing:=set(cols)-set(features.columns): raise ValueError(f"Feature table missing {model} fields: {sorted(missing)}")
 mi=matches.set_index("match_id",drop=False); fi=features.set_index("match_id",drop=False); by_id={mid:{} for mid in mids}
 for r in p.itertuples(index=False):
  if r.actual not in CLASS_ORDER or r.predicted not in CLASS_ORDER: raise ValueError(f"Invalid class label for {r.model}/{r.match_id}")
  probs=[float(r.p_H),float(r.p_D),float(r.p_A)]
  if not all(math.isfinite(x) and 0<=x<=1 for x in probs): raise ValueError(f"Invalid probability for {r.model}/{r.match_id}")
  if not math.isclose(sum(probs),1,rel_tol=0,abs_tol=1e-8): raise ValueError(f"Probabilities do not sum to 1 for {r.model}/{r.match_id}")
  if CLASS_ORDER[int(np.argmax(probs))]!=r.predicted: raise ValueError(f"Saved label disagrees with probabilities for {r.model}/{r.match_id}")
  m=mi.loc[r.match_id]; f=fi.loc[r.match_id]
  if r.actual!=m.outcome_90m or r.actual!=f.outcome_90m: raise ValueError(f"Actual class differs across sources: {r.match_id}")
  if r.season!=m.season or pd.Timestamp(r.date).date()!=pd.Timestamp(m.date).date(): raise ValueError(f"Season/date mismatch: {r.match_id}")
  if f.season!=m.season or pd.Timestamp(f.date).date()!=pd.Timestamp(m.date).date(): raise ValueError(f"Feature date/season mismatch: {r.match_id}")
  hg,ag=int(m.regulation_home_goals),int(m.regulation_away_goals)
  if hg<0 or ag<0: raise ValueError(f"Invalid regulation score: {r.match_id}")
  by_id[r.match_id][r.model]={"predicted":r.predicted,"probabilities":dict(zip(CLASS_ORDER,probs)),"correct":bool(r.predicted==r.actual),"features":{c:_clean(f[c]) for c in names[r.model]}}
 fixtures=[]
 for mid in sorted(mids,key=lambda x:(pd.Timestamp(mi.loc[x].date),x)):
  m=mi.loc[mid]; ps=by_id[mid]
  if set(ps)!=set(MODEL_IDS): raise ValueError(f"Missing model prediction: {mid}")
  fixtures.append({"match_id":mid,"season":str(m.season),"date":pd.Timestamp(m.date).date().isoformat(),"stage":str(m.stage),"competition_phase":str(m.competition_phase),"format_era":str(m.format_era),"home_team":str(m.home_team),"away_team":str(m.away_team),"actual":{"home_goals":int(m.regulation_home_goals),"away_goals":int(m.regulation_away_goals),"outcome":str(m.outcome_90m)},"predictions":{model:ps[model] for model in MODEL_IDS}})
 return {"schema_version":1,"generated_at_utc":generated_at_utc or datetime.now(timezone.utc).isoformat(),"target":"90-minute H/D/A","class_order":CLASS_ORDER,"record_count":len(fixtures),"model_ids":MODEL_IDS,"feature_names_by_model":names,"provenance":{"prediction_source":"data/results/predictions.csv (period=final_test only)","match_source":"data/processed/ucl_matches.csv","feature_source":"data/processed/historical_features.csv","join_key":"match_id","match_id_definition":"source_file stem plus colon plus source_line","feature_timing":"historical_features.csv stores start-of-day team state; results update only after every match on that calendar date has received features","prediction_generation":"saved predictions only; no fitting or inference performed by this exporter","source_sha256":source_hashes or {}},"fixtures":fixtures}
def main():
 paths={"predictions":ROOT/"data/results/predictions.csv","matches":ROOT/"data/processed/ucl_matches.csv","features":ROOT/"data/processed/historical_features.csv","model_config":ROOT/"data/results/model_config.json"}
 for path in paths.values():
  if not path.exists(): raise FileNotFoundError(path)
 payload=build_payload(pd.read_csv(paths["predictions"]),pd.read_csv(paths["matches"]),pd.read_csv(paths["features"]),json.loads(paths["model_config"].read_text(encoding="utf-8")),source_hashes={k:_sha256(v) for k,v in paths.items()})
 DEFAULT_OUTPUT.parent.mkdir(parents=True,exist_ok=True); DEFAULT_OUTPUT.write_text(json.dumps(payload,indent=2,allow_nan=False)+"\n",encoding="utf-8")
 print(f"Wrote {DEFAULT_OUTPUT} ({payload['record_count']} fixtures; {payload['record_count']*len(MODEL_IDS)} predictions).")
if __name__=="__main__": main()
