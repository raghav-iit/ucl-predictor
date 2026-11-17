(() => {
  "use strict";
  const $ = id => document.getElementById(id);
  const CLASS_ORDER = ["H", "D", "A"];
  const CLASS_NAMES = {H:"Home win", D:"Draw", A:"Away win"};
  const number = (x,d=4) => (x===null || x===undefined || !Number.isFinite(Number(x))) ? "—" : Number(x).toFixed(d);
  const pct = (x,d=1) => (x===null || x===undefined || !Number.isFinite(Number(x))) ? "—" : (100*Number(x)).toFixed(d)+"%";
  const esc = s => String(s ?? "").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const setBody = (id,html) => {const b=$(id)?.querySelector("tbody");if(b)b.innerHTML=html;};
  const safeDate = d => String(d||"").slice(0,10);
  function summary(state,prefix) {
    state=state||{}; const n=Number(state.played||0), out={};
    out[prefix+"_prior_matches"]=n;
    if(n){
      out[prefix+"_points_per_match"]=Number(state.points||0)/n;
      out[prefix+"_goals_for_per_match"]=Number(state.goals_for||0)/n;
      out[prefix+"_goals_against_per_match"]=Number(state.goals_against||0)/n;
      out[prefix+"_goal_diff_per_match"]=(Number(state.goals_for||0)-Number(state.goals_against||0))/n;
      out[prefix+"_win_rate"]=Number(state.wins||0)/n;
      out[prefix+"_draw_rate"]=Number(state.draws||0)/n;
    }else{
      ["points_per_match","goals_for_per_match","goals_against_per_match","goal_diff_per_match","win_rate","draw_rate"].forEach(k=>out[prefix+"_"+k]=null);
    }
    return out;
  }
  function venue(state,which,prefix){
    state=state||{}; const n=Number(state[which+"_played"]||0);
    return {[prefix+"_"+which+"_prior_matches"]:n,[prefix+"_"+which+"_points_per_match"]:n?Number(state[which+"_points"]||0)/n:null};
  }
  function recent(state,prefix){
    const items=(state?.recent_results||[]).slice(-5), n=items.length, out={};
    out[prefix+"_recent_matches"]=n;
    out[prefix+"_recent5_points_per_match"]=n?items.reduce((s,x)=>s+Number(x.points||0),0)/n:null;
    out[prefix+"_recent5_goal_diff_per_match"]=n?items.reduce((s,x)=>s+Number(x.goal_difference||0),0)/n:null;
    return out;
  }
  function buildFeatures(state,homeKey,awayKey){
    const h=state.teams[homeKey]||{}, a=state.teams[awayKey]||{};
    const f=Object.assign({},summary(h,"home"),summary(a,"away"),venue(h,"home","home_team"),venue(a,"away","away_team"));
    const he=Number(h.elo_rating??1500), ae=Number(a.elo_rating??1500);
    f.elo_home=he; f.elo_away=ae; f.elo_difference=he-ae+60;
    Object.assign(f,recent(h,"home"),recent(a,"away"));
    f.recent5_points_difference=(f.home_recent5_points_per_match==null||f.away_recent5_points_per_match==null)?null:f.home_recent5_points_per_match-f.away_recent5_points_per_match;
    f.recent5_goal_diff_difference=(f.home_recent5_goal_diff_per_match==null||f.away_recent5_goal_diff_per_match==null)?null:f.home_recent5_goal_diff_per_match-f.away_recent5_goal_diff_per_match;
    return {features:f,coldStart:{home:!h.played,away:!a.played}};
  }
  function softmax(values){
    const mx=Math.max.apply(null,values), es=values.map(v=>Math.exp(v-mx)), sum=es.reduce((a,b)=>a+b,0);
    return es.map(v=>v/sum);
  }
  function infer(model,features){
    const x=model.features.map((name,i)=>{
      const v=features[name], imputed=(v===null||v===undefined||!Number.isFinite(Number(v)))?model.imputer_medians[i]:Number(v);
      return (imputed-model.scaler_mean[i])/model.scaler_scale[i];
    });
    const logits=model.classes.map((c,j)=>model.intercept[j]+x.reduce((s,v,i)=>s+v*model.coefficients[j][i],0));
    const ps=softmax(logits), byClass={};
    model.classes.forEach((c,i)=>byClass[c]=ps[i]);
    const probabilities={H:byClass.H,D:byClass.D,A:byClass.A};
    let predicted="H"; CLASS_ORDER.forEach(c=>{if(probabilities[c]>probabilities[predicted])predicted=c;});
    return {probabilities,predicted};
  }
  function outcome(c){return CLASS_NAMES[c]||c||"—";}
  function renderMetrics(data){
    const rows=data.metrics.filter(r=>["validation","final_test"].includes(r.period)&&(r.competition_phase==null||r.competition_phase===""));
    const rank={Baseline:0,"Model A":1,"Model B":2,"Model C":3};
    rows.sort((a,b)=>a.period===b.period?rank[a.model]-rank[b.model]:(a.period==="validation"?-1:1));
    setBody("metricsTable",rows.map(r=>"<tr><td>"+(r.period==="final_test"?"Final test":"Validation")+"</td><td>"+esc(r.model)+"</td><td>"+r.n+"</td><td>"+number(r.log_loss,4)+"</td><td>"+number(r.multiclass_brier,4)+"</td><td>"+pct(r.accuracy)+"</td><td>"+number(r.f1_macro,4)+"</td></tr>").join(""));
    const final=rows.filter(r=>r.period==="final_test"), a=final.find(r=>r.model==="Model A"), b=final.find(r=>r.model==="Model B"), c=final.find(r=>r.model==="Model C"), base=final.find(r=>r.model==="Baseline");
    if(base&&a&&b&&c)$("resultConclusion").innerHTML="<strong>Final test ("+base.n+" common matches):</strong> Model A "+number(a.log_loss,4)+" log loss / "+number(a.multiclass_brier,4)+" Brier; B "+number(b.log_loss,4)+" / "+number(b.multiclass_brier,4)+"; C "+number(c.log_loss,4)+" / "+number(c.multiclass_brier,4)+"; baseline "+number(base.log_loss,4)+" / "+number(base.multiclass_brier,4)+". Model A beats the baseline on both primary scores; B is slightly worse than A, and C is close to A. Differences are small and uncertainty is not estimated.";
  }
  function renderConfusion(data,model){
    const rs=data.confusion.filter(r=>r.period==="final_test"&&r.model===model), map=new Map(rs.map(r=>[r.actual+r.predicted,Number(r.count)]));
    setBody("confusionTable",CLASS_ORDER.map(a=>"<tr><th>"+a+" — "+outcome(a)+"</th>"+CLASS_ORDER.map(p=>"<td>"+(map.get(a+p)||0)+"</td>").join("")+"</tr>").join(""));
  }
  function renderDraw(data){
    const wanted=["Model A | C=0.003","Model B | C=0.003","Model C | C=0.003","Model C | C=0.003 | balanced"];
    const rs=data.draw_diagnostics.filter(r=>wanted.includes(r.model_spec));
    setBody("drawTable",rs.map(r=>"<tr><td>"+esc(r.model_spec)+"</td><td>"+number(r.log_loss,4)+"</td><td>"+number(r.multiclass_brier,4)+"</td><td>"+pct(r.accuracy)+"</td><td>"+r.predicted_D+"</td><td>"+pct(r.recall_D)+"</td></tr>").join(""));
  }
  function renderErrors(data){
    const model=$("errorModel").value, season=$("errorSeason").value, actual=$("errorActual").value;
    let rows=data.final_test_predictions.filter(r=>r.model===model);
    if(season!=="all")rows=rows.filter(r=>r.season===season);
    if(actual!=="all")rows=rows.filter(r=>r.actual===actual);
    const missed=rows.filter(r=>r.actual==="D"&&r.predicted!=="D");
    const errors=missed.length?missed:rows.filter(r=>r.actual!==r.predicted);
    $("errorCount").textContent=rows.length+" matching model/season/outcome rows; showing "+Math.min(errors.length,30)+" errors"+(missed.length?" (missed draws first)":"")+".";
    setBody("errorTable",errors.slice(0,30).map(r=>"<tr><td>"+esc(r.home_team)+" – "+esc(r.away_team)+"</td><td>"+esc(r.season)+"<br>"+esc(safeDate(r.date))+"</td><td>"+esc(outcome(r.actual))+"</td><td>"+esc(outcome(r.predicted))+"</td><td>"+pct(r.p_H)+"</td><td>"+pct(r.p_D)+"</td><td>"+pct(r.p_A)+"</td><td>"+esc(r.regulation_home_goals)+"–"+esc(r.regulation_away_goals)+"</td></tr>").join("")||"<tr><td colspan=\"8\">No errors match these filters.</td></tr>");
  }
  function renderSummary(data){
    $("coverageSummary").innerHTML="<strong>"+Number(data.match_rows).toLocaleString()+"</strong> parsed match rows · "+data.seasons.length+" seasons · "+esc(data.date_start)+" to "+esc(data.date_end);
    $("heroMatches").textContent=Number(data.match_rows).toLocaleString(); $("heroSeasons").textContent=String(data.seasons.length);
    [["H","outcomeH"],["D","outcomeD"],["A","outcomeA"]].forEach(([c,id])=>{const n=Number(data.outcome_counts[c]||0);$(id).textContent=n.toLocaleString()+" ("+pct(n/data.match_rows)+")";});
    const manifest=data.source_manifest||[];
    setBody("sourceTable",manifest.map(r=>"<tr><td>"+esc(r.season||r.source_file||"—")+"</td><td>"+esc(r.parsed_match_count??"—")+"</td><td>"+esc(r.parsed_team_count??"—")+"</td><td>"+esc(r.date_min??"—")+" – "+esc(r.date_max??"—")+"</td><td>"+esc(String(r.sha256||"").slice(0,12))+"…</td></tr>").join(""));
    const s=data.split_counts, cards=[["Development fit","2015/16–2020/21",s.validation_train],["Validation","2021/22–2022/23",s.validation],["Final model fit","2015/16–2022/23",s.final_train],["Final chronological test","2023/24–2025/26",s.final_test]];
    $("splitTimeline").innerHTML=cards.map(c=>"<article class=\"split-card\"><span>"+esc(c[0])+"</span><strong>"+Number(c[2]).toLocaleString()+" matches</strong><span>"+esc(c[1])+"</span></article>").join("");
    $("dataStamp").textContent="Static research data generated "+data.generated_at_utc+". Historical model results remain distinct from manual future-fixture estimates.";
  }
  function renderPrediction(params,state){
    const note=$("predictionStateNote"), keys=Object.keys(state.teams).filter(k=>state.team_labels&&state.team_labels[k]).sort((a,b)=>state.team_labels[a].localeCompare(state.team_labels[b]));
    ["homeTeam","awayTeam"].forEach(id=>{$(id).innerHTML=keys.map(k=>"<option value=\""+esc(k)+"\">"+esc(state.team_labels[k])+" · "+esc(k)+"</option>").join("");});
    if(keys.length>1)$("awayTeam").selectedIndex=1;
    const cutoff=state.as_of_date, now=new Date(), today=new Date(now.getTime()-now.getTimezoneOffset()*60000).toISOString().slice(0,10);
    const next=new Date(cutoff+"T00:00:00");next.setDate(next.getDate()+1);const nextDay=next.toISOString().slice(0,10), minDate=today>nextDay?today:nextDay;
    $("matchDate").min=minDate;$("matchDate").value=minDate;note.textContent="Saved team history through "+cutoff+". Dates must be on/after "+minDate+".";
    $("predictionForm").addEventListener("submit",ev=>{
      ev.preventDefault();
      const home=$("homeTeam").value,away=$("awayTeam").value,name=$("modelName").value,date=$("matchDate").value,out=$("predictionOutput");
      if(home===away){out.innerHTML="<p class=\"cold-note\">Choose two different teams.</p>";return;}
      if(!date||date<minDate){out.innerHTML="<p class=\"cold-note\">Choose a date on or after "+esc(minDate)+".</p>";return;}
      const built=buildFeatures(state,home,away), result=infer(params.models[name],built.features), best=result.predicted;
      const probs=CLASS_ORDER.map(c=>"<div class=\"probability "+(c===best?"top":"")+"\"><span>"+c+" · "+CLASS_NAMES[c]+"</span><strong>"+pct(result.probabilities[c])+"</strong><div class=\"prediction-bar\"><i style=\"width:"+Math.max(0,Math.min(100,100*result.probabilities[c]))+"%\"></i></div></div>").join("");
      const featureRows=params.models[name].features.map(n=>"<tr><td>"+esc(n)+"</td><td>"+(built.features[n]===null||built.features[n]===undefined?"Missing":number(built.features[n],4))+"</td></tr>").join("");
      const cold=Object.entries(built.coldStart).filter(x=>x[1]).map(x=>x[0]).join(" and ");
      out.innerHTML="<p class=\"eyebrow\">"+esc(name)+" · "+esc(date)+"</p><h3>"+esc(state.team_labels[home])+" vs "+esc(state.team_labels[away])+"</h3><div class=\"probabilities\">"+probs+"</div><p><span class=\"prediction-result\">Highest estimated probability: "+esc(CLASS_NAMES[best])+"</span></p><p class=\"small\">Inputs use the state snapshot through "+esc(cutoff)+". Values shown are before saved training-fitted imputation and scaling.</p>"+(cold?"<p class=\"cold-note\">Cold start for "+esc(cold)+": zero prior matches, Elo 1500, and missing rates. The fitted training imputer supplies missing values for inference.</p>":"")+"<details class=\"details\"><summary>Inspect pre-match feature values ("+params.models[name].features.length+")</summary><div class=\"table-wrap\"><table class=\"feature-table\"><thead><tr><th>Feature</th><th>Value</th></tr></thead><tbody>"+featureRows+"</tbody></table></div></details><p class=\"small\">Probabilities are model estimates, not guarantees. This manual scenario is not checked against an official fixture list.</p>";
    });
  }
  function initialize(){
    Promise.all([
      fetch("site_data/research_results.json").then(r=>{if(!r.ok)throw Error("Research results file unavailable");return r.json();}),
      fetch("site_data/model_parameters.json").then(r=>{if(!r.ok)throw Error("Model parameter file unavailable");return r.json();}),
      fetch("site_data/team_state.json").then(r=>{if(!r.ok)throw Error("Team-state file unavailable");return r.json();})
    ]).then(([data,params,state])=>{
      renderSummary(data);renderMetrics(data);renderDraw(data);renderErrors(data);renderConfusion(data,$("confusionModel").value);renderPrediction(params,state);
      const seasons=[...new Set(data.final_test_predictions.map(r=>r.season))].sort();
      $("errorSeason").innerHTML="<option value=\"all\">All test seasons</option>"+seasons.map(s=>"<option value=\""+esc(s)+"\">"+esc(s)+"</option>").join("");
      ["errorModel","errorSeason","errorActual"].forEach(id=>$(id).addEventListener("change",()=>renderErrors(data)));
      $("confusionModel").addEventListener("change",()=>renderConfusion(data,$("confusionModel").value));
    }).catch(err=>{$("coverageSummary").textContent="Static data could not be loaded: "+err.message+". Rebuild the site data from the project root.";$("predictionStateNote").textContent="Saved prediction assets could not be loaded.";$("dataStamp").textContent="Build error: "+err.message;});
  }
  window.UCLPredictor={buildFeatures,infer,softmax};
  const menu=$("menuToggle");menu?.addEventListener("click",()=>{const nav=$("siteNav"),open=nav.classList.toggle("open");menu.setAttribute("aria-expanded",String(open));});
  initialize();
})();
