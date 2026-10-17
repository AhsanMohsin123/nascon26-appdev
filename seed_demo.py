import asyncio, asyncpg, json, hmac, hashlib
SALT="demo-salt-nascon26"
def sign(i,p): 
    msg=(i+"|"+json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False)).encode()
    return hmac.new(SALT.encode(),msg,hashlib.sha256).hexdigest()
async def main():
    c=await asyncpg.connect("postgresql://nascon:nascon_pass@localhost:5432/nascon_db")
    lid="league-alpha-1"
    teams=["Lions","Tigers","Eagles","Falcons"]
    # config with points+qual
    cfg={"league_id":lid,"sport_id":"football","teams":teams,"points":{"win":3,"draw":1,"loss":0},"qualification":{"spots":2},"lots_seed":42}
    await c.execute("UPDATE leagues SET config=$1, sport_id='football' WHERE id=$2", json.dumps(cfg), lid)
    for t in teams:
        await c.execute("INSERT INTO league_teams(league_id,team_id) VALUES($1,$2) ON CONFLICT DO NOTHING",lid,t)
    fixtures=[("am1","Lions","Tigers"),("am2","Eagles","Falcons"),("am3","Lions","Eagles"),("am4","Tigers","Falcons"),("am5","Lions","Falcons"),("am6","Tigers","Eagles")]
    for mid,h,a in fixtures:
        await c.execute("DELETE FROM match_events WHERE match_id=$1",mid)
        await c.execute("INSERT INTO matches(id,league_id,sport_id,home_team_id,away_team_id,status) VALUES($1,$2,'football',$3,$4,'upcoming') ON CONFLICT(id) DO UPDATE SET status='upcoming',home_team_id=$3,away_team_id=$4,league_id=$2",mid,lid,h,a)
    # play results
    async def ev(eid,mid,seq,typ,pl):
        await c.execute("INSERT INTO match_events(id,match_id,sequence,type,payload,signature) VALUES($1,$2,$3,$4,$5,$6)",eid,mid,seq,typ,json.dumps(pl),sign(eid,pl))
    results={"am1":("Lions",3,"Tigers",1),"am2":("Eagles",2,"Falcons",2),"am3":("Lions",1,"Eagles",0),"am4":("Tigers",2,"Falcons",0)}
    for mid,(h,hs,a,as_) in results.items():
        seq=1; await ev(f"{mid}-s",mid,seq,"match_start",{}); seq+=1
        for _ in range(hs): await ev(f"{mid}-h{seq}",mid,seq,"score",{"team_id":h,"event_type":"goal"}); seq+=1
        for _ in range(as_): await ev(f"{mid}-a{seq}",mid,seq,"score",{"team_id":a,"event_type":"goal"}); seq+=1
        await ev(f"{mid}-e",mid,seq,"match_end",{})
        await c.execute("UPDATE matches SET status='completed' WHERE id=$1",mid)
    # am5, am6 in-progress for live demo
    await ev("am5-s","am5",1,"match_start",{}); await ev("am5-g","am5",2,"score",{"team_id":"Lions","event_type":"goal"})
    await c.execute("UPDATE matches SET status='in_progress' WHERE id='am5'")
    await c.close(); print("SEEDED league-alpha-1")
asyncio.run(main())
