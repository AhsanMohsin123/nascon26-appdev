import asyncio, asyncpg, json, hmac, hashlib
SALT="demo-salt-nascon26"
def sign(i,p): 
    msg=(i+"|"+json.dumps(p,sort_keys=True,separators=(",",":"),ensure_ascii=False)).encode()
    return hmac.new(SALT.encode(),msg,hashlib.sha256).hexdigest()
async def main():
    c=await asyncpg.connect("postgresql://nascon:nascon_pass@localhost:5432/nascon_db")
    async def ev(eid,mid,seq,typ,pl):
        await c.execute("INSERT INTO match_events(id,match_id,sequence,type,payload,signature) VALUES($1,$2,$3,$4,$5,$6) ON CONFLICT(id) DO NOTHING",eid,mid,seq,typ,json.dumps(pl),sign(eid,pl))
    async def league(lid,sport,teams,fixtures,results,event_name):
        cfg={"league_id":lid,"sport_id":sport,"teams":teams,"points":{"win":3,"draw":1,"loss":0},"qualification":{"spots":2},"lots_seed":42}
        await c.execute("DELETE FROM leagues WHERE id=$1",lid)
        await c.execute("INSERT INTO leagues(id,tenant_id,sport_id,config) VALUES($1,'tenant-alpha',$2,$3)",lid,sport,json.dumps(cfg))
        await c.execute("DELETE FROM league_teams WHERE league_id=$1",lid)
        for t in teams: await c.execute("INSERT INTO league_teams(league_id,team_id) VALUES($1,$2)",lid,t)
        for mid,h,a in fixtures:
            await c.execute("DELETE FROM match_events WHERE match_id=$1",mid)
            await c.execute("INSERT INTO matches(id,league_id,sport_id,home_team_id,away_team_id,status) VALUES($1,$2,$3,$4,$5,'upcoming') ON CONFLICT(id) DO UPDATE SET status='upcoming',league_id=$2,sport_id=$3,home_team_id=$4,away_team_id=$5",mid,lid,sport,h,a)
        for mid,(h,hs,a,as_) in results.items():
            seq=1; await ev(f"{mid}-s",mid,seq,"match_start",{}); seq+=1
            for _ in range(hs): await ev(f"{mid}-h{seq}",mid,seq,"score",{"team_id":h,"event_type":event_name}); seq+=1
            for _ in range(as_): await ev(f"{mid}-a{seq}",mid,seq,"score",{"team_id":a,"event_type":event_name}); seq+=1
            await ev(f"{mid}-e",mid,seq,"match_end",{})
            await c.execute("UPDATE matches SET status='completed' WHERE id=$1",mid)
    # Basketball
    await league("basketball-league","basketball",["Hawks","Bulls","Heat","Jazz"],
        [("bb1","Hawks","Bulls"),("bb2","Heat","Jazz"),("bb3","Hawks","Heat"),("bb4","Bulls","Jazz")],
        {"bb1":("Hawks",88,"Bulls",76),"bb2":("Heat",91,"Jazz",91),"bb3":("Hawks",79,"Heat",70)},"two_pointer")
    # Cricket
    await league("cricket-league","cricket",["Kings","Royals","Giants","Stars"],
        [("ck1","Kings","Royals"),("ck2","Giants","Stars"),("ck3","Kings","Giants")],
        {"ck1":("Kings",45,"Royals",30),"ck2":("Giants",22,"Stars",22)},"single")
    await c.close(); print("SEEDED basketball-league + cricket-league")
asyncio.run(main())
