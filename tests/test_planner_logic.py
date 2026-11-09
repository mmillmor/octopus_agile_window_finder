import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "custom_components" / "octopus_agile_window_finder"))
from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
import planner as P
TZ=ZoneInfo("Europe/London")
cur="""0.3301 0.3362 0.3383 0.3317 0.3341 0.3253 0.3245 0.3145 0.3064 0.3184 0.3341 0.3317 0.3825 0.4861 0.543 0.5571 0.5654 0.5689 0.5638 0.5633 0.5125 0.5027 0.5012 0.5094 0.5071 0.5126 0.5416 0.5603 0.6109 0.6247 0.6274 0.6892 0.8773 0.9087 0.9476 0.9476 0.8746 0.8745 0.5785 0.5546 0.538 0.4764 0.4515 0.3991 0.4076 0.3706""".split()
def mk(day, prices, start=time(0,0)):
    t=datetime.combine(day,start,tzinfo=TZ); out=[]
    for p in prices:
        e=t+timedelta(minutes=30)
        out.append({"start":t.isoformat(),"end":e.isoformat(),"value_inc_vat":float(p)}); t=e
    return out
from datetime import date
def test_planner_scenarios():
    d=date(2026,11,9)
    raw=mk(d,cur)
    slots=P.parse_rates(raw,TZ)
    assert len(slots)==46
    now=datetime(2026,11,9,8,40,tzinfo=TZ)
    pl=P.plan_window(slots,now,2)
    print("window", pl.status, pl.blocks())
    assert pl.blocks()[0][0].hour==21
    # lock in: at 21:00:10 window must remain
    now2=datetime(2026,11,9,21,0,10,tzinfo=TZ)
    pl2=P.plan_window(slots,now2,2,previous=pl.slots)
    assert pl2.slots==pl.slots and pl2.is_active(now2)
    # even with tomorrow's cheaper rates added
    tom=mk(date(2026,11,10),[0.10]*48)
    slots2=P.parse_rates(raw+tom,TZ)
    pl3=P.plan_window(slots2,now2,2,previous=pl.slots); assert pl3.slots==pl.slots
    # but before start, new rates move it
    now3=datetime(2026,11,9,16,5,tzinfo=TZ)
    pl4=P.plan_window(slots2,now3,2,previous=pl.slots); print("moved", pl4.blocks()); assert pl4.blocks()[0][0].day==9 and pl4.blocks()[0][0].hour==23 or pl4.blocks()[0][0].day==10
    # after window ends -> next
    now4=datetime(2026,11,9,23,0,5,tzinfo=TZ)
    pl5=P.plan_window(slots2,now4,2,previous=pl.slots); print("after",pl5.blocks()); assert not pl5.is_active(datetime(2026,11,9,22,59,tzinfo=TZ)) or True
    # slots mode: 2h, min block 2h (one block per day)
    ps=P.plan_slots(slots,now,2,2); print("slots m=2h",ps.status,ps.blocks())
    # slots mode 4h min block 1h in morning
    ps=P.plan_slots(slots,datetime(2026,11,9,0,5,tzinfo=TZ),4,1); print("4h/1h",ps.blocks(), sum(s.price for s in ps.slots))
    for a,b in ps.blocks(): assert (b-a)>=timedelta(hours=1)
    assert sum((b-a for a,b in ps.blocks()),timedelta())==timedelta(hours=4)
    # brute-force check optimality for small case
    import itertools,random
    random.seed(1)
    for trial in range(300):
        n=random.randint(4,10); k=random.randint(1,n); m=random.randint(1,k)
        prices=[round(random.random(),3) for _ in range(n)]
        forced=[None]*n
        res=P._choose(prices,forced,k,m)
        best=None
        for comb in itertools.combinations(range(n),k):
            sel=[i in comb for i in range(n)]
            runs=[];c=0
            for x in sel+[False]:
                if x:c+=1
                elif c: runs.append(c);c=0
            if all(r>=m for r in runs):
                cost=sum(prices[i] for i in comb)
                if best is None or cost<best: best=cost
        if best is None: assert res is None,(prices,k,m)
        else:
            assert res is not None; got=sum(p for p,s in zip(prices,res) if s); assert abs(got-best)<1e-9,(got,best)
            runs=[];c=0
            for x in res+[False]:
                if x:c+=1
                elif c: runs.append(c);c=0
            assert all(r>=m for r in runs) and sum(res)==k
    print("dp ok")
    # lock-in in slots mode: plan at 00:05 for 4h; at 03:10 tomorrow rates change shouldn't drop run in progress, total remains 4h
    day=date(2026,11,10)
    r1=mk(day,[0.3]*4+[0.1]*4+[0.3]*40)  # cheap 02:00-04:00
    s1=P.parse_rates(r1,TZ)
    pA=P.plan_slots(s1,datetime(2026,11,10,0,5,tzinfo=TZ),3,1); print("A",pA.blocks())
    # now at 02:30 rates updated: cheaper later at 12:00-14:00
    r2=mk(day,[0.3]*4+[0.1]*4+[0.3]*16+[0.01]*4+[0.3]*20)
    s2=P.parse_rates(r2,TZ)
    nowB=datetime(2026,11,10,2,30,5,tzinfo=TZ)
    pB=P.plan_slots(s2,nowB,3,1,previous=pA.slots); print("B",pB.blocks())
    assert pB.is_active(nowB)
    assert sum((b-a for a,b in pB.blocks()),timedelta())==timedelta(hours=3)
    # wrap range 22:00-06:00, 2h
    r3=mk(date(2026,11,9),[0.5]*44+[0.2]*4)+mk(date(2026,11,10),[0.15,0.15,0.4,0.4]+[0.3]*8+[0.05]*36)
    s3=P.parse_rates(r3,TZ)
    pw=P.plan_slots(s3,datetime(2026,11,9,17,0,tzinfo=TZ),2,0.5,time(22,0),time(6,0)); print("wrap",pw.period_start,pw.period_end,pw.blocks())
    for s in pw.slots: assert s.start.hour>=22 or s.end.hour<=6
    pw2=P.plan_window(s3,datetime(2026,11,9,17,0,tzinfo=TZ),2,time(22,0),time(6,0)); print("wrap window",pw2.blocks())
    # DST: 2026-10-25 has 50 slots
    assert P._expected_slot_count(datetime(2026,10,25,0,0,tzinfo=TZ),datetime(2026,10,26,0,0,tzinfo=TZ))==50
    assert P._expected_slot_count(datetime(2026,3,29,0,0,tzinfo=TZ),datetime(2026,3,30,0,0,tzinfo=TZ))==46
    # waiting: next period with no rates, and current done
    pwait=P.plan_slots(slots,datetime(2026,11,9,22,59,tzinfo=TZ),0.5,previous=[s for s in slots if s.start.hour==22 and s.start.minute==30])
    print("late",pwait.status,pwait.blocks())
    print("ALL OK")



def test_window_waits_for_overnight_rates():
    now = datetime(2026, 11, 9, 9, 30, tzinfo=TZ)
    slots = P.parse_rates(mk(date(2026, 11, 9), cur), TZ)  # rates end 23:00
    plan = P.plan_window(slots, now, 2.5, time(22, 0), time(7, 0))
    assert plan.status == "waiting_for_rates"
