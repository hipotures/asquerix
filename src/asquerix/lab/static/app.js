import './inspect.js';
import './gpu.js';
const {element,number,programView,curve,replayComparison}=LabInspect;
let capabilities, inventory, defaults, selectedId=null, selectedCampaign=null, selectedProgram=null, fixedDraft=null;
const ACTIVE=['QUEUED','PREPARING','RUNNING','PAUSE_REQUESTED','FINALIZING'];
const PHASES={QUEUED:'Waiting for the GPU worker',PREPARING:'Preparing common initial worlds',CONTROLS:'Evaluating fixed controls',SEARCH:'Searching programs',TRAINING:'Evaluating programs on the training bank',HOLDOUT:'Evaluating frozen winners on the holdout bank',REPLAYS:'Recording selected replays',FINALIZING:'Writing report and publishing',PAUSE_REQUESTED:'Pausing after the current group'};
// "Name · continued · continued" (older campaigns) and "Name · continuation 2" both read as base name + depth.
function lineage(name){const match=/^(.*?)((?: · continued)+| · continuation (\d+))$/.exec(name);if(!match)return {base:name,depth:0};return {base:match[1],depth:match[3]?Number(match[3]):match[2].split(' · continued').length-1};}
const PAGE=10;
let parentCounts={},bestKnown=null,programTotal=0,lastUpdate=0,chartArgs=null,resizeTimer=null;
addEventListener('resize',()=>{clearTimeout(resizeTimer);resizeTimer=setTimeout(()=>{if(chartArgs&&!document.getElementById('detail').hidden)curve(document.getElementById('live-curve'),...chartArgs);},150);});
function duration(seconds){if(typeof seconds!=='number')return '—';const s=Math.round(seconds);if(s<60)return `${s} s`;if(s<3600)return `${Math.floor(s/60)} min ${String(s%60).padStart(2,'0')} s`;return `${Math.floor(s/3600)} h ${String(Math.floor(s%3600/60)).padStart(2,'0')} min`;}
function plannedEpisodes(spec){const candidates=spec.search.methods.length*spec.search.candidate_budget_per_method,fixed=spec.controls.length+spec.fixed_programs.length,winners=spec.search.methods.length*(spec.continuation_of?2:1);return ((candidates+fixed)*spec.datasets.training.valid_count+(winners+fixed)*spec.datasets.holdout.valid_count)*spec.operator_replicates;}
function freshness(){const target=document.getElementById('campaign-freshness');if(!target||!lastUpdate)return;const seconds=Math.round((Date.now()-lastUpdate)/1000);target.textContent=ACTIVE.includes(selectedCampaign?.state)?`updated ${seconds<2?'just now':seconds+' s ago'}`:'';}
setInterval(freshness,1000);
let programSort='rank', catalogOffset=0, programOffset=0, currentCandidates=[], stream=null, refreshTimer=null, csrf=sessionStorage.getItem('asquerix-csrf')||'';
const form=document.getElementById('campaign-form');
const error=document.getElementById('error');
const field=name=>form.elements.namedItem(name);
const value=name=>field(name).value;
const numeric=name=>Number(value(name));
const checked=name=>field(name).checked;
function fail(message){error.textContent=message;error.hidden=false;}
function view(name){for(const id of ['catalog','create','detail'])document.getElementById(id).hidden=id!==name;error.hidden=true;}
async function api(path,{method='GET',body,key}={}){
  const response=await fetch('/api/v1'+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-Asquerix-Client':'lab-v1',...(csrf?{'X-CSRF-Token':csrf}:{}),...(method==='POST'?{'Idempotency-Key':key||crypto.randomUUID()}:{})},body:body===undefined?undefined:JSON.stringify(body)});
  const data=await response.json();
  if(response.status===401){document.getElementById('login').hidden=false;throw new Error('Sign in to connect to the laboratory.');}
  if(!response.ok)throw new Error(typeof data.detail==='string'?`${data.node_path?data.node_path+': ':''}${data.detail}`:JSON.stringify(data.detail));
  return data;
}
function buildAdvanced(){
  const operators=document.getElementById('operator-settings');operators.replaceChildren();
  const intervals={COMPRESS:['compress_fraction','Compression fraction',0.999],EXPAND:['expand_fraction','Expansion fraction',.25],MOVE:['move_distance','Movement radius (unit lengths)',.5],ROTATE:['rotate_angle_rad','Signed angle limit (rad)',Math.PI/4]};
  for(const [op,weight] of Object.entries(defaults.generation.weights)){
    const card=element('div',undefined,'card'),label=element('label',op+' generation weight'),input=element('input');input.name='weight_'+op;input.type='number';input.min='0';input.max='1000';input.value=String(weight);label.append(input);card.append(label);
    if(intervals[op])for(const bound of ['minimum','maximum']){
      const [key,title,cap]=intervals[op],rangeLabel=element('label',title+' '+bound),range=element('input');range.name=key+'_'+bound;range.type='number';range.step='any';range.min='0.000001';range.max=String(cap);range.value=String(defaults.generation[key][bound]);rangeLabel.append(range);card.append(rangeLabel);
    }
    operators.append(card);
  }
  const selectors=document.getElementById('selector-settings');selectors.replaceChildren();
  for(const kind of capabilities.selectors){const label=element('label',kind,'check'),input=element('input');input.type='checkbox';input.name='selector_'+kind;input.checked=true;label.prepend(input);selectors.append(label);}
  const mutations=document.getElementById('mutation-settings');mutations.replaceChildren();
  for(const [kind,weight] of Object.entries(defaults.generation.mutation_weights)){const label=element('label',kind+' weight'),input=element('input');input.type='number';input.name='mutation_'+kind;input.value=String(weight);input.min='0';input.max='1000';label.append(input);mutations.append(label);}
}
function spec(){
  const result=structuredClone(defaults);
  result.name=value('name');result.description=value('description');result.n=numeric('n');result.initial_side=numeric('initial_side');result.device=value('device');result.batch_capacity=numeric('batch_capacity');
  result.search.methods=value('method')==='both'?capabilities.methods:value('method')==='fixed'?[]:[value('method')];
  result.search.seed=value('search_seed');const byTime=value('stop_rule')==='time';
  result.search.time_budget_seconds=byTime?numeric('time_budget'):null;result.search.candidate_budget_per_method=byTime?1000000:numeric('candidate_budget');result.search.initial_pool=numeric('initial_pool');result.search.lambda=numeric('lambda');
  result.datasets.initializer_seed=value('initializer_seed');result.datasets.training={first_id:value('training_first_id'),valid_count:numeric('training_count')};result.datasets.holdout={first_id:value('holdout_first_id'),valid_count:numeric('holdout_count')};result.operator_seed=value('operator_seed');result.operator_replicates=numeric('replicates');
  result.controls=[...(checked('legacy_control')?['legacy_compress']:[]),...(checked('pulse_control')?['pulse_rotate']:[])];
  result.fixed_programs=value('method')==='fixed'?[fixedDraft||capabilities.controls[value('fixed_control')]]:[];
  result.work_limits={dispatches:numeric('dispatches'),compression_attempts:numeric('attempts'),contact_sweeps:numeric('sweeps'),constraint_visits:value('visits')?numeric('visits'):null};
  result.recording={...result.recording,automatic:checked('automatic_replays'),mode:value('recording_mode'),max_traces:numeric('max_traces'),max_frames_per_trace:numeric('max_frames'),max_trace_mib:numeric('trace_mib')};
  result.pose_evidence=value('pose_evidence');
  result.limits={max_seconds:byTime?Math.max(numeric('max_seconds'),numeric('time_budget')+600):numeric('max_seconds'),max_artifact_mib:numeric('artifact_mib')};result.publication.enabled=checked('publication');result.slice_sweeps=numeric('slice_sweeps');result.slice_dispatches=numeric('slice_dispatches');
  result.thresholds=value('thresholds').trim()?value('thresholds').split(',').map(Number):[];
  for(const name of ['min_nodes','max_nodes','repeat_probability','condition_probability','attempt_min','attempt_max','sweep_min','sweep_max'])result.generation[name]=numeric(name);
  for(const op of Object.keys(result.generation.weights))result.generation.weights[op]=numeric('weight_'+op);
  for(const key of ['compress_fraction','expand_fraction','move_distance','rotate_angle_rad'])for(const bound of ['minimum','maximum'])result.generation[key][bound]=numeric(key+'_'+bound);
  result.generation.selectors=capabilities.selectors.filter(kind=>checked('selector_'+kind));
  for(const kind of Object.keys(result.generation.mutation_weights))result.generation.mutation_weights[kind]=numeric('mutation_'+kind);
  return result;
}
function plan(){
  const data=spec(),fixed=data.controls.length+data.fixed_programs.length,methods=data.search.methods.length;
  const perProgram=data.datasets.training.valid_count*data.operator_replicates,lambda=data.search.lambda||Math.max(1,Math.floor(data.batch_capacity/perProgram));
  const stop=data.search.time_budget_seconds?`Search for ${duration(data.search.time_budget_seconds)} (${methods>1?`${duration(data.search.time_budget_seconds/methods)} per method`:'one method'})`:`Search until ${data.search.candidate_budget_per_method} programs per method`;
  document.getElementById('plan-summary').textContent=`${stop}, then holdout on ${data.datasets.holdout.valid_count} untouched starts. Each program runs on ${perProgram} training starts; (1 + λ) uses λ = ${lambda}, random search evaluates up to ${Math.max(lambda,Math.floor(data.batch_capacity/perProgram))} programs per GPU batch. ${fixed} fixed control(s). Hard stop after ${duration(data.limits.max_seconds)}. Exact poses: ${data.pose_evidence==='important'?'controls, improvements and the best 50 per method':'every program'}.`;
  return data;
}
async function catalog(){
  const page=await api(`/campaigns?limit=30&offset=${catalogOffset}&query=${encodeURIComponent(document.getElementById('catalog-query').value)}&state=${encodeURIComponent(document.getElementById('catalog-state').value)}`);
  const target=document.getElementById('campaign-list');target.replaceChildren();
  if(!page.total){const empty=element('div',undefined,'card empty');empty.append(element('h2','No campaigns recorded.'),element('p','Create a finite campaign, choose the detected GPU, and inspect actual programs and recorded geometry here.','muted'));target.append(empty);}
  for(const campaign of page.items){const card=element('article',undefined,'card'),title=element('h2',`n=${campaign.spec.n} · ${(({base,depth})=>depth?`${base} · continuation ${depth}`:base)(lineage(campaign.spec.name))}`),open=element('button','Open campaign');open.addEventListener('click',()=>openCampaign(campaign.id));card.append(title,element('p',`n=${campaign.spec.n} · ${campaign.spec.search.methods.join(' + ')||'Fixed programs'} · ${campaign.state} · ${campaign.device_uuid||campaign.spec.device}`,'muted'),element('p',`${campaign.summary.completed_candidates||0} candidates completed · ${campaign.summary.completed_episode_executions||0} scientific episodes · publication ${campaign.publication.status||'PENDING'}`),open);target.append(card);}
  document.getElementById('catalog-page').textContent=`${catalogOffset+1}–${Math.min(catalogOffset+30,page.total)} of ${page.total}`;
  document.getElementById('catalog-previous').disabled=catalogOffset===0;document.getElementById('catalog-next').disabled=catalogOffset+30>=page.total;
}
async function inspect(candidate){
  selectedProgram=candidate;document.getElementById('episodes-heading').hidden=false;
  for(const row of document.querySelectorAll('#program-table tr'))row.classList.toggle('selected',row.dataset.candidateId===candidate.id);
  const related=[...currentCandidates];
  if(candidate.parent_id&&!related.some(item=>item.id===candidate.parent_id))try{related.push(await api(`/campaigns/${selectedId}/candidate/${encodeURIComponent(candidate.parent_id)}`));}catch{}
  programView(document.getElementById('program-inspector'),candidate,related);document.getElementById('clone-program').hidden=false;
  const episodes=await api(`/campaigns/${selectedId}/episodes?candidate_id=${encodeURIComponent(candidate.id)}&limit=10`),target=document.getElementById('episode-list');target.replaceChildren();
  const table=element('table',undefined,'episodes'),head=element('tr');
  for(const [text,cls] of [['Start',''],['Best L','num'],['Final L','num'],['Validation',''],['','']])head.append(element('th',text,cls));
  table.append(element('thead'));table.tHead.append(head);const body=element('tbody');table.append(body);
  for(const episode of episodes.items){
    const row=element('tr'),valid=episode.validation.status==='NUMERICALLY_VALIDATED';
    const start=element('td',`${episode.bank} ${episode.initial_id}`);start.title=`Replicate ${episode.replicate}`;
    const status=element('td',valid?'✓ validated':episode.validation.status.toLowerCase().replaceAll('_',' '),valid?'ok':'bad');status.title=episode.validation.status;
    const cell=element('td'),button=element('button','Replay');button.title='Queue a recorded geometric replay of this episode';
    button.addEventListener('click',async()=>{try{const queued=await api(`/campaigns/${selectedId}/replays`,{method:'POST',body:{candidate_id:candidate.id,episode_key:episode.episode_key,mode:'accepted',max_frames:256,max_mib:10}});button.textContent=queued.state==='QUEUED'?'Queued':queued.state.toLowerCase();button.disabled=true;}catch(e){fail(e.message);}});
    cell.append(button);row.append(start,element('td',number(episode.best_L),'num'),element('td',number(episode.current_L),'num'),status,cell);body.append(row);}
  if(!episodes.items.length){target.append(element('p','Exact poses were not kept for this program: only controls, improvements and the best 50 programs per method keep them. Its score still covers every episode, each validated on the CPU.','muted'));return;}
  target.append(table);
  if(episodes.total>episodes.items.length)target.append(element('p',`Showing ${episodes.items.length} of ${episodes.total} episodes.`,'muted'));
}
async function programs(){
  const page=await api(`/campaigns/${selectedId}/programs?limit=${PAGE}&offset=${programOffset}&sort=${programSort}`);currentCandidates=page.items;
  for(const header of document.querySelectorAll('#tab-programs th'))header.removeAttribute('aria-sort');
  document.querySelector(`#tab-programs .sort[data-sort=${programSort}]`).closest('th').setAttribute('aria-sort','ascending');
  const target=document.getElementById('program-table');target.replaceChildren();
  for(const candidate of page.items){
    const row=element('tr'),score=candidate.score||{},valid=score.validation_counts?.NUMERICALLY_VALIDATED||0;
    row.dataset.candidateId=candidate.id;row.classList.toggle('selected',selectedProgram?.id===candidate.id);
    const label=element('td',`${candidate.arm.replaceAll('_',' ')} · #${candidate.position}`);label.title=candidate.id;
    const validity=element('td',`${valid}/${score.expected_episodes||0}${score.eligible?' ✓':''}`);validity.title=score.eligible?'All episodes independently validated; eligible for ranking':'Incomplete or not all episodes validated';
    const rank=programSort==='rank'&&score.eligible?String(programOffset+page.items.indexOf(candidate)+1):'';
    row.append(element('td',rank,'num rank'),label,element('td',number(score.mean_best_L),'num'),element('td',number(score.best_L),'num'),validity);
    const cell=element('td'),button=element('button','Inspect');button.addEventListener('click',()=>inspect(candidate).catch(e=>fail(e.message)));cell.append(button);row.append(cell);target.append(row);}
  programTotal=page.total;const last=Math.max(0,Math.ceil(page.total/PAGE)-1)*PAGE;
  document.getElementById('program-page').textContent=page.total?`${programOffset+1}–${Math.min(programOffset+PAGE,page.total)} of ${page.total}`:'none yet';
  for(const button of document.querySelectorAll('.pager button'))button.disabled=Number(button.dataset.pages)<0||button.id==='program-first'?programOffset===0:programOffset>=last;
  const comparison=await api(`/campaigns/${selectedId}/comparison`),key=document.getElementById('live-curve-axis').value;
  // The server returns only improvements with their positions, plus per-method totals for the axis length.
  const points=[];
  for(const candidate of comparison.candidates){if(['controls','fixed'].includes(candidate.arm))continue;
    points.push({arm:candidate.arm,candidate_id:candidate.id,x:key==='evaluations'?candidate.x_evaluations:key==='work'?candidate.x_work:candidate.x_time,y:candidate.score.mean_best_L});}
  const xTotal=Math.max(1,...Object.values(comparison.totals||{}).map(total=>key==='evaluations'?total.evaluations:key==='work'?total.work:total.time));
  const known=bestKnown?.entries.find(entry=>entry.n===selectedCampaign.spec.n),source=bestKnown?.source;
  const note=document.getElementById('best-known-source');note.textContent=known?`Best known upper bound s(${known.n}) ≤ ${known.printed}${known.author?` — ${known.author}`:''}${known.optimal_in_source?' (proved optimal there)':''}. Source: ${source.author}, “${source.title}”, ${source.citation}, Table 1. Display only; never used by the search.`:'';
  const references=comparison.candidates.filter(item=>['controls','fixed'].includes(item.arm)&&item.score?.eligible).map(item=>({label:(item.name||`${item.arm} #${item.position}`).replaceAll('_',' '),value:item.score.mean_best_L}));
  if(known)references.push({label:`best known (${source.revision_year})`,value:known.upper_bound,kind:'best-known'});
  const inherited=summary=>summary?.continuation?.inherited_candidates;
  const marker=key==='evaluations'&&inherited(selectedCampaign.summary)?{x:inherited(selectedCampaign.summary)/selectedCampaign.spec.search.methods.length,label:'continuation starts'}:null;
  chartArgs=[points,{xMax:xTotal,marker,xLabel:key==='evaluations'?'Completed candidates per method':key==='work'?'Charged work per method':'Method execution time (s)',references,onSelect:async point=>inspect(await api(`/campaigns/${selectedId}/candidate/${encodeURIComponent(point.candidate_id)}`))}];
  curve(document.getElementById('live-curve'),...chartArgs);
}
async function history(){
  const page=await api(`/campaigns/${selectedId}/history?limit=1`),target=document.getElementById('live-history');target.replaceChildren();
  if(!page.total){target.append(element('p','No durable events yet.'));return;}
  const slider=element('input'),label=element('p'),detail=element('pre'),known=element('div');slider.type='range';slider.min='0';slider.max=String(page.total-1);slider.value=String(page.total-1);slider.setAttribute('aria-label','Campaign history event');
  const show=async()=>{const state=await api(`/campaigns/${selectedId}/history-state?index=${slider.value}`);label.textContent=`Event ${state.event.id} · ${state.event.kind} · ${new Date(state.event.created*1000).toLocaleString()}`;detail.textContent=JSON.stringify(state.event.payload,null,2);known.replaceChildren();if(state.candidate)programView(known,state.candidate,state.candidates||[]);known.prepend(element('p',`Known parent: ${state.parent_id||'none'}; ${state.completed_candidates} candidate evaluations were complete at this event.`,'muted'));};
  slider.addEventListener('input',()=>show().catch(e=>fail(e.message)));target.append(slider,label,known,detail);await show();
}
function replays(){
  const records=(selectedCampaign.replays||[]).filter(record=>record.state==='REPLAY_MATCHED'||record.state==='REPLAY_MISMATCH').map(record=>record.document);
  replayComparison(document.getElementById('live-replays'),records,replay=>'/api/v1/artifacts/'+replay.artifacts.find(item=>item.path.endsWith('.html')).id);
}
// Rates count only this campaign's own work: a continuation's inherited episodes and programs are subtracted.
function speed(spec,summary){
  const inherited=parentCounts[spec.continuation_of]||{episodes:0,programs:0},seconds=summary.elapsed_execution_seconds||0;
  if(seconds<1)return '—';
  const episodes=((summary.completed_episode_executions||0)-inherited.episodes)/seconds,programs=((summary.completed_candidates||0)-inherited.programs)/seconds;
  const perGeneration=programs>0?spec.search.lambda/programs:null;
  return `${episodes.toFixed(1)} episodes/s\n${programs.toFixed(2)} programs/s${perGeneration?` · ${duration(perGeneration)} per generation`:''}`;
}
async function refresh(){
  if(!selectedId)return;
  selectedCampaign=await api(`/campaigns/${selectedId}`);
  const parentId=selectedCampaign.spec.continuation_of;
  if(parentId&&!parentCounts[parentId]){try{const parent=await api(`/campaigns/${parentId}`);parentCounts[parentId]={episodes:parent.summary.completed_episode_executions||0,programs:parent.summary.completed_candidates||0};}catch{parentCounts[parentId]={episodes:0,programs:0};}}const {spec,summary,state,publication}=selectedCampaign;
  const {base,depth}=lineage(spec.name);
  document.getElementById('campaign-n').textContent=`n = ${spec.n}`;document.getElementById('campaign-name').textContent=base;
  document.getElementById('campaign-lineage').textContent=depth?` · continuation ${depth}`:'';document.title=`n=${spec.n} · ${base} — Asquerix`;
  const scope=document.getElementById('campaign-scope');scope.textContent=`${spec.datasets.training.valid_count} training and ${spec.datasets.holdout.valid_count} holdout starts`;
  if(spec.continuation_of){const link=element('a','the previous campaign');link.href='#'+spec.continuation_of;link.addEventListener('click',event=>{event.preventDefault();openCampaign(spec.continuation_of);});scope.append(' · continues ',link);}
  const badge=document.getElementById('campaign-state');badge.dataset.state=state;badge.textContent=state.charAt(0)+state.slice(1).toLowerCase().replaceAll('_',' ');
  const metrics=document.getElementById('campaign-metrics');metrics.replaceChildren();
  for(const [label,text] of [[spec.search.time_budget_seconds?'Programs tried':'Programs tried / candidate budget',spec.search.time_budget_seconds?String(summary.completed_candidates||0):`${summary.completed_candidates||0} / ${spec.search.methods.length*spec.search.candidate_budget_per_method}`],['Scientific episodes',String(summary.completed_episode_executions||0)],['Best mean L (training)',number(summary.training_incumbent?.mean_best_L)],['GPU execution time',duration(summary.elapsed_execution_seconds)],['Speed',speed(spec,summary)]]){const box=element('div',undefined,'metric'),[main,...detail]=text.split('\n');box.append(element('small',label),element('strong',main));if(detail.length)box.append(element('small',detail.join(' ')));metrics.append(box);}
  const active=ACTIVE.includes(state),plan=plannedEpisodes(spec),done=summary.completed_episode_executions||0;
  const activity=document.getElementById('campaign-activity');activity.dataset.active=String(active);
  const searching=spec.search.methods.includes(summary.arm);
  activity.textContent=active?`${PHASES[summary.phase]||PHASES[state]||'Working'}${summary.arm?' · '+summary.arm.replaceAll('_',' '):''}${searching?' · generation '+(summary.generation??0):''}`
    :state==='COMPLETED'?`Finished: ${done} scientific episodes in ${duration(summary.elapsed_execution_seconds)} of GPU execution`
    :state==='PARTIAL'?`Stopped before completion (${{USER_STOP:'stopped by user',EXECUTION_DEADLINE:'execution time limit reached'}[summary.stop_reason]||'stopped'}); completed results are kept`
    :state==='PAUSED'?'Paused; Resume continues from the last finished group'
    :`${state==='FAILED'?'Failed':'Interrupted'}${summary.error?': '+summary.error:''}`;
  const timed=spec.search.time_budget_seconds,seconds=summary.elapsed_execution_seconds||0;
  const fraction=state==='COMPLETED'?1:timed?Math.min(1,seconds/timed):Math.min(1,done/Math.max(1,plan));
  document.getElementById('campaign-progress-bar').style.width=`${(fraction*100).toFixed(1)}%`;
  document.querySelector('.activity .progress').setAttribute('aria-valuenow',String(Math.round(fraction*100)));
  document.getElementById('campaign-progress-label').textContent=timed&&state!=='COMPLETED'?`${duration(Math.min(seconds,timed))} of ${duration(timed)} search time · ${done} scientific episodes${seconds>=timed?' · holdout and replays':''}`:`${done} / ${state==='COMPLETED'?done:plan} scientific episodes${state==='COMPLETED'?'':' (holdout count is an upper bound)'}`;
  lastUpdate=Date.now();freshness();
  const published=publication.status==='PUBLISHED',status=publication.status||(active?'PENDING':'NONE');
  const line=document.getElementById('campaign-provenance');
  line.replaceChildren(`${spec.device} · ${selectedCampaign.device_uuid||'GPU not resolved yet'} · profile ${(summary.profile_hash||spec.evaluation_profile).slice(0,12)} · GitHub: `);
  if(published){const link=element('a',`published, commit ${publication.commit_sha.slice(0,7)}`);link.href=publication.url;link.target='_blank';link.rel='noopener';line.append(link);}
  else line.append({PENDING:'published after the campaign finishes',LOCAL_ONLY:'not published (local results only)',FAILED:`publication failed (${publication.error||'see server log'}); local results are kept`,NONE:'not published'}[status]||status);
  // Show only the lifecycle actions that apply to the current state.
  document.getElementById('pause-campaign').hidden=!['QUEUED','PREPARING','RUNNING'].includes(state);document.getElementById('resume-campaign').hidden=!['PAUSED','INTERRUPTED'].includes(state);document.getElementById('stop-campaign').hidden=!['QUEUED','PREPARING','RUNNING','PAUSE_REQUESTED','PAUSED'].includes(state);
  document.getElementById('continue-campaign').hidden=!(['COMPLETED','PARTIAL'].includes(state)&&spec.search.methods.length);
  document.querySelector('.campaign-bar .divider').hidden=['pause','resume','stop'].every(name=>document.getElementById(name+'-campaign').hidden);
  const report=document.getElementById('open-report');report.hidden=!summary.report_artifact_id;if(!report.hidden)report.href='/api/v1/artifacts/'+summary.report_artifact_id;
  const download=document.getElementById('download-export');download.hidden=summary.report_status!=='READY';download.href=`/api/v1/campaigns/${selectedId}/export`;
  await programs();
  if(!document.getElementById('tab-history').hidden)await history();
  if(!document.getElementById('tab-replays').hidden)replays();
}
async function openCampaign(identifier){
  document.getElementById('continue-form').hidden=true;selectedId=identifier;selectedProgram=null;programOffset=0;location.hash=identifier;view('detail');if(stream)stream.close();await refresh();
  stream=new EventSource(`/api/v1/campaigns/${identifier}/events`);
  let last=0n;
  stream.addEventListener('progress',event=>{const id=BigInt(event.lastEventId||'0');if(id<=last)return;last=id;if(!refreshTimer)refreshTimer=setTimeout(()=>{refreshTimer=null;refresh().catch(e=>fail(e.message));},700);});
  stream.addEventListener('reset',()=>{last=0n;refresh().catch(e=>fail(e.message));});
}
function stopRule(){for(const label of form.querySelectorAll('[data-stop]'))label.hidden=label.dataset.stop!==value('stop_rule');}
field('stop_rule').addEventListener('change',()=>{stopRule();plan();});
function create(){stopRule();if(stream)stream.close();selectedId=null;location.hash='';view('create');for(const input of form.querySelectorAll('input[data-step]'))stepperState(input);plan();}
for(const name of ['pause','resume','stop'])document.getElementById(name+'-campaign').addEventListener('click',async()=>{try{await api(`/campaigns/${selectedId}/${name}`,{method:'POST'});await refresh();}catch(e){fail(e.message);}});
document.getElementById('new-campaign').addEventListener('click',create);document.getElementById('cancel-create').addEventListener('click',()=>{view('catalog');catalog();});document.getElementById('back-catalog').addEventListener('click',()=>{if(stream)stream.close();selectedId=null;location.hash='';view('catalog');catalog();});
document.getElementById('review-plan').addEventListener('click',()=>{try{plan();}catch(e){fail(e.message);}});
form.addEventListener('submit',async event=>{event.preventDefault();const button=document.getElementById('launch-campaign');button.disabled=true;try{const queued=await api('/campaigns',{method:'POST',body:plan()});await openCampaign(queued.id);}catch(e){fail(e.message);}finally{button.disabled=false;}});
document.getElementById('filter-catalog').addEventListener('click',()=>{catalogOffset=0;catalog().catch(e=>fail(e.message));});
for(const [id,change] of [['catalog-previous',-30],['catalog-next',30]])document.getElementById(id).addEventListener('click',()=>{catalogOffset=Math.max(0,catalogOffset+change);catalog();});
for(const button of document.querySelectorAll('.pager button'))button.addEventListener('click',()=>{
  const last=Math.max(0,Math.ceil(programTotal/PAGE)-1)*PAGE;
  programOffset=button.id==='program-first'?0:button.id==='program-last'?last:Math.min(last,Math.max(0,programOffset+Number(button.dataset.pages)*PAGE));
  programs().catch(e=>fail(e.message));});
document.getElementById('live-curve-axis').addEventListener('change',()=>programs());
for(const button of document.querySelectorAll('#tab-programs .sort'))button.addEventListener('click',()=>{programSort=button.dataset.sort;programOffset=0;programs().catch(e=>fail(e.message));});
for(const button of document.querySelectorAll('[data-tab]'))button.addEventListener('click',async()=>{for(const tab of ['programs','history','replays'])document.getElementById('tab-'+tab).hidden=tab!==button.dataset.tab;for(const other of document.querySelectorAll('[data-tab]'))other.setAttribute('aria-selected',String(other===button));if(button.dataset.tab==='history')await history();if(button.dataset.tab==='replays')replays();});
// Arrow keys, the spinner and the wheel step the batch and storage size fields by powers of two;
// typed values are kept as entered. Keys are handled directly; spinner/wheel steps are any input that is
// not typing or deleting (browsers differ in the event they raise for a step).
function stepped(input,up){
  const mode=input.dataset.step,value=Number(input.dataset.previous??input.value),min=Number(input.min||1),max=Number(input.max||Infinity);
  if(!Number.isFinite(value)||value<=0)return;
  let next;
  if(mode==='pow2')next=up?2**Math.floor(Math.log2(value)+1):2**Math.ceil(Math.log2(value)-1);
  else{const unit=Number(mode);next=up?(Math.floor(value/unit)+1)*unit:(Math.ceil(value/unit)-1)*unit;}
  input.value=String(Math.min(max,Math.max(min,next)));input.dataset.previous=input.value;stepperState(input);
}
document.addEventListener('focusin',event=>{const input=event.target;if(input.dataset?.step)input.dataset.previous=input.value;});
// Explicit − / + buttons replace the browser spinner, which browsers implement inconsistently.
function stepperState(input){const wrap=input.parentElement;if(!wrap?.classList.contains('stepper'))return;const value=Number(input.value),min=Number(input.min||1),max=Number(input.max||Infinity);
  const [down,up]=wrap.querySelectorAll('button');down.disabled=!(value>min);up.disabled=!(value<max);up.title=up.disabled?`Maximum ${input.max}`:up.dataset.title;down.title=down.disabled?`Minimum ${input.min||1}`:down.dataset.title;}
function addSteppers(root=document){for(const input of root.querySelectorAll('input[data-step]')){if(input.parentElement.classList.contains('stepper'))continue;
  const wrap=element('span',undefined,'stepper'),pow2=input.dataset.step==='pow2';input.replaceWith(wrap);wrap.append(input);
  for(const [up,text,title] of [[false,'−',pow2?'Halve':`−${input.dataset.step}`],[true,'+',pow2?'Double':`+${input.dataset.step}`]]){
    const button=element('button',text);button.type='button';button.dataset.title=title;button.setAttribute('aria-label',title);
    button.addEventListener('click',()=>{input.dataset.previous=input.value;stepped(input,up);input.dispatchEvent(new Event('change',{bubbles:true}));stepperState(input);});
    up?wrap.append(button):wrap.insertBefore(button,input);}
  input.addEventListener('input',()=>stepperState(input));stepperState(input);}}
addSteppers();
document.addEventListener('keydown',event=>{const input=event.target;if(!input.dataset?.step||!['ArrowUp','ArrowDown'].includes(event.key))return;event.preventDefault();input.dataset.previous=input.value;stepped(input,event.key==='ArrowUp');});
document.addEventListener('input',event=>{
  const input=event.target;if(!input.dataset?.step)return;
  const typing=/^(insert|delete)/.test(event.inputType||'');
  const previous=Number(input.dataset.previous),current=Number(input.value);
  if(!typing&&Number.isFinite(previous)&&current!==previous){const up=current>previous;input.value=String(previous);stepped(input,up);}
  else input.dataset.previous=input.value;
});
const continueForm=document.getElementById('continue-form');
function continueRule(){const rule=continueForm.elements.namedItem('continue_rule').value;for(const label of continueForm.querySelectorAll('[data-continue]'))label.hidden=label.dataset.continue!==rule;}
continueForm.elements.namedItem('continue_rule').addEventListener('change',continueRule);
document.getElementById('continue-campaign').addEventListener('click',()=>{
  const {spec}=selectedCampaign,f=continueForm.elements;
  f.namedItem('additional').value='1000';f.namedItem('continue_rule').value='time';f.namedItem('continue_time').value=String(spec.search.time_budget_seconds||300);continueRule();const {base,depth}=lineage(spec.name);f.namedItem('name').value=`${base.slice(0,130)} · continuation ${depth+1}`;
  f.namedItem('device').replaceChildren(...inventory.items.map(item=>{const option=element('option',`${item.name} · ${item.device}`);option.value=item.device;return option;}));f.namedItem('device').value=spec.device;
  f.namedItem('batch_capacity').value=String(spec.batch_capacity);f.namedItem('max_seconds').value=String(spec.limits.max_seconds);f.namedItem('max_artifact_mib').value=String(spec.limits.max_artifact_mib);
  f.namedItem('automatic_replays').checked=spec.recording.automatic;f.namedItem('publication').checked=spec.publication.enabled;
  document.getElementById('continue-locked').textContent=`Kept from the original so results stay comparable: n=${spec.n}, initial side ${spec.initial_side}, ${spec.datasets.training.valid_count} training and ${spec.datasets.holdout.valid_count} holdout starts, all seeds, the evaluation profile and work caps, the generation and mutation law, λ=${spec.search.lambda}, methods (${spec.search.methods.join(', ')}) and controls. Change those with “Clone as draft”, which starts from scratch.`;
  for(const input of continueForm.querySelectorAll('input[data-step]'))stepperState(input);
  continueForm.hidden=false;f.namedItem('additional').focus();});
document.getElementById('cancel-continue').addEventListener('click',()=>{continueForm.hidden=true;});
continueForm.addEventListener('submit',async event=>{event.preventDefault();const f=continueForm.elements,button=continueForm.querySelector('[type=submit]');button.disabled=true;
  try{const created=await api(`/campaigns/${selectedId}/continue`,{method:'POST',body:{...(f.namedItem('continue_rule').value==='time'?{additional_candidates_per_method:1000000,time_budget_seconds:Number(f.namedItem('continue_time').value)}:{additional_candidates_per_method:Number(f.namedItem('additional').value)}),name:f.namedItem('name').value,device:f.namedItem('device').value,batch_capacity:Number(f.namedItem('batch_capacity').value),max_seconds:Number(f.namedItem('max_seconds').value),max_artifact_mib:Number(f.namedItem('max_artifact_mib').value),automatic_replays:f.namedItem('automatic_replays').checked,publication:f.namedItem('publication').checked}});
    continueForm.hidden=true;await openCampaign(created.id);}catch(e){fail(e.message);}finally{button.disabled=false;}});
document.getElementById('clone-program').addEventListener('click',()=>{fixedDraft=structuredClone(selectedProgram.program.authored);field('method').value='fixed';field('name').value=(fixedDraft.name||'Inspected strategy')+' evaluation';field('fixed_control').querySelector('[value=cloned]').disabled=false;field('fixed_control').value='cloned';field('legacy_control').checked=false;field('pulse_control').checked=false;create();});
field('fixed_control').addEventListener('change',()=>{fixedDraft=null;});
document.getElementById('clone-campaign').addEventListener('click',async()=>{try{const clone=await api(`/campaigns/${selectedId}/clone`,{method:'POST'});const draft=await api(`/campaigns/${clone.id}`);defaults=draft.spec;field('name').value=defaults.name;field('n').value=defaults.n;field('training_count').value=defaults.datasets.training.valid_count;field('holdout_count').value=defaults.datasets.holdout.valid_count;field('candidate_budget').value=defaults.search.candidate_budget_per_method;field('initial_pool').value=defaults.search.initial_pool;field('lambda').value=defaults.search.lambda;buildAdvanced();create();}catch(e){fail(e.message);}});
document.getElementById('login-form').addEventListener('submit',async event=>{event.preventDefault();try{const result=await api('/session',{method:'POST',body:{token:document.getElementById('access-token').value}});csrf=result.csrf_token;sessionStorage.setItem('asquerix-csrf',csrf);document.getElementById('access-token').value='';document.getElementById('login').hidden=true;await start();}catch(e){fail(e.message);}});
async function start(){capabilities=await api('/capabilities');field('n').removeAttribute('max');try{bestKnown=await api('/references/best-known');}catch{bestKnown=null;}defaults=capabilities.defaults;inventory=await api('/devices');buildAdvanced();field('device').replaceChildren();for(const device of inventory.items){const option=element('option',`${device.name} · ${device.uuid}`);option.value=device.device;field('device').append(option);}document.getElementById('device-summary').textContent=inventory.items.length?inventory.items.map(item=>item.name).join(', '):'No accessible CUDA GPU';document.getElementById('launch-campaign').disabled=!inventory.items.length;document.getElementById('resource-warning').textContent=inventory.items.map(item=>`${item.device}: ${item.memory_used_mib}/${item.memory_total_mib} MiB in use, ${item.utilization_percent}% device activity. ${item.warning}`).join(' ');const identifier=location.hash.slice(1);if(/^[a-f0-9]{32}$/.test(identifier))await openCampaign(identifier);else await catalog();}
start().catch(e=>fail(e.message));
