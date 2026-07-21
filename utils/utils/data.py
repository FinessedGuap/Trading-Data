import requests
import pandas as pd
import streamlit as st
from datetime import datetime
import json


def get_headers(notion_token):
    return {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


@st.cache_data(ttl=300)
def get_all_trades(notion_token, database_id):
    headers = get_headers(notion_token)
    all_results = []
    has_more = True
    start_cursor = None
    try:
        while has_more:
            payload = {}
            if start_cursor:
                payload["start_cursor"] = start_cursor
            r = requests.post(
               f"https://api.notion.com/v1/databases/{database_id}/query",
                headers=headers, json=payload, timeout=10
            )
            data = r.json()
            if r.status_code == 401:
                raise Exception("Invalid Notion token — check your NOTION_TOKEN secret")
            if r.status_code == 404:
                raise Exception("Database not found — check your DATABASE_ID secret")
            if r.status_code != 200:
                raise Exception(f"Notion API error {r.status_code}")
            all_results.extend(data['results'])
            has_more = data['has_more']
            start_cursor = data.get('next_cursor')
        return all_results
    except requests.exceptions.Timeout:
        raise Exception("Notion connection timed out — check your internet connection")
    except requests.exceptions.ConnectionError:
        raise Exception("Can't reach Notion — check your internet connection")


def extract_property(prop):
    if prop is None:
        return None
    pt = prop['type']
    if pt == 'title': return prop['title'][0]['plain_text'] if prop['title'] else None
    elif pt == 'rich_text': return prop['rich_text'][0]['plain_text'] if prop['rich_text'] else None
    elif pt == 'number': return prop['number']
    elif pt == 'select': return prop['select']['name'] if prop['select'] else None
    elif pt == 'multi_select': return [x['name'] for x in prop['multi_select']]
    elif pt == 'date': return prop['date']['start'] if prop['date'] else None
    elif pt == 'checkbox': return prop['checkbox']
    elif pt == 'formula': f = prop['formula']; return f.get(f['type'])
    elif pt == 'status': return prop['status']['name'] if prop['status'] else None
    else: return str(prop.get(pt, ''))


def extract_str(prop):
    val = extract_property(prop)
    return ', '.join(val) if isinstance(val, list) else val


def parse_r(value):
    if value is None or str(value).strip() in ['', 'nan']:
        return None
    try:
        return float(str(value).strip().upper().replace('RR', '').replace('+', '').strip())
    except:
        return None


def parse_date(x):
    if pd.isna(x) or x is None or str(x).strip() == '':
        return pd.NaT
    try:
        from dateutil import parser as _p
        ts = pd.Timestamp(_p.isoparse(str(x)))
        return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
    except:
        try:
            from dateutil import parser as _p
            ts = pd.Timestamp(_p.parse(str(x)))
            return ts.tz_convert('Australia/Sydney').tz_localize(None) if ts.tzinfo else ts
        except:
            return pd.NaT


@st.cache_data(ttl=300)
def load_and_process(notion_token, database_id):
    try:
        raw = get_all_trades(notion_token, database_id)
        if not raw:
            return pd.DataFrame(), "empty"
        rows = []
        for trade in raw:
            props = trade['properties']
            row = {}
            for cn, cd in props.items():
                if cn == 'Entry Confluences':
                    val = extract_property(cd)
                    row[cn] = ', '.join(val) if isinstance(val, list) else val
                else:
                    row[cn] = extract_str(cd)
            rows.append(row)
        df = pd.DataFrame(rows)
        df.columns = df.columns.str.strip()
        df['Date'] = df['Date'].apply(parse_date)
        df['Date'] = pd.Series(df['Date'].tolist(), dtype='datetime64[ns]')
        df['R_Result'] = df['R Result'].apply(parse_r)
        if 'Time of Trade' in df.columns:
            def ph(t):
                try:
                    t = str(t).strip()
                    if ':' in t:
                        h = int(t.split(':')[0])
                        if 'PM' in t.upper() and h != 12: h += 12
                        if 'AM' in t.upper() and h == 12: h = 0
                        return f"{h:02d}:00"
                except:
                    pass
                return None
            df['Hour'] = df['Time of Trade'].apply(ph)
        df = df.sort_values('Date').reset_index(drop=True)
        if 'Pair' in df.columns:
            df['Pair'] = df['Pair'].str.strip()
        return df, "ok"
    except Exception as e:
        return pd.DataFrame(), f"error:{str(e)}"
        

def save_coach_memory(headers, page_id, profile, character):
    try:
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers
        )
        if response.status_code == 200:
            blocks = response.json().get('results', [])
            for block in blocks:
                requests.delete(
                    f"https://api.notion.com/v1/blocks/{block['id']}",
                    headers=headers
                )
        memory = {
            'profile': profile,
            'character': character,
            'updated': datetime.now().isoformat()
        }
        requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers,
            json={"children": [{
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [{"type": "text", "text": {"content": json.dumps(memory)}}],
                    "language": "json"
                }
            }]}
        )
        return True
    except:
        return False


def load_coach_memory(headers, page_id):
    try:
        response = requests.get(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=headers
        )
        if response.status_code != 200:
            return None, None
        blocks = response.json().get('results', [])
        for block in blocks:
            if block['type'] == 'code':
                text = block['code']['rich_text'][0]['text']['content']
                memory = json.loads(text)
                return memory.get('profile'), memory.get('character')
        return None, None
    except:
        return None, None
