from bta.ai import providers as p

def test_no_keys_degrade(monkeypatch):
    monkeypatch.setattr(p,'providers',lambda: [])
    r=p.complete('CRITIC',{'source_url':'https://example.com'},'Find errors')
    assert r.status=='UNAVAILABLE' and not r.provider

def test_fallback_after_provider_quota(monkeypatch):
    monkeypatch.setattr(p,'providers',lambda: [('groq','x','a'),('gemini','x','b'),('cloudflare','x','c')])
    p.COOLDOWN.clear()
    calls=[]
    def fake(name,*args):
        calls.append(name)
        if name=='groq': raise ValueError('quota exceeded')
        return 'Supported evidence only. More research is needed.'
    monkeypatch.setattr(p,'_request',fake)
    result=p.complete('ROLE',{'verified':False},'Critique selection')
    assert result.status=='COMPLETE' and result.provider=='gemini' and calls==['groq','gemini']
    assert result.attempted==('groq','gemini')

def test_private_material_never_sent(monkeypatch):
    monkeypatch.setattr(p,'providers',lambda:[('groq','m','k')])
    r=p.complete('CHAT',{'memo':'private@email.com'},'hello')
    assert r.status=='BLOCKED'
