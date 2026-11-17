import json,sys,unittest
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from export_historical_match_centre import MODEL_IDS,build_payload
class ExportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.p=pd.read_csv(ROOT/"data/results/predictions.csv"); cls.m=pd.read_csv(ROOT/"data/processed/ucl_matches.csv"); cls.m["match_id"]=cls.m.source_file.astype(str).str.replace(".txt","",regex=False)+":"+cls.m.source_line.astype(int).astype(str); cls.f=pd.read_csv(ROOT/"data/processed/historical_features.csv"); cls.c=json.loads((ROOT/"data/results/model_config.json").read_text()); cls.out=build_payload(cls.p,cls.m,cls.f,cls.c,generated_at_utc="2026-01-01T00:00:00+00:00")
 def test_counts_models(self):
  fs=self.out["fixtures"]; self.assertEqual(len(fs),503); self.assertEqual(len({x["match_id"] for x in fs}),503); self.assertEqual(self.out["model_ids"],MODEL_IDS); self.assertTrue(all(set(x["predictions"])==set(MODEL_IDS) for x in fs)); self.assertEqual(sum(len(x["predictions"]) for x in fs),2012)
 def test_probabilities_labels_actual_correct(self):
  for f in self.out["fixtures"]:
   self.assertIn(f["actual"]["outcome"],["H","D","A"])
   for p in f["predictions"].values():
    self.assertIn(p["predicted"],["H","D","A"]); self.assertEqual(list(p["probabilities"]),["H","D","A"]); self.assertAlmostEqual(sum(p["probabilities"].values()),1,places=8); self.assertEqual(p["correct"],p["predicted"]==f["actual"]["outcome"])
 def test_feature_order_and_target_exclusion(self):
  self.assertEqual(self.out["feature_names_by_model"]["Baseline"],[])
  for f in self.out["fixtures"]:
   for model,p in f["predictions"].items():
    self.assertEqual(list(p["features"]),self.out["feature_names_by_model"][model]); self.assertFalse({"actual","outcome_90m","regulation_home_goals","regulation_away_goals"}&set(p["features"]))
 def test_invalid_probability_and_label_rejected(self):
  p=self.p.copy(); i=p.index[p.period.eq("final_test")][0]; p.loc[i,"p_H"]=0.9
  with self.assertRaisesRegex(ValueError,"do not sum to 1"): build_payload(p,self.m,self.f,self.c)
  p=self.p.copy(); i=p.index[p.period.eq("final_test")][0]; p.loc[i,"predicted"]="X"
  with self.assertRaisesRegex(ValueError,"Invalid class label"): build_payload(p,self.m,self.f,self.c)
 def test_missing_join_rows_rejected(self):
  ids=set(self.p.loc[self.p.period.eq("final_test"),"match_id"])
  with self.assertRaisesRegex(ValueError,"no matching actual match row"): build_payload(self.p,self.m[~self.m.match_id.isin(ids)],self.f,self.c)
  with self.assertRaisesRegex(ValueError,"no historical feature row"): build_payload(self.p,self.m,self.f[~self.f.match_id.isin(ids)],self.c)
if __name__=="__main__": unittest.main()
