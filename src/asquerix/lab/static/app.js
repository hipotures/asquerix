import './inspect.js';
const {element,number,programView,curve,replayComparison}=LabInspect;
let capabilities, inventory, defaults, selectedId=null, selectedCampaign=null, selectedProgram=null, fixedDraft=null;
let catalogOffset=0, programOffset=0, currentCandidates=[], stream=null, refreshTimer=null, csrf=sessionStorage.getItem('asquerix-csrf')||'';
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
  result.search.seed=value('search_seed');result.search.candidate_budget_per_method=numeric('candidate_budget');result.search.initial_pool=numeric('initial_pool');result.search.lambda=numeric('lambda');
  result.datasets.initializer_seed=value('initializer_seed');result.datasets.training={first_id:value('training_first_id'),valid_count:numeric('training_count')};result.datasets.holdout={first_id:value('holdout_first_id'),valid_count:numeric('holdout_count')};result.operator_seed=value('operator_seed');result.operator_replicates=numeric('replicates');
  result.controls=[...(checked('legacy_control')?['legacy_compress']:[]),...(checked('pulse_control')?['pulse_rotate']:[])];
  result.fixed_programs=value('method')==='fixed'?[fixedDraft||capabilities.controls[value('fixed_control')]]:[];
  result.work_limits={dispatches:numeric('dispatches'),compression_attempts:numeric('attempts'),contact_sweeps:numeric('sweeps'),constraint_visits:value('visits')?numeric('visits'):null};
  result.recording={...result.recording,automatic:checked('automatic_replays'),mode:value('recording_mode'),max_traces:numeric('max_traces'),max_frames_per_trace:numeric('max_frames'),max_trace_mib:numeric('trace_mib')};
  result.limits={max_seconds:numeric('max_seconds'),max_artifact_mib:numeric('artifact_mib')};result.publication.enabled=checked('publication');result.slice_sweeps=numeric('slice_sweeps');result.slice_dispatches=numeric('slice_dispatches');
  result.thresholds=value('thresholds').trim()?value('thresholds').split(',').map(Number):[];
  for(const name of ['min_nodes','max_nodes','repeat_probability','condition_probability','attempt_min','attempt_max','sweep_min','sweep_max'])result.generation[name]=numeric(name);
  for(const op of Object.keys(result.generation.weights))result.generation.weights[op]=numeric('weight_'+op);
  for(const key of ['compress_fraction','expand_fraction','move_distance','rotate_angle_rad'])for(const bound of ['minimum','maximum'])result.generation[key][bound]=numeric(key+'_'+bound);
  result.generation.selectors=capabilities.selectors.filter(kind=>checked('selector_'+kind));
  for(const kind of Object.keys(result.generation.mutation_weights))result.generation.mutation_weights[kind]=numeric('mutation_'+kind);
  return result;
}
function plan(){
  const data=spec(),candidateCount=data.search.methods.length*data.search.candidate_budget_per_method,fixed=data.controls.length+data.fixed_programs.length;
  const episodes=(candidateCount+fixed)*data.datasets.training.valid_count*data.operator_replicates;
  const holdout=(data.search.methods.length+fixed)*data.datasets.holdout.valid_count*data.operator_replicates;
  const bytes=(episodes+holdout)*(24*data.n+2048);
  document.getElementById('plan-summary').textContent=`${candidateCount} new candidate evaluations; ${episodes} logical training episodes; up to ${holdout} holdout episodes after winners are frozen. Approximate native evidence ${(bytes/1048576).toFixed(2)} MiB, plus reports/replays within declared quotas. Maximum ${data.limits.max_seconds} execution seconds. Automatic replay cap ${data.recording.automatic?data.recording.max_traces:0}. No unmeasured time forecast.`;
  return data;
}
async function catalog(){
  const page=await api(`/campaigns?limit=30&offset=${catalogOffset}&query=${encodeURIComponent(document.getElementById('catalog-query').value)}&state=${encodeURIComponent(document.getElementById('catalog-state').value)}`);
  const target=document.getElementById('campaign-list');target.replaceChildren();
  if(!page.total){const empty=element('div',undefined,'card empty');empty.append(element('h2','No campaigns recorded.'),element('p','Create a finite campaign, choose the detected GPU, and inspect actual programs and recorded geometry here.','muted'));target.append(empty);}
  for(const campaign of page.items){const card=element('article',undefined,'card'),title=element('h2',campaign.spec.name),open=element('button','Open campaign');open.addEventListener('click',()=>openCampaign(campaign.id));card.append(title,element('p',`n=${campaign.spec.n} · ${campaign.spec.search.methods.join(' + ')||'Fixed programs'} · ${campaign.state} · ${campaign.device_uuid||campaign.spec.device}`,'muted'),element('p',`${campaign.summary.completed_candidates||0} candidates completed · ${campaign.summary.completed_episode_executions||0} scientific episodes · publication ${campaign.publication.status||'PENDING'}`),open);target.append(card);}
  document.getElementById('catalog-page').textContent=`${catalogOffset+1}–${Math.min(catalogOffset+30,page.total)} of ${page.total}`;
  document.getElementById('catalog-previous').disabled=catalogOffset===0;document.getElementById('catalog-next').disabled=catalogOffset+30>=page.total;
}
async function inspect(candidate){
  selectedProgram=candidate;
  const related=[...currentCandidates];
  if(candidate.parent_id&&!related.some(item=>item.id===candidate.parent_id))try{related.push(await api(`/campaigns/${selectedId}/candidate/${encodeURIComponent(candidate.parent_id)}`));}catch{}
  programView(document.getElementById('program-inspector'),candidate,related);document.getElementById('clone-program').hidden=false;
  const episodes=await api(`/campaigns/${selectedId}/episodes?candidate_id=${encodeURIComponent(candidate.id)}&limit=10`),target=document.getElementById('episode-list');target.replaceChildren();
  for(const episode of episodes.items){const box=element('p',`${episode.bank} start ${episode.initial_id} / replicate ${episode.replicate}: best L ${number(episode.best_L)}, current L ${number(episode.current_L)} · ${episode.validation.status}`),button=element('button','Queue geometric replay');button.addEventListener('click',async()=>{try{const queued=await api(`/campaigns/${selectedId}/replays`,{method:'POST',body:{candidate_id:candidate.id,episode_key:episode.episode_key,mode:'accepted',max_frames:256,max_mib:10}});box.append(element('small',` Replay ${queued.state}`));}catch(e){fail(e.message);}});box.append(button);target.append(box);}
}
async function programs(){
  const page=await api(`/campaigns/${selectedId}/programs?limit=50&offset=${programOffset}`);currentCandidates=page.items;
  const target=document.getElementById('program-table');target.replaceChildren();
  for(const candidate of page.items){const row=element('tr'),score=candidate.score||{};for(const text of [`${candidate.arm} / ${candidate.position}`,number(score.mean_best_L),number(score.best_L),`${score.validation_counts?.NUMERICALLY_VALIDATED||0}/${score.expected_episodes||0}${score.eligible?' eligible':''}`])row.append(element('td',text));const cell=element('td'),button=element('button','Inspect');button.addEventListener('click',()=>inspect(candidate).catch(e=>fail(e.message)));cell.append(button);row.append(cell);target.append(row);}
  document.getElementById('program-page').textContent=`${programOffset+1}–${Math.min(programOffset+50,page.total)} of ${page.total}`;document.getElementById('program-previous').disabled=programOffset===0;document.getElementById('program-next').disabled=programOffset+50>=page.total;
  const comparison=await api(`/campaigns/${selectedId}/comparison`),key=document.getElementById('live-curve-axis').value;
  const points=[],counts={},work={},incumbent={};
  for(const candidate of comparison.candidates){if(['controls','fixed'].includes(candidate.arm))continue;counts[candidate.arm]=(counts[candidate.arm]||0)+(candidate.score.complete?1:0);work[candidate.arm]=(work[candidate.arm]||0)+(candidate.score.total_charged_work||0);if(candidate.score.eligible){incumbent[candidate.arm]=Math.min(incumbent[candidate.arm]??Infinity,candidate.score.mean_best_L);points.push({arm:candidate.arm,candidate_id:candidate.id,x:key==='evaluations'?counts[candidate.arm]:key==='work'?work[candidate.arm]:candidate.arm_execution_elapsed_seconds,y:incumbent[candidate.arm]});}}
  curve(document.getElementById('live-curve'),points,{xLabel:key==='evaluations'?'Completed candidates':key==='work'?'Charged work':'Arm execution seconds',onSelect:async point=>inspect(await api(`/campaigns/${selectedId}/candidate/${encodeURIComponent(point.candidate_id)}`))});
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
async function refresh(){
  if(!selectedId)return;
  selectedCampaign=await api(`/campaigns/${selectedId}`);const {spec,summary,state,publication}=selectedCampaign;
  document.getElementById('campaign-name').textContent=spec.name;document.getElementById('campaign-scope').textContent=`n=${spec.n} · ${spec.device} / ${selectedCampaign.device_uuid||'resolving physical identity'} · ${summary.profile_hash||spec.evaluation_profile} · training ${spec.datasets.training.valid_count}, holdout ${spec.datasets.holdout.valid_count}`;const badge=document.getElementById('campaign-state');badge.dataset.state=state;badge.textContent=state.charAt(0)+state.slice(1).toLowerCase().replaceAll('_',' ');
  const metrics=document.getElementById('campaign-metrics');metrics.replaceChildren();
  for(const [label,text] of [['Completed candidates',`${summary.completed_candidates||0} / ${spec.search.methods.length*spec.search.candidate_budget_per_method}`],['Scientific episodes',String(summary.completed_episode_executions||0)],['Training incumbent mean L',number(summary.training_incumbent?.mean_best_L)],['Execution seconds',number(summary.elapsed_execution_seconds)]]){const box=element('div',undefined,'metric');box.append(element('small',label),element('strong',text));metrics.append(box);}
  document.getElementById('campaign-phase').textContent=`Phase ${summary.phase||state} · ${summary.arm||'preparation / fixed controls'} · generation ${summary.generation??'—'} · ${summary.active_episodes||0} active episode slots. Completed counts advance after finalized chunks. Browser disconnection does not stop the worker.`;
  document.getElementById('publication-state').textContent=`Publication: ${publication.status||'PENDING'}${publication.commit_sha?' · '+publication.commit_sha:''}${summary.error?' · '+summary.error:''}`;
  // Show only the lifecycle actions that apply to the current state.
  document.getElementById('pause-campaign').hidden=!['QUEUED','PREPARING','RUNNING'].includes(state);document.getElementById('resume-campaign').hidden=!['PAUSED','INTERRUPTED'].includes(state);document.getElementById('stop-campaign').hidden=!['QUEUED','PREPARING','RUNNING','PAUSE_REQUESTED','PAUSED'].includes(state);
  document.querySelector('.campaign-bar .divider').hidden=['pause','resume','stop'].every(name=>document.getElementById(name+'-campaign').hidden);
  const report=document.getElementById('open-report');report.hidden=!summary.report_artifact_id;if(!report.hidden)report.href='/api/v1/artifacts/'+summary.report_artifact_id;
  const download=document.getElementById('download-export');download.hidden=summary.report_status!=='READY';download.href=`/api/v1/campaigns/${selectedId}/export`;
  await programs();
  if(!document.getElementById('tab-history').hidden)await history();
  if(!document.getElementById('tab-replays').hidden)replays();
}
async function openCampaign(identifier){
  selectedId=identifier;selectedProgram=null;programOffset=0;location.hash=identifier;view('detail');if(stream)stream.close();await refresh();
  stream=new EventSource(`/api/v1/campaigns/${identifier}/events`);
  let last=0n;
  stream.addEventListener('progress',event=>{const id=BigInt(event.lastEventId||'0');if(id<=last)return;last=id;if(!refreshTimer)refreshTimer=setTimeout(()=>{refreshTimer=null;refresh().catch(e=>fail(e.message));},700);});
  stream.addEventListener('reset',()=>{last=0n;refresh().catch(e=>fail(e.message));});
}
function create(){if(stream)stream.close();selectedId=null;location.hash='';view('create');plan();}
for(const name of ['pause','resume','stop'])document.getElementById(name+'-campaign').addEventListener('click',async()=>{try{await api(`/campaigns/${selectedId}/${name}`,{method:'POST'});await refresh();}catch(e){fail(e.message);}});
document.getElementById('new-campaign').addEventListener('click',create);document.getElementById('cancel-create').addEventListener('click',()=>{view('catalog');catalog();});document.getElementById('back-catalog').addEventListener('click',()=>{if(stream)stream.close();selectedId=null;location.hash='';view('catalog');catalog();});
document.getElementById('review-plan').addEventListener('click',()=>{try{plan();}catch(e){fail(e.message);}});
form.addEventListener('submit',async event=>{event.preventDefault();const button=document.getElementById('launch-campaign');button.disabled=true;try{const queued=await api('/campaigns',{method:'POST',body:plan()});await openCampaign(queued.id);}catch(e){fail(e.message);}finally{button.disabled=false;}});
document.getElementById('filter-catalog').addEventListener('click',()=>{catalogOffset=0;catalog().catch(e=>fail(e.message));});
for(const [id,change] of [['catalog-previous',-30],['catalog-next',30]])document.getElementById(id).addEventListener('click',()=>{catalogOffset=Math.max(0,catalogOffset+change);catalog();});
for(const [id,change] of [['program-previous',-50],['program-next',50]])document.getElementById(id).addEventListener('click',()=>{programOffset=Math.max(0,programOffset+change);programs();});
document.getElementById('live-curve-axis').addEventListener('change',()=>programs());
for(const button of document.querySelectorAll('[data-tab]'))button.addEventListener('click',async()=>{for(const tab of ['programs','history','replays'])document.getElementById('tab-'+tab).hidden=tab!==button.dataset.tab;for(const other of document.querySelectorAll('[data-tab]'))other.setAttribute('aria-selected',String(other===button));if(button.dataset.tab==='history')await history();if(button.dataset.tab==='replays')replays();});
document.getElementById('clone-program').addEventListener('click',()=>{fixedDraft=structuredClone(selectedProgram.program.authored);field('method').value='fixed';field('name').value=(fixedDraft.name||'Inspected strategy')+' evaluation';field('fixed_control').querySelector('[value=cloned]').disabled=false;field('fixed_control').value='cloned';field('legacy_control').checked=false;field('pulse_control').checked=false;create();});
field('fixed_control').addEventListener('change',()=>{fixedDraft=null;});
document.getElementById('clone-campaign').addEventListener('click',async()=>{try{const clone=await api(`/campaigns/${selectedId}/clone`,{method:'POST'});const draft=await api(`/campaigns/${clone.id}`);defaults=draft.spec;field('name').value=defaults.name;field('n').value=defaults.n;field('training_count').value=defaults.datasets.training.valid_count;field('holdout_count').value=defaults.datasets.holdout.valid_count;field('candidate_budget').value=defaults.search.candidate_budget_per_method;field('initial_pool').value=defaults.search.initial_pool;field('lambda').value=defaults.search.lambda;buildAdvanced();create();}catch(e){fail(e.message);}});
document.getElementById('login-form').addEventListener('submit',async event=>{event.preventDefault();try{const result=await api('/session',{method:'POST',body:{token:document.getElementById('access-token').value}});csrf=result.csrf_token;sessionStorage.setItem('asquerix-csrf',csrf);document.getElementById('access-token').value='';document.getElementById('login').hidden=true;await start();}catch(e){fail(e.message);}});
async function start(){capabilities=await api('/capabilities');defaults=capabilities.defaults;inventory=await api('/devices');buildAdvanced();field('device').replaceChildren();for(const device of inventory.items){const option=element('option',`${device.name} · ${device.uuid}`);option.value=device.device;field('device').append(option);}document.getElementById('device-summary').textContent=inventory.items.length?inventory.items.map(item=>item.name).join(', '):'No accessible CUDA GPU';document.getElementById('launch-campaign').disabled=!inventory.items.length;document.getElementById('resource-warning').textContent=inventory.items.map(item=>`${item.device}: ${item.memory_used_mib}/${item.memory_total_mib} MiB in use, ${item.utilization_percent}% device activity. ${item.warning}`).join(' ');const identifier=location.hash.slice(1);if(/^[a-f0-9]{32}$/.test(identifier))await openCampaign(identifier);else await catalog();}
start().catch(e=>fail(e.message));
