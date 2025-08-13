import os, json
import pandas as pd

os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY','sk-test123')

import llm_client, services
from services import KeywordService, generate_brief_with_variant
from scoring import add_scores
from eval_logger import log_eval, LOG_PATH
from eval_utils import load_evals_df

def fake_generate_keywords_raw(self, prompt: str):
    if 'content_brief' in prompt.lower():
        return '{"title":"Ergonomic Chair Buying Guide","outline":["Intro","Top 5 Features","FAQ"],"sections":{"Intro":"Intro text","Top 5 Features":["Lumbar support","Adjustable height"],"FAQ":["What is ergonomic?" ]}}'
    return "Here you go:\n" + json.dumps({
        "informational":["how to choose ergonomic chair","benefits ergonomic seating"],
        "transactional":["buy ergonomic chair online","best ergonomic chair under 200"],
        "branded":["brandx ergonomic pro"]
    }) + "\nThanks"

llm_client.KeywordLLMClient.generate_keywords_raw = fake_generate_keywords_raw

svc = KeywordService(llm_client.KeywordLLMClient.create_default())
kw = svc.generate_keywords("Online office furniture store", industry="Furniture", audience="Remote workers", location="US")
print('Parsed keyword categories:', {k: len(v) for k,v in kw.items()})
rows=[]
for cat,kws in kw.items():
    for k in kws:
        rows.append({'keyword':k,'category':cat})
df = pd.DataFrame(rows)
scored = add_scores(df, intent_col='category', kw_col='keyword')
print('Top scored rows:')
print(scored.sort_values('priority').head(3)[['priority','keyword','opportunity']].to_string(index=False))

brief_output, prompt_used, latency_ms, usage = generate_brief_with_variant(keyword='ergonomic chair for back pain', variant='A')
print('Brief chars:', len(brief_output), 'Latency ms:', round(latency_ms,1))

log_eval(variant='A', keyword='ergonomic chair for back pain', prompt=prompt_used, output=brief_output, latency_ms=latency_ms,
         tokens_prompt=None, tokens_completion=None, user_rating=5, user_notes='Looks good', extra={'app_version':'beta-mvp','auto_flags':['test-flag'],'is_json':True})
print('Logged evaluation line to', LOG_PATH)

ede = load_evals_df()
print('Loaded eval rows:', len(ede))
print('Variant A avg rating:', round(ede[ede.variant=='A'].user_rating.mean(),2))
print('Most recent auto_flags:', ede.iloc[0].get('auto_flags'))
print('Manual smoke test complete.')
