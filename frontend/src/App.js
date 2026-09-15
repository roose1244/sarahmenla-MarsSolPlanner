import React, { useEffect, useState } from 'react';

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const SCENE_URL = `${BACKEND}/api/mars/plan_three.html`;

export default function App(){
  const [regen, setRegen] = useState(false);
  const [status, setStatus] = useState('READY');
  const [key, setKey] = useState(0);

  useEffect(()=>{
    fetch(`${BACKEND}/api/health`).then(r=>r.json())
      .then(()=>setStatus('ONLINE')).catch(()=>setStatus('OFFLINE'));
  },[]);

  const regenerate = async () => {
    setRegen(true); setStatus('REGENERATING…');
    try {
      const r = await fetch(`${BACKEND}/api/regenerate`, {method:'POST'});
      if (!r.ok) throw new Error(await r.text());
      setStatus('ONLINE'); setKey(k=>k+1);
    } catch(e){ setStatus('ERR: ' + e.message.slice(0,40)); }
    setRegen(false);
  };

  return (
    <div style={styles.page} data-testid="mars-app">
      <header style={styles.header}>
        <div>
          <div style={styles.brand}>■ SOL-WINDOW PLANNER</div>
          <div style={styles.tagline}>MARS ROUTE FINDER · HIGH-TECH TERRAIN VIEW</div>
        </div>
        <div style={styles.right}>
          <span style={{...styles.pill, borderColor: status==='ONLINE'?'#5ff0a2':'#ff9b83',
                        color: status==='ONLINE'?'#5ff0a2':'#ff9b83'}} data-testid="status-pill">
            ● {status}
          </span>
          <button onClick={regenerate} disabled={regen} style={styles.btn}
                  data-testid="regenerate-btn">
            {regen ? '↻ RUNNING…' : '↻ RE-PLAN'}
          </button>
          <a href={SCENE_URL} target="_blank" rel="noreferrer" style={styles.btn}
             data-testid="open-tab-btn">↗ OPEN TAB</a>
        </div>
      </header>
      <iframe key={key} src={SCENE_URL} title="Sol-Window Scene"
              style={styles.frame} data-testid="scene-iframe" />
    </div>
  );
}

const styles = {
  page:{position:'fixed',inset:0,background:'#050308',color:'#f4e4c8',
        display:'flex',flexDirection:'column',fontFamily:'Space Grotesk,system-ui'},
  header:{display:'flex',justifyContent:'space-between',alignItems:'center',
          padding:'12px 20px',borderBottom:'1px solid #8a3a1e',
          background:'linear-gradient(180deg,#0a0710,#050308)',flexShrink:0},
  brand:{fontFamily:'JetBrains Mono,monospace',fontSize:12,fontWeight:700,
         color:'#ff8a2c',letterSpacing:'0.24em'},
  tagline:{fontFamily:'JetBrains Mono,monospace',fontSize:9,color:'#c9a37c',
           letterSpacing:'0.16em',textTransform:'uppercase',marginTop:3},
  right:{display:'flex',gap:12,alignItems:'center'},
  pill:{fontFamily:'JetBrains Mono,monospace',fontSize:9,fontWeight:700,
        letterSpacing:'0.14em',padding:'5px 10px',border:'1px solid'},
  btn:{background:'transparent',color:'#ff8a2c',border:'1px solid #ff7a3a',
       padding:'7px 14px',fontSize:10,cursor:'pointer',fontWeight:700,
       letterSpacing:'0.14em',textTransform:'uppercase',
       fontFamily:'JetBrains Mono,monospace',textDecoration:'none'},
  frame:{flex:1,width:'100%',border:'none',background:'#050308'},
};
