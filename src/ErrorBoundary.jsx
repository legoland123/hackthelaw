import React from "react";
export default class ErrorBoundary extends React.Component {
  constructor(p){ super(p); this.state = { hasError:false, err:null }; }
  static getDerivedStateFromError(err){ return { hasError:true, err }; }
  componentDidCatch(err, info){ console.error("App crash:", err, info); }
  render(){
    if(this.state.hasError){
      return (
        <div style={{padding:20,color:"#fff",background:"#3b0e3e"}}>
          <h2>Something broke rendering this page.</h2>
          <pre style={{whiteSpace:"pre-wrap"}}>{String(this.state.err)}</pre>
        </div>
      );
    }
    return this.props.children;
  }
}
